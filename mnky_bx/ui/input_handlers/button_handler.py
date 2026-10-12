# mnky_bx/ui/input_handlers/button_handler.py
"""
Physical button input handler (via Arduino)
"""

from typing import Optional, Dict
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class ButtonHandler:
    """Handles physical button input from Arduino"""

    def __init__(self, config: Dict):
        """
        Initialize button handler

        Args:
            config: Arduino configuration dict
        """
        self.config = config
        self.arduino_controller = None
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to Arduino for button input

        Returns:
            True if successful
        """
        try:
            # Import here to avoid circular dependency
            from mnky_bx.hardware.arduino.arduino_uno_controller import ArduinoUnoController

            port = self.config.get('port', 'COM4')
            self.arduino_controller = ArduinoUnoController(port, self.config)

            if self.arduino_controller.connect():
                self.connected = True
                logger.info(f"Button handler connected to {port}")
                return True

            return False

        except Exception as e:
            logger.error(f"Button handler connection error: {e}")
            return False

    def get_input(self) -> Optional['InputData']:
        """
        Get button input (non-blocking)

        Returns:
            InputData or None
        """
        if not self.connected or not self.arduino_controller:
            return None

        from mnky_bx.ui.input_system import InputData, InputType, InputEvent

        button_press = self.arduino_controller.get_button_press()

        if button_press:
            event_map = {
                'left': InputEvent.LEFT_PRESSED,
                'right': InputEvent.RIGHT_PRESSED,
            }

            return InputData(
                event_type=event_map.get(button_press, InputEvent.LEFT_PRESSED),
                input_method=InputType.BUTTON,
                timestamp=datetime.now(),
                value=button_press
            )

        return None

    def process_event(self, pygame_event) -> Optional['InputData']:
        """Buttons don't use pygame events, only get_input()"""
        return None

    def cleanup(self) -> None:
        """Cleanup Arduino connection"""
        if self.arduino_controller:
            self.arduino_controller.disconnect()
            self.connected = False