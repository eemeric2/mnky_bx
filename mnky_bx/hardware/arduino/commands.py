# mnky_bx/hardware/arduino/commands.py
"""
Arduino command protocol for unified button + reward control
Defines all commands sent to and received from Arduino Uno
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class ButtonID(Enum):
    """Button identifiers"""
    LEFT = "20"
    RIGHT = "21"


class LEDCommand(Enum):
    """LED control commands"""
    LEFT_ON = "1"  # Turn on left button LED
    RIGHT_ON = "2"  # Turn on right button LED
    BOTH_ON = "3"  # Turn on both LEDs
    ALL_OFF = "4"  # Turn off all LEDs


class RewardCommand(Enum):
    """Reward/motor commands"""
    MOTOR_FORWARD = "G0 X5\n"  # Move reward motor forward (5mm)
    MOTOR_BACKWARD = "G0 X0\n"  # Move reward motor backward (home)
    MOTOR_HOME = "G92 X0 Y0 Z0\n"  # Set home position


class ConnectionCommand(Enum):
    """Connection verification"""
    GRBL_HANDSHAKE = "Grbl 1.1h ['$' for help]"
    RESET = "\x18"  # Ctrl+X for reset


@dataclass
class ArduinoCommand:
    """Represents a command to send to Arduino"""
    command_type: str  # 'led', 'motor', 'homing'
    command_id: str  # Specific command (e.g., "1" for LEFT_ON)
    parameter: int = 0  # Optional parameter (e.g., duration)
    timestamp: float = None  # When command was issued


@dataclass
class ArduinoResponse:
    """Represents a response from Arduino"""
    raw_data: str  # Raw serial data
    parsed_command: str  # What command this was (e.g., "LEFT_BUTTON_PRESSED")
    timestamp: float = None  # When response received
    is_error: bool = False


# Command mapping for easy reference
COMMAND_MAP = {
    # LED commands
    'led_left_on': LEDCommand.LEFT_ON.value,
    'led_right_on': LEDCommand.RIGHT_ON.value,
    'led_both_on': LEDCommand.BOTH_ON.value,
    'led_all_off': LEDCommand.ALL_OFF.value,

    # Motor commands
    'motor_forward': RewardCommand.MOTOR_FORWARD.value,
    'motor_backward': RewardCommand.MOTOR_BACKWARD.value,
    'motor_home': RewardCommand.MOTOR_HOME.value,

    # Button responses
    'button_left': ButtonID.LEFT.value,
    'button_right': ButtonID.RIGHT.value,
}

# Response parsing map
RESPONSE_PARSE_MAP = {
    "20": "left_button_pressed",
    "21": "right_button_pressed",
    "ok": "command_acknowledged",
}