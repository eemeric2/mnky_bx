# setup_directories.py
"""
Cross-platform directory setup script for mnky_bx kiosk system
Updated for unified Arduino controller architecture

Usage: python setup_directories.py [project_root] [num_subjects] [experiments]
Example: python setup_directories.py . 12 gambling_experiment blackjack
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class DirectorySetup:
    """Setup complete mnky_bx directory structure"""

    def __init__(self,
                 project_root: str = ".",
                 num_subjects: int = 12,
                 experiments: Optional[List[str]] = None):
        """
        Initialize setup

        Args:
            project_root: Root directory for project
            num_subjects: Number of subject directories to create
            experiments: List of experiment names (default: gambling_experiment, blackjack)
        """
        self.project_root = Path(project_root)
        self.num_subjects = num_subjects
        self.experiments = experiments or ["gambling_experiment", "blackjack"]

        # Statistics
        self.created_dirs = 0
        self.existing_dirs = 0
        self.created_files = 0

    def print_header(self, text: str, char: str = "=") -> None:
        """Print formatted header"""
        width = 60
        print(f"\n{char * width}")
        print(f" {text.center(width - 2)} ")
        print(f"{char * width}\n")

    def print_section(self, text: str) -> None:
        """Print section header"""
        print(f"\n{'─' * 60}")
        print(f"  {text}")
        print(f"{'─' * 60}")

    def create_dir(self, path: str, description: str = "") -> None:
        """
        Create directory and log result

        Args:
            path: Relative path from project root
            description: Human-readable description
        """
        full_path = self.project_root / path

        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {path}")
            self.created_dirs += 1
        else:
            print(f"  → Exists: {path}")
            self.existing_dirs += 1

    def create_init_file(self, path: str) -> None:
        """
        Create __init__.py file in package directory

        Args:
            path: Package directory path
        """
        full_path = self.project_root / path / "__init__.py"

        if not full_path.exists():
            full_path.touch()
            self.created_files += 1

    def create_file_with_content(self, path: str, content: str) -> None:
        """
        Create file with specified content

        Args:
            path: File path
            content: File content
        """
        full_path = self.project_root / path

        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            print(f"  ✓ Created: {path}")
            self.created_files += 1
        else:
            print(f"  → Exists: {path}")

    # ============ SETUP METHODS ============

    def setup_core_package(self) -> None:
        """Create core package structure"""
        self.print_section("Core Package Structure")

        modules = [
            "mnky_bx",
            "mnky_bx/core",
            "mnky_bx/hardware",
            "mnky_bx/hardware/arduino",  # ← NEW: Unified Arduino
            "mnky_bx/hardware/camera",
            "mnky_bx/database",
            "mnky_bx/logging",
            "mnky_bx/notifications",
            "mnky_bx/face_recognition_system",
            "mnky_bx/utils",
            "mnky_bx/ui",
        ]

        for module in modules:
            self.create_dir(module)

    def setup_documentation(self) -> None:
        """Create documentation structure"""
        self.print_section("Documentation Structure")

        docs_dirs = [
            "docs",
            "docs/original_scripts",
            "docs/examples",
        ]

        for doc_dir in docs_dirs:
            self.create_dir(doc_dir)

    def setup_tests(self) -> None:
        """Create tests structure"""
        self.print_section("Tests Structure")

        test_dirs = [
            "tests",
            "tests/fixtures",
            "tests/fixtures/sample_frames",
            "tests/fixtures/test_subjects",
            "tests/fixtures/mock_hardware",
        ]

        for test_dir in test_dirs:
            self.create_dir(test_dir)

    def setup_experiments(self) -> None:
        """Create experiments structure"""
        self.print_section("Experiments Structure")

        self.create_dir("experiments")

        for experiment in self.experiments:
            base_path = f"experiments/{experiment}"

            dirs = [
                base_path,
                f"{base_path}/subject_params",
                f"{base_path}/analysis",
                f"{base_path}/analysis/results",
                f"{base_path}/data",
                f"{base_path}/data/Media",
            ]

            for dir_path in dirs:
                self.create_dir(dir_path)

    def setup_subjects(self) -> None:
        """Create subjects directory structure"""
        self.print_section("Subjects Directory Structure")

        # Create not_recognized directory
        not_recognized_dirs = [
            "subjects/not_recognized",
            "subjects/not_recognized/raw_images",
            "subjects/not_recognized/face_images",
            "subjects/not_recognized/embeddings",
        ]

        for dir_path in not_recognized_dirs:
            self.create_dir(dir_path)

        # Create individual subject directories
        for i in range(1, self.num_subjects + 1):
            subject_id = f"subject_id_{i:02d}"

            if i == 1 or i % 3 == 0:  # Print progress periodically
                print(f"\n  Creating directories for {subject_id}...")

            # Face encoding directories
            face_dirs = [
                f"subjects/{subject_id}",
                f"subjects/{subject_id}/face_encodings",
                f"subjects/{subject_id}/face_encodings/reference_faces",
                f"subjects/{subject_id}/face_encodings/temp",
            ]

            for dir_path in face_dirs:
                self.create_dir(dir_path)

            # Experiment directories for each subject
            for experiment in self.experiments:
                exp_dirs = [
                    f"subjects/{subject_id}/{experiment}",
                    f"subjects/{subject_id}/{experiment}/session_001",
                    f"subjects/{subject_id}/{experiment}/session_001/trial_images",
                    f"subjects/{subject_id}/{experiment}/session_001/Media",
                ]

                for dir_path in exp_dirs:
                    self.create_dir(dir_path)

    def setup_config(self) -> None:
        """Create configuration directory and sample files"""
        self.print_section("Configuration Directory")

        self.create_dir("config")

    def create_python_packages(self) -> None:
        """Create __init__.py files for all Python packages"""
        self.print_section("Creating Python Package Files")

        python_modules = [
            "mnky_bx",
            "mnky_bx/core",
            "mnky_bx/hardware",
            "mnky_bx/hardware/arduino",  # ← NEW
            "mnky_bx/hardware/camera",
            "mnky_bx/database",
            "mnky_bx/logging",
            "mnky_bx/notifications",
            "mnky_bx/face_recognition_system",
            "mnky_bx/utils",
            "mnky_bx/ui",
            "experiments",
            "tests",
        ]

        for experiment in self.experiments:
            python_modules.append(f"experiments/{experiment}")

        for module in python_modules:
            self.create_init_file(module)

        print(f"\n  ✓ Created {self.created_files} __init__.py files")

    def create_readme_files(self) -> None:
        """Create README files for key directories"""
        self.print_section("Creating README Files")

        # Not Recognized README
        not_recognized_readme = (
            "# Not Recognized\n\n"
            "This directory contains face images from subjects that could not be "
            "recognized by the face recognition system.\n\n"
            "## Structure\n\n"
            "- `raw_images/` - Original unidentified face crops\n"
            "- `face_images/` - Processed face images with context\n"
            "- `embeddings/` - Face embeddings for clustering analysis\n\n"
            "## Usage\n\n"
            "These images are useful for:\n"
            "1. Discovering new subjects not yet in the system\n"
            "2. Clustering analysis to identify potential new subjects\n"
            "3. Training data for improving the recognition model\n"
            "4. Troubleshooting recognition failures\n\n"
            "## Cleanup\n\n"
            "Old unrecognized images can be archived after clustering analysis.\n"
        )

        # Docs README
        docs_readme = (
            "# Documentation\n\n"
            "Complete documentation for the mnky_bx kiosk system.\n\n"
            "## Contents\n\n"
            "- `ARCHITECTURE.md` - System architecture and design\n"
            "- `ORIGINAL_SCRIPT_REFERENCE.md` - Mapping from original monolithic script\n"
            "- `REFACTORING_GUIDE.md` - How the refactoring was done\n"
            "- `API.md` - API reference for all modules\n"
            "- `original_scripts/` - Original monolithic script for reference\n\n"
            "## Getting Started\n\n"
            "1. Read `ARCHITECTURE.md` for overview\n"
            "2. Review `original_scripts/MonkeyBoxGamblingExperiment.py` for context\n"
            "3. Check `examples/` for sample implementations\n"
            "4. Review module docstrings for detailed API info\n"
        )

        # Tests README
        tests_readme = (
            "# Tests\n\n"
            "Unit tests, integration tests, and test fixtures.\n\n"
            "## Structure\n\n"
            "- `test_*.py` - Individual test modules\n"
            "- `fixtures/` - Test data and mock objects\n"
            "  - `sample_frames/` - Sample camera frames\n"
            "  - `test_subjects/` - Test subject data\n"
            "  - `mock_hardware/` - Mock hardware for testing\n\n"
            "## Running Tests\n\n"
            "```bash\n"
            "pytest tests/\n"
            "pytest tests/test_camera_system.py -v\n"
            "```\n\n"
            "## Fixtures\n\n"
            "Mock hardware and test data available in `fixtures/`.\n"
        )

        # Experiments README
        experiments_readme = (
            "# Experiments\n\n"
            "User-implemented experiment modules.\n\n"
            "## Structure\n\n"
            "Each experiment follows this structure:\n\n"
            "```\n"
            "experiment_name/\n"
            "├── experiment.py           # Main experiment class (user implements)\n"
            "├── config.json             # Experiment configuration\n"
            "├── subject_params/         # Subject-specific parameters\n"
            "│   ├── default.json\n"
            "│   └── subject_id_*.json\n"
            "├── analysis/               # Analysis scripts and results\n"
            "├── data/                   # Experimental data\n"
            "└── Media/                  # Media files\n"
            "```\n\n"
            "## Creating a New Experiment\n\n"
            "1. Create directory: `experiments/my_experiment/`\n"
            "2. Create config.json with experiment parameters\n"
            "3. Create experiment.py and subclass ExperimentBase\n"
            "4. Implement required methods (draw_stimuli, wait_for_response, etc.)\n"
            "5. Add to launcher.py\n\n"
            "See `examples/` for templates.\n"
        )

        readmes = {
            "subjects/not_recognized/README.md": not_recognized_readme,
            "docs/README.md": docs_readme,
            "tests/README.md": tests_readme,
            "experiments/README.md": experiments_readme,
        }

        for path, content in readmes.items():
            self.create_file_with_content(path, content)

    def create_sample_configs(self) -> None:
        """Create sample configuration files"""
        self.print_section("Creating Sample Configuration Files")

        # Kiosk config
        kiosk_config = {
            "kiosk_id": "kiosk_001",
            "display": {
                "width": 1920,
                "height": 1080,
                "fullscreen": True,
                "refresh_rate": 60
            },
            "hardware": {
                "arduino_port": "COM4",
                "camera_index": 0,
                "motion_detection_timeout_s": 300,
                "face_detection_timeout_s": 10,
                "motion_threshold": 5000,
                "frames_to_stabilize": 30
            },
            "arduino": {
                "port": "COM4",
                "baud_rate": 115200,
                "connection_timeout_s": 5,
                "max_reward_position": 10,
                "reward_pulse_duration_ms": 500,
                "retry_attempts": 3,
                "retry_delay_ms": 500
            },
            "storage": {
                "enable_video_encoding": True,
                "video_quality": "medium",
                "video_codec": "h265",
                "jpeg_quality": 85,
                "cleanup_old_jpegs_after_days": 7,
                "max_session_storage_mb": 500
            },
            "logging": {
                "level": "DEBUG",
                "log_directory": "subjects/"
            },
            "notifications": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            },
            "session_management": {
                "max_subjects_per_kiosk": 12,
                "auto_cleanup_interval_hours": 24
            }
        }

        # Face recognition config
        face_config = {
            "embedding_model": "facenet",
            "confidence_threshold": 0.7,
            "distance_threshold": 0.6,
            "max_faces_per_image": 1,
            "face_detection_method": "opencv_cascade",
            "recognition_strategy": "best_from_trial",
            "unrecognized_clustering": {
                "enabled": True,
                "method": "kmeans",
                "num_clusters": "auto",
                "min_cluster_size": 3
            },
            "logging": {
                "save_all_frames": True,
                "save_cropped_faces": True,
                "save_embeddings": True
            }
        }

        # Notification config template
        notification_config = {
            "notifications": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "from_email": "kiosk@lab.edu",
                "alert_emails": ["experimenter@lab.edu"],
                "alert_numbers": ["+14105551234"],
                "twilio_account_sid": "YOUR_ACCOUNT_SID",
                "twilio_auth_token": "YOUR_AUTH_TOKEN",
                "twilio_phone": "+1234567890"
            }
        }

        # Default experiment config
        experiment_config = {
            "experiment_name": "Template Experiment",
            "experiment_version": "1.0",
            "enable_face_recognition": True,
            "use_subject_parameters": True,
            "max_trials": 48,
            "timing": {
                "iti_ms": 1000,
                "max_response_time_ms": 5000,
                "outcome_display_ms": 1500
            },
            "subject_adaptation": {
                "enabled": True,
                "parameters_can_adapt": [
                    "iti_ms",
                    "max_response_time_ms",
                    "trial_difficulty",
                    "reward_magnitude"
                ]
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
            }
        }

        # Default subject parameters
        default_subject_params = {
            "iti_ms": 1000,
            "max_response_time_ms": 5000,
            "trial_difficulty": 2,
            "reward_magnitude": 5,
            "reward_type": "juice",
            "stimulus_size": 100
        }

        # Gambling experiment config (example)
        gambling_config = {
            "experiment_name": "Gambling Task",
            "experiment_version": "1.0",
            "enable_face_recognition": True,
            "use_subject_parameters": True,
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
            }
        }

        # Save configs
        configs = {
            "config/kiosk_config.json": kiosk_config,
            "config/face_recognition_config.json": face_config,
            "config/notification_config_TEMPLATE.json": notification_config,
        }

        for config_path, config_data in configs.items():
            full_path = self.project_root / config_path

            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
                print(f"  ✓ Created: {config_path}")
                self.created_files += 1
            else:
                print(f"  → Exists: {config_path}")

        # Create experiment configs for each experiment
        for experiment in self.experiments:
            config_path = f"experiments/{experiment}/config.json"
            full_path = self.project_root / config_path

            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    json.dump(gambling_config, f, indent=2)
                print(f"  ✓ Created: {config_path}")
                self.created_files += 1

            # Create default subject parameters
            default_params_path = f"experiments/{experiment}/subject_params/default.json"
            full_path = self.project_root / default_params_path

            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w') as f:
                    json.dump(default_subject_params, f, indent=2)
                print(f"  ✓ Created: {default_params_path}")
                self.created_files += 1

    def create_placeholder_files(self) -> None:
        """Create placeholder Python files for key modules"""
        self.print_section("Creating Placeholder Module Files")

        placeholder_content = "# TODO: Implement this module\npass\n"

        placeholders = {
            "mnky_bx/hardware/arduino/protocol.py": "# Arduino communication protocol\n" + placeholder_content,
            "mnky_bx/hardware/arduino/commands.py": "# Arduino command definitions\n" + placeholder_content,
            "mnky_bx/hardware/arduino/arduino_uno_controller.py": "# Unified Arduino Uno controller\n" + placeholder_content,
            "mnky_bx/core/experiment_base.py": "# Base experiment class\n" + placeholder_content,
            "mnky_bx/database/schemas.py": "# Database schema definitions\n" + placeholder_content,
        }

        for file_path, content in placeholders.items():
            self.create_file_with_content(file_path, content)

    def print_summary(self) -> None:
        """Print setup summary"""
        self.print_header("Setup Complete!", "=")

        total_dirs = self.created_dirs + self.existing_dirs

        print("Summary:")
        print(f"  • Directories created: {self.created_dirs}")
        print(f"  • Directories existing: {self.existing_dirs}")
        print(f"  • Total directories: {total_dirs}")
        print(f"  • Files created: {self.created_files}")
        print()
        print("Project Structure:")
        print("  • Core package: mnky_bx/")
        print("    - Core modules, hardware (including unified Arduino), database, logging")
        print("    - Face recognition system, UI, utilities")
        print(f"  • Experiments: experiments/ ({len(self.experiments)} templates)")
        for exp in self.experiments:
            print(f"    - {exp}")
        print(f"  • Subjects: subjects/ ({self.num_subjects} subject directories)")
        print("  • Documentation: docs/")
        print("  • Tests: tests/")
        print("  • Configuration: config/")
        print()
        print("Next Steps:")
        print("  1. Review config files in config/")
        print("  2. Update notification_config.json with email/SMS credentials")
        print("  3. Update hardware port in kiosk_config.json (currently 'COM4')")
        print("  4. Create experiment.py files in each experiments/*/")
        print("  5. Add subject metadata.json files to each subject directory")
        print("  6. Run: pip install -r requirements.txt")
        print("  7. Run launcher: python mnky_bx/launcher.py")
        print()
        print("Key Changes in This Version:")
        print("  ✓ Unified Arduino controller (buttons + reward on single device)")
        print("  ✓ Filesystem image storage (no BLOBs in database)")
        print("  ✓ Face recognition system for subject identification")
        print("  ✓ Async video encoding support")
        print("  ✓ Subject-adaptive parameters")
        print("  ✓ Comprehensive logging and error handling")
        print("  ✓ Email/SMS notifications")
        print()

    def run(self) -> None:
        """Execute full setup"""
        self.print_header("MNKY_BX Directory Setup Script", "=")

        print("Configuration:")
        print(f"  Project root: {self.project_root}")
        print(f"  Number of subjects: {self.num_subjects}")
        print(f"  Experiments: {', '.join(self.experiments)}")
        print()

        try:
            self.setup_core_package()
            self.setup_documentation()
            self.setup_tests()
            self.setup_experiments()
            self.setup_subjects()
            self.setup_config()
            self.create_python_packages()
            self.create_readme_files()
            self.create_sample_configs()
            self.create_placeholder_files()
            self.print_summary()

        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    # Parse command line arguments
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    num_subjects = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    experiments = sys.argv[3:] if len(sys.argv) > 3 else ["gambling_experiment", "blackjack"]

    # Run setup
    setup = DirectorySetup(project_root, num_subjects, experiments)
    setup.run()


if __name__ == "__main__":
    main()