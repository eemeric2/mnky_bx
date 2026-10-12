# mnky_bx/hardware/arduino/arduino_uno_controller.py
"""
Unified Arduino Uno controller for buttons + reward
Handles both input (buttons) and output (reward motor) on single device
"""

import threading
import time
import queue
from typing import Optional, Callable, Dict, List
from datetime import datetime
import logging

from .protocol import ArduinoProtocol
from .commands import (
    ButtonID, LEDCommand, RewardCommand,
    ArduinoCommand, ArduinoResponse, RESPONSE_PARSE_MAP
)

logger = logging.getLogger(__name__)


class ArduinoUnoController:
    """
    Controls single Arduino Uno for both buttons and reward

    Architecture:
    - Serial protocol for communication
    - Button reading thread (continuous monitoring)
    - LED control for feedback
    - Motor control for reward delivery
    - Health monitoring and error handling
    """

    def __init__(self, port: str, config: Dict):
        """
        Initialize Arduino Uno controller

        Args:
            port: Serial port (e.g., 'COM4')
            config: Configuration dict with:
                - baud_rate: Serial speed (default 115200)
                - max_reward_position: Max motor extension
                - reward_pulse_duration_ms: How long to hold motor
        """
        self.port = port
        self.config = config

        # Communication
        self.protocol = ArduinoProtocol(port, config.get('baud_rate', 115200))
        self.is_connected = False

        # Button monitoring
        self.button_reading_active = False
        self.button_reading_thread = None
        self.button_pressed = None  # 'left', 'right', or None
        self.button_callback = None  # Optional callback on button press

        # LED state
        self.led_state = {}  # {'left': bool, 'right': bool}

        # Reward/motor control
        self.motor_position = 0
        self.max_motor_position = config.get('max_reward_position', 10)
        self.reward_pulse_duration_ms = config.get('reward_pulse_duration_ms', 500)

        # Statistics
        self.button_press_count = {'left': 0, 'right': 0}
        self.reward_delivery_count = 0
        self.error_count = 0

    def connect(self) -> bool:
        """
        Establish connection to Arduino

        Returns:
            True if successful
        """
        try:
            if self.protocol.connect():
                self.is_connected = True

                # Initialize motor position
                if not self._home_motor():
                    logger.warning("Motor homing failed")

                # Start button reading thread
                self._start_button_reading()

                logger.info("Arduino Uno controller initialized successfully")
                return True

            else:
                logger.error("Failed to connect to Arduino")
                return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Arduino"""
        self._stop_button_reading()
        self.protocol.disconnect()
        self.is_connected = False

    # ============ BUTTON CONTROL ============

    def _start_button_reading(self) -> None:
        """Start background thread for button monitoring"""
        if self.button_reading_active:
            return

        self.button_reading_active = True
        self.button_reading_thread = threading.Thread(
            target=self._button_reading_loop,
            daemon=True
        )
        self.button_reading_thread.start()
        logger.info("Button reading thread started")

    def _stop_button_reading(self) -> None:
        """Stop button monitoring thread"""
        self.button_reading_active = False

        if self.button_reading_thread:
            self.button_reading_thread.join(timeout=2.0)
            logger.info("Button reading thread stopped")

    def _button_reading_loop(self) -> None:
        """
        Continuous loop: read button presses from Arduino
        Runs in separate thread
        """
        while self.button_reading_active and self.is_connected:
            try:
                # Check for incoming data (non-blocking)
                if self.protocol.serial_connection.in_waiting > 0:
                    data = self.protocol.serial_connection.readline().decode('utf-8').strip()

                    # Parse button press
                    if data == ButtonID.LEFT.value:
                        self.button_pressed = "left"
                        self.button_press_count['left'] += 1
                        logger.debug("LEFT button pressed")

                        if self.button_callback:
                            self.button_callback("left")

                    elif data == ButtonID.RIGHT.value:
                        self.button_pressed = "right"
                        self.button_press_count['right'] += 1
                        logger.debug("RIGHT button pressed")

                        if self.button_callback:
                            self.button_callback("right")

                time.sleep(0.01)  # Small delay to prevent CPU spinning

            except Exception as e:
                logger.error(f"Button reading error: {e}")
                self.error_count += 1

    def set_button_callback(self, callback: Callable) -> None:
        """
        Set callback function called when button is pressed

        Args:
            callback: Function(button_id: str) called with 'left' or 'right'
        """
        self.button_callback = callback

    def get_button_press(self) -> Optional[str]:
        """
        Get last button pressed (non-blocking)

        Returns:
            'left', 'right', or None
        """
        button = self.button_pressed
        self.button_pressed = None  # Clear after reading
        return button

    # ============ LED CONTROL ============

    def set_led(self, button_id: str, state: bool) -> bool:
        """
        Control LED on button

        Args:
            button_id: 'left' or 'right'
            state: True (on) or False (off)

        Returns:
            True if successful
        """
        if not self.is_connected:
            logger.warning("Arduino not connected")
            return False

        try:
            if button_id == 'left':
                command = LEDCommand.LEFT_ON.value if state else LEDCommand.ALL_OFF.value
            elif button_id == 'right':
                command = LEDCommand.RIGHT_ON.value if state else LEDCommand.ALL_OFF.value
            else:
                logger.error(f"Unknown button ID: {button_id}")
                return False

            success = self.protocol.send_command_with_retry(command + '\n')

            if success:
                self.led_state[button_id] = state
                logger.debug(f"LED {button_id} {'ON' if state else 'OFF'}")

            return success

        except Exception as e:
            logger.error(f"LED control error: {e}")
            self.error_count += 1
            return False

    def set_all_leds(self, state: bool) -> bool:
        """
        Control all LEDs simultaneously

        Args:
            state: True (on) or False (off)

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            command = LEDCommand.BOTH_ON.value if state else LEDCommand.ALL_OFF.value
            success = self.protocol.send_command_with_retry(command + '\n')

            if success:
                self.led_state = {'left': state, 'right': state}

            return success

        except Exception as e:
            logger.error(f"All LEDs control error: {e}")
            return False

    # ============ REWARD/MOTOR CONTROL ============

    def _home_motor(self) -> bool:
        """
        Move motor to home position (0)

        Returns:
            True if successful
        """
        try:
            # Set home position
            success = self.protocol.send_command_with_retry(
                RewardCommand.MOTOR_HOME.value,
                expected_response="ok"
            )

            if success:
                self.motor_position = 0
                logger.info("Motor homed successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Motor homing error: {e}")
            return False

    def deliver_reward(self, amount: int = 1, hold_time_ms: Optional[int] = None) -> bool:
        """
        Deliver reward (juice/food)

        Args:
            amount: Amount of reward (1-10, mapped to motor distance)
            hold_time_ms: How long to hold (default from config)

        Returns:
            True if successful
        """
        if not self.is_connected:
            logger.warning("Arduino not connected")
            return False

        if hold_time_ms is None:
            hold_time_ms = self.reward_pulse_duration_ms

        try:
            # Clamp amount to valid range
            amount = max(1, min(amount, self.max_motor_position))

            # Calculate motor position
            motor_distance = amount  # Simple 1:1 mapping

            # Send motor forward command
            logger.info(f"Delivering reward: amount={amount}, distance={motor_distance}mm")

            command = f"G0 X{motor_distance}\n"
            success = self.protocol.send_command_with_retry(command, expected_response="ok")

            if success:
                self.motor_position = motor_distance
                self.reward_delivery_count += 1

                # Hold for specified duration
                time.sleep(hold_time_ms / 1000.0)

                # Return to home
                self._home_motor()

            return success

        except Exception as e:
            logger.error(f"Reward delivery error: {e}")
            self.error_count += 1
            return False

    def get_motor_position(self) -> int:
        """Get current motor position"""
        return self.motor_position

    # ============ STATISTICS & HEALTH ============

    def get_statistics(self) -> Dict:
        """Get usage statistics"""
        return {
            'is_connected': self.is_connected,
            'button_presses': self.button_press_count.copy(),
            'reward_deliveries': self.reward_delivery_count,
            'errors': self.error_count,
            'motor_position': self.motor_position
        }

    def health_check(self) -> Dict:
        """
        Perform health check on Arduino connection

        Returns:
            {
                'connected': bool,
                'buttons_responsive': bool,
                'motor_responsive': bool,
                'led_responsive': bool,
                'last_error': str or None
            }
        """
        health = {
            'connected': self.is_connected,
            'buttons_responsive': False,
            'motor_responsive': False,
            'led_responsive': False,
            'last_error': None
        }

        if not self.is_connected:
            health['last_error'] = "Not connected"
            return health

        try:
            # Test LED control
            if self.set_led('left', True):
                health['led_responsive'] = True
                self.set_led('left', False)

            # Test motor homing
            if self._home_motor():
                health['motor_responsive'] = True

            # Buttons are monitored continuously
            health['buttons_responsive'] = self.button_reading_active

        except Exception as e:
            health['last_error'] = str(e)

        return health