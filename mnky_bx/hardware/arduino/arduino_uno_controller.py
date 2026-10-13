"""Arduino Uno controller - USB/Serial connection"""
import threading
import time
from typing import Optional, Tuple, Callable
from .base_controller import HardwareController, HardwareStats
from .protocol import SerialProtocol
from .commands import ButtonID, LEDCommand, RewardCommand

class ArduinoUnoController(HardwareController):
    """
    USB-connected Arduino Uno for button input and reward motor control.
    - Serial port: COM4 (Windows) or /dev/ttyUSB0 (Linux)
    - Baud: 115200
    - Protocol: Plain text commands (non-blocking)
    """
    
    def __init__(self, config: dict):
        """
        config keys:
            - port: str (e.g., "COM4" or "/dev/ttyUSB0")
            - baudrate: int (default 115200)
            - motor_max_position: float (default 10.0 mm)
            - motor_pulse_duration_ms: int (default 500 ms)
        """
        super().__init__(config)
        
        self.port = config.get('port', 'COM4')
        self.baudrate = config.get('baudrate', 115200)
        self.protocol = SerialProtocol(self.port, self.baudrate)
        
        self.motor_max_position = config.get('motor_max_position', 10.0)
        self.motor_pulse_duration_ms = config.get('motor_pulse_duration_ms', 500)
        self.motor_current_position = 0.0
        
        self.button_listener_thread = None
        self.button_callback: Optional[Callable] = None
        self.stop_listener = threading.Event()
    
    def connect(self) -> bool:
        """Establish serial connection and verify Arduino is ready."""
        if not self.protocol.connect():
            return False
        
        # Wait for Arduino initialization string
        print("Waiting for Arduino initialization...")
        start_time = time.time()
        while time.time() - start_time < 5.0:
            line = self.protocol.read_line()
            if line and "ready" in line.lower():
                self.is_connected = True
                print(f"Arduino Uno connected and ready!")
                self.home_motor()  # Home on startup
                return True
            time.sleep(0.1)
        
        # Fallback: assume ready after timeout
        print("No initialization string received, assuming ready")
        self.is_connected = True
        self.home_motor()
        return True
    
    def disconnect(self) -> bool:
        """Stop listeners and close connection."""
        if self.button_listener_thread:
            self.stop_listener.set()
            self.button_listener_thread.join(timeout=2.0)
        
        return self.protocol.disconnect()
    
    def health_check(self) -> dict:
        """Verify Arduino is responsive."""
        errors = []
        
        # Check connection
        if not self.is_connected:
            errors.append("Not connected")
            return {
                'connected': False,
                'buttons_responsive': False,
                'motor_responsive': False,
                'leds_responsive': False,
                'battery_level': None,
                'signal_strength': None,
                'errors': errors
            }
        
        # Test motor responsiveness
        motor_ok = False
        try:
            response = self.protocol.send_command("MOTOR_POS", expect_response=True, timeout_s=1.0)
            if response:
                motor_ok = True
            else:
                errors.append("Motor not responding")
        except:
            errors.append("Motor communication error")
        
        # Test LED responsiveness
        leds_ok = False
        try:
            response = self.protocol.send_command("LED_L_BLINK 100", expect_response=True, timeout_s=1.0)
            if response:
                leds_ok = True
            else:
                errors.append("LEDs not responding")
        except:
            errors.append("LED communication error")
        
        return {
            'connected': self.is_connected,
            'buttons_responsive': True,  # Always listening in background
            'motor_responsive': motor_ok,
            'leds_responsive': leds_ok,
            'battery_level': None,  # USB powered
            'signal_strength': None,  # Wired connection
            'errors': errors
        }
    
    def start_button_listener(self, callback: Callable) -> bool:
        """Start background thread to read button presses."""
        if self.button_listener_thread and self.button_listener_thread.is_alive():
            print("Button listener already running")
            return False
        
        self.button_callback = callback
        self.stop_listener.clear()
        self.button_listener_thread = threading.Thread(
            target=self._button_listener_loop,
            daemon=True
        )
        self.button_listener_thread.start()
        return True
    
    def stop_button_listener(self) -> bool:
        """Stop button listener thread."""
        if self.button_listener_thread:
            self.stop_listener.set()
            self.button_listener_thread.join(timeout=2.0)
            self.button_listener_thread = None
        return True
    
    def _button_listener_loop(self):
        """Background thread: continuously read button presses."""
        while not self.stop_listener.is_set():
            try:
                line = self.protocol.read_line(timeout_s=0.5)
                if line:
                    if line == ButtonID.LEFT.value:  # "20"
                        if self.button_callback:
                            self.button_callback("left", int(time.time() * 1000))
                        self.stats.button_presses_left += 1
                    elif line == ButtonID.RIGHT.value:  # "21"
                        if self.button_callback:
                            self.button_callback("right", int(time.time() * 1000))
                        self.stats.button_presses_right += 1
            except Exception as e:
                print(f"Button listener error: {e}")
                self.stats.errors += 1
                time.sleep(0.1)
    
    def get_button_press(self) -> Tuple[Optional[str], Optional[int]]:
        """Non-blocking poll (fallback if not using callback)."""
        # Could implement a queue here, but typically use callback
        return (None, None)
    
    def set_led(self, led_id: str, state: bool, color: tuple = None) -> bool:
        """Control LED."""
        try:
            if state:
                cmd = f"LED_{led_id.upper()}_ON"
            else:
                cmd = f"LED_{led_id.upper()}_OFF"
            
            self.protocol.send_command(cmd)
            return True
        except Exception as e:
            print(f"LED error: {e}")
            self.stats.errors += 1
            return False
    
    def blink_led(self, led_id: str, duration_ms: int, count: int = 1) -> bool:
        """Blink LED."""
        try:
            cmd = f"LED_{led_id.upper()}_BLINK {duration_ms} {count}"
            self.protocol.send_command(cmd)
            return True
        except Exception as e:
            print(f"LED blink error: {e}")
            self.stats.errors += 1
            return False
    
    def home_motor(self) -> bool:
        """Move motor to home position."""
        try:
            response = self.protocol.send_command("MOTOR_HOME", expect_response=True, timeout_s=2.0)
            if response and "ok" in response.lower():
                self.motor_current_position = 0.0
                return True
            return False
        except Exception as e:
            print(f"Home motor error: {e}")
            self.stats.errors += 1
            return False
    
    def get_motor_position(self) -> Optional[Tuple[float, float, float]]:
        """Get current motor position."""
        try:
            response = self.protocol.send_command("MOTOR_POS", expect_response=True, timeout_s=1.0)
            if response:
                # Parse response like "X:0.0 Y:0.0 Z:0.0"
                parts = response.split()
                x = float(parts[0].split(':')[1]) if len(parts) > 0 else 0.0
                y = float(parts[1].split(':')[1]) if len(parts) > 1 else 0.0
                z = float(parts[2].split(':')[1]) if len(parts) > 2 else 0.0
                return (x, y, z)
        except Exception as e:
            print(f"Get position error: {e}")
        return None
    
    def move_motor(self, distance_mm: float, duration_ms: int = 500) -> bool:
        """Deliver reward by moving motor."""
        try:
            # Clamp distance
            distance_mm = max(-self.motor_max_position, 
                             min(self.motor_max_position, distance_mm))
            
            cmd = f"MOTOR_MOVE {distance_mm} {duration_ms}"
            response = self.protocol.send_command(cmd, expect_response=True, timeout_s=2.0)
            
            if response and "ok" in response.lower():
                self.motor_current_position = distance_mm
                self.stats.reward_deliveries += 1
                return True
            return False
        except Exception as e:
            print(f"Move motor error: {e}")
            self.stats.errors += 1
            return False
    
    def is_motor_moving(self) -> bool:
        """Check if motor is currently moving."""
        try:
            response = self.protocol.send_command("MOTOR_MOVING", expect_response=True, timeout_s=1.0)
            return response and "yes" in response.lower()
        except:
            return False
    
    def get_stats(self) -> HardwareStats:
        """Return statistics."""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = HardwareStats()