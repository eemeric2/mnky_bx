# mnky_bx/hardware/arduino/reward_only_controller.py
"""
Minimal Arduino controller for reward delivery only
Used when buttons are handled by input system
"""

import time
import logging
from typing import Dict, Optional

from .protocol import ArduinoProtocol
from .commands import RewardCommand

logger = logging.getLogger(__name__)


class RewardOnlyController:
    """
    Simplified Arduino controller for reward delivery only
    Buttons are handled by input system (keyboard/touchscreen)
    """

    def __init__(self, port: str, config: Dict):
        """
        Initialize reward controller

        Args:
            port: Serial port
            config: Configuration dict
        """
        self.port = port
        self.config = config
        self.protocol = ArduinoProtocol(port, config.get('baud_rate', 115200))
        self.is_connected = False

        # Reward tracking
        self.motor_position = 0
        self.max_motor_position = config.get('max_reward_position', 10)
        self.reward_pulse_duration_ms = config.get('reward_pulse_duration_ms', 500)
        self.reward_delivery_count = 0

    def connect(self) -> bool:
        """Connect to Arduino"""
        try:
            if self.protocol.connect():
                self.is_connected = True

                # Home motor
                if self._home_motor():
                    logger.info("Reward controller initialized")
                    return True

            return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Arduino"""
        self.protocol.disconnect()
        self.is_connected = False

    def _home_motor(self) -> bool:
        """Move motor to home position"""
        try:
            success = self.protocol.send_command_with_retry(
                RewardCommand.MOTOR_HOME.value,
                expected_response="ok"
            )

            if success:
                self.motor_position = 0
                logger.info("Motor homed")

            return success

        except Exception as e:
            logger.error(f"Homing error: {e}")
            return False

    def deliver_reward(self, amount: int = 1, hold_time_ms: Optional[int] = None) -> bool:
        """
        Deliver reward

        Args:
            amount: Reward amount (1-10)
            hold_time_ms: How long to hold

        Returns:
            True if successful
        """
        if not self.is_connected:
            logger.warning("Not connected")
            return False

        if hold_time_ms is None:
            hold_time_ms = self.reward_pulse_duration_ms

        try:
            amount = max(1, min(amount, self.max_motor_position))

            logger.info(f"Delivering reward: {amount}")

            command = f"G0 X{amount}\n"
            success = self.protocol.send_command_with_retry(command, expected_response="ok")

            if success:
                self.motor_position = amount
                self.reward_delivery_count += 1

                # Hold
                time.sleep(hold_time_ms / 1000.0)

                # Home
                self._home_motor()

            return success

        except Exception as e:
            logger.error(f"Reward delivery error: {e}")
            return False

    def get_statistics(self) -> Dict:
        """Get statistics"""
        return {
            'is_connected': self.is_connected,
            'reward_deliveries': self.reward_delivery_count,
            'motor_position': self.motor_position
        }