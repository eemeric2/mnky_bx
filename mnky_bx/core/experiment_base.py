# mnky_bx/core/experiment_base.py
"""
Base experiment class - provides framework for all experiments
Users subclass this and implement pygame-specific methods
"""


class ExperimentBase:
    """
    Base experiment class with unified input handling
    Supports keyboard, buttons, and touchscreen
    """
    def __init__(self,
                 experiment_name,
                 subject_id,
                 kiosk_manager,
                 logger,
                 notification_manager,
                 hardware_config):
        """
        Initialize experiment base

        Args:
            experiment_name: Directory name in experiments/
            subject_id: Subject identifier
            kiosk_manager: KioskManager instance
            logger: ExperimentLogger instance
            notification_manager: NotificationManager instance
            hardware_config: Hardware configuration dict
        """
        self.experiment_name = experiment_name
        self.subject_id = subject_id
        self.kiosk_manager = kiosk_manager
        self.logger = logger
        self.notifier = notification_manager
        self.hardware_config = hardware_config

        # Load experiment-specific config
        self.config = ConfigLoader.load_experiment_config(experiment_name)

        # Initialize session
        session = kiosk_manager.start_session(subject_id, experiment_name)
        self.session_dir = session['session_dir']

        # Initialize database in session directory
        self.db_path = self.session_dir / f"exp_{session['timestamp_str']}.db"
        self.db_connection = None
        self.setup_database()

        """
        Initialize experiment with unified Arduino controller
        """
        # ← NEW: Unified input system
        self.input_manager = UnifiedInputManager(hardware_config.get('input_system', {}))
        self.input_manager.initialize()
        self.input_manager.register_listener(self)

        # ← Updated: Arduino only for reward (buttons via input system)
        self.arduino_reward = None
        self.setup_arduino_reward()
        
        # Current trial state
        self.choice = None
        self.ts_button_press = None

    def setup_arduino_reward(self) -> bool:
        """
        Setup Arduino for reward delivery only
        (Buttons now handled by input system)

        Returns:
            True if successful or not required
        """
        try:
            # Check if buttons are handled by Arduino or input system
            enabled_inputs = self.hardware_config.get('input_system', {}).get('enabled_inputs', [])

            if 'button' in enabled_inputs:
                # Buttons via Arduino - use full controller
                from mnky_bx.hardware.arduino.arduino_uno_controller import ArduinoUnoController

                arduino_config = self.hardware_config.get('input_system', {}).get('arduino', {})
                self.arduino_reward = ArduinoUnoController(
                    arduino_config.get('port', 'COM4'),
                    arduino_config
                )

                if self.arduino_reward.connect():
                    self.logger.log_hardware_event('Arduino', 'Connected for buttons and reward')
                    return True
                else:
                    self.logger.log_error("Failed to connect to Arduino")
                    return False

            else:
                # Reward only - use minimal controller
                from mnky_bx.hardware.arduino.reward_only_controller import RewardOnlyController

                arduino_config = self.hardware_config.get('input_system', {}).get('arduino', {})
                self.arduino_reward = RewardOnlyController(
                    arduino_config.get('port', 'COM4'),
                    arduino_config
                )

                if self.arduino_reward.connect():
                    self.logger.log_hardware_event('Arduino', 'Connected for reward only')
                    return True
                else:
                    self.logger.log_error("Failed to connect to Arduino (reward)")
                    return False

        except Exception as e:
            self.logger.log_error(f"Arduino reward setup error: {e}", exc_info=True)
            return False

    # ← NEW: Input callback implementation
    def on_input(self, input_data: InputData) -> None:
        """
        Called by input system when input event occurs

        Args:
            input_data: InputData object with event details
        """
        if input_data.event_type == InputEvent.LEFT_PRESSED:
            self.choice = 'left'
            self.ts_button_press = pygame.time.get_ticks()
            self.logger.log_hardware_event(
                'Input',
                f'LEFT pressed via {input_data.input_method.value}'
            )

        elif input_data.event_type == InputEvent.RIGHT_PRESSED:
            self.choice = 'right'
            self.ts_button_press = pygame.time.get_ticks()
            self.logger.log_hardware_event(
                'Input',
                f'RIGHT pressed via {input_data.input_method.value}'
            )

        elif input_data.event_type == InputEvent.QUIT:
            self.logger.log_hardware_event('Input', 'QUIT event')
            self.cleanup()
            sys.exit(0)

    def wait_for_response(self) -> bool:
        """
        Wait for response (button, keyboard, or touchscreen)
        Works with all input methods

        Returns:
            True if response received
        """
        running = True
        start_time = pygame.time.get_ticks()

        while running:
            # Handle pygame events (keyboard + touchscreen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                # Let input system handle the event
                self.input_manager.handle_pygame_event(event)

            # Check for button input from Arduino
            self.input_manager.check_button_input()

            # Check if we got a response
            if self.choice in ['left', 'right']:
                return True

            # Check timeout
            if pygame.time.get_ticks() - start_time > self.max_RT:
                self.choice = 'no response'
                return False

            pygame.time.delay(4)

        return False

    def setup_arduino(self) -> bool:
        """
        Setup unified Arduino Uno for buttons + reward
        
        Returns:
            True if successful
        """
        try:
            arduino_config = self.hardware_config.get('arduino', {})
            port = arduino_config.get('port', 'COM4')
            
            self.arduino = ArduinoUnoController(port, arduino_config)
            
            if self.arduino.connect():
                # Set button callback
                self.arduino.set_button_callback(self._on_button_pressed)
                
                self.logger.log_hardware_event('Arduino', 'Connected and initialized')
                return True
            
            else:
                self.logger.log_error("Failed to connect to Arduino")
                self.notifier.send_alert(
                    subject="Arduino Connection Failed",
                    message=f"Could not establish connection to {port}"
                )
                return False
        
        except Exception as e:
            self.logger.log_error(f"Arduino setup error: {e}", exc_info=True)
            return False
    
    def _on_button_pressed(self, button_id: str) -> None:
        """
        Callback when button is pressed
        
        Args:
            button_id: 'left' or 'right'
        """
        self.choice = button_id
        self.ts_button_press = pygame.time.get_ticks()
        self.logger.log_hardware_event('Button', f'{button_id} pressed')
    
    def activate_trial_leds(self) -> None:
        """
        Activate LEDs based on trial type
        Called at start of stimulus presentation
        """
        if not self.arduino or not self.arduino.is_connected:
            return
        
        try:
            if self.trial_type == 'no choice sure':
                if self.opt_sp_config == 'left':
                    self.arduino.set_led('left', True)
                else:
                    self.arduino.set_led('right', True)
            else:  # choice or gamble trials
                self.arduino.set_all_leds(True)
            
            self.logger.log_hardware_event('LED', f'Activated for {self.trial_type}')
        
        except Exception as e:
            self.logger.log_error(f"LED activation error: {e}")
    
    def deactivate_trial_leds(self) -> None:
        """
        Deactivate all LEDs
        Called after response window closes
        """
        if not self.arduino or not self.arduino.is_connected:
            return
        
        try:
            self.arduino.set_all_leds(False)
            self.logger.log_hardware_event('LED', 'Deactivated')
        
        except Exception as e:
            self.logger.log_error(f"LED deactivation error: {e}")
    
    def deliver_reward(self) -> None:
        """
        Deliver reward (reward motor)
        Called when trial is successful
        """
        if not self.arduino or not self.arduino.is_connected:
            self.logger.log_error("Arduino not connected, cannot deliver reward")
            return
        
        try:
            reward_amount = self.trial_params.get('reward_magnitude', 5)
            
            success = self.arduino.deliver_reward(amount=reward_amount)
            
            if success:
                self.ts_reward_delivered = pygame.time.get_ticks()
                self.logger.log_hardware_event('Reward', 
                    f'Delivered: {reward_amount}')
            else:
                self.logger.log_error("Reward delivery failed")
        
        except Exception as e:
            self.logger.log_error(f"Reward delivery error: {e}")
    
    def run_trial(self):
        """
        UPDATED: Run trial with unified Arduino control
        """
        self.setup_new_trial()
        
        # Activate LEDs
        self.activate_trial_leds()
        
        self.draw_stimuli()
        pygame.display.flip()
        self.ts_stimuli_on = pygame.time.get_ticks()
        
        # Wait for response (button presses handled via callback)
        self.wait_for_response()
        
        # Deactivate LEDs
        self.deactivate_trial_leds()
        
        self.handle_choice()
        self.reveal_outcome()
        pygame.time.delay(250)
        
        # Deliver reward if successful
        if self.success:
            self.deliver_reward()
        
        # Camera cleanup
        self.camera_system.stop_picture_capture()
        self.capture_manager.save_metadata_to_database(self.db_connection)
        self.capture_manager.save_trial_statistics(self.db_connection, self.current_trial)

    def deactivate_trial_leds(self) -> None:
        """Deactivate LEDs"""
        if not self.arduino_reward:
            return

        if hasattr(self.arduino_reward, 'set_all_leds'):
            try:
                self.arduino_reward.set_all_leds(False)
                self.logger.log_hardware_event('LED', 'Deactivated')
            except Exception as e:
                self.logger.log_error(f"LED deactivation error: {e}")

    def deliver_reward(self) -> None:
        """
        Deliver reward via Arduino
        Works with both full controller (buttons+reward) and reward-only
        """
        if not self.arduino_reward or not self.arduino_reward.is_connected:
            self.logger.log_error("Arduino not connected for reward")
            return

        try:
            reward_amount = self.trial_params.get('reward_magnitude', 5)

            # Both controllers have deliver_reward method
            success = self.arduino_reward.deliver_reward(amount=reward_amount)

            if success:
                self.ts_reward_delivered = pygame.time.get_ticks()
                self.logger.log_hardware_event('Reward', f'Delivered: {reward_amount}')
            else:
                self.logger.log_error("Reward delivery failed")

        except Exception as e:
            self.logger.log_error(f"Reward delivery error: {e}")

    def cleanup(self):
        """Cleanup including input system"""
        # Cleanup input system
        if self.input_manager:
            stats = self.input_manager.get_statistics()
            self.logger.log_hardware_event('Input', f'Stats: {stats}')
            self.input_manager.cleanup()

        # Cleanup Arduino
        if self.arduino_reward:
            self.arduino_reward.disconnect()

    def run(self):
        """Main experiment loop"""
        try:
            # User subclass implements pygame UI
            self._run_experiment()
        except Exception as e:
            self.logger.log_error(f"Experiment failed: {e}", exc_info=True)
            self.notifier.send_alert(
                subject=f"Experiment failed on {self.kiosk_manager.config['kiosk_id']}",
                message=f"Subject: {self.subject_id}\nExperiment: {self.experiment_name}\nError: {str(e)}"
            )
            raise
        finally:
            self.cleanup()

    def _run_experiment(self):
        """Override this in subclass to implement experiment logic"""
        raise NotImplementedError("Subclass must implement _run_experiment()")