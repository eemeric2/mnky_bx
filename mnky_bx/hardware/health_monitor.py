# mnky_bx/hardware/health_monitor.py (UPDATED)

class HardwareHealthMonitor:
    """Monitor hardware health"""

    def __init__(self, config, notification_manager):
        self.config = config
        self.notifier = notification_manager
        self.failures = {}

    def check_arduino(self, arduino_controller) -> bool:
        """
        Check Arduino health

        Returns:
            True if healthy
        """
        try:
            health = arduino_controller.health_check()

            if not health['connected']:
                self._handle_hardware_failure(
                    device='arduino',
                    error='Not connected',
                    severity='critical'
                )
                return False

            if not health['buttons_responsive']:
                self._handle_hardware_failure(
                    device='arduino_buttons',
                    error='Buttons not responsive',
                    severity='warning'
                )

            if not health['motor_responsive']:
                self._handle_hardware_failure(
                    device='arduino_motor',
                    error='Motor not responsive',
                    severity='critical'
                )
                return False

            if not health['led_responsive']:
                self._handle_hardware_failure(
                    device='arduino_led',
                    error='LEDs not responsive',
                    severity='warning'
                )

            return True

        except Exception as e:
            self._handle_hardware_failure(
                device='arduino',
                error=str(e),
                severity='critical'
            )
            return False

    def check_all_hardware(self, arduino_controller, camera_system) -> Dict:
        """Full hardware health check"""
        return {
            'arduino': self.check_arduino(arduino_controller),
            'camera': self._check_camera(camera_system),
            'network': self._check_network()
        }

    def _handle_hardware_failure(self, device: str, error: str, severity: str):
        """Handle hardware failure"""
        self.failures[device] = {
            'error': error,
            'timestamp': datetime.now(),
            'severity': severity
        }

        logging.warning(f"Hardware failure: {device} - {error}")

        if severity == 'critical':
            self.notifier.send_alert(
                subject=f"CRITICAL: {device} failure",
                message=f"Device: {device}\nError: {error}"
            )