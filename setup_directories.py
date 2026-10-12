# setup_directories.py
"""
Cross-platform directory setup script for mnky_bx
Usage: python setup_directories.py [project_root] [num_subjects]
"""

import os
import sys
from pathlib import Path
from typing import List

class DirectorySetup:
    def __init__(self, project_root: str = ".", num_subjects: int = 12):
        self.project_root = Path(project_root)
        self.num_subjects = num_subjects
        self.experiments = ["gambling_experiment", "blackjack"]
        self.created_dirs = 0
        self.existing_dirs = 0
    
    def create_dir(self, path: str, description: str = "") -> None:
        """Create directory and log result"""
        full_path = self.project_root / path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {path}")
            self.created_dirs += 1
        else:
            print(f"→ Exists: {path}")
            self.existing_dirs += 1
    
    def create_init_file(self, path: str) -> None:
        """Create __init__.py file"""
        full_path = self.project_root / path / "__init__.py"
        
        if not full_path.exists():
            full_path.touch()
            print(f"✓ Created: {path}/__init__.py")
    
    def setup_core_package(self) -> None:
        """Create core package structure"""
        print("\n" + "="*50)
        print("Creating core package structure...")
        print("="*50)
        
        modules = [
            "mnky_bx",
            "mnky_bx/core",
            "mnky_bx/hardware",
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
    
    def setup_experiments(self) -> None:
        """Create experiments structure"""
        print("\n" + "="*50)
        print("Creating experiments structure...")
        print("="*50)
        
        self.create_dir("experiments")
        
        for experiment in self.experiments:
            base_path = f"experiments/{experiment}"
            self.create_dir(base_path)
            self.create_dir(f"{base_path}/subject_params")
            self.create_dir(f"{base_path}/analysis")
            self.create_dir(f"{base_path}/analysis/results")
            self.create_dir(f"{base_path}/data")
            self.create_dir(f"{base_path}/data/Media")
    
    def setup_subjects(self) -> None:
        """Create subjects directory structure"""
        print("\n" + "="*50)
        print("Creating subjects directory structure...")
        print("="*50)
        
        # Create not_recognized directory
        self.create_dir("subjects/not_recognized")
        self.create_dir("subjects/not_recognized/raw_images")
        self.create_dir("subjects/not_recognized/face_images")
        self.create_dir("subjects/not_recognized/embeddings")
        
        # Create subject directories
        for i in range(1, self.num_subjects + 1):
            subject_id = f"subject_id_{i:02d}"
            
            print(f"\nCreating directories for {subject_id}...")
            
            base_subject = f"subjects/{subject_id}"
            self.create_dir(base_subject)
            self.create_dir(f"{base_subject}/face_encodings")
            self.create_dir(f"{base_subject}/face_encodings/reference_faces")
            self.create_dir(f"{base_subject}/face_encodings/temp")
            
            # Create experiment directories for each subject
            for experiment in self.experiments:
                exp_path = f"{base_subject}/{experiment}"
                self.create_dir(exp_path)
                self.create_dir(f"{exp_path}/session_001")
                self.create_dir(f"{exp_path}/session_001/trial_images")
                self.create_dir(f"{exp_path}/session_001/Media")
    
    def setup_config(self) -> None:
        """Create configuration directory"""
        print("\n" + "="*50)
        print("Creating configuration directory...")
        print("="*50)
        
        self.create_dir("config")
    
    def create_init_files(self) -> None:
        """Create __init__.py files for Python packages"""
        print("\n" + "="*50)
        print("Creating __init__.py files...")
        print("="*50)
        
        python_modules = [
            "mnky_bx",
            "mnky_bx/core",
            "mnky_bx/hardware",
            "mnky_bx/hardware/camera",
            "mnky_bx/database",
            "mnky_bx/logging",
            "mnky_bx/notifications",
            "mnky_bx/face_recognition_system",
            "mnky_bx/utils",
            "mnky_bx/ui",
            "experiments",
        ]
        
        for experiment in self.experiments:
            python_modules.append(f"experiments/{experiment}")
        
        for module in python_modules:
            self.create_init_file(module)
    
    def print_summary(self) -> None:
        """Print setup summary"""
        print("\n" + "="*50)
        print("✓ Directory setup complete!")
        print("="*50)
        print(f"\nSummary:")
        print(f"  • Directories created: {self.created_dirs}")
        print(f"  • Directories existing: {self.existing_dirs}")
        print(f"  • Core package: mnky_bx/")
        print(f"  • Experiments: experiments/ (with {len(self.experiments)} templates)")
        print(f"  • Subjects: subjects/ (with {self.num_subjects} subject directories)")
        print(f"  • Config: config/")
        print(f"\nNext steps:")
        print(f"  1. Add configuration files to config/")
        print(f"  2. Create experiment.py files in each experiment")
        print(f"  3. Add subject metadata.json files")
        print(f"  4. Run: pip install -r requirements.txt")
        print()
    
    def run(self) -> None:
        """Execute full setup"""
        print("\n" + "="*60)
        print(" " * 10 + "MNKY_BX Directory Setup Script")
        print("="*60)
        
        self.setup_core_package()
        self.setup_experiments()
        self.setup_subjects()
        self.setup_config()
        self.create_init_files()
        self.print_summary()


if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    num_subjects = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    
    setup = DirectorySetup(project_root, num_subjects)
    setup.run()