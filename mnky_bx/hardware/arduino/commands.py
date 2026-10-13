# mnky_bx/hardware/arduino/commands.py
"""
Arduino command protocol for unified button + reward control
Defines all commands sent to and received from Arduino Uno
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict

class ButtonID(Enum):
    LEFT = "20"
    RIGHT = "21"
    CENTER = "22"

class LEDCommand(Enum):
    """LED commands - same format for both controllers"""
    LEFT_ON = "LED_L_ON"
    LEFT_OFF = "LED_L_OFF"
    LEFT_BLINK = "LED_L_BLINK"
    
    RIGHT_ON = "LED_R_ON"
    RIGHT_OFF = "LED_R_OFF"
    RIGHT_BLINK = "LED_R_BLINK"
    
    CENTER_ON = "LED_C_ON"
    CENTER_OFF = "LED_C_OFF"
    CENTER_BLINK = "LED_C_BLINK"

class RewardCommand(Enum):
    """Reward motor commands - same format for both controllers"""
    HOME = "MOTOR_HOME"
    GET_POSITION = "MOTOR_POS"
    MOVE = "MOTOR_MOVE"
    IS_MOVING = "MOTOR_MOVING"

# Command mapping for easy lookup
COMMAND_MAP = {
    "led_left_on": LEDCommand.LEFT_ON.value,
    "led_left_off": LEDCommand.LEFT_OFF.value,
    "led_right_on": LEDCommand.RIGHT_ON.value,
    "led_right_off": LEDCommand.RIGHT_OFF.value,
    "motor_home": RewardCommand.HOME.value,
    "motor_move": RewardCommand.MOVE.value,
}