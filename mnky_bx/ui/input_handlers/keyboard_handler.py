# mnky_bx/ui/input_handlers/keyboard_handler.py
"""
Keyboard input handler
"""

import pygame
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class KeyboardHandler:
    """Handles pygame keyboard events"""

    def __init__(self):
        """Initialize keyboard handler"""
        self.key_map = {
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_q: "quit",
            pygame.K_ESCAPE: "quit",
            pygame.K_BACKSPACE: "back",
            pygame.K_RETURN: "confirm",
        }

    def process_event(self, pygame_event) -> Optional['InputData']:
        """
        Process pygame keyboard event

        Args:
            pygame_event: pygame.event object

        Returns:
            InputData or None
        """
        from mnky_bx.ui.input_system import InputData, InputType, InputEvent

        if pygame_event.type != pygame.KEYDOWN:
            return None

        key = pygame_event.key

        if key in self.key_map:
            event_name = self.key_map[key]

            # Map to InputEvent
            event_map = {
                "left_pressed": InputEvent.LEFT_PRESSED,
                "right_pressed": InputEvent.RIGHT_PRESSED,
                "quit": InputEvent.QUIT,
                "back": InputEvent.BACK,
                "confirm": InputEvent.CONFIRM,
            }

            return InputData(
                event_type=event_map.get(event_name, InputEvent.LEFT_PRESSED),
                input_method=InputType.KEYBOARD,
                timestamp=datetime.now()
            )

        return None