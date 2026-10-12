# mnky_bx/ui/input_system.py
"""
Unified input system supporting keyboard, buttons, and touchscreen
Abstracts away the complexity of different input methods
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InputType(Enum):
    """Input method type"""
    KEYBOARD = "keyboard"
    BUTTON = "button"
    TOUCHSCREEN = "touchscreen"


class InputEvent(Enum):
    """Input events"""
    LEFT_PRESSED = "left_pressed"
    RIGHT_PRESSED = "right_pressed"
    BUTTON_RELEASED = "button_released"
    QUIT = "quit"
    BACK = "back"
    CONFIRM = "confirm"


@dataclass
class InputData:
    """Represents an input event"""
    event_type: InputEvent
    input_method: InputType
    timestamp: datetime
    position: Optional[tuple] = None  # (x, y) for touchscreen
    value: Optional[str] = None  # Additional data
    duration_ms: Optional[float] = None  # How long button was held


class InputEventListener:
    """Callback interface for input events"""

    def on_input(self, input_data: InputData) -> None:
        """Called when input event occurs"""
        raise NotImplementedError


class UnifiedInputManager:
    """
    Manages all input types and provides unified interface

    Supports:
    - Keyboard (pygame events)
    - Physical buttons (Arduino serial)
    - Touchscreen (pygame mouse events mapped to UI regions)
    """

    def __init__(self, config: Dict):
        """
        Initialize input system

        Args:
            config: Configuration dict with:
                - enabled_inputs: List of ['keyboard', 'button', 'touchscreen']
                - arduino_port: Port for button Arduino (if enabled)
                - touchscreen_regions: Clickable regions for touchscreen
        """
        self.config = config
        self.enabled_inputs = config.get('enabled_inputs', ['keyboard', 'button'])

        # Input handlers
        self.handlers = {}
        self.listeners: List[InputEventListener] = []

        # Statistics
        self.input_count = {'keyboard': 0, 'button': 0, 'touchscreen': 0}

    def register_listener(self, listener: InputEventListener) -> None:
        """Register callback for input events"""
        self.listeners.append(listener)

    def unregister_listener(self, listener: InputEventListener) -> None:
        """Unregister callback"""
        if listener in self.listeners:
            self.listeners.remove(listener)

    def initialize(self) -> bool:
        """Initialize all enabled input handlers"""
        logger.info(f"Initializing input system with: {self.enabled_inputs}")

        try:
            # Initialize keyboard handler (always available with pygame)
            if 'keyboard' in self.enabled_inputs:
                from .input_handlers.keyboard_handler import KeyboardHandler
                self.handlers['keyboard'] = KeyboardHandler()
                logger.info("Keyboard input enabled")

            # Initialize button handler (requires Arduino)
            if 'button' in self.enabled_inputs:
                from .input_handlers.button_handler import ButtonHandler
                button_config = self.config.get('arduino', {})
                self.handlers['button'] = ButtonHandler(button_config)

                if self.handlers['button'].connect():
                    logger.info("Button input enabled (Arduino connected)")
                else:
                    logger.warning("Button input requested but Arduino not available")
                    del self.handlers['button']

            # Initialize touchscreen handler
            if 'touchscreen' in self.enabled_inputs:
                from .input_handlers.touchscreen_handler import TouchscreenHandler
                touchscreen_config = self.config.get('touchscreen', {})
                self.handlers['touchscreen'] = TouchscreenHandler(touchscreen_config)
                logger.info("Touchscreen input enabled")

            return True

        except Exception as e:
            logger.error(f"Input system initialization error: {e}")
            return False

    def handle_pygame_event(self, pygame_event) -> None:
        """
        Route pygame event to appropriate handler

        Args:
            pygame_event: pygame event object
        """
        # Route to keyboard handler
        if 'keyboard' in self.handlers:
            input_data = self.handlers['keyboard'].process_event(pygame_event)
            if input_data:
                self._dispatch_input(input_data)

        # Route to touchscreen handler
        if 'touchscreen' in self.handlers:
            input_data = self.handlers['touchscreen'].process_event(pygame_event)
            if input_data:
                self._dispatch_input(input_data)

    def check_button_input(self) -> Optional[InputData]:
        """
        Check for button input from Arduino
        (Called periodically, non-blocking)
        """
        if 'button' in self.handlers:
            input_data = self.handlers['button'].get_input()
            if input_data:
                self._dispatch_input(input_data)
                return input_data

        return None

    def _dispatch_input(self, input_data: InputData) -> None:
        """Dispatch input event to all listeners"""
        self.input_count[input_data.input_method.value] += 1

        logger.debug(f"Input: {input_data.event_type.value} via {input_data.input_method.value}")

        for listener in self.listeners:
            try:
                listener.on_input(input_data)
            except Exception as e:
                logger.error(f"Listener error: {e}")

    def get_statistics(self) -> Dict:
        """Get input statistics"""
        return {
            'total_keyboard': self.input_count['keyboard'],
            'total_button': self.input_count['button'],
            'total_touchscreen': self.input_count['touchscreen'],
            'enabled_inputs': self.enabled_inputs,
            'active_handlers': list(self.handlers.keys())
        }

    def cleanup(self) -> None:
        """Cleanup all handlers"""
        for handler in self.handlers.values():
            if hasattr(handler, 'cleanup'):
                handler.cleanup()

        logger.info("Input system cleaned up")