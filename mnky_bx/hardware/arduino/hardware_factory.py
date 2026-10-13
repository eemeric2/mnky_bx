"""Factory to instantiate correct hardware controller based on config"""
from typing import Optional
from .base_controller import HardwareController
from .arduino_uno_controller import ArduinoUnoController
from .adafruit_feather_controller import AdafruitFeatherController

class HardwareFactory:
    """
    Factory pattern for hardware controller instantiation.
    Reads kiosk_config.json to determine which hardware is available.
    """
    
    @staticmethod
    def create_controller(config: dict) -> Optional[HardwareController]:
        """
        Create hardware controller based on config.
        
        config structure:
        {
            "hardware_type": "arduino_uno" | "adafruit_feather" | "auto",
            "arduino_uno": {
                "port": "COM4",
                "baudrate": 115200,
                ...
            },
            "adafruit_feather": {
                "port": "COM3",
                "baudrate": 115200,
                ...
            }
        }
        
        If "auto", tries to detect which hardware is available.
        """
        
        hw_type = config.get('hardware_type', 'auto').lower()
        
        if hw_type == 'arduino_uno':
            arduino_config = config.get('arduino_uno', {})
            return ArduinoUnoController(arduino_config)
        
        elif hw_type == 'adafruit_feather':
            feather_config = config.get('adafruit_feather', {})
            return AdafruitFeatherController(feather_config)
        
        elif hw_type == 'auto':
            # Try to detect which hardware is available
            # First, try Arduino Uno
            arduino_config = config.get('arduino_uno', {'port': 'COM4'})
            controller = ArduinoUnoController(arduino_config)
            if controller.connect():
                print("Auto-detected: Arduino Uno")
                return controller
            else:
                controller.disconnect()
            
            # Then try Adafruit Feather
            feather_config = config.get('adafruit_feather', {'port': 'COM3'})
            controller = AdafruitFeatherController(feather_config)
            if controller.connect():
                print("Auto-detected: Adafruit Feather")
                return controller
            else:
                controller.disconnect()
            
            print("ERROR: No hardware detected!")
            return None
        
        else:
            print(f"Unknown hardware_type: {hw_type}")
            return None