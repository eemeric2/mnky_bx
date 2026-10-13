"""Adafruit Feather nRF52840 controller - BLE wireless reward delivery ONLY"""
import threading
import time
from typing import Optional, Tuple, Callable
from .base_controller import HardwareController, HardwareStats, ControllerType
from .protocol import SerialProtocol
from .commands import RewardCommand

class AdafruitFeatherRewardOnlyController(HardwareController):
    """
    Wireless BLE-connected Adafruit Feather nRF52840.
    
    PURPOSE: Reward motor control ONLY (button input is handled by touchscreen)
    
    - Connection: BLE serial port (COM3 on Windows, /dev/ttyACM0 on Linux)
    - Baud: 115200
    - Protocol: Text-based commands over serial
    
    Key features:
    - Wireless operation (no USB tether to enclosure)
    - Battery monitoring and low-battery alerts
    - BLE signal strength monitoring
    - Lightweight (only motor commands, no button/LED overhead)
    - Integrates with touchscreen input system
    
    Usage with Touchscreen:
        feather = AdafruitFeatherRewardOnlyController(config)
        feather.connect()
        
        touchscreen = TouchscreenInputManager(config)
        touchscreen.start()  # Handles button input
        
        feather.move_motor(5.0, 500)  # Deliver reward
        feather.disconnect()
    """
    
    controller_type = ControllerType.ADAFRUIT_FEATHER_REWARD_ONLY
    
    def __init__(self, config: dict):
        """
        config keys:
            - port: str (e.g., "COM3" or "/dev/ttyACM0")
            - baudrate: int (default 115200)
            - ble_device_name: str (for identification, default "mnky_bx_feather")
            - motor_max_position: float (default 10.0 mm)
            - motor_pulse_duration_ms: int (default 500 ms)
            - battery_warning_threshold: float (default 20%)
        """
        super().__init__(config)
        
        self.port = config.get('port', 'COM3')
        self.baudrate = config.get('baudrate', 115200)
        self.protocol = SerialProtocol(self.port, self.baudrate)
        
        self.ble_device_name = config.get('ble_device_name', 'mnky_bx_feather')
        self.motor_max_position = config.get('motor_max_position', 10.0)
        self.motor_pulse_duration_ms = config.get('motor_pulse_duration_ms', 500)
        self.motor_current_position = 0.0
        
        # Battery & Signal monitoring
        self.battery_level = 100.0
        self.signal_strength = 0.0
        self.battery_warning_threshold = config.get('battery_warning_threshold', 20.0)
        
        self.battery_check_thread = None
        self.stop_battery_check = threading.Event()
    
    def connect(self) -> bool:
        """Establish BLE connection and verify Feather is ready."""
        if not self.protocol.connect():
            print(f"Failed to connect to Feather on {self.port}")
            return False
        
        # Wait for Feather initialization string
        print(f"Waiting for Feather BLE initialization on {self.port}...")
        start_time = time.time()
        while time.time() - start_time < 5.0:
            line = self.protocol.read_line()
            if line and "feather" in line.lower() and "ready" in line.lower():
                self.is_connected = True
                print(f"✓ Adafruit Feather connected on {self.port}")
                self.home_motor()
                self._start_battery_monitor()
                return True
            time.sleep(0.1)
        
        # Fallback: assume ready after timeout
        print("No initialization string received, assuming Feather is ready")
        self.is_connected = True
        self.home_motor()
        self._start_battery_monitor()
        return True
    
    def disconnect(self) -> bool:
        """Stop all threads and close connection."""
        if self.battery_check_thread:
            self.stop_battery_check.set()
            self.battery_check_thread.join(timeout=2.0)
        
        return self.protocol.disconnect()
    
    def health_check(self) -> dict:
        """Verify Feather is responsive and check battery/signal."""
        errors = []
        
        if not self.is_connected:
            errors.append("Feather not connected")
            return {
                'connected': False,
                'buttons_responsive': False,
                'motor_responsive': False,
                'leds_responsive': False,
                'battery_level': None,
                'signal_strength': None,
                'errors': errors
            }
        
        # Check battery
        if self.battery_level < self.battery_warning_threshold:
            errors.append(f"Low battery: {self.battery_level:.1f}%")
        
        # Check signal strength
        if self.signal_strength < 10:
            errors.append(f"Weak BLE signal: {self.signal_strength:.1f}%")
        
        # Test motor responsiveness
        motor_ok = False
        try:
            response = self.protocol.send_command("MOTOR_POS", expect_response=True, timeout_s=1.0)
            motor_ok = response is not None
            if not motor_ok:
                errors.append("Motor not responding")
        except Exception as e:
            errors.append(f"Motor communication error: {e}")
        
        return {
            'connected': self.is_connected,
            'buttons_responsive': False,  # This controller doesn't handle buttons
            'motor_responsive': motor_ok,
            'leds_responsive': False,      # This controller doesn't handle LEDs
            'battery_level': self.battery_level,
            'signal_strength': self.signal_strength,
            'errors': errors
        }
    
    # ===== Button Input (NOT SUPPORTED) =====
    def start_button_listener(self, callback: Callable) -> bool:
        """
        Button input is NOT supported on this controller.
        Use TouchscreenInputManager instead.
        """
        print("⚠ WARNING: AdafruitFeatherRewardOnlyController does not support button input.")
        print("           Use TouchscreenInputManager for button handling.")
        return False
    
    def stop_button_listener(self) -> bool:
        """No-op: this controller doesn't listen for buttons."""
        return True
    
    # ===== LED Control (NOT SUPPORTED) =====
    def set_led(self, led_id: str, state: bool, color: tuple = None) -> bool:
        """
        LED control is NOT supported on this controller.
        Touchscreen can render visual feedback instead.
        """
        print("⚠ WARNING: AdafruitFeatherRewardOnlyController does not support LED control.")
        print("           Use TouchscreenInputManager for visual feedback.")
        return False
    
    def blink_led(self, led_id: str, duration_ms: int, count: int = 1) -> bool:
        """LED blink is NOT supported on this controller."""
        return False
    
    # ===== Reward Motor Control (SUPPORTED) =====
    def home_motor(self) -> bool:
        """Move motor to home position."""
        try:
            response = self.protocol.send_command("MOTOR_HOME", expect_response=True, timeout_s=2.0)
            if response and "ok" in response.lower():
                self.motor_current_position = 0.0
                print("✓ Motor homed")
                return True
            print("✗ Motor home failed")
            return False
        except Exception as e:
            print(f"✗ Home motor error: {e}")
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
        """
        Deliver reward by moving motor.
        
        Args:
            distance_mm: Distance to move (clamped to [-max_position, +max_position])
            duration_ms: Motor run duration in milliseconds
        
        Returns:
            True if command sent successfully
        """
        try:
            # Clamp distance to safe range
            distance_mm = max(-self.motor_max_position,
                             min(self.motor_max_position, distance_mm))
            
            cmd = f"MOTOR_MOVE {distance_mm} {duration_ms}"
            response = self.protocol.send_command(cmd, expect_response=True, timeout_s=2.0)
            
            if response and "ok" in response.lower():
                self.motor_current_position = distance_mm
                self.stats.reward_deliveries += 1
                print(f"✓ Reward delivered: {distance_mm}mm for {duration_ms}ms")
                return True
            
            print(f"✗ Move motor failed: {response}")
            return False
        except Exception as e:
            print(f"✗ Move motor error: {e}")
            self.stats.errors += 1
            return False
    
    def is_motor_moving(self) -> bool:
        """Check if motor is currently moving."""
        try:
            response = self.protocol.send_command("MOTOR_MOVING", expect_response=True, timeout_s=1.0)
            return response and "yes" in response.lower()
        except:
            return False
    
    # ===== Battery & Signal Monitoring =====
    def _start_battery_monitor(self):
        """Start background thread to monitor battery and signal strength."""
        if self.battery_check_thread and self.battery_check_thread.is_alive():
            return
        
        self.stop_battery_check.clear()
        self.battery_check_thread = threading.Thread(
            target=self._battery_monitor_loop,
            daemon=True
        )
        self.battery_check_thread.start()
    
    def _battery_monitor_loop(self):
        """
        Background thread: periodically check battery level and BLE signal strength.
        Runs every 10 seconds.
        """
        while not self.stop_battery_check.is_set():
            try:
                # Query battery level
                response = self.protocol.send_command("BATTERY", expect_response=True, timeout_s=1.0)
                if response:
                    try:
                        self.battery_level = float(response)
                    except ValueError:
                        pass
                
                # Query BLE signal strength
                response = self.protocol.send_command("SIGNAL", expect_response=True, timeout_s=1.0)
                if response:
                    try:
                        self.signal_strength = float(response)
                    except ValueError:
                        pass
                
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"Battery monitor error: {e}")
                time.sleep(10)
    
    # ===== Statistics =====
    def get_stats(self) -> HardwareStats:
        """Return accumulated statistics."""
        return self.stats
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = HardwareStats()