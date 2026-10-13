"""Base controller defining hardware interface"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

@dataclass
class HardwareStats:
    button_presses_left: int = 0
    button_presses_right: int = 0
    reward_deliveries: int = 0
    errors: int = 0
    connection_uptime_s: float = 0.0

class HardwareController(ABC):
    """Abstract base for both Arduino Uno and Adafruit Feather"""
    
    def __init__(self, config: dict):
        self.config = config
        self.is_connected = False
        self.stats = HardwareStats()
        
    # ===== Connection Management =====
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to hardware. Return True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection gracefully."""
        pass
    
    @abstractmethod
    def health_check(self) -> dict:
        """
        Verify hardware is responsive.
        Returns:
            {
                'connected': bool,
                'buttons_responsive': bool,
                'motor_responsive': bool,
                'leds_responsive': bool,
                'battery_level': float (0-100, or None if wired),
                'signal_strength': float (0-100, or None if wired),
                'errors': list of str
            }
        """
        pass
    
    # ===== Button Input (Non-blocking) =====
    @abstractmethod
    def start_button_listener(self, callback):
        """
        Start background thread listening for button presses.
        Callback signature: callback(button_id: str, timestamp_ms: int)
        button_id: "left" or "right"
        """
        pass
    
    @abstractmethod
    def stop_button_listener(self) -> bool:
        """Stop button listener thread."""
        pass
    
    @abstractmethod
    def get_button_press(self) -> tuple:
        """
        Non-blocking read of last button press (polling fallback).
        Returns: (button_id, timestamp_ms) or (None, None)
        """
        pass
    
    # ===== LED Control =====
    @abstractmethod
    def set_led(self, led_id: str, state: bool, color: tuple = None) -> bool:
        """
        Control LED feedback.
        led_id: "left", "right", "center"
        state: True (on) or False (off)
        color: RGB tuple (for RGB LEDs), or None for simple on/off
        Returns: True if command sent successfully
        """
        pass
    
    @abstractmethod
    def blink_led(self, led_id: str, duration_ms: int, count: int = 1) -> bool:
        """Blink LED (useful for feedback during trial)."""
        pass
    
    # ===== Reward Motor Control =====
    @abstractmethod
    def home_motor(self) -> bool:
        """Move motor to home position (0,0,0). Return True if successful."""
        pass
    
    @abstractmethod
    def get_motor_position(self) -> tuple:
        """Return current (x, y, z) position or None if not available."""
        pass
    
    @abstractmethod
    def move_motor(self, distance_mm: float, duration_ms: int = 500) -> bool:
        """
        Deliver reward by moving motor.
        distance_mm: distance to move (positive or negative)
        duration_ms: how long to run motor (pulse width for servo control)
        Returns: True if command sent
        """
        pass
    
    @abstractmethod
    def is_motor_moving(self) -> bool:
        """Check if motor is currently moving."""
        pass
    
    # ===== Utility =====
    @abstractmethod
    def get_stats(self) -> HardwareStats:
        """Return accumulated statistics."""
        pass
    
    @abstractmethod
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        pass