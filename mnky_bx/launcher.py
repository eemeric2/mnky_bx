# mnky_bx/launcher.py (UPDATED)

def main():
    """
    Launcher with support for different platforms and input methods
    """
    from mnky_bx.utils.config_loader import ConfigLoader
    from mnky_bx.notifications.notification_manager import NotificationManager
    from mnky_bx.core.kiosk_manager import KioskManager
    from mnky_bx.face_recognition_system.recognition_engine import FaceRecognitionEngine
    from mnky_bx.face_recognition_system.subject_parameter_manager import SubjectParameterManager
    from mnky_bx.logging.experiment_logger import ExperimentLogger
    from mnky_bx.ui.launcher_ui import LauncherGUI

    import logging

    # Detect platform and load appropriate config
    import platform
    system = platform.system()

    if system == "Linux":
        # Assume Raspberry Pi
        print("Detected Linux system (Raspberry Pi)")
        config_file = "config/raspi_touchscreen_config.json"
    else:
        # Windows or macOS - use desktop config
        config_file = "config/kiosk_config.json"

    print(f"Loading config from: {config_file}")

    # Load configs
    try:
        kiosk_config = ConfigLoader.load_config(config_file)
    except FileNotFoundError:
        print(f"Config not found: {config_file}")
        kiosk_config = ConfigLoader.load_kiosk_config()  # Fallback

    face_config = ConfigLoader.load_face_recognition_config()

    # Initialize systems
    notification_manager = NotificationManager(kiosk_config)
    kiosk_manager = KioskManager(kiosk_config)
    recognition_engine = FaceRecognitionEngine(face_config)

    # Launch GUI
    launcher = LauncherGUI(kiosk_config)
    selection = launcher.show()

    if not selection:
        return

    experiment_name = selection['experiment']
    param_manager = SubjectParameterManager(experiment_name)

    # Initialize session
    session = kiosk_manager.start_session(
        subject_id="TBD",
        experiment_name=experiment_name
    )

    logger = ExperimentLogger(session['log_file'], level=logging.DEBUG)

    # Load experiment
    import importlib
    experiment_module = importlib.import_module(
        f'experiments.{experiment_name}.experiment'
    )

    ExperimentClass = experiment_module.GamblingExperiment

    # Run
    try:
        experiment = ExperimentClass(
            experiment_name=experiment_name,
            subject_id=None,
            kiosk_manager=kiosk_manager,
            logger=logger,
            notification_manager=notification_manager,
            hardware_config=kiosk_config.get('input_system', {}),
            recognition_engine=recognition_engine,
            parameter_manager=param_manager
        )

        experiment.run()

    except Exception as e:
        logger.log_error(f"Experiment error: {e}", exc_info=True)
        raise