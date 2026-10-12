# mnky_bx/hardware/hardware_interface.py (UPDATED)
"""
Abstract hardware interfaces for dependency injection
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict


class ButtonController(ABC):
    """Abstract interface for button input"""

    @abstractmethod
    def get_button_press(self) -> Optional[str]:
        """Get last button pressed ('left', 'right', or None)"""
        pass

    @abstractmethod
    def set_button_callback(self, callback: Callable) -> None:
        """Set callback for button presses"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class RewardController(ABC):
    """Abstract interface for reward delivery"""

    @abstractmethod
    def deliver_reward(self, amount: int = 1) -> bool:
        """Deliver reward, returns True if successful"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class LEDController(ABC):
    """Abstract interface for LED control"""

    @abstractmethod
    def set_led(self, button_id: str, state: bool) -> bool:
        """Control LED for a button"""
        pass

    @abstractmethod
    def set_all_leds(self, state: bool) -> bool:
        """Control all LEDs"""
        pass


class ArduinoController(ButtonController, RewardController, LEDController):
    """Unified Arduino controller implements all interfaces"""
    pass