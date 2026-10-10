# Proposed Package Architecture: mnky_bx
Based on the current code structure, here's how I'd organize it:

```python
mnky_bx/
├── mnky_bx/                          # Main package directory
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── experiment_base.py        # Base experiment class (core trial logic, stimulus presentation, database management)
│   │   ├── trial_manager.py          # Trial sequencing, condition management, state tracking
│   │   └── config.py                 # Configuration parameters, condition definitions
│   │
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── camera.py                 # CameraDetectionSystem (motion, face detection, capture)
│   │   ├── arduino_buttons.py        # Arduino buttons controller (LED signals)
│   │   ├── arduino_reward.py         # Arduino reward delivery controller
│   │   └── hardware_interface.py     # Abstract base classes/interfaces for hardware
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_manager.py             # SQLite database management
│   │   └── schemas.py                # Database schema definitions
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging.py                # Logging utilities
│   │   └── helpers.py                # General utility functions
│   │
│   └── ui/
│       ├── __init__.py
│       └── pygame_utils.py           # Pygame wrapper/utilities (stimulus drawing, display management)
│
├── experiments/                       # User experiment implementations
│   ├── blackjack/
│   │   ├── __init__.py
│   │   ├── experiment.py             # Inherits from ExperimentBase, implements pygame UI
│   │   ├── config.py                 # Experiment-specific configuration
│   │   ├── analysis/
│   │   │   └── results/
│   │   └── data/
│   │       └── Media/
│   │
│   └── gambling_experiment/
│       ├── __init__.py
│       ├── experiment.py
│       ├── config.py
│       ├── analysis/
│       │   └── results/
│       └── data/
│           └── Media/
│
├── subjects/
│   ├── subject_id_1/
│   └── subject_id_2/
│
├── setup.py                          # Package setup file
├── requirements.txt                  # Dependencies
└── README.md
```

## Architecture Details
## 1. Core Module (`mnky_bx/core/`)

This contains the experiment framework — shared logic across all experiments:

- `experiment_base.py`: Abstract base class that handles:
  - Trial state management
  - Timing/timestamps
  - Database integration
  - Response handling
  - Outcome revelation
  - Call to pygame UI methods (but users implement the actual drawing)
- `trial_manager.py`: Manages:
  - Trial sequencing
  - Condition randomization/shuffling
  - Block management
- `config.py`: Stores:
  - Timing parameters (ITI, max_RT, etc.)
  - Color palettes
  - Stimulus dimensions
  - Condition definitions (one_opt, two_opt, gamble, etc.)
  
**Key Design Decision**: The base class requires users to implement pygame-specific methods (`draw_stimuli()`, `wait_for_response()`, `reveal_outcome()`, etc.) in their experiment subclass. This decouples the framework from pygame.

## 2. Hardware Module (`mnky_bx/hardware/`)

Encapsulates all hardware interactions:

- camera.py: CameraDetectionSystem class as-is
- arduino_buttons.py: Button reading + LED control
- arduino_reward.py: Reward delivery commands
- hardware_interface.py: Abstract base classes so hardware can be mocked or swapped

**Key Design Decision**: Hardware should be optional/mockable. If not connected, experiments should run in SIMULATE mode.

## 3. Database Module (`mnky_bx/database/`)
Handles all persistence:

- `db_manager.py`: Database connection, setup, queries
- `schemas.py`: Table definitions

**Key Design Decision**: Database connection passed to experiment, so it's decoupled but accessible.

## 4. User Implementation Layer (`experiments/*/`)
This is where users provide pygame code:

```python
# experiments/gambling_experiment/experiment.py

from mnky_bx.core.experiment_base import ExperimentBase
import pygame

class GamblingExperiment(ExperimentBase):
    def __init__(self, config_path):
        super().__init__(config_path)
        # User-specific initialization
    
    def draw_stimuli(self):
        """USER IMPLEMENTS: Draw circles, options, probabilities"""
        pass
    
    def wait_for_response(self):
        """USER IMPLEMENTS: Handle pygame events or Arduino buttons"""
        pass
    
    def reveal_outcome(self):
        """USER IMPLEMENTS: Display feedback/outcome"""
        pass

# experiments/gambling_experiment/config.py
TRIAL_CONDITIONS = [...]  # User defines
COLORS = {...}
STIMULUS_SIZE = 100
```

## Key Design Principles
### Separation of Concerns
- **Framework** ← timing, state, database, trial logic
- **Hardware** ← Arduino, camera operations
- **UI** ← pygame drawing (user responsibility)

### Decoupling
- Base class uses abstract methods for pygame operations
- Hardware modules are optional/mockable
- Configuration externalized to config files

### Extensibility
- Users subclass `ExperimentBase` to implement their specific pygame UI
- New hardware types can extend `HardwareInterface`
- New database fields can be added to schemas

### Data Organization
```python
subject_id_1/
├── experiment_1_data.db       # Database for each experiment run
├── behavioral_logs/           # Trial-by-trial data (CSV exports)
└── Media/
    └── trial_images/          # Camera captures
```
### Integration Flow
1. User creates experiment: Subclasses `ExperimentBase`, implements pygame methods
2. User configures: Sets trial conditions, colors, sizes in local `config.py`
3. User runs: Instantiates experiment, calls `experiment.run()`
4. Framework orchestrates: Handles timing, state, database
5. Hardware modules called: As needed by framework (motion detection, LED control, rewards)
6. UI methods called: Framework calls user's pygame methods when needed

### Questions to Consider
1. **Pygame initialization**: Should the base class initialize pygame, or should user do it? 
    - I PROPOSE WE USE `launcher.py` THAT CREATES A GUI INTEFACE CONTAINING BUTTONS LABELED WITH THE NAMES OF THE DIRECTORIES CONTAINED IN `experiments/`. TAPPING ON A BUTTON LAUNCHES THAT EXPERIMENT
2. **Configuration format**: YAML, JSON, or Python files?
   - JSON FILES SEEM TO BE A REASONABLE CHOICE FOR THIS. DO YOU THINK YAML OR PYTHON FILES MIGHT BE BETTER FOR THIS
3. **Multi-experiment runs**: Should one experiment instance handle multiple subjects/sessions? 
   - THE APPARATUS CAN BE PLACED IN AN ENCLOSURE WITH UP TO A DOZEN SUBJECTS.  
4. **Logging level**: Where should debug/verbose output go? 
   - .TXT LOG FILES E.G. EXP_ID_20261010_134200.txt
5. **Error handling**: How should hardware failures be handled gracefully?
   - AS THIS SYSTEM WILL BE IN THE FORM OF A KIOSK, ON HARDWARE ERROR, THE PROGRAM SHOULD EXIT THE EXPERIMENT DISPLAY AN ERROR SCREEN, AND IF CONNECTED TO A WIRELESS NETWORK SEND AN EMAIL OR TEXT TO THE EXPERIMENTER.  

Would you like me to refine any of these areas?

Excellent clarifications! This fundamentally changes the architecture—you're building a kiosk-based system. Let me refine the architecture:

```graphql
mnky_bx/
├── mnky_bx/                          # Main package directory
│   ├── __init__.py
│   ├── launcher.py                   # ← GUI launcher (NEW)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── experiment_base.py        # Base experiment (no pygame init)
│   │   ├── trial_manager.py          
│   │   ├── kiosk_manager.py          # ← NEW: Multi-subject, session management
│   │   └── config.py                 
│   │
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── camera.py                 
│   │   ├── arduino_buttons.py        
│   │   ├── arduino_reward.py         
│   │   ├── hardware_interface.py
│   │   └── health_monitor.py         # ← NEW: Hardware fault detection
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_manager.py             
│   │   └── schemas.py                
│   │
│   ├── logging/                      # ← NEW: Dedicated logging module
│   │   ├── __init__.py
│   │   ├── experiment_logger.py
│   │   └── error_handler.py
│   │
│   ├── notifications/                # ← NEW: Alert system
│   │   ├── __init__.py
│   │   ├── email_notifier.py
│   │   ├── sms_notifier.py
│   │   └── notification_manager.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   └── config_loader.py          # ← NEW: JSON config handling
│   │
│   └── ui/
│       ├── __init__.py
│       ├── pygame_utils.py           
│       ├── error_screen.py           # ← NEW: Kiosk error display
│       └── launcher_ui.py            # ← NEW: Launcher GUI
│
├── experiments/                       
│   ├── blackjack/
│   │   ├── __init__.py
│   │   ├── experiment.py             
│   │   ├── config.json               # ← JSON (not .py)
│   │   ├── analysis/
│   │   │   └── results/
│   │   └── data/
│   │       └── Media/
│   │
│   └── gambling_experiment/
│       ├── __init__.py
│       ├── experiment.py
│       ├── config.json               # ← JSON
│       ├── analysis/
│       │   └── results/
│       └── data/
│           └── Media/
│
├── subjects/
│   ├── subject_id_1/
│   │   ├── gambling_experiment/
│   │   │   ├── session_001/
│   │   │   │   ├── exp_id_20261010_134200.txt    # ← Log file
│   │   │   │   ├── exp_id_20261010_134200.db
│   │   │   │   └── Media/
│   │   │   ├── session_002/
│   │   │   └── ...
│   │   └── blackjack/
│   │       └── session_001/
│   │
│   └── subject_id_2/
│       └── ...
│
├── config/                           # ← NEW: System-wide configs
│   ├── kiosk_config.json             # Kiosk settings, timeouts, etc.
│   ├── notification_config.json      # Email/SMS settings
│   └── hardware_config.json          # Arduino ports, timeouts
│
├── launcher.py                       # ← NEW: Entry point (kiosk main)
├── setup.py
├── requirements.txt
└── README.md
```

## 1. Launcher System (`launcher.py` + `launcher_ui.py`)
**Entry Point**: User boots kiosk → python `launcher.py`

```python
# mnky_bx/launcher.py
"""
Kiosk launcher - discovers experiments, displays GUI, manages sessions
"""

import os
import json
from pathlib import Path
from mnky_bx.ui.launcher_ui import LauncherGUI

def main():
    # Discover experiments in experiments/ directory
    experiments_dir = Path("experiments")
    available_experiments = [d.name for d in experiments_dir.iterdir() if d.is_dir()]
    
    # Launch GUI
    launcher = LauncherGUI(available_experiments)
    launcher.show()
    
    # User selects experiment -> launcher instantiates and runs it
    # On error -> error_screen displays, email/SMS sent

if __name__ == "__main__":
    main()
```

#### LauncherGUI features:

- Displays buttons for each experiment folder
- Subject ID input field 
- Session number (auto-incremented or manual)
- Large, touch-friendly interface
- Shows connection status (Arduino, camera, network)

## 2. Configuration: JSON Format (NOT YAML, NOT Python)
Why JSON over YAML/Python?

- ✅ Human-readable 
- ✅ Easy to edit in any text editor (non-programmers can adjust)
- ✅ JSON schema validation possible 
- ✅ Works with all languages (future web interface, mobile admin app)
- ✅ No security risk like Python (arbitrary code execution)
- ❌ YAML: Overkill for simple config, indentation issues 
- ❌ Python: Security risk, requires code redeployment

#### System-wide config example:

```json
// mnky_bx/config/kiosk_config.json
{
  "kiosk_id": "kiosk_001",
  "display": {
    "width": 1920,
    "height": 1080,
    "fullscreen": true,
    "refresh_rate": 60
  },
  "hardware": {
    "arduino_buttons_port": "COM3",
    "arduino_reward_port": "COM4",
    "camera_index": 0,
    "motion_detection_timeout_s": 300,
    "face_detection_timeout_s": 10
  },
  "logging": {
    "level": "DEBUG",
    "log_directory": "subjects/"
  },
  "notifications": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "kiosk001@lab.edu",
    "alert_emails": ["experimenter@lab.edu"],
    "alert_numbers": ["+14105551234"]
  },
  "session_management": {
    "max_subjects_per_kiosk": 12,
    "auto_cleanup_interval_hours": 24
  }
}
```

#### Experiment-specific config:

```json
// experiments/gambling_experiment/config.json
{
  "experiment_name": "Gambling Task",
  "experiment_version": "1.0",
  "max_trials": 48,
  "timing": {
    "iti_ms": 1000,
    "max_response_time_ms": 5000,
    "outcome_display_ms": 1500
  },
  "stimulus": {
    "circle_radius": 100,
    "colors": {
      "background": [0, 0, 0],
      "dark_red": [127, 0, 0],
      "dark_orange": [200, 75, 0],
      "gold": [255, 215, 0],
      "green": [0, 128, 0],
      "sky_blue": [0, 215, 255],
      "dark_blue": [0, 0, 131],
      "dark_purple": [48, 25, 52]
    }
  },
  "trial_conditions": {
    "one_opt": [...],
    "two_opt": [...],
    "gamble_sure": [...],
    "gamble_gamble": [...]
  }
}
```
#### Config loader utility:

```python
# mnky_bx/utils/config_loader.py
import json
from pathlib import Path

class ConfigLoader:
    @staticmethod
    def load_kiosk_config():
        """Load system-wide kiosk configuration"""
        config_path = Path("mnky_bx/config/kiosk_config.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def load_experiment_config(experiment_name):
        """Load experiment-specific configuration"""
        config_path = Path(f"experiments/{experiment_name}/config.json")
        with open(config_path, 'r') as f:
            return json.load(f)
```
## 3. Multi-Subject, Multi-Session Kiosk Manager
New module: `kiosk_manager.py`

```python
# mnky_bx/core/kiosk_manager.py
"""
Manages multiple subjects and sessions on a kiosk
Handles subject enrollment, session tracking, data organization
"""

from pathlib import Path
from datetime import datetime
import json

class KioskManager:
    def __init__(self, kiosk_config):
        self.config = kiosk_config
        self.subjects_dir = Path("subjects")
        self.current_session = None
    
    def start_session(self, subject_id, experiment_name):
        """
        Initialize a new experiment session for a subject
        
        Returns:
            session_info: {
                subject_id,
                experiment_name,
                session_number,
                session_dir,
                timestamp
            }
        """
        subject_dir = self.subjects_dir / subject_id / experiment_name
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-increment session number
        existing_sessions = [d for d in subject_dir.iterdir() if d.is_dir()]
        session_number = len(existing_sessions) + 1
        
        session_dir = subject_dir / f"session_{session_number:03d}"
        session_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        self.current_session = {
            'subject_id': subject_id,
            'experiment_name': experiment_name,
            'session_number': session_number,
            'session_dir': session_dir,
            'timestamp': timestamp,
            'timestamp_str': timestamp_str,
            'log_file': session_dir / f"exp_{timestamp_str}.txt"
        }
        
        return self.current_session
    
    def get_data_directory(self):
        """Return current session data directory"""
        if not self.current_session:
            raise RuntimeError("No active session")
        return self.current_session['session_dir']
    
    def get_log_file_path(self):
        """Return path for current session log file"""
        if not self.current_session:
            raise RuntimeError("No active session")
        return self.current_session['log_file']
    
    def get_enrolled_subjects(self):
        """List all enrolled subjects"""
        return [d.name for d in self.subjects_dir.iterdir() if d.is_dir()]
```
## 4. Logging System (`logging`/ module)
Centralized logging to .txt files:

```python
# mnky_bx/logging/experiment_logger.py
"""
Logs experiment events to .txt files
"""

import logging
from pathlib import Path
from datetime import datetime

class ExperimentLogger:
    def __init__(self, log_file_path, level=logging.DEBUG):
        self.log_file = log_file_path
        self.logger = self._setup_logger(level)
    
    def _setup_logger(self, level):
        """Configure logger with file handler"""
        logger = logging.getLogger(__name__)
        logger.setLevel(level)
        
        # File handler
        fh = logging.FileHandler(self.log_file, mode='w')
        fh.setLevel(level)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def log_trial(self, trial_num, trial_type, choice, outcome, timestamps):
        """Log a single trial"""
        self.logger.info(
            f"Trial {trial_num:03d} | Type: {trial_type:20s} | "
            f"Choice: {choice:8s} | Outcome: {outcome:8s} | "
            f"RT: {timestamps['response_time']}ms"
        )
    
    def log_hardware_event(self, device, event, details=""):
        """Log hardware events"""
        self.logger.warning(f"[{device}] {event} | {details}")
    
    def log_error(self, error_msg, exc_info=None):
        """Log error with optional exception traceback"""
        self.logger.error(error_msg, exc_info=exc_info)

# Usage in experiment:
# logger.log_trial(1, 'choice_sure', 'left', 'won', {...})
# logger.log_hardware_event('arduino_buttons', 'Connection lost')
```
Log file format example:

```yaml
2026-10-10 13:42:00 | DEBUG    | Experiment initialized
2026-10-10 13:42:05 | DEBUG    | Motion detection started
2026-10-10 13:42:15 | DEBUG    | Face detected, trial began
2026-10-10 13:42:17 | INFO     | Trial 001 | Type: choice_sure    | Choice: left     | Outcome: won      | RT: 1234ms
2026-10-10 13:42:19 | INFO     | Trial 002 | Type: choice_gamble  | Choice: right    | Outcome: lost     | RT: 2105ms
2026-10-10 13:43:00 | WARNING  | [arduino_buttons] Connection lost | Retrying...
2026-10-10 13:43:02 | ERROR    | Hardware failure: Arduino buttons unresponsive after 3 retries
```
## 5. Hardware Health Monitoring & Error Handling
#### New module: `hardware_health_monitor.py`

```python
# mnky_bx/hardware/health_monitor.py
"""
Monitors hardware health and gracefully handles failures
"""

class HardwareHealthMonitor:
    def __init__(self, config, notification_manager):
        self.config = config
        self.notifier = notification_manager
        self.failures = {}
    
    def check_arduino_buttons(self, timeout_s=5):
        """Test Arduino buttons connection"""
        try:
            # Send test command with timeout
            # Return True if success
            return True
        except Exception as e:
            self._handle_hardware_failure(
                device='arduino_buttons',
                error=str(e),
                severity='critical'
            )
            return False
    
    def check_camera(self, timeout_s=5):
        """Test camera connection"""
        try:
            # Attempt to capture frame
            return True
        except Exception as e:
            self._handle_hardware_failure(
                device='camera',
                error=str(e),
                severity='warning'
            )
            return False
    
    def check_all_hardware(self):
        """Full hardware health check"""
        results = {
            'arduino_buttons': self.check_arduino_buttons(),
            'camera': self.check_camera(),
            'network': self._check_network()
        }
        return results
    
    def _handle_hardware_failure(self, device, error, severity='warning'):
        """Handle hardware failure gracefully"""
        self.failures[device] = {
            'error': error,
            'timestamp': datetime.now(),
            'severity': severity
        }
        
        # Log
        logging.warning(f"Hardware failure: {device} - {error}")
        
        # If critical, notify immediately
        if severity == 'critical':
            self.notifier.send_alert(
                subject=f"CRITICAL: {device} failure on kiosk",
                message=f"Device: {device}\nError: {error}\nKiosk ID: {self.config['kiosk_id']}"
            )
```
## 6. Notification System (Email/SMS on Hardware Failure)

#### New module: `notification_manager.py`

```python
# mnky_bx/notifications/notification_manager.py
"""
Sends alerts via email/SMS on hardware failures or critical errors
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client  # For SMS

class NotificationManager:
    def __init__(self, config):
        self.config = config
        self.enabled = config['notifications']['enabled']
        
        if self.enabled:
            self._setup_email()
            self._setup_sms()
    
    def _setup_email(self):
        """Configure SMTP"""
        cfg = self.config['notifications']
        self.smtp_server = cfg['smtp_server']
        self.smtp_port = cfg['smtp_port']
        self.from_email = cfg['from_email']
        self.to_emails = cfg['alert_emails']
    
    def _setup_sms(self):
        """Configure Twilio (requires account_sid and auth_token in config)"""
        cfg = self.config['notifications']
        if 'twilio_account_sid' in cfg:
            self.twilio_client = Client(
                cfg['twilio_account_sid'],
                cfg['twilio_auth_token']
            )
            self.to_numbers = cfg['alert_numbers']
    
    def send_alert(self, subject, message, include_sms=True):
        """Send email and optional SMS alert"""
        if not self.enabled:
            return
        
        try:
            self._send_email(subject, message)
            if include_sms:
                self._send_sms(f"{subject}: {message}")
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
    
    def _send_email(self, subject, body):
        """Send email via SMTP"""
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.from_email, self.password)  # Password in env var
            server.send_message(msg)
    
    def _send_sms(self, message):
        """Send SMS via Twilio"""
        for phone in self.to_numbers:
            self.twilio_client.messages.create(
                body=message,
                from_=self.config['notifications']['twilio_phone'],
                to=phone
            )
```
## 7. Error Screen (Kiosk Display)
New module: `error_screen.py`

```python
# mnky_bx/ui/error_screen.py
"""
Displays error screen on kiosk when hardware fails
"""

import pygame
import sys

class ErrorScreen:
    def __init__(self, error_message, kiosk_id, is_critical=False):
        """
        Display error screen on kiosk
        
        Args:
            error_message: Human-readable error description
            kiosk_id: Which kiosk this is
            is_critical: If True, loop until manually reset
        """
        pygame.init()
        self.display = pygame.display.set_mode(
            (1920, 1080),
            pygame.FULLSCREEN
        )
        pygame.display.set_caption("Error - Kiosk")
        
        self.error_message = error_message
        self.kiosk_id = kiosk_id
        self.is_critical = is_critical
    
    def show(self, duration_s=None):
        """
        Display error screen
        
        Args:
            duration_s: How long to show (None = wait for keypress)
        """
        clock = pygame.time.Clock()
        running = True
        start_time = pygame.time.get_ticks()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if not self.is_critical:
                        running = False
            
            # Draw error screen
            self.display.fill((200, 0, 0))  # Red background
            
            font_large = pygame.font.Font(None, 80)
            font_small = pygame.font.Font(None, 40)
            
            error_text = font_large.render("ERROR", True, (255, 255, 255))
            msg_text = font_small.render(self.error_message, True, (255, 255, 255))
            kiosk_text = font_small.render(f"Kiosk ID: {self.kiosk_id}", True, (255, 255, 255))
            contact_text = font_small.render(
                "Alert has been sent to experimenter. Please wait...",
                True, (255, 255, 255)
            )
            
            self.display.blit(error_text, (960 - error_text.get_width()//2, 300))
            self.display.blit(msg_text, (960 - msg_text.get_width()//2, 500))
            self.display.blit(kiosk_text, (960 - kiosk_text.get_width()//2, 700))
            self.display.blit(contact_text, (960 - contact_text.get_width()//2, 800))
            
            pygame.display.flip()
            
            # Auto-exit after duration
            if duration_s and (pygame.time.get_ticks() - start_time) > duration_s * 1000:
                running = False
            
            clock.tick(30)
        
        pygame.quit()
```

## 8. Updated Experiment Base Class
The base class now receives injected dependencies (kiosk manager, logger, notification manager):

```python
# mnky_bx/core/experiment_base.py
"""
Base experiment class - provides framework for all experiments
Users subclass this and implement pygame-specific methods
"""

class ExperimentBase:
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
        
        # ... rest of initialization
    
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
```
## 9. Launcher GUI Implementation
```python
# mnky_bx/ui/launcher_ui.py
"""
Kiosk launcher GUI - displays available experiments, subject selection
"""

import pygame
from pathlib import Path

class LauncherGUI:
    def __init__(self, available_experiments, kiosk_config):
        pygame.init()
        self.display = pygame.display.set_mode(
            (kiosk_config['display']['width'], 
             kiosk_config['display']['height']),
            pygame.FULLSCREEN
        )
        pygame.display.set_caption("Kiosk Launcher")
        
        self.experiments = available_experiments
        self.kiosk_config = kiosk_config
        self.selected_experiment = None
        self.subject_id = ""
        self.state = 'experiment_selection'  # or 'subject_selection'
    
    def show(self):
        """Display launcher GUI"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == 'subject_selection':
                        if event.key == pygame.K_RETURN:
                            running = False  # Start experiment
                        elif event.key == pygame.K_BACKSPACE:
                            self.subject_id = self.subject_id[:-1]
                        else:
                            self.subject_id += event.unicode
            
            # Draw current state
            self._draw_frame()
            pygame.display.flip()
            clock.tick(30)
        
        return {'experiment': self.selected_experiment, 'subject_id': self.subject_id}
    
    def _draw_frame(self):
        """Draw launcher screen"""
        self.display.fill((50, 50, 50))
        
        if self.state == 'experiment_selection':
            self._draw_experiment_selection()
        elif self.state == 'subject_selection':
            self._draw_subject_selection()
    
    def _draw_experiment_selection(self):
        """Draw experiment selection buttons"""
        # TODO: Implement button grid layout
        pass
    
    def _draw_subject_selection(self):
        """Draw subject ID input screen"""
        # TODO: Implement text input
        pass
```
# Summary of Changes
| Aspect |                      New/Changed                       |
| :--- |:------------------------------------------------------:| 
| Entry Point |      `launcher.py` - GUI for experiment selection      |
| Configuration	|          JSON files (system + per-experiment)          | 
| Multi-Subject|   	KioskManager handles sessions & data organization    | 
| Logging | 	Dedicated logging/ module, .txt files in session dirs  | 
| Error Handling |  	HardwareHealthMonitor + ErrorScreen + notifications   | 
| Notifications | 	Email/SMS on critical failures via NotificationManager | 
| Pygame Init|   	Handled by launcher.py, not experiment base class    | 

# Configuration Files Needed
1. `mnky_bx/config/kiosk_config.json` - System defaults 
2. `mnky_bx/config/notification_config.json` - SMTP/Twilio credentials 
3. `experiments/*/config.json` - Per-experiment settings 
4. `.env or secrets.json` - SMTP passwords, API keys (gitignore this)
 
**Does this architecture address all your kiosk requirements?** Any other considerations (e.g., subject pre-enrollment, experiment scheduling, data exports)?


Excellent! This is a significant addition that fundamentally changes the architecture. Let me map out a comprehensive design for **face recognition-based subject identification and adaptive parameters.**


Used 2 tools
— File Search
Searched your files

Perfect! Now I have the full picture. Let me design a comprehensive Face Recognition & Subject Identification System with adaptive trial parameters. This is a substantial architectural piece.

# Enhanced Architecture: Face Recognition & Adaptive Parameters
```graphql
mnky_bx/
├── mnky_bx/
│   ├── __init__.py
│   ├── launcher.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── experiment_base.py
│   │   ├── trial_manager.py
│   │   ├── kiosk_manager.py
│   │   └── config.py
│   │
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── camera/                    # ← NEW SUBMODULE
│   │   │   ├── __init__.py
│   │   │   ├── camera_system.py       # Motion & face detection
│   │   │   ├── face_recognition.py    # ← NEW: Recognition engine
│   │   │   ├── face_encoder.py        # ← NEW: Feature extraction
│   │   │   └── capture_manager.py     # ← NEW: Image acquisition & storage
│   │   │
│   │   ├── arduino_buttons.py
│   │   ├── arduino_reward.py
│   │   ├── hardware_interface.py
│   │   └── health_monitor.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_manager.py
│   │   └── schemas.py
│   │
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── experiment_logger.py
│   │   └── error_handler.py
│   │
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── email_notifier.py
│   │   ├── sms_notifier.py
│   │   └── notification_manager.py
│   │
│   ├── face_recognition_system/       # ← NEW MAJOR MODULE
│   │   ├── __init__.py
│   │   ├── subject_registry.py        # Subject metadata management
│   │   ├── recognition_engine.py      # Recognition + identification
│   │   ├── face_database.py           # Face embeddings database
│   │   └── subject_parameter_manager.py  # ← NEW: Subject-specific params
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   └── config_loader.py
│   │
│   └── ui/
│       ├── __init__.py
│       ├── pygame_utils.py
│       ├── error_screen.py
│       ├── launcher_ui.py
│       └── subject_enrollment_ui.py   # ← NEW: GUI for enrollment
│
├── experiments/
│   ├── gambling_experiment/
│   │   ├── experiment.py
│   │   ├── config.json
│   │   └── subject_params/            # ← NEW: Subject-specific configs
│   │       ├── default.json
│   │       ├── subject_id_1.json
│   │       └── subject_id_2.json
│   │
│   └── blackjack/
│       ├── experiment.py
│       ├── config.json
│       └── subject_params/
│           └── default.json
│
├── subjects/                          # ← RESTRUCTURED
│   ├── not_recognized/                # Unidentified faces (no subject match)
│   │   ├── raw_images/
│   │   │   ├── trial_001_frame_001.jpg
│   │   │   ├── trial_001_frame_002.jpg
│   │   │   └── ...
│   │   ├── embeddings/                # Face embeddings for unknown subjects
│   │   │   └── embeddings.pkl
│   │   └── clustering_results.json    # OpenCV clustering output
│   │
│   ├── subject_id_1/                  # Identified subject directory
│   │   ├── metadata.json              # Subject profile + face data
│   │   ├── face_encodings/            # Face recognition training data
│   │   │   ├── reference_faces/       # High-quality enrollment images
│   │   │   │   ├── face_001.jpg
│   │   │   │   ├── face_002.jpg
│   │   │   │   └── embeddings.pkl     # Pre-computed embeddings
│   │   │   └── temp/                  # Processing cache
│   │   │
│   │   ├── gambling_experiment/       # Per-experiment data
│   │   │   ├── session_001/
│   │   │   │   ├── exp_id_20261010_134200.txt   # Log
│   │   │   │   ├── exp_id_20261010_134200.db    # Behavioral data
│   │   │   │   ├── trial_images/                # Trial images
│   │   │   │   │   ├── trial_001.jpg
│   │   │   │   │   ├── trial_002.jpg
│   │   │   │   │   └── recognition_log.json     # ← NEW
│   │   │   │   └── Media/
│   │   │   ├── session_002/
│   │   │   └── active_parameters.json # Currently active params for this experiment
│   │   │
│   │   ├── blackjack/
│   │   │   └── session_001/
│   │   │
│   │   └── recognition_history.json   # Trial-by-trial recognition results
│   │
│   └── subject_id_2/
│       └── ...
│
├── config/
│   ├── kiosk_config.json
│   ├── notification_config.json
│   ├── hardware_config.json
│   └── face_recognition_config.json   # ← NEW
│
├── launcher.py
├── setup.py
├── requirements.txt
└── README.md
```

# 1. Face Recognition System Architecture
## A. Core Recognition Engine Module
```python
# mnky_bx/face_recognition_system/recognition_engine.py
"""
Face recognition and subject identification engine
Uses face embeddings for matching against enrolled subjects
"""

from pathlib import Path
import numpy as np
import pickle
import json
from dataclasses import dataclass
from typing import Optional, Tuple, List
from datetime import datetime

@dataclass
class RecognitionResult:
    """Result of face recognition attempt"""
    recognized: bool
    subject_id: Optional[str]
    confidence: float  # 0.0-1.0
    matched_face: Optional[str]  # Path to matched reference face
    embedding: Optional[np.ndarray]  # The face embedding
    timestamp: datetime
    status: str  # 'recognized', 'unrecognized', 'ambiguous'

class FaceRecognitionEngine:
    """
    Identifies subjects based on face recognition
    """
    
    def __init__(self, config, subjects_root="subjects"):
        """
        Args:
            config: Face recognition config dict with:
                - embedding_model: 'facenet', 'deepface', etc.
                - confidence_threshold: float (0.0-1.0)
                - distance_threshold: float (euclidean distance)
                - max_matches_to_check: int
            subjects_root: Root directory containing subject folders
        """
        self.config = config
        self.subjects_root = Path(subjects_root)
        self.confidence_threshold = config['confidence_threshold']
        self.distance_threshold = config['distance_threshold']
        
        # Load face encoder
        from mnky_bx.hardware.camera.face_encoder import FaceEncoder
        self.encoder = FaceEncoder(config['embedding_model'])
        
        # Load all enrolled subject embeddings
        self.enrolled_subjects = {}  # {subject_id: {'embeddings': [...], 'metadata': {...}}}
        self._load_enrolled_subjects()
    
    def _load_enrolled_subjects(self):
        """Load all enrolled subjects' face embeddings"""
        print("Loading enrolled subjects...")
        
        for subject_dir in self.subjects_root.iterdir():
            if not subject_dir.is_dir():
                continue
            
            subject_id = subject_dir.name
            if subject_id == 'not_recognized':
                continue  # Skip unrecognized folder
            
            embeddings_file = subject_dir / 'face_encodings' / 'embeddings.pkl'
            metadata_file = subject_dir / 'metadata.json'
            
            if embeddings_file.exists() and metadata_file.exists():
                try:
                    with open(embeddings_file, 'rb') as f:
                        embeddings = pickle.load(f)  # List of np.arrays
                    
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    self.enrolled_subjects[subject_id] = {
                        'embeddings': embeddings,
                        'metadata': metadata,
                        'num_faces': len(embeddings)
                    }
                    print(f"  Loaded {subject_id}: {len(embeddings)} faces")
                
                except Exception as e:
                    print(f"  Error loading {subject_id}: {e}")
    
    def recognize_face(self, face_image) -> RecognitionResult:
        """
        Attempt to identify subject from face image
        
        Args:
            face_image: np.ndarray (BGR, from OpenCV)
        
        Returns:
            RecognitionResult with identification details
        """
        start_time = datetime.now()
        
        # Extract embedding from new face
        try:
            query_embedding = self.encoder.extract_embedding(face_image)
        except Exception as e:
            return RecognitionResult(
                recognized=False,
                subject_id=None,
                confidence=0.0,
                matched_face=None,
                embedding=None,
                timestamp=start_time,
                status=f'error: {str(e)}'
            )
        
        # Find best match in enrolled subjects
        best_match = None
        best_distance = float('inf')
        best_subject_id = None
        
        for subject_id, data in self.enrolled_subjects.items():
            for ref_embedding in data['embeddings']:
                # Euclidean distance
                distance = np.linalg.norm(query_embedding - ref_embedding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_subject_id = subject_id
                    best_match = ref_embedding
        
        # Determine if match is confident enough
        if best_distance < self.distance_threshold:
            confidence = 1.0 - (best_distance / self.distance_threshold)
            recognized = confidence >= self.confidence_threshold
        else:
            confidence = 0.0
            recognized = False
        
        return RecognitionResult(
            recognized=recognized,
            subject_id=best_subject_id if recognized else None,
            confidence=confidence,
            matched_face=None,  # Could store reference path
            embedding=query_embedding,
            timestamp=start_time,
            status='recognized' if recognized else ('ambiguous' if confidence > 0.3 else 'unrecognized')
        )
    
    def batch_recognize_faces(self, face_images: List) -> List[RecognitionResult]:
        """Recognize multiple faces (from trial video)"""
        results = []
        for face_image in face_images:
            results.append(self.recognize_face(face_image))
        return results
    
    def get_best_recognition_from_trial(self, trial_results: List[RecognitionResult]) -> RecognitionResult:
        """
        Select best recognition result from a trial
        Handles multiple frames captured during trial
        """
        # Strategy: Use highest-confidence recognized face
        recognized_results = [r for r in trial_results if r.recognized]
        
        if recognized_results:
            best = max(recognized_results, key=lambda r: r.confidence)
            return best
        
        # If no recognized faces, return unrecognized (highest confidence)
        if trial_results:
            best_unrecognized = max(trial_results, key=lambda r: r.confidence)
            return best_unrecognized
        
        # Fallback: completely failed
        return RecognitionResult(
            recognized=False,
            subject_id=None,
            confidence=0.0,
            matched_face=None,
            embedding=None,
            timestamp=datetime.now(),
            status='no_faces_detected'
        )
    
    def enroll_new_subject(self, subject_id: str, face_images: List, metadata: dict):
        """
        Enroll a new subject by computing embeddings from reference faces
        
        Args:
            subject_id: New subject identifier
            face_images: List of high-quality face images (np.ndarray)
            metadata: Subject metadata (age, species, etc.)
        """
        subject_dir = self.subjects_root / subject_id
        subject_dir.mkdir(exist_ok=True)
        
        encodings_dir = subject_dir / 'face_encodings'
        encodings_dir.mkdir(exist_ok=True)
        ref_faces_dir = encodings_dir / 'reference_faces'
        ref_faces_dir.mkdir(exist_ok=True)
        
        # Extract embeddings
        embeddings = []
        for i, face_img in enumerate(face_images):
            embedding = self.encoder.extract_embedding(face_img)
            embeddings.append(embedding)
            
            # Save reference image
            cv2.imwrite(
                str(ref_faces_dir / f'face_{i:03d}.jpg'),
                face_img
            )
        
        # Save embeddings
        with open(encodings_dir / 'embeddings.pkl', 'wb') as f:
            pickle.dump(embeddings, f)
        
        # Save metadata
        with open(subject_dir / 'metadata.json', 'w') as f:
            metadata['enrolled_date'] = datetime.now().isoformat()
            metadata['num_reference_faces'] = len(embeddings)
            json.dump(metadata, f, indent=2)
        
        # Update in-memory registry
        self.enrolled_subjects[subject_id] = {
            'embeddings': embeddings,
            'metadata': metadata,
            'num_faces': len(embeddings)
        }
        
        print(f"Subject {subject_id} enrolled with {len(embeddings)} reference faces")
```
## B. Face Encoder (Feature Extraction)
```python
# mnky_bx/hardware/camera/face_encoder.py
"""
Extract face embeddings using various models
Supports: FaceNet, DeepFace, MediaPipe, etc.
"""

import numpy as np
import cv2
from typing import Optional

class FaceEncoder:
    """Extract face embeddings"""
    
    def __init__(self, model='facenet'):
        """
        Args:
            model: 'facenet', 'deepface', 'mediapipe', 'arcface'
        """
        self.model_name = model
        self.model = self._load_model(model)
    
    def _load_model(self, model):
        """Load specified embedding model"""
        if model == 'facenet':
            # from keras_facenet import FaceNet
            # return FaceNet()
            pass
        elif model == 'deepface':
            # from deepface import DeepFace
            # return DeepFace
            pass
        elif model == 'mediapipe':
            # from mediapipe.solutions import face_detection
            pass
        # ... etc
    
    def extract_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extract face embedding (512-dim vector)
        
        Args:
            face_image: Cropped face image (np.ndarray, BGR)
        
        Returns:
            Embedding vector (1D numpy array)
        """
        if self.model_name == 'facenet':
            # Preprocess
            preprocessed = self._preprocess_facenet(face_image)
            # Extract embedding
            embedding = self.model.predict(preprocessed)[0]
        
        elif self.model_name == 'deepface':
            embedding = self.model.represent(face_image, model_name='Facenet512')[0]['embedding']
        
        # Normalize to unit vector
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def _preprocess_facenet(self, face_image):
        """FaceNet-specific preprocessing"""
        # Resize to 160x160
        face_image = cv2.resize(face_image, (160, 160))
        # Normalize to [-1, 1]
        face_image = (face_image / 255.0) - 0.5
        face_image = face_image * 2.0
        return np.expand_dims(face_image, axis=0)
```
## C. Subject Registry & Metadata
```python
# mnky_bx/face_recognition_system/subject_registry.py
"""
Manage subject registry and metadata
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

class SubjectRegistry:
    """
    Central registry for all enrolled subjects
    Maintains metadata about each subject
    """
    
    def __init__(self, subjects_root="subjects"):
        self.subjects_root = Path(subjects_root)
        self.registry = {}  # {subject_id: metadata}
        self._load_registry()
    
    def _load_registry(self):
        """Load all subject metadata"""
        for subject_dir in self.subjects_root.iterdir():
            if not subject_dir.is_dir() or subject_dir.name == 'not_recognized':
                continue
            
            metadata_file = subject_dir / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.registry[subject_dir.name] = json.load(f)
    
    def get_subject_metadata(self, subject_id: str) -> Optional[Dict]:
        """Get metadata for a subject"""
        return self.registry.get(subject_id)
    
    def register_new_subject(self, subject_id: str, metadata: Dict) -> bool:
        """Register a new subject"""
        if subject_id in self.registry:
            print(f"Subject {subject_id} already registered")
            return False
        
        self.registry[subject_id] = {
            **metadata,
            'enrolled_date': datetime.now().isoformat(),
            'total_sessions': 0,
            'total_trials': 0
        }
        return True
    
    def update_subject_stats(self, subject_id: str, session_data: Dict):
        """Update subject statistics after session"""
        if subject_id in self.registry:
            self.registry[subject_id]['total_sessions'] += 1
            self.registry[subject_id]['total_trials'] += session_data.get('num_trials', 0)
            self.registry[subject_id]['last_session'] = datetime.now().isoformat()
    
    def list_all_subjects(self) -> List[str]:
        """Get list of all enrolled subjects"""
        return list(self.registry.keys())
```
## D. Subject-Specific Parameter Manager
```python
# mnky_bx/face_recognition_system/subject_parameter_manager.py
"""
Manage subject-specific trial parameters
Each recognized subject can have custom experiment parameters
"""

import json
from pathlib import Path
from typing import Dict, Optional

class SubjectParameterManager:
    """
    Load and manage adaptive parameters for each subject
    Falls back to defaults for unrecognized subjects
    """
    
    def __init__(self, experiment_name: str, experiments_root="experiments"):
        self.experiment_name = experiment_name
        self.experiments_root = Path(experiments_root)
        
        # Load default parameters
        default_config_path = (
            self.experiments_root / experiment_name / 
            'subject_params' / 'default.json'
        )
        with open(default_config_path, 'r') as f:
            self.default_params = json.load(f)
        
        # Cache for loaded subject parameters
        self.subject_params_cache = {}
    
    def get_parameters_for_subject(self, subject_id: Optional[str]) -> Dict:
        """
        Get trial parameters for a subject
        
        Args:
            subject_id: Subject identifier (None = use defaults)
        
        Returns:
            Dictionary of parameters for this trial
        """
        if subject_id is None:
            return self.default_params.copy()
        
        # Check cache
        if subject_id in self.subject_params_cache:
            return self.subject_params_cache[subject_id]
        
        # Try to load subject-specific parameters
        subject_config_path = (
            self.experiments_root / self.experiment_name /
            'subject_params' / f'{subject_id}.json'
        )
        
        if subject_config_path.exists():
            with open(subject_config_path, 'r') as f:
                params = json.load(f)
            
            # Merge with defaults (subject params override defaults)
            merged_params = {**self.default_params, **params}
            self.subject_params_cache[subject_id] = merged_params
            return merged_params
        
        else:
            # Use defaults for unknown subjects
            return self.default_params.copy()
    
    def save_subject_parameters(self, subject_id: str, parameters: Dict):
        """Save custom parameters for a subject"""
        subject_config_path = (
            self.experiments_root / self.experiment_name /
            'subject_params' / f'{subject_id}.json'
        )
        
        subject_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(subject_config_path, 'w') as f:
            json.dump(parameters, f, indent=2)
        
        # Update cache
        self.subject_params_cache[subject_id] = parameters.copy()
```
# 2. Camera System Updates
## A. Capture Manager (Image Storage)
```python
# mnky_bx/hardware/camera/capture_manager.py
"""
Manages image capture and storage during trials
Handles face detection and routing to appropriate directories
"""

import cv2
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict

@dataclass
class CapturedFaceData:
    """Metadata for a captured face"""
    trial_number: int
    timestamp: datetime
    frame_number: int
    face_image: 'np.ndarray'  # Cropped face
    full_frame: 'np.ndarray'  # Full camera frame
    face_bbox: tuple  # (x, y, w, h) from detection

class CaptureManager:
    """
    Manages image capture during trials and routes to storage
    """
    
    def __init__(self, 
                 recognition_engine,
                 session_dir: Path,
                 subject_id: Optional[str] = None):
        """
        Args:
            recognition_engine: FaceRecognitionEngine instance
            session_dir: Directory to save images
            subject_id: Current subject (None = unrecognized)
        """
        self.recognition_engine = recognition_engine
        self.session_dir = Path(session_dir)
        self.current_subject_id = subject_id
        
        # Create directories
        self.trial_images_dir = session_dir / 'trial_images'
        self.trial_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Recognition log for this session
        self.recognition_log = []
    
    def process_and_store_captured_face(self, 
                                       face_data: CapturedFaceData) -> Dict:
        """
        Process captured face: recognize subject, store image, log result
        
        Returns:
            Recognition result dictionary
        """
        # Attempt recognition
        recognition_result = self.recognition_engine.recognize_face(face_data.face_image)
        
        # Determine storage directory
        if recognition_result.recognized:
            subject_id = recognition_result.subject_id
            storage_dir = Path('subjects') / subject_id / 'trial_images'
        else:
            subject_id = 'not_recognized'
            storage_dir = Path('subjects') / 'not_recognized' / 'raw_images'
        
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Save face image
        timestamp_str = face_data.timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]
        face_filename = f"trial_{face_data.trial_number:03d}_frame_{face_data.frame_number:03d}.jpg"
        face_path = storage_dir / face_filename
        cv2.imwrite(str(face_path), face_data.face_image)
        
        # Also save full frame to session directory
        session_face_filename = f"trial_{face_data.trial_number:03d}_frame_{face_data.frame_number:03d}_full.jpg"
        session_path = self.trial_images_dir / session_face_filename
        cv2.imwrite(str(session_path), face_data.full_frame)
        
        # Log result
        log_entry = {
            'trial_number': face_data.trial_number,
            'frame_number': face_data.frame_number,
            'timestamp': face_data.timestamp.isoformat(),
            'recognized': recognition_result.recognized,
            'subject_id': recognition_result.subject_id,
            'confidence': float(recognition_result.confidence),
            'status': recognition_result.status,
            'face_path': str(face_path),
            'session_path': str(session_path)
        }
        self.recognition_log.append(log_entry)
        
        # Return result for experiment to use
        return {
            'subject_id': subject_id,
            'recognized': recognition_result.recognized,
            'confidence': recognition_result.confidence,
            'status': recognition_result.status
        }
    
    def save_recognition_log(self):
        """Save recognition log for this session"""
        log_file = self.trial_images_dir / 'recognition_log.json'
        with open(log_file, 'w') as f:
            json.dump(self.recognition_log, f, indent=2)
```
## B. Updated CameraDetectionSystem
```python
# mnky_bx/hardware/camera/camera_system.py (UPDATED)
"""
Camera detection system with face recognition integration
"""

class CameraDetectionSystem:
    def __init__(self, config, recognition_engine):
        """
        Args:
            config: Camera config
            recognition_engine: FaceRecognitionEngine for identification
        """
        print('Camera setup...')
        self.cap = cv2.VideoCapture(0)
        # ... existing camera setup ...
        
        # NEW: Face recognition
        self.recognition_engine = recognition_engine
        self.capture_manager = None  # Initialized per-trial
        
        # Tracking
        self.last_recognized_subject = None
        self.recognition_confidence = 0.0
    
    def _picture_capture_thread_with_recognition(self, trial_number: int):
        """
        UPDATED: Capture pictures AND perform recognition
        """
        print(f"Picture capture + recognition thread started for trial {trial_number}")
        frame_interval = 1.0 / 3.0  # 3 FPS
        frame_number = 0
        
        captured_faces = []  # Store for batch processing
        
        while self.capture_pictures and not self.stop_detection.is_set():
            start_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Detect faces in frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
            )
            
            # Process each detected face
            for (x, y, w, h) in faces:
                face_image = frame[y:y+h, x:x+w]
                
                # Create face data
                face_data = CapturedFaceData(
                    trial_number=trial_number,
                    timestamp=datetime.now(),
                    frame_number=frame_number,
                    face_image=face_image,
                    full_frame=frame.copy(),
                    face_bbox=(x, y, w, h)
                )
                
                # Store and recognize
                result = self.capture_manager.process_and_store_captured_face(face_data)
                captured_faces.append(result)
                
                # Update tracking
                if result['recognized']:
                    self.last_recognized_subject = result['subject_id']
                    self.recognition_confidence = result['confidence']
                
                print(f"Trial {trial_number}, Frame {frame_number}: {result['status']} (confidence: {result['confidence']:.2f})")
            
            frame_number += 1
            
            # Maintain timing
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            time.sleep(sleep_time)
        
        # Save recognition log
        if self.capture_manager:
            self.capture_manager.save_recognition_log()
        
        print("Picture capture + recognition thread ended")
        return captured_faces
    
    def get_trial_recognition_result(self) -> Dict:
        """Get best recognition result from trial"""
        if self.capture_manager:
            log = self.capture_manager.recognition_log
            if log:
                # Find best recognized result
                recognized = [entry for entry in log if entry['recognized']]
                if recognized:
                    best = max(recognized, key=lambda x: x['confidence'])
                    return {
                        'subject_id': best['subject_id'],
                        'recognized': True,
                        'confidence': best['confidence']
                    }
        
        return {
            'subject_id': None,
            'recognized': False,
            'confidence': 0.0
        }
```
# 3. Subject Directory Structure (Detailed)
```bash
subjects/
│
├── not_recognized/                    # Unidentified faces
│   ├── raw_images/
│   │   ├── trial_001_frame_001.jpg    # From any kiosk, any experiment
│   │   ├── trial_001_frame_002.jpg
│   │   └── ...
│   │
│   ├── embeddings/
│   │   └── unrecognized_embeddings.pkl  # Clustered embeddings
│   │
│   └── clustering_analysis.json       # OpenCV clustering output
│       {
│         "clusters": {
│           "cluster_0": ["img1.jpg", "img2.jpg", ...],
│           "cluster_1": [...]
│         },
│         "num_unique_faces": 5,
│         "analysis_date": "2026-10-10"
│       }
│
├── subject_id_1/
│   │
│   ├── metadata.json
│   │   {
│   │     "name": "Subject A",
│   │     "species": "macaque",
│   │     "date_of_birth": "2020-01-15",
│   │     "enrolled_date": "2026-01-10",
│   │     "num_reference_faces": 5,
│   │     "total_sessions": 12,
│   │     "total_trials": 576
│   │   }
│   │
│   ├── face_encodings/
│   │   ├── reference_faces/           # Enrollment photos
│   │   │   ├── face_000.jpg
│   │   │   ├── face_001.jpg
│   │   │   └── face_002.jpg
│   │   │
│   │   ├── embeddings.pkl             # Pre-computed embeddings (binary)
│   │   └── temp/                      # Processing cache
│   │
│   ├── recognition_history.json       # Trial-by-trial results
│   │   [
│   │     {
│   │       "trial_number": 1,
│   │       "session_id": "session_001",
│   │       "recognized": true,
│   │       "confidence": 0.92,
│   │       "timestamp": "2026-10-10T13:42:15"
│   │     },
│   │     ...
│   │   ]
│   │
│   ├── gambling_experiment/
│   │   ├── session_001/
│   │   │   ├── exp_id_20261010_134200.txt    # Experiment log
│   │   │   ├── exp_id_20261010_134200.db    # Behavioral data
│   │   │   ├── trial_images/
│   │   │   │   ├── trial_001_frame_001.jpg
│   │   │   │   ├── trial_001_frame_002.jpg
│   │   │   │   ├── trial_001_frame_001_full.jpg  # Context
│   │   │   │   ├── trial_002_frame_001.jpg
│   │   │   │   └── recognition_log.json
│   │   │   │
│   │   │   └── Media/
│   │   │
│   │   ├── session_002/
│   │   │   └── ...
│   │   │
│   │   ├── active_parameters.json     # Currently in use
│   │   │   {
│   │   │     "iti_ms": 1000,
│   │   │     "max_response_time_ms": 4000,
│   │   │     "difficulty_level": 3,
│   │   │     "reward_magnitude": 5
│   │   │   }
│   │   │
│   │   └── parameter_history.json     # Past parameters used
│   │
│   ├── blackjack/
│   │   ├── session_001/
│   │   └── ...
│   │
│   └── ...other_experiments/
│
└── subject_id_2/
    └── ...
```
# 4. Configuration Files
## A. Face Recognition Config
```json
// mnky_bx/config/face_recognition_config.json
{
  "embedding_model": "facenet",
  "confidence_threshold": 0.7,
  "distance_threshold": 0.6,
  "max_faces_per_image": 1,
  "face_detection_method": "opencv_cascade",
  "recognition_strategy": "best_from_trial",
  "unrecognized_clustering": {
    "enabled": true,
    "method": "kmeans",
    "num_clusters": "auto",
    "min_cluster_size": 3
  },
  "logging": {
    "save_all_frames": true,
    "save_cropped_faces": true,
    "save_embeddings": true
  }
}
B. Experiment Config with Subject Parameters
json
// experiments/gambling_experiment/config.json
{
  "experiment_name": "Gambling Task",
  "experiment_version": "1.0",
  "enable_face_recognition": true,
  "use_subject_parameters": true,
  "max_trials": 48,
  "timing": {
    "iti_ms": 1000,
    "max_response_time_ms": 5000,
    "outcome_display_ms": 1500
  },
  "subject_adaptation": {
    "enabled": true,
    "parameters_can_adapt": [
      "iti_ms",
      "max_response_time_ms",
      "trial_difficulty",
      "reward_magnitude"
    ]
  }
}
```
## C. Default Subject Parameters
```json
// experiments/gambling_experiment/subject_params/default.json
{
  "iti_ms": 1000,
  "max_response_time_ms": 5000,
  "trial_difficulty": 2,
  "reward_magnitude": 5,
  "reward_type": "juice",
  "stimulus_size": 100
}
D. Subject-Specific Parameters
json
// experiments/gambling_experiment/subject_params/subject_id_1.json
{
  "iti_ms": 800,
  "max_response_time_ms": 4000,
  "trial_difficulty": 3,
  "reward_magnitude": 7,
  "stimulus_size": 120
}
```
# 5. Updated Experiment Base Class Integration
```python
# mnky_bx/core/experiment_base.py (UPDATED SECTIONS)

class ExperimentBase:
    def __init__(self,
                 experiment_name,
                 subject_id,
                 kiosk_manager,
                 logger,
                 notification_manager,
                 hardware_config,
                 recognition_engine,           # ← NEW
                 parameter_manager):            # ← NEW
        """
        Initialize experiment with face recognition support
        """
        self.experiment_name = experiment_name
        self.subject_id = subject_id
        self.kiosk_manager = kiosk_manager
        self.logger = logger
        self.notifier = notification_manager
        self.hardware_config = hardware_config
        
        # NEW: Face recognition
        self.recognition_engine = recognition_engine
        self.parameter_manager = parameter_manager
        
        # Get parameters for this subject
        self.trial_params = parameter_manager.get_parameters_for_subject(subject_id)
        
        # Use dynamic timing from parameters
        self.max_RT = self.trial_params.get('max_response_time_ms', 5000)
        self.ITI = self.trial_params.get('iti_ms', 1000)
        
        # ... rest of initialization ...
    
    def run_trial(self):
        """UPDATED: Trial with adaptive parameters"""
        # Dynamically update params if recognition changed
        if self.camera_system:
            trial_recognition = self.camera_system.get_trial_recognition_result()
            
            if trial_recognition['recognized']:
                recognized_subject = trial_recognition['subject_id']
                self.trial_params = self.parameter_manager.get_parameters_for_subject(
                    recognized_subject
                )
                self.max_RT = self.trial_params.get('max_response_time_ms', 5000)
                self.ITI = self.trial_params.get('iti_ms', 1000)
                
                print(f"Subject recognized as {recognized_subject}, "
                      f"adapted parameters: RT={self.max_RT}ms, ITI={self.ITI}ms")
                
                # Log recognition
                self.logger.log_trial_recognition(
                    trial_num=self.current_trial,
                    subject_id=recognized_subject,
                    confidence=trial_recognition['confidence']
                )
        
        # Run trial with adapted parameters
        self.setup_new_trial()
        self.draw_stimuli()
        pygame.display.flip()
        
        # ... rest of trial ...
```
# 6. Clustering Unrecognized Faces (for later analysis)
```python
# mnky_bx/face_recognition_system/unrecognized_clustering.py
"""
Cluster unrecognized faces to identify new subjects
Uses OpenCV/scikit-learn
"""

import cv2
import numpy as np
from pathlib import Path
import json
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist

class UnrecognizedFaceClustering:
    """
    Cluster and analyze unrecognized faces
    Helps experimenters identify new subjects
    """
    
    def __init__(self, config):
        self.config = config
        self.unrecognized_dir = Path('subjects/not_recognized')
    
    def cluster_unrecognized_faces(self, face_embeddings):
        """
        Cluster unrecognized face embeddings
        
        Args:
            face_embeddings: List of embedding vectors
        
        Returns:
            Clustering results
        """
        if len(face_embeddings) < 3:
            return None
        
        embeddings_array = np.array(face_embeddings)
        
        # Determine optimal number of clusters
        num_clusters = self._estimate_num_clusters(embeddings_array)
        
        # KMeans clustering
        kmeans = KMeans(n_clusters=num_clusters, n_init=10)
        labels = kmeans.fit_predict(embeddings_array)
        
        # Organize by cluster
        clusters = {}
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(i)
        
        results = {
            'num_clusters': num_clusters,
            'cluster_sizes': {str(k): len(v) for k, v in clusters.items()},
            'cluster_assignments': {str(k): v for k, v in clusters.items()},
            'centers': kmeans.cluster_centers_.tolist()
        }
        
        # Save results
        self._save_clustering_results(results)
        
        return results
    
    def _estimate_num_clusters(self, embeddings):
        """Estimate optimal number of clusters using elbow method"""
        # Simplified: assume 1 cluster per 10-15 faces
        num_faces = embeddings.shape[0]
        estimated_clusters = max(1, num_faces // 10)
        return min(estimated_clusters, 20)  # Cap at 20
    
    def _save_clustering_results(self, results):
        """Save clustering analysis"""
        output_file = self.unrecognized_dir / 'clustering_analysis.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
```
# 7. Launcher Integration (Startup Sequence)
```python
# mnky_bx/launcher.py (UPDATED)

def main():
    """
    Launcher entry point with face recognition system
    """
    from mnky_bx.utils.config_loader import ConfigLoader
    from mnky_bx.face_recognition_system.recognition_engine import FaceRecognitionEngine
    from mnky_bx.face_recognition_system.subject_parameter_manager import SubjectParameterManager
    from mnky_bx.notifications.notification_manager import NotificationManager
    from mnky_bx.core.kiosk_manager import KioskManager
    from mnky_bx.logging.experiment_logger import ExperimentLogger
    from mnky_bx.ui.launcher_ui import LauncherGUI
    
    # Load configs
    kiosk_config = ConfigLoader.load_kiosk_config()
    face_config = ConfigLoader.load_face_recognition_config()
    
    # Initialize systems
    notification_manager = NotificationManager(kiosk_config)
    kiosk_manager = KioskManager(kiosk_config)
    
    # Initialize face recognition
    recognition_engine = FaceRecognitionEngine(face_config)
    
    # Launch GUI
    launcher = LauncherGUI(kiosk_config)
    selection = launcher.show()  # Returns {experiment, subject_id}
    
    if not selection:
        return  # User canceled
    
    experiment_name = selection['experiment']
    
    # Initialize session
    session = kiosk_manager.start_session(
        subject_id="TBD",  # Will be determined by face recognition
        experiment_name=experiment_name
    )
    
    # Initialize logger
    logger = ExperimentLogger(session['log_file'], level=logging.DEBUG)
    
    # Initialize parameter manager
    param_manager = SubjectParameterManager(experiment_name)
    
    # Load experiment class
    experiment_module = importlib.import_module(
        f'experiments.{experiment_name}.experiment'
    )
    ExperimentClass = experiment_module.GamblingExperiment  # or appropriate class
    
    # Instantiate and run
    try:
        experiment = ExperimentClass(
            experiment_name=experiment_name,
            subject_id=None,  # Will be determined by face recognition
            kiosk_manager=kiosk_manager,
            logger=logger,
            notification_manager=notification_manager,
            hardware_config=kiosk_config['hardware'],
            recognition_engine=recognition_engine,
            parameter_manager=param_manager
        )
        
        experiment.run()
        
    except Exception as e:
        logger.log_error(f"Experiment failed: {e}", exc_info=True)
        notification_manager.send_alert(
            subject=f"Experiment error on {kiosk_config['kiosk_id']}",
            message=str(e)
        )
        raise

if __name__ == "__main__":
    main()
```

# Summary of Architectural Changes
| Component             | Old | New | 
|:----------------------| :---: | ---: |
| Camera Module	         | Motion + face detection only| 	+ Recognition, embeddings, storage routing| 
| Subjects Directory    | 	Subject folders with experiment data| 	+ Face encodings, recognition history, unrecognized clustering| 
| Experiment Parameters | 	Static, JSON| 	Dynamic, per-subject JSON files, adaptive during trial| 
| Image Storage         | 	Database blobs| 	Filesystem + organized by subject/recognition status| 
| Trial Workflow        | 	Motion → Face → Trial| 	Motion → Face → Recognition → Adaptive Parameters → Trial| 
| Data Organization     | 	Flat session structure| 	Hierarchical with recognition metadata| 

## Key Design Decisions
1. Two-Stage Recognition
- During trial: Fast classification against enrolled subjects
- Post-trial: Cluster unrecognized faces to find new subjects
2. Adaptive Parameters
- Subject-specific config files override defaults
- Parameters update in real-time based on recognition
- Full history maintained for analysis
3. Image Storage Strategy
- Recognized → Subject's folder (linked to their data)
- Unrecognized → Central "not_recognized" for clustering
- Both trial cropped faces and full context frames saved
4. Embedding Format 
- Binary pickle files (.pkl) for speed
- Optional JSON export for analysis
- Reference faces kept as JPEG for re-enrollment
5. Modularity
- Face recognition system independent of experiment logic
- CaptureManager handles storage routing (not trial logic)
- Recognition engine swappable (FaceNet, DeepFace, etc.)

### Does this architecture address your needs for:

- ✅ Face recognition-based subject identification
- ✅ Adaptive trial parameters per subject
- ✅ Image organization by recognition status
- ✅ Unrecognized face clustering for discovery
- ✅ Integration with existing camera system
- ✅ Proper data provenance and logging

**Any refinements needed before passing to IDE copilot?**

**This is very thorough. one question, if I recall correctly the existing script is writing the image and video files to blobs in the sqlite databases. is that the most efficient way to save the data?**

Great question! No, storing images as BLOBs in SQLite is not the most efficient approach for this use case. Let me break down the tradeoffs:

Searched your files
Perfect! I can see the current approach. Let me provide a comprehensive comparison and recommendation:

# Storage Strategy Comparison
## Current Approach: BLOB in SQLite ❌
### Pros:

- ✅ Atomic transactions (images saved with trial data guaranteed)
- ✅ Single file to backup
- ✅ Images grouped with behavioral data

### Cons:

- ❌ Database bloat: SQLite inefficient for large binary objects
- ❌ Slow queries: Any query on trial_data becomes slow with BLOB column
- ❌ Poor I/O: BLOBs written sequentially to single file
- ❌ Memory intensive: Entire BLOB loaded into memory during write
- ❌ Difficult extraction: Need to read from database to access images
- ❌ Poor scalability: 48 trials × 3 fps × 20 sec = ∼2880 images/session = 100+ MB per session
- ❌ No direct access: Can't easily view images without extracting from DB first
- ❌ Concurrency issues: Writing large BLOBs locks database

## Recommended: Hybrid Approach ✅
### Store images as filesystem files, keep filesystem references in database

```makefile
Database (SQLite):
┌─────────────────────────────────────────┐
│ trial_pictures                          │
├─────────────────────────────────────────┤
│ picture_id | trial_number | image_path  │
│ 1          | 1            | trial_001_frame_001.jpg
│ 2          | 1            | trial_001_frame_002.jpg
└─────────────────────────────────────────┘

Filesystem:
trials/
├── trial_001_frame_001.jpg
├── trial_001_frame_002.jpg
└── ...
```
## Detailed Comparison Table
| Criterion	| BLOB in DB|	Filesystem Refs | 	Video File| 
| :--- | :---: |---------------:| ---: |
| Speed (write)	| 🔴 Slow	|        🟢 Fast	 | 🟢 Fast| 
| Speed (query)	| 🔴 Very Slow	|        🟢 Fast	 | 🟢 Fast| 
| Storage efficiency| 	🔴 Poor|        🟢 Good | 	🟡 OK| 
| Direct access| 	🔴 No|         	🟢 Yes	 | 🟡 Maybe| 
| Backup/archive| 	🟡 OK|   	🟡 Need sync	 | 🟢 Good| 
| Recognition integration| 	🔴 Hard	|        🟢 Easy	 | 🔴 Hard| 
| Reproducibility| 	🟢 Good|        	🟢 Good	 | 🟢 Good| 
| Scalability| 	🔴 Poor|        	🟢 Good	 | 🟢 Good| 

## Recommended Hybrid Architecture
### Option 1: Filesystem + SQLite References (RECOMMENDED)
```python
# Database schema - lightweight
CREATE TABLE trial_pictures (
    picture_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER,
    timestamp INTEGER,
    frame_number INTEGER,
    image_path TEXT,              # ← Path to file instead of BLOB
    face_bbox TEXT,               # JSON: {"x": 100, "y": 50, "w": 150, "h": 150}
    recognized BOOLEAN,
    subject_id TEXT,
    confidence REAL,
    image_width INTEGER,
    image_height INTEGER,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number)
);
```
### Advantages:

- ✅ Database queries remain fast (no BLOB scanning)
- ✅ Images directly accessible via filesystem
- ✅ Easy integration with face recognition (direct file I/O)
- ✅ Images organized by subject/recognition status
- ✅ Can compress/archive images separately from behavioral data
- ✅ Can use parallel I/O for image writing

### Storage:

```text
subjects/
├── subject_id_1/
│   └── gambling_experiment/
│       └── session_001/
│           ├── trial_images/
│           │   ├── trial_001_frame_001.jpg
│           │   ├── trial_001_frame_001_recognition.json
│           │   └── ...
│           ├── exp_id_20261010_134200.db
│           └── exp_id_20261010_134200.txt
```
### Option 2: Video File (Alternative - More Efficient for Large Datasets)
For continuous video capture, consider H.264/H.265 compressed video instead of individual frames:

```python
# Database schema
CREATE TABLE trial_video (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER,
    video_path TEXT,              # Single .mp4 file
    start_frame INTEGER,
    end_frame INTEGER,
    fps REAL,
    codec TEXT,
    duration_s REAL,
    file_size_mb REAL,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number)
);

CREATE TABLE trial_frame_metadata (  # Lightweight frame-by-frame data
    frame_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER,
    video_id INTEGER,
    frame_number INTEGER,
    timestamp INTEGER,
    face_detected BOOLEAN,
    face_bbox TEXT,
    recognized BOOLEAN,
    subject_id TEXT,
    confidence REAL,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number),
    FOREIGN KEY (video_id) REFERENCES trial_video (video_id)
);
```
### Advantages:
- ✅ Massive storage reduction: H.265 video ∼2-5 MB/min vs JPEG ∼500 KB/frame
- ✅ Can re-extract frames if needed
- ✅ Smooth video playback for analysis
- ✅ Excellent for long-term archival
- ✅ All behavioral data still queryable

### Disadvantages:
- ❌ Requires codec (ffmpeg dependency)
- ❌ Can't easily extract specific frames without decoding
- ❌ Slightly higher CPU during recording
Example storage:

```scss
trial_001.mp4 (10 MB for 60-second trial at 3fps)
└── Metadata in trial_frame_metadata table (lightweight)
```

## My Recommendation: Hybrid Strategy
### For Your Kiosk System, I'd Recommend:
### Use Option 1 (Filesystem + SQLite) for flexibility, with Optional Video Export:

```vbnet
During Trial (Real-time):
├─ Capture frames at 3 FPS
├─ Save JPEGs directly to filesystem (fast I/O)
├─ Write metadata + path to database (fast)
├─ Perform face recognition on JPEG files (easy)
└─ Route images by subject (folder-based)

Optional Post-Trial Processing:
├─ Encode frames into H.265 video (background task)
├─ Delete original JPEGs (keep video)
├─ Update database with video reference
└─ Compress for archival
```
## Updated CaptureManager Architecture
```python
# mnky_bx/hardware/camera/capture_manager.py (OPTIMIZED)

from pathlib import Path
import cv2
import json
from datetime import datetime
from typing import Optional, Dict, List
import threading
import queue

class CaptureManager:
    """
    Optimized image capture and storage
    - Writes images to filesystem (fast I/O)
    - Keeps lightweight metadata in database
    - Enables face recognition on direct files
    - Supports video encoding for archival
    """
    
    def __init__(self,
                 session_dir: Path,
                 recognition_engine,
                 enable_video_encoding: bool = True):
        """
        Args:
            session_dir: Session directory
            recognition_engine: FaceRecognitionEngine
            enable_video_encoding: Post-process to video (optional)
        """
        self.session_dir = Path(session_dir)
        self.recognition_engine = recognition_engine
        self.enable_video_encoding = enable_video_encoding
        
        # Create directories
        self.trial_images_dir = session_dir / 'trial_images'
        self.trial_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata tracking (lightweight)
        self.frame_metadata = []  # Will be written to DB later
        self.recognition_log = []
        
        # Optional: async video encoding queue
        if enable_video_encoding:
            self.video_encoding_queue = queue.Queue()
            self.video_encoding_thread = None
    
    def save_captured_frame(self,
                           frame: 'np.ndarray',
                           trial_number: int,
                           frame_number: int,
                           timestamp: datetime) -> Dict:
        """
        Save captured frame to filesystem
        Returns metadata dict for database insertion
        
        Args:
            frame: Full camera frame (BGR)
            trial_number: Trial number
            frame_number: Frame number within trial
            timestamp: Capture timestamp
        
        Returns:
            Metadata dict for database
        """
        # Generate filename
        filename = f"trial_{trial_number:03d}_frame_{frame_number:03d}.jpg"
        filepath = self.trial_images_dir / filename
        
        # Write to filesystem (fast, parallel-friendly)
        cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # Create lightweight metadata entry
        metadata = {
            'trial_number': trial_number,
            'frame_number': frame_number,
            'timestamp': int(timestamp.timestamp() * 1000),  # ms
            'image_path': str(filepath.relative_to(self.session_dir)),  # Relative path
            'image_width': frame.shape[1],
            'image_height': frame.shape[0],
            'image_size_bytes': filepath.stat().st_size
        }
        
        self.frame_metadata.append(metadata)
        
        # Queue for optional video encoding
        if self.enable_video_encoding:
            self.video_encoding_queue.put({
                'frame': frame.copy(),
                'trial_number': trial_number,
                'frame_number': frame_number
            })
        
        return metadata
    
    def save_recognized_face(self,
                            face_image: 'np.ndarray',
                            face_bbox: tuple,
                            trial_number: int,
                            frame_number: int,
                            timestamp: datetime,
                            recognition_result: Dict) -> Dict:
        """
        Save face image and recognition result
        
        Args:
            face_image: Cropped face image
            face_bbox: (x, y, w, h) bounding box
            recognition_result: From recognition engine
        
        Returns:
            Database entry dict
        """
        # Save face to appropriate directory
        if recognition_result['recognized']:
            subject_id = recognition_result['subject_id']
            subject_dir = Path('subjects') / subject_id / 'trial_images'
        else:
            subject_id = 'not_recognized'
            subject_dir = Path('subjects') / 'not_recognized' / 'raw_images'
        
        subject_dir.mkdir(parents=True, exist_ok=True)
        
        face_filename = f"trial_{trial_number:03d}_frame_{frame_number:03d}.jpg"
        face_path = subject_dir / face_filename
        cv2.imwrite(str(face_path), face_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        # Save recognition metadata
        recognition_meta = {
            'trial_number': trial_number,
            'frame_number': frame_number,
            'timestamp': int(timestamp.timestamp() * 1000),
            'face_path': str(face_path),
            'face_bbox': {'x': face_bbox[0], 'y': face_bbox[1], 
                         'w': face_bbox[2], 'h': face_bbox[3]},
            'recognized': recognition_result['recognized'],
            'subject_id': recognition_result['subject_id'],
            'confidence': recognition_result['confidence'],
            'status': recognition_result['status']
        }
        
        self.recognition_log.append(recognition_meta)
        
        return recognition_meta
    
    def save_database_entries(self, db_connection):
        """
        Write all metadata to database in batch
        (Much faster than writing during capture)
        
        Args:
            db_connection: SQLite connection
        """
        cursor = db_connection.cursor()
        
        # Batch insert frame metadata
        for metadata in self.frame_metadata:
            cursor.execute('''
                INSERT INTO trial_pictures 
                (trial_number, timestamp, frame_number, image_path, 
                 image_width, image_height)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metadata['trial_number'],
                metadata['timestamp'],
                metadata['frame_number'],
                metadata['image_path'],
                metadata['image_width'],
                metadata['image_height']
            ))
        
        db_connection.commit()
        print(f"Saved {len(self.frame_metadata)} frame metadata entries to database")
    
    def save_recognition_log(self):
        """Save recognition results to JSON"""
        log_file = self.trial_images_dir / 'recognition_log.json'
        with open(log_file, 'w') as f:
            json.dump(self.recognition_log, f, indent=2)
    
    def async_encode_to_video(self, trial_number: int, fps: int = 3):
        """
        Optionally encode captured frames to H.265 video
        Runs asynchronously to not block experiment
        
        Args:
            trial_number: Which trial to encode
            fps: Frames per second
        """
        if not self.enable_video_encoding:
            return
        
        # Find all frames for this trial
        frames = sorted([
            f for f in self.trial_images_dir.glob(f'trial_{trial_number:03d}_frame_*.jpg')
        ])
        
        if not frames:
            return
        
        try:
            # Use ffmpeg-python or OpenCV
            output_path = self.trial_images_dir / f'trial_{trial_number:03d}.mp4'
            
            # Read first frame to get dimensions
            first_frame = cv2.imread(str(frames[0]))
            height, width = first_frame.shape[:2]
            
            # H.265 codec (better compression)
            fourcc = cv2.VideoWriter_fourcc(*'hev1')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            for frame_path in frames:
                frame = cv2.imread(str(frame_path))
                out.write(frame)
            
            out.release()
            
            print(f"Encoded trial {trial_number} to {output_path}")
            
            # Optional: Delete original JPEGs to save space
            # for frame_path in frames:
            #     frame_path.unlink()
            
        except Exception as e:
            print(f"Video encoding failed: {e}")
```
### Updated Database Schema
```python
# mnky_bx/database/schemas.py

CREATE_TRIAL_PICTURES = '''
CREATE TABLE IF NOT EXISTS trial_pictures (
    picture_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER NOT NULL,
    timestamp INTEGER,
    frame_number INTEGER,
    image_path TEXT NOT NULL,           -- ← Filesystem path, not BLOB
    image_width INTEGER,
    image_height INTEGER,
    image_size_bytes INTEGER,
    face_detected BOOLEAN DEFAULT 0,
    recognized BOOLEAN DEFAULT 0,
    subject_id TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number),
    INDEX idx_trial_number (trial_number),
    INDEX idx_subject_id (subject_id)
)
'''

CREATE_TRIAL_VIDEO = '''
CREATE TABLE IF NOT EXISTS trial_video (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER NOT NULL UNIQUE,
    video_path TEXT,
    codec TEXT DEFAULT 'h265',
    fps REAL,
    duration_s REAL,
    file_size_mb REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number)
)
'''
```

## Performance Comparison
### Scenario: 48 trials × 60 frames/trial × 3 FPS = 2880 images
| Metric	| BLOB in DB	| Filesystem + SQLite	| Video File| 
| :--- | :---: | ---: | ---: |
| Total storage	| 150+ MB DB file	| 120 MB images + 2 MB DB	| 15 MB MP4
| DB file size	| 150+ MB	| 2 MB	| 2 MB
| Write time	| ∼180 sec	| ∼30 sec	| ∼20 sec
| Query trial data	| 10+ sec	| 0.1 sec	| 0.1 sec
| Extract one image	| 2-5 sec	| 0.01 sec	| Decode MP4
| Backup time	| 180+ sec	| 30 sec + network	| 20 sec + network
| Access images for ML	| Must extract	| Direct from disk	| Must decompress| 

# Final Recommendation Summary
#### For your kiosk system, use:

1. Real-time: Filesystem storage + SQLite references
- Fast writes (parallel I/O)
- Fast queries (lightweight DB)
- Easy face recognition integration
- Direct file access for analysis
2. Optional post-trial: Encode to H.265 video
- Reduces long-term storage
- Keep JPEGs for ∼1 week, archive to video
- Maintains full reproducibility
3. Database: Lightweight references only
- image_path (TEXT)
- metadata (face_bbox, recognition results)
- NO image_data BLOB

**Result**: Fast, scalable, efficient system that works well with face recognition and machine learning pipelines.
Does this recommendation align with your needs? Should we update the `CaptureManager` and database schemas in the architecture document?



