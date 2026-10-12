# mnky_bx/utils/storage_utils.py
"""
Storage utilities for archival, cleanup, and reporting
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import shutil
from typing import Dict, List, Optional

class StorageManager:
    """
    Manage filesystem storage: cleanup, archival, reporting
    """
    
    def __init__(self, subjects_root: Path = Path("subjects")):
        self.subjects_root = Path(subjects_root)
    
    def get_session_storage_size(self, subject_id: str, 
                                 experiment_name: str,
                                 session_number: int) -> Dict:
        """
        Calculate storage used by a session
        
        Returns:
            {
                'total_mb': float,
                'images_mb': float,
                'videos_mb': float,
                'database_mb': float,
                'logs_mb': float
            }
        """
        session_dir = (self.subjects_root / subject_id / 
                      experiment_name / f"session_{session_number:03d}")
        
        if not session_dir.exists():
            return {'total_mb': 0}
        
        sizes = {
            'total_bytes': 0,
            'images_bytes': 0,
            'videos_bytes': 0,
            'database_bytes': 0,
            'logs_bytes': 0
        }
        
        for file_path in session_dir.rglob('*'):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                sizes['total_bytes'] += file_size
                
                if file_path.suffix == '.jpg':
                    sizes['images_bytes'] += file_size
                elif file_path.suffix == '.mp4':
                    sizes['videos_bytes'] += file_size
                elif file_path.suffix == '.db':
                    sizes['database_bytes'] += file_size
                elif file_path.suffix == '.txt':
                    sizes['logs_bytes'] += file_size
        
        return {
            'total_mb': sizes['total_bytes'] / (1024 * 1024),
            'images_mb': sizes['images_bytes'] / (1024 * 1024),
            'videos_mb': sizes['videos_bytes'] / (1024 * 1024),
            'database_mb': sizes['database_bytes'] / (1024 * 1024),
            'logs_mb': sizes['logs_bytes'] / (1024 * 1024)
        }
    
    def cleanup_old_jpeg_frames(self, subject_id: str,
                               experiment_name: str,
                               session_number: int,
                               keep_days: int = 7):
        """
        Delete JPEG frames after they've been encoded to video
        (Saves space while keeping videos for reference)
        
        Args:
            keep_days: Keep JPEGs for N days after session
        """
        session_dir = (self.subjects_root / subject_id /
                      experiment_name / f"session_{session_number:03d}")
        
        trial_images_dir = session_dir / 'trial_images'
        if not trial_images_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        
        for jpeg_file in trial_images_dir.glob('trial_*_frame_*.jpg'):
            file_mtime = datetime.fromtimestamp(jpeg_file.stat().st_mtime)
            
            if file_mtime < cutoff_time:
                # Check if corresponding video exists
                trial_num = jpeg_file.name.split('_')[1]
                video_file = trial_images_dir / f'trial_{trial_num}.mp4'
                
                if video_file.exists():
                    jpeg_file.unlink()
                    print(f"Deleted {jpeg_file.name}")
    
    def compute_file_checksum(self, file_path: Path) -> str:
        """
        Compute SHA256 checksum for archival integrity
        
        Args:
            file_path: Path to file
        
        Returns:
            Hex checksum string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def generate_storage_report(self, subject_id: str) -> Dict:
        """
        Generate storage report for a subject
        
        Returns:
            {
                'subject_id': str,
                'total_storage_mb': float,
                'experiments': {
                    'experiment_name': {
                        'total_mb': float,
                        'sessions': [...]
                    }
                }
            }
        """
        subject_dir = self.subjects_root / subject_id
        
        if not subject_dir.exists():
            return None
        
        report = {
            'subject_id': subject_id,
            'total_storage_mb': 0,
            'generated_at': datetime.now().isoformat(),
            'experiments': {}
        }
        
        for exp_dir in subject_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            
            exp_name = exp_dir.name
            exp_size = sum(f.stat().st_size for f in exp_dir.rglob('*') 
                          if f.is_file()) / (1024 * 1024)
            
            report['experiments'][exp_name] = {
                'total_mb': exp_size,
                'sessions': []
            }
            
            for session_dir in sorted(exp_dir.iterdir()):
                if session_dir.is_dir() and session_dir.name.startswith('session_'):
                    session_size = sum(f.stat().st_size for f in session_dir.rglob('*')
                                      if f.is_file()) / (1024 * 1024)
                    
                    report['experiments'][exp_name]['sessions'].append({
                        'session_name': session_dir.name,
                        'storage_mb': session_size
                    })
            
            report['total_storage_mb'] += exp_size
        
        return report
    
    def save_storage_report(self, report: Dict, output_path: Optional[Path] = None):
        """Save storage report to JSON"""
        if output_path is None:
            output_path = (self.subjects_root / report['subject_id'] / 
                          'storage_report.json')
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Storage report saved to {output_path}")