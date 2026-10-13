# mnky_bx
behavioral data acquisition platform

# MNKY_BX

## UPDATED ARCHITECTURE: Filesystem + SQLite Hybrid Storage
```markdown
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
│   │   ├── camera/
│   │   │   ├── __init__.py
│   │   │   ├── camera_system.py
│   │   │   ├── face_recognition.py
│   │   │   ├── face_encoder.py
│   │   │   └── capture_manager.py          # ← OPTIMIZED
│   │   │
│   │   ├── arduino_buttons.py
│   │   ├── arduino_reward.py
│   │   ├── hardware_interface.py
│   │   └── health_monitor.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_manager.py
│   │   └── schemas.py                      # ← UPDATED
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
│   ├── face_recognition_system/
│   │   ├── __init__.py
│   │   ├── subject_registry.py
│   │   ├── recognition_engine.py
│   │   ├── face_database.py
│   │   ├── subject_parameter_manager.py
│   │   └── unrecognized_clustering.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   ├── config_loader.py
│   │   └── storage_utils.py                # ← NEW: Storage helpers
│   │
│   └── ui/
│       ├── __init__.py
│       ├── pygame_utils.py
│       ├── error_screen.py
│       ├── launcher_ui.py
│       └── subject_enrollment_ui.py
│
├── experiments/
│   ├── gambling_experiment/
│   │   ├── experiment.py
│   │   ├── config.json
│   │   └── subject_params/
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
├── subjects/
│   ├── not_recognized/
│   │   ├── raw_images/
│   │   │   ├── trial_001_frame_001.jpg
│   │   │   ├── trial_001_frame_002.jpg
│   │   │   └── ...
│   │   ├── embeddings/
│   │   │   └── embeddings.pkl
│   │   └── clustering_results.json
│   │
│   ├── subject_id_1/
│   │   ├── metadata.json
│   │   ├── face_encodings/
│   │   │   ├── reference_faces/
│   │   │   │   ├── face_001.jpg
│   │   │   │   ├── face_002.jpg
│   │   │   │   └── embeddings.pkl
│   │   │   └── temp/
│   │   │
│   │   ├── gambling_experiment/
│   │   │   ├── session_001/
│   │   │   │   ├── exp_id_20261010_134200.txt
│   │   │   │   ├── exp_id_20261010_134200.db   # ← Lightweight, no BLOBs
│   │   │   │   ├── trial_images/               # ← Filesystem storage
│   │   │   │   │   ├── trial_001_frame_001.jpg
│   │   │   │   │   ├── trial_001_frame_001_full.jpg
│   │   │   │   │   ├── trial_002_frame_001.jpg
│   │   │   │   │   ├── recognition_log.json
│   │   │   │   │   └── trial_001.mp4           # ← Optional encoded video
│   │   │   │   └── Media/
│   │   │   ├── session_002/
│   │   │   └── ...
│   │   │
│   │   ├── blackjack/
│   │   │   └── session_001/
│   │   │
│   │   └── recognition_history.json
│   │
│   └── subject_id_2/
│       └── ...
│
├── config/
│   ├── kiosk_config.json
│   ├── notification_config.json
│   ├── hardware_config.json
│   └── face_recognition_config.json
│
├── launcher.py
├── setup.py
├── requirements.txt
└── README.md
```
## 1. Updated Database Schemas
```python
# mnky_bx/database/schemas.py
"""
Database schemas - optimized for lightweight storage
Images stored on filesystem, only metadata/references in DB
"""

# Main trial data table (unchanged)
CREATE_TRIAL_DATA = '''
CREATE TABLE IF NOT EXISTS trial_data (
    trial_number INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_type TEXT,
    win_Amount1 INTEGER,
    lose_Amount1 INTEGER,
    pWin1 REAL,
    win_Amount2 INTEGER,
    lose_Amount2 INTEGER,
    pWin2 REAL,
    opt_sp_config TEXT,
    choice TEXT,
    success BOOLEAN,
    reward_magnitude INTEGER,
    ts_trial_start INTEGER,
    ts_motion_detect INTEGER,
    ts_face_detect INTEGER,
    ts_stimuli_on INTEGER,
    ts_button_press INTEGER,
    ts_outcome_reveal INTEGER,
    ts_reward_delivered INTEGER,
    ts_trial_end INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
'''

# ← NEW: Lightweight trial pictures table (NO BLOB)
CREATE_TRIAL_PICTURES = '''
CREATE TABLE IF NOT EXISTS trial_pictures (
    picture_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER NOT NULL,
    timestamp INTEGER,
    frame_number INTEGER,
    image_path TEXT NOT NULL,              -- Relative path to filesystem
    image_width INTEGER,
    image_height INTEGER,
    image_size_bytes INTEGER,              -- For storage reporting
    face_detected BOOLEAN DEFAULT 0,
    recognized BOOLEAN DEFAULT 0,
    subject_id TEXT,                       -- Subject if recognized
    recognition_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number),
    INDEX idx_trial_number (trial_number),
    INDEX idx_subject_id (subject_id),
    INDEX idx_recognized (recognized)
)
'''

# ← NEW: Trial video encoding (optional)
CREATE_TRIAL_VIDEO = '''
CREATE TABLE IF NOT EXISTS trial_video (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER NOT NULL UNIQUE,
    video_path TEXT NOT NULL,              -- Path to .mp4 file
    codec TEXT DEFAULT 'h265',
    fps REAL,
    duration_s REAL,
    file_size_mb REAL,
    encoding_status TEXT,                  -- 'pending', 'completed', 'failed'
    encoded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number),
    INDEX idx_trial_number (trial_number)
)
'''

# ← NEW: Recognition results per trial
CREATE_RECOGNITION_RESULTS = '''
CREATE TABLE IF NOT EXISTS recognition_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trial_number INTEGER NOT NULL,
    recognized BOOLEAN,
    subject_id TEXT,
    confidence REAL,
    num_frames_analyzed INTEGER,           -- Frames with face detected
    num_frames_recognized INTEGER,         -- Frames where subject matched
    best_match_frame INTEGER,
    detection_status TEXT,                 -- 'successful', 'no_faces', 'ambiguous'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trial_number) REFERENCES trial_data (trial_number),
    INDEX idx_trial_number (trial_number),
    INDEX idx_subject_id (subject_id)
)
'''

# ← NEW: Session-level statistics
CREATE_SESSION_STATS = '''
CREATE TABLE IF NOT EXISTS session_stats (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT,
    experiment_name TEXT,
    session_number INTEGER,
    total_trials INTEGER,
    total_frames_captured INTEGER,
    total_frames_with_faces INTEGER,
    recognized_frames INTEGER,
    unrecognized_frames INTEGER,
    average_recognition_confidence REAL,
    total_storage_mb REAL,
    session_duration_minutes REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
'''

# ← NEW: Storage tracking for archival
CREATE_STORAGE_MANIFEST = '''
CREATE TABLE IF NOT EXISTS storage_manifest (
    manifest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    file_type TEXT,                        -- 'jpeg', 'mp4', 'metadata'
    file_path TEXT,
    file_size_bytes INTEGER,
    checksum TEXT,                         -- SHA256 for integrity
    archived BOOLEAN DEFAULT 0,
    archived_location TEXT,
    archived_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session_stats (session_id)
)
'''

# Initialization function
def initialize_database(db_connection):
    """Create all tables"""
    cursor = db_connection.cursor()
    
    schemas = [
        CREATE_TRIAL_DATA,
        CREATE_TRIAL_PICTURES,
        CREATE_TRIAL_VIDEO,
        CREATE_RECOGNITION_RESULTS,
        CREATE_SESSION_STATS,
        CREATE_STORAGE_MANIFEST
    ]
    
    for schema in schemas:
        try:
            cursor.execute(schema)
        except Exception as e:
            print(f"Schema error: {e}")
    
    db_connection.commit()
    print("Database initialized successfully")
```
## 2. Optimized CaptureManager
```python
# mnky_bx/hardware/camera/capture_manager.py
"""
Optimized image capture and storage system
- Fast filesystem writes (parallel I/O)
- Lightweight database (references only)
- Face recognition on direct files
- Optional async video encoding
"""

import cv2
import json
import threading
import queue
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
import numpy as np

@dataclass
class CapturedFrameData:
    """Metadata for a captured frame"""
    trial_number: int
    timestamp: datetime
    frame_number: int
    frame_image: 'np.ndarray'           # Full camera frame (BGR)
    face_bbox: Optional[Tuple] = None   # (x, y, w, h) if face detected
    face_image: Optional['np.ndarray'] = None  # Cropped face if detected


class CaptureManager:
    """
    Manages efficient image capture and storage during trials
    
    Strategy:
    1. Capture frames at 3 FPS during trial
    2. Write directly to filesystem (fast, parallel-friendly)
    3. Detect faces and route to subject directories
    4. Log lightweight metadata to database
    5. Optionally encode to video asynchronously
    """
    
    def __init__(self,
                 session_dir: Path,
                 recognition_engine,
                 subject_id: Optional[str] = None,
                 enable_video_encoding: bool = True,
                 video_quality: str = 'medium'):
        """
        Initialize capture manager
        
        Args:
            session_dir: Session directory (e.g., subjects/subject_id/exp/session_001)
            recognition_engine: FaceRecognitionEngine instance
            subject_id: Current subject (None = unrecognized)
            enable_video_encoding: Post-process to H.265 (background task)
            video_quality: 'low', 'medium', 'high' (affects compression)
        """
        self.session_dir = Path(session_dir)
        self.recognition_engine = recognition_engine
        self.current_subject_id = subject_id
        self.enable_video_encoding = enable_video_encoding
        self.video_quality = video_quality
        
        # Create directories
        self.trial_images_dir = session_dir / 'trial_images'
        self.trial_images_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory tracking (will batch write to DB later)
        self.frame_metadata = []         # Lightweight frame info
        self.recognition_results = []    # Recognition results per frame
        self.trial_stats = {}            # Stats by trial
        
        # Video encoding queue (async)
        self.video_encoding_enabled = enable_video_encoding
        self.video_queue = queue.Queue()
        self.video_encoding_thread = None
        self.video_encoding_stop = threading.Event()
        
        if enable_video_encoding:
            self._start_video_encoding_thread()
    
    def save_captured_frame(self,
                           frame_data: CapturedFrameData) -> Dict:
        """
        Save captured frame to filesystem
        
        Args:
            frame_data: CapturedFrameData object
        
        Returns:
            Metadata dict for tracking/database
        """
        trial_num = frame_data.trial_number
        frame_num = frame_data.frame_number
        
        # Initialize trial stats if needed
        if trial_num not in self.trial_stats:
            self.trial_stats[trial_num] = {
                'frames_captured': 0,
                'frames_with_faces': 0,
                'frames_recognized': 0,
                'total_size_bytes': 0
            }
        
        # Generate filename and save full frame
        full_filename = f"trial_{trial_num:03d}_frame_{frame_num:03d}_full.jpg"
        full_path = self.trial_images_dir / full_filename
        
        cv2.imwrite(str(full_path), frame_data.frame_image, 
                   [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        file_size = full_path.stat().st_size
        
        # Create metadata entry
        metadata = {
            'trial_number': trial_num,
            'frame_number': frame_num,
            'timestamp': int(frame_data.timestamp.timestamp() * 1000),  # ms
            'image_path': str(full_path.relative_to(self.session_dir)),
            'image_width': frame_data.frame_image.shape[1],
            'image_height': frame_data.frame_image.shape[0],
            'image_size_bytes': file_size,
            'face_detected': frame_data.face_bbox is not None,
            'recognized': False,
            'subject_id': None,
            'recognition_confidence': 0.0
        }
        
        # Update stats
        self.trial_stats[trial_num]['frames_captured'] += 1
        self.trial_stats[trial_num]['total_size_bytes'] += file_size
        
        # Queue for video encoding
        if self.video_encoding_enabled:
            self.video_queue.put({
                'trial_number': trial_num,
                'frame': frame_data.frame_image.copy(),
                'sequence_number': frame_num
            })
        
        self.frame_metadata.append(metadata)
        return metadata
    
    def process_detected_face(self,
                             frame_data: CapturedFrameData) -> Dict:
        """
        Process detected face: recognize, save, log
        
        Args:
            frame_data: CapturedFrameData with face_image and face_bbox
        
        Returns:
            Recognition result dict
        """
        trial_num = frame_data.trial_number
        frame_num = frame_data.frame_number
        
        if frame_data.face_image is None or frame_data.face_bbox is None:
            return {'recognized': False, 'subject_id': None, 'confidence': 0.0}
        
        # Perform face recognition
        recognition_result = self.recognition_engine.recognize_face(
            frame_data.face_image
        )
        
        # Determine storage directory based on recognition
        if recognition_result.recognized:
            subject_id = recognition_result.subject_id
            storage_base = Path('subjects') / subject_id
        else:
            subject_id = 'not_recognized'
            storage_base = Path('subjects') / 'not_recognized'
        
        # Create appropriate directories
        face_images_dir = storage_base / 'face_images'
        face_images_dir.mkdir(parents=True, exist_ok=True)
        
        # Save cropped face image
        face_filename = f"trial_{trial_num:03d}_frame_{frame_num:03d}.jpg"
        face_path = face_images_dir / face_filename
        cv2.imwrite(str(face_path), frame_data.face_image, 
                   [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        # Save full context frame to same location
        full_face_filename = f"trial_{trial_num:03d}_frame_{frame_num:03d}_context.jpg"
        full_face_path = face_images_dir / full_face_filename
        cv2.imwrite(str(full_face_path), frame_data.frame_image)
        
        # Create recognition log entry
        recognition_entry = {
            'trial_number': trial_num,
            'frame_number': frame_num,
            'timestamp': frame_data.timestamp.isoformat(),
            'recognized': recognition_result.recognized,
            'subject_id': recognition_result.subject_id,
            'confidence': float(recognition_result.confidence),
            'status': recognition_result.status,
            'face_path': str(face_path),
            'context_path': str(full_face_path),
            'face_bbox': {
                'x': frame_data.face_bbox[0],
                'y': frame_data.face_bbox[1],
                'w': frame_data.face_bbox[2],
                'h': frame_data.face_bbox[3]
            }
        }
        
        self.recognition_results.append(recognition_entry)
        
        # Update trial stats
        self.trial_stats[trial_num]['frames_with_faces'] += 1
        if recognition_result.recognized:
            self.trial_stats[trial_num]['frames_recognized'] += 1
        
        # Update frame metadata with recognition info
        for meta in self.frame_metadata:
            if (meta['trial_number'] == trial_num and 
                meta['frame_number'] == frame_num):
                meta['face_detected'] = True
                meta['recognized'] = recognition_result.recognized
                meta['subject_id'] = recognition_result.subject_id
                meta['recognition_confidence'] = float(recognition_result.confidence)
                break
        
        return {
            'recognized': recognition_result.recognized,
            'subject_id': recognition_result.subject_id,
            'confidence': float(recognition_result.confidence),
            'status': recognition_result.status
        }
    
    def get_trial_best_recognition(self, trial_number: int) -> Dict:
        """
        Get best recognition result from trial
        (Highest confidence recognized or best unrecognized)
        
        Args:
            trial_number: Trial to query
        
        Returns:
            Best recognition result
        """
        trial_results = [r for r in self.recognition_results 
                        if r['trial_number'] == trial_number]
        
        if not trial_results:
            return {
                'recognized': False,
                'subject_id': None,
                'confidence': 0.0,
                'status': 'no_faces_detected'
            }
        
        # Prefer recognized faces with highest confidence
        recognized = [r for r in trial_results if r['recognized']]
        if recognized:
            best = max(recognized, key=lambda r: r['confidence'])
            return {
                'recognized': True,
                'subject_id': best['subject_id'],
                'confidence': best['confidence'],
                'status': 'recognized'
            }
        
        # Otherwise, return highest confidence unrecognized
        best = max(trial_results, key=lambda r: r['confidence'])
        return {
            'recognized': False,
            'subject_id': None,
            'confidence': best['confidence'],
            'status': 'unrecognized'
        }
    
    def save_metadata_to_database(self, db_connection):
        """
        Batch write all captured metadata to database
        Called once per trial (efficient, non-blocking)
        
        Args:
            db_connection: SQLite connection
        """
        cursor = db_connection.cursor()
        
        # Write frame metadata
        for metadata in self.frame_metadata:
            try:
                cursor.execute('''
                    INSERT INTO trial_pictures 
                    (trial_number, timestamp, frame_number, image_path, 
                     image_width, image_height, image_size_bytes,
                     face_detected, recognized, subject_id, recognition_confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata['trial_number'],
                    metadata['timestamp'],
                    metadata['frame_number'],
                    metadata['image_path'],
                    metadata['image_width'],
                    metadata['image_height'],
                    metadata['image_size_bytes'],
                    metadata['face_detected'],
                    metadata['recognized'],
                    metadata['subject_id'],
                    metadata['recognition_confidence']
                ))
            except Exception as e:
                print(f"Error inserting frame metadata: {e}")
        
        db_connection.commit()
        print(f"Saved {len(self.frame_metadata)} frame metadata entries")
        
        # Reset for next trial
        self.frame_metadata.clear()
    
    def save_recognition_log_json(self):
        """
        Save recognition results to JSON for quick analysis
        Called once per session
        """
        log_file = self.trial_images_dir / 'recognition_log.json'
        with open(log_file, 'w') as f:
            json.dump(self.recognition_results, f, indent=2)
        
        print(f"Saved {len(self.recognition_results)} recognition entries to JSON")
    
    def save_trial_statistics(self, db_connection, trial_number: int):
        """
        Save trial-level statistics
        
        Args:
            db_connection: SQLite connection
            trial_number: Trial number
        """
        if trial_number not in self.trial_stats:
            return
        
        stats = self.trial_stats[trial_number]
        recognition = self.get_trial_best_recognition(trial_number)
        
        cursor = db_connection.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO recognition_results
                (trial_number, recognized, subject_id, confidence,
                 num_frames_analyzed, num_frames_recognized, detection_status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                trial_number,
                recognition['recognized'],
                recognition['subject_id'],
                recognition['confidence'],
                stats['frames_with_faces'],
                stats['frames_recognized'],
                recognition['status']
            ))
            
            db_connection.commit()
            print(f"Trial {trial_number} statistics saved")
            
        except Exception as e:
            print(f"Error saving trial statistics: {e}")
    
    # ============ VIDEO ENCODING (ASYNC) ============
    
    def _start_video_encoding_thread(self):
        """Start async video encoding thread"""
        self.video_encoding_stop.clear()
        self.video_encoding_thread = threading.Thread(
            target=self._video_encoding_worker,
            daemon=True
        )
        self.video_encoding_thread.start()
        print("Video encoding thread started")
    
    def _video_encoding_worker(self):
        """
        Background thread: encode frames to H.265 video
        Groups frames by trial, processes asynchronously
        """
        trial_frames = {}  # {trial_num: [(seq_num, frame), ...]}
        
        while not self.video_encoding_stop.is_set():
            try:
                # Get frame from queue with timeout
                item = self.video_queue.get(timeout=1.0)
                
                trial_num = item['trial_number']
                frame = item['frame']
                seq_num = item['sequence_number']
                
                if trial_num not in trial_frames:
                    trial_frames[trial_num] = []
                
                trial_frames[trial_num].append((seq_num, frame))
                
                # When we have enough frames or queue is empty, encode
                if len(trial_frames[trial_num]) >= 60:  # Buffer of ~20 seconds
                    self._encode_trial_video(trial_num, trial_frames[trial_num])
                    del trial_frames[trial_num]
                
            except queue.Empty:
                # Periodically flush partial trials
                for trial_num, frames in list(trial_frames.items()):
                    if frames:
                        self._encode_trial_video(trial_num, frames)
                        del trial_frames[trial_num]
            
            except Exception as e:
                print(f"Video encoding error: {e}")
    
    def _encode_trial_video(self, trial_number: int, frames: List[Tuple]):
        """
        Encode trial frames to H.265 video
        
        Args:
            trial_number: Trial ID
            frames: List of (sequence_number, frame) tuples
        """
        if not frames or len(frames) < 3:
            return
        
        try:
            # Sort by sequence number
            frames.sort(key=lambda x: x[0])
            frame_images = [f[1] for f in frames]
            
            # Get dimensions from first frame
            height, width = frame_images[0].shape[:2]
            
            # Output path
            output_path = self.trial_images_dir / f'trial_{trial_number:03d}.mp4'
            
            # Video quality settings
            quality_presets = {
                'low': {
                    'crf': 28,      # 0=lossless, 51=worst quality
                    'preset': 'fast'
                },
                'medium': {
                    'crf': 23,
                    'preset': 'medium'
                },
                'high': {
                    'crf': 18,
                    'preset': 'slow'
                }
            }
            
            preset = quality_presets.get(self.video_quality, quality_presets['medium'])
            
            # Use OpenCV VideoWriter with H.265
            fourcc = cv2.VideoWriter_fourcc(*'hev1')  # H.265
            fps = 3.0
            
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            for frame in frame_images:
                out.write(frame)
            
            out.release()
            
            # Get file size
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            
            print(f"Encoded trial {trial_number} to {output_path} ({file_size_mb:.1f} MB)")
            
        except Exception as e:
            print(f"Video encoding failed for trial {trial_number}: {e}")
    
    def stop_video_encoding(self, wait_timeout: float = 30.0):
        """
        Stop video encoding thread gracefully
        
        Args:
            wait_timeout: Max seconds to wait for thread
        """
        print("Stopping video encoding thread...")
        self.video_encoding_stop.set()
        
        if self.video_encoding_thread:
            self.video_encoding_thread.join(timeout=wait_timeout)
            print("Video encoding thread stopped")
    
    def cleanup(self):
        """Clean up all resources"""
        # Stop video encoding
        if self.video_encoding_enabled:
            self.stop_video_encoding()
        
        print("CaptureManager cleanup complete")
```
## 3. Updated CameraDetectionSystem
```python
# mnky_bx/hardware/camera/camera_system.py (UPDATED)
"""
Camera detection system with face recognition integration
Optimized for filesystem storage
"""

import cv2
import threading
import queue
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import numpy as np

class CameraDetectionSystem:
    """
    Motion detection → Face detection → Face recognition
    Captures and stores images efficiently
    """
    
    def __init__(self, config, recognition_engine):
        """
        Args:
            config: Camera configuration dict
            recognition_engine: FaceRecognitionEngine instance
        """
        print('Camera setup...')
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Face detection cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Motion detection
        self.background_subtractor = None
        self.motion_threshold = config.get('motion_threshold', 5000)
        self.frames_to_stabilize = config.get('frames_to_stabilize', 30)
        
        # Detection flags
        self.motion_detected_flag = False
        self.face_detected_flag = False
        
        # Threading controls
        self.detection_active = False
        self.detection_thread = None
        self.stop_detection = threading.Event()
        
        # Face recognition
        self.recognition_engine = recognition_engine
        self.capture_manager = None  # Set per-trial
        
        # Picture capture during trials
        self.capture_pictures = False
        self.picture_thread = None
        self.trial_number = 0
        
        # Tracking
        self.last_recognized_subject = None
        self.recognition_confidence = 0.0
    
    def reset_for_new_detection_cycle(self):
        """Reset detection system for new motion->face cycle"""
        print("Resetting detection system...")
        
        self.stop_all_detection()
        
        # Reset flags
        self.motion_detected_flag = False
        self.face_detected_flag = False
        
        # Create fresh background subtractor
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=50,
            history=500
        )
        
        # Stabilize background model
        print("Stabilizing background model...")
        for i in range(self.frames_to_stabilize):
            ret, frame = self.cap.read()
            if ret:
                self.background_subtractor.apply(frame)
        
        print("Detection system reset complete")
    
    def _detection_thread(self):
        """
        Main detection thread: motion -> face detection
        """
        print("Detection thread started")
        
        while not self.stop_detection.is_set() and self.detection_active:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Phase 1: Motion Detection
            if not self.motion_detected_flag:
                fg_mask = self.background_subtractor.apply(frame)
                motion_area = cv2.countNonZero(fg_mask)
                
                if motion_area > self.motion_threshold:
                    print(f"Motion detected! Area: {motion_area}")
                    self.motion_detected_flag = True
            
            # Phase 2: Face Detection (only after motion detected)
            elif not self.face_detected_flag:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(50, 50)
                )
                
                if len(faces) > 0:
                    print(f"Face detected! {len(faces)} face(s) found")
                    self.face_detected_flag = True
            
            time.sleep(0.03)  # ~30 FPS
        
        print("Detection thread ended")
    
    def start_detection_cycle(self):
        """Start motion->face detection cycle"""
        if self.detection_thread and self.detection_thread.is_alive():
            return False
        
        self.detection_active = True
        self.stop_detection.clear()
        
        self.detection_thread = threading.Thread(target=self._detection_thread)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        return True
    
    def is_motion_detected(self) -> bool:
        """Check if motion has been detected"""
        return self.motion_detected_flag
    
    def is_face_detected(self) -> bool:
        """Check if face has been detected"""
        return self.face_detected_flag
    
    # ============ PICTURE CAPTURE WITH RECOGNITION ============
    
    def start_picture_capture(self, capture_manager, trial_number: int):
        """
        Start capturing pictures at 3 FPS during trial
        
        Args:
            capture_manager: CaptureManager instance
            trial_number: Trial number
        """
        if self.picture_thread and self.picture_thread.is_alive():
            return False
        
        self.capture_pictures = True
        self.trial_number = trial_number
        self.capture_manager = capture_manager
        
        self.picture_thread = threading.Thread(
            target=self._picture_capture_thread,
            args=(trial_number,)
        )
        self.picture_thread.daemon = True
        self.picture_thread.start()
        
        return True
    
    def _picture_capture_thread(self, trial_number: int):
        """
        Capture pictures at 3 FPS during trial with face recognition
        Writes directly to filesystem (fast I/O)
        """
        print(f"Picture capture thread started for trial {trial_number}")
        
        frame_interval = 1.0 / 3.0  # 3 FPS
        frame_number = 0
        
        while self.capture_pictures and not self.stop_detection.is_set():
            start_time = time.time()
            
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            timestamp = datetime.now()
            
            # Save full frame
            frame_data = {
                'trial_number': trial_number,
                'timestamp': timestamp,
                'frame_number': frame_number,
                'frame_image': frame,
                'face_bbox': None,
                'face_image': None
            }
            
            # Save to filesystem (fast)
            self.capture_manager.save_captured_frame(frame_data)
            
            # Detect faces in frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )
            
            # Process each detected face
            for (x, y, w, h) in faces:
                face_image = frame[y:y+h, x:x+w]
                
                # Process face: recognize and route to storage
                face_data = {
                    'trial_number': trial_number,
                    'timestamp': timestamp,
                    'frame_number': frame_number,
                    'frame_image': frame,
                    'face_bbox': (x, y, w, h),
                    'face_image': face_image
                }
                
                result = self.capture_manager.process_detected_face(face_data)
                
                if result['recognized']:
                    self.last_recognized_subject = result['subject_id']
                    self.recognition_confidence = result['confidence']
                    print(f"Trial {trial_number}: Recognized {result['subject_id']} "
                          f"(confidence: {result['confidence']:.2f})")
            
            frame_number += 1
            
            # Maintain timing
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            time.sleep(sleep_time)
        
        print(f"Picture capture thread ended (captured {frame_number} frames)")
    
    def stop_picture_capture(self):
        """Stop picture capture"""
        self.capture_pictures = False
        
        if self.picture_thread and self.picture_thread.is_alive():
            self.picture_thread.join(timeout=2.0)
    
    def stop_all_detection(self):
        """Stop all detection threads"""
        self.detection_active = False
        self.capture_pictures = False
        self.stop_detection.set()
        
        # Wait for threads to finish
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
        
        if self.picture_thread and self.picture_thread.is_alive():
            self.picture_thread.join(timeout=1.0)
    
    def get_trial_recognition_result(self) -> Dict:
        """
        Get best recognition result from trial
        
        Returns:
            {
                'subject_id': str or None,
                'recognized': bool,
                'confidence': float,
                'status': str
            }
        """
        if not self.capture_manager:
            return {
                'subject_id': None,
                'recognized': False,
                'confidence': 0.0,
                'status': 'no_capture_manager'
            }
        
        return self.capture_manager.get_trial_best_recognition(self.trial_number)
    
    def cleanup(self):
        """Cleanup all resources"""
        self.stop_all_detection()
        if self.cap:
            self.cap.release()
        print("Camera system cleanup complete")
```
## 4. Storage Utilities
```python
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
```
## 5. Updated Experiment Base Class Integration
```python
# mnky_bx/core/experiment_base.py (KEY SECTIONS UPDATED)

class ExperimentBase:
    def __init__(self,
                 experiment_name,
                 subject_id,
                 kiosk_manager,
                 logger,
                 notification_manager,
                 hardware_config,
                 recognition_engine,
                 parameter_manager):
        """
        Initialize experiment with optimized storage
        """
        # ... existing initialization ...
        
        # Initialize camera system
        from mnky_bx.hardware.camera.camera_system import CameraDetectionSystem
        from mnky_bx.hardware.camera.capture_manager import CaptureManager
        
        self.camera_system = CameraDetectionSystem(hardware_config, recognition_engine)
        
        # Create session directory
        session = kiosk_manager.start_session(subject_id, experiment_name)
        self.session_dir = session['session_dir']
        
        # Initialize capture manager (filesystem storage)
        self.capture_manager = CaptureManager(
            session_dir=self.session_dir,
            recognition_engine=recognition_engine,
            subject_id=subject_id,
            enable_video_encoding=True,
            video_quality='medium'
        )
    
    def run_trial(self):
        """
        Run single trial with adaptive parameters
        """
        # ... setup and stimulus drawing ...
        
        # Start picture capture (filesystem-based)
        self.camera_system.start_picture_capture(
            self.capture_manager,
            self.current_trial
        )
        
        self.wait_for_response()
        self.camera_system.stop_picture_capture()
        
        # ← NEW: Save captured frame metadata to database (batch)
        self.capture_manager.save_metadata_to_database(self.db_connection)
        
        # Save trial statistics
        self.capture_manager.save_trial_statistics(
            self.db_connection,
            self.current_trial
        )
        
        # Get recognition result for this trial
        trial_recognition = self.camera_system.get_trial_recognition_result()
        
        if trial_recognition['recognized']:
            print(f"Subject recognized: {trial_recognition['subject_id']} "
                  f"(confidence: {trial_recognition['confidence']:.2f})")
            self.logger.log_trial_recognition(
                trial_num=self.current_trial,
                subject_id=trial_recognition['subject_id'],
                confidence=trial_recognition['confidence']
            )
        
        # Handle choice and deliver reward
        self.handle_choice()
        self.reveal_outcome()
        self.deliver_reward()
    
    def cleanup(self):
        """
        Cleanup at end of session
        """
        # Save recognition log JSON
        self.capture_manager.save_recognition_log_json()
        
        # Stop video encoding
        self.capture_manager.stop_video_encoding()
        
        # Generate storage report
        from mnky_bx.utils.storage_utils import StorageManager
        storage_manager = StorageManager()
        report = storage_manager.generate_storage_report(self.subject_id)
        if report:
            storage_manager.save_storage_report(report)
        
        # Close database
        if self.db_connection:
            self.db_connection.close()
        
        # Cleanup camera
        self.camera_system.cleanup()
        
        print("Experiment cleanup complete")
```
## 6. Configuration File Updates
```json
// mnky_bx/config/kiosk_config.json (UPDATED)
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
    "face_detection_timeout_s": 10,
    "motion_threshold": 5000,
    "frames_to_stabilize": 30
  },
  "storage": {
    "enable_video_encoding": true,
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
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
  }
}
```
## 7. Directory Structure Summary
```python
subjects/
├── not_recognized/
│   ├── raw_images/                      # Unidentified faces
│   │   ├── trial_001_frame_001.jpg
│   │   └── ...
│   ├── face_images/
│   │   ├── trial_001_frame_001.jpg
│   │   ├── trial_001_frame_001_context.jpg
│   │   └── ...
│   └── embeddings.pkl
│
└── subject_id_1/
    ├── metadata.json
    ├── face_encodings/
    │   ├── reference_faces/
    │   │   └── face_*.jpg
    │   └── embeddings.pkl
    │
    └── gambling_experiment/
        └── session_001/
            ├── exp_id_20261010_134200.db      # ← Lightweight, no BLOBs
            ├── exp_id_20261010_134200.txt     # ← Log file
            └── trial_images/                   # ← Filesystem storage
                ├── trial_001_frame_001_full.jpg
                ├── trial_001_frame_002_full.jpg
                ├── trial_001.mp4               # ← Optional H.265 video
                └── recognition_log.json        # ← Recognition results
```
## Summary of Changes
| Component| 	Old	New|
| :--- | :---: |
| Image Storage| 	SQLite BLOB	Filesystem JPEG + path reference| 
| Database Size| 	150+ MB (bloated)	2 MB (lightweight)| 
| Write Performance| 	Slow (serial)	Fast (parallel I/O)| 
| Query Performance| 	Very slow	Fast (no BLOB scanning)| 
| Direct File Access| 	Requires extraction	Direct filesystem access| 
| Video Encoding| 	Manual post-processing	Automatic async background thread| 
| Space Efficiency	Poor| 	Excellent (H.265 option)| 
| Face Recognition	Difficult| 	Easy (direct files)| 
| Metadata Handling| 	All in DB	Split: references in DB, details in JSON| 

This optimized architecture provides:

- ✅ Fast capture: Parallel filesystem I/O during trials
- ✅ Fast queries: Lightweight database for behavioral analysis
- ✅ Fast queries: Lightweight database for behavioral analysis
- ✅ Easy integration: Face recognition works directly on files
- ✅ Scalability: Handles many sessions without database bloat
- ✅ Flexibility: Optional video encoding for archival
- ✅ Reproducibility: Full image storage with metadata
- ✅ Transparency: Direct access to trial images for inspection

Ready to pass to IDE copilot!

### Python Alternative (Cross-Platform works on any OS):
```python
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
```
#### Quick Start Commands
```bash
cd /path/to/mnky_bx
python setup_directories.py . 12
```

There are 2 separate entities for arduino_buttons.py and arduino_reward.py. in a recent hardware update a single arduino uno is used for both monitoring buttons and reward output.

This is a common integration point that needs careful design. Let me create a unified Arduino interface that handles both buttons and rewards on a single device.

## Updated Hardware Architecture
```bash
mnky_bx/hardware/
├── __init__.py
├── arduino/                          # ← NEW: Unified Arduino module
│   ├── __init__.py
│   ├── arduino_interface.py          # ← NEW: Base interface
│   ├── arduino_uno_controller.py     # ← NEW: Single Arduino Uno handler
│   ├── protocol.py                   # ← NEW: Communication protocol
│   └── commands.py                   # ← NEW: Command definitions
│
├── camera/
│   ├── __init__.py
│   ├── camera_system.py
│   ├── face_recognition.py
│   ├── face_encoder.py
│   └── capture_manager.py
│
├── health_monitor.py
└── hardware_interface.py             # ← Abstract base classes
```
## 1. Command Protocol Definition
```python
# mnky_bx/hardware/arduino/commands.py
"""
Arduino command protocol for unified button + reward control
Defines all commands sent to and received from Arduino Uno
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict

class ButtonID(Enum):
    """Button identifiers"""
    LEFT = "20"
    RIGHT = "21"

class LEDCommand(Enum):
    """LED control commands"""
    LEFT_ON = "1"          # Turn on left button LED
    RIGHT_ON = "2"         # Turn on right button LED
    BOTH_ON = "3"          # Turn on both LEDs
    ALL_OFF = "4"          # Turn off all LEDs

class RewardCommand(Enum):
    """Reward/motor commands"""
    MOTOR_FORWARD = "G0 X5\n"     # Move reward motor forward (5mm)
    MOTOR_BACKWARD = "G0 X0\n"    # Move reward motor backward (home)
    MOTOR_HOME = "G92 X0 Y0 Z0\n" # Set home position

class ConnectionCommand(Enum):
    """Connection verification"""
    GRBL_HANDSHAKE = "Grbl 1.1h ['$' for help]"
    RESET = "\x18"  # Ctrl+X for reset

@dataclass
class ArduinoCommand:
    """Represents a command to send to Arduino"""
    command_type: str       # 'led', 'motor', 'homing'
    command_id: str         # Specific command (e.g., "1" for LEFT_ON)
    parameter: int = 0      # Optional parameter (e.g., duration)
    timestamp: float = None # When command was issued

@dataclass
class ArduinoResponse:
    """Represents a response from Arduino"""
    raw_data: str           # Raw serial data
    parsed_command: str     # What command this was (e.g., "LEFT_BUTTON_PRESSED")
    timestamp: float = None # When response received
    is_error: bool = False

# Command mapping for easy reference
COMMAND_MAP = {
    # LED commands
    'led_left_on': LEDCommand.LEFT_ON.value,
    'led_right_on': LEDCommand.RIGHT_ON.value,
    'led_both_on': LEDCommand.BOTH_ON.value,
    'led_all_off': LEDCommand.ALL_OFF.value,
    
    # Motor commands
    'motor_forward': RewardCommand.MOTOR_FORWARD.value,
    'motor_backward': RewardCommand.MOTOR_BACKWARD.value,
    'motor_home': RewardCommand.MOTOR_HOME.value,
    
    # Button responses
    'button_left': ButtonID.LEFT.value,
    'button_right': ButtonID.RIGHT.value,
}

# Response parsing map
RESPONSE_PARSE_MAP = {
    "20": "left_button_pressed",
    "21": "right_button_pressed",
    "ok": "command_acknowledged",
}
```

## 2. Arduino Communication Protocol
```python
# mnky_bx/hardware/arduino/protocol.py
"""
Communication protocol for Arduino Uno
Handles serial communication, error checking, retries
"""

import serial
import time
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ArduinoProtocol:
    """
    Low-level Arduino communication protocol
    Handles serial encoding/decoding, timeouts, retries
    """
    
    # Protocol constants
    BAUD_RATE = 115200
    TIMEOUT = 1.0          # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5      # seconds
    
    def __init__(self, port: str, baud_rate: int = BAUD_RATE):
        """
        Initialize serial connection
        
        Args:
            port: Serial port (e.g., 'COM4', '/dev/ttyACM0')
            baud_rate: Communication speed (default 115200 for GRBL)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.is_connected = False
    
    def connect(self, timeout_s: float = 5.0) -> bool:
        """
        Establish connection to Arduino
        
        Args:
            timeout_s: How long to wait for handshake
        
        Returns:
            True if successful connection
        """
        try:
            logger.info(f"Connecting to Arduino on {self.port}...")
            
            self.serial_connection = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=self.TIMEOUT
            )
            
            # Wait for GRBL handshake
            start_time = time.time()
            while time.time() - start_time < timeout_s:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.readline().decode('utf-8').strip()
                    logger.debug(f"Received: {data}")
                    
                    if "Grbl 1.1h" in data:
                        self.is_connected = True
                        logger.info("Arduino connected and ready!")
                        return True
                
                time.sleep(0.1)
            
            logger.error("Arduino handshake timeout")
            return False
        
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Arduino"""
        if self.serial_connection:
            self.serial_connection.close()
            self.is_connected = False
            logger.info("Arduino disconnected")
    
    def send_command(self, command: str, wait_for_response: bool = True) -> Optional[str]:
        """
        Send command to Arduino
        
        Args:
            command: Command string (e.g., "G0 X5\n")
            wait_for_response: Whether to wait for "ok" response
        
        Returns:
            Response from Arduino or None
        """
        if not self.is_connected:
            logger.error("Arduino not connected")
            return None
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            logger.debug(f"Sending: {command.strip()}")
            self.serial_connection.write(command.encode('utf-8'))
            
            if wait_for_response:
                response = self.read_response()
                return response
            
            return None
        
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def read_response(self, timeout_s: float = None) -> Optional[str]:
        """
        Read response from Arduino with timeout
        
        Args:
            timeout_s: How long to wait for response
        
        Returns:
            Response string or None if timeout
        """
        if timeout_s is None:
            timeout_s = self.TIMEOUT
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_s:
            if self.serial_connection.in_waiting > 0:
                try:
                    data = self.serial_connection.readline().decode('utf-8').strip()
                    logger.debug(f"Received: {data}")
                    return data
                except Exception as e:
                    logger.error(f"Error reading response: {e}")
                    return None
            
            time.sleep(0.01)
        
        logger.warning(f"Response timeout after {timeout_s}s")
        return None
    
    def send_command_with_retry(self, command: str, 
                               expected_response: str = "ok",
                               max_retries: int = None) -> bool:
        """
        Send command with automatic retry on failure
        
        Args:
            command: Command to send
            expected_response: What response indicates success
            max_retries: Number of retries (default MAX_RETRIES)
        
        Returns:
            True if successful
        """
        if max_retries is None:
            max_retries = self.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                response = self.send_command(command, wait_for_response=True)
                
                if response and expected_response.lower() in response.lower():
                    logger.info(f"Command successful (attempt {attempt + 1})")
                    return True
                
                if attempt < max_retries - 1:
                    logger.warning(f"Retry {attempt + 1}/{max_retries}...")
                    time.sleep(self.RETRY_DELAY)
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
        
        logger.error(f"Command failed after {max_retries} attempts")
        return False
    
    def flush_buffer(self) -> None:
        """Clear any pending data in serial buffer"""
        if self.serial_connection:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
```

## 3. Unified Arduino Uno Controller
```python
# mnky_bx/hardware/arduino/arduino_uno_controller.py
"""
Unified Arduino Uno controller for buttons + reward
Handles both input (buttons) and output (reward motor) on single device
"""

import threading
import time
import queue
from typing import Optional, Callable, Dict, List
from datetime import datetime
import logging

from .protocol import ArduinoProtocol
from .commands import (
    ButtonID, LEDCommand, RewardCommand,
    ArduinoCommand, ArduinoResponse, RESPONSE_PARSE_MAP
)

logger = logging.getLogger(__name__)

class ArduinoUnoController:
    """
    Controls single Arduino Uno for both buttons and reward
    
    Architecture:
    - Serial protocol for communication
    - Button reading thread (continuous monitoring)
    - LED control for feedback
    - Motor control for reward delivery
    - Health monitoring and error handling
    """
    
    def __init__(self, port: str, config: Dict):
        """
        Initialize Arduino Uno controller
        
        Args:
            port: Serial port (e.g., 'COM4')
            config: Configuration dict with:
                - baud_rate: Serial speed (default 115200)
                - max_reward_position: Max motor extension
                - reward_pulse_duration_ms: How long to hold motor
        """
        self.port = port
        self.config = config
        
        # Communication
        self.protocol = ArduinoProtocol(port, config.get('baud_rate', 115200))
        self.is_connected = False
        
        # Button monitoring
        self.button_reading_active = False
        self.button_reading_thread = None
        self.button_pressed = None  # 'left', 'right', or None
        self.button_callback = None  # Optional callback on button press
        
        # LED state
        self.led_state = {}  # {'left': bool, 'right': bool}
        
        # Reward/motor control
        self.motor_position = 0
        self.max_motor_position = config.get('max_reward_position', 10)
        self.reward_pulse_duration_ms = config.get('reward_pulse_duration_ms', 500)
        
        # Statistics
        self.button_press_count = {'left': 0, 'right': 0}
        self.reward_delivery_count = 0
        self.error_count = 0
    
    def connect(self) -> bool:
        """
        Establish connection to Arduino
        
        Returns:
            True if successful
        """
        try:
            if self.protocol.connect():
                self.is_connected = True
                
                # Initialize motor position
                if not self._home_motor():
                    logger.warning("Motor homing failed")
                
                # Start button reading thread
                self._start_button_reading()
                
                logger.info("Arduino Uno controller initialized successfully")
                return True
            
            else:
                logger.error("Failed to connect to Arduino")
                return False
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Arduino"""
        self._stop_button_reading()
        self.protocol.disconnect()
        self.is_connected = False
    
    # ============ BUTTON CONTROL ============
    
    def _start_button_reading(self) -> None:
        """Start background thread for button monitoring"""
        if self.button_reading_active:
            return
        
        self.button_reading_active = True
        self.button_reading_thread = threading.Thread(
            target=self._button_reading_loop,
            daemon=True
        )
        self.button_reading_thread.start()
        logger.info("Button reading thread started")
    
    def _stop_button_reading(self) -> None:
        """Stop button monitoring thread"""
        self.button_reading_active = False
        
        if self.button_reading_thread:
            self.button_reading_thread.join(timeout=2.0)
            logger.info("Button reading thread stopped")
    
    def _button_reading_loop(self) -> None:
        """
        Continuous loop: read button presses from Arduino
        Runs in separate thread
        """
        while self.button_reading_active and self.is_connected:
            try:
                # Check for incoming data (non-blocking)
                if self.protocol.serial_connection.in_waiting > 0:
                    data = self.protocol.serial_connection.readline().decode('utf-8').strip()
                    
                    # Parse button press
                    if data == ButtonID.LEFT.value:
                        self.button_pressed = "left"
                        self.button_press_count['left'] += 1
                        logger.debug("LEFT button pressed")
                        
                        if self.button_callback:
                            self.button_callback("left")
                    
                    elif data == ButtonID.RIGHT.value:
                        self.button_pressed = "right"
                        self.button_press_count['right'] += 1
                        logger.debug("RIGHT button pressed")
                        
                        if self.button_callback:
                            self.button_callback("right")
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
            
            except Exception as e:
                logger.error(f"Button reading error: {e}")
                self.error_count += 1
    
    def set_button_callback(self, callback: Callable) -> None:
        """
        Set callback function called when button is pressed
        
        Args:
            callback: Function(button_id: str) called with 'left' or 'right'
        """
        self.button_callback = callback
    
    def get_button_press(self) -> Optional[str]:
        """
        Get last button pressed (non-blocking)
        
        Returns:
            'left', 'right', or None
        """
        button = self.button_pressed
        self.button_pressed = None  # Clear after reading
        return button
    
    # ============ LED CONTROL ============
    
    def set_led(self, button_id: str, state: bool) -> bool:
        """
        Control LED on button
        
        Args:
            button_id: 'left' or 'right'
            state: True (on) or False (off)
        
        Returns:
            True if successful
        """
        if not self.is_connected:
            logger.warning("Arduino not connected")
            return False
        
        try:
            if button_id == 'left':
                command = LEDCommand.LEFT_ON.value if state else LEDCommand.ALL_OFF.value
            elif button_id == 'right':
                command = LEDCommand.RIGHT_ON.value if state else LEDCommand.ALL_OFF.value
            else:
                logger.error(f"Unknown button ID: {button_id}")
                return False
            
            success = self.protocol.send_command_with_retry(command + '\n')
            
            if success:
                self.led_state[button_id] = state
                logger.debug(f"LED {button_id} {'ON' if state else 'OFF'}")
            
            return success
        
        except Exception as e:
            logger.error(f"LED control error: {e}")
            self.error_count += 1
            return False
    
    def set_all_leds(self, state: bool) -> bool:
        """
        Control all LEDs simultaneously
        
        Args:
            state: True (on) or False (off)
        
        Returns:
            True if successful
        """
        if not self.is_connected:
            return False
        
        try:
            command = LEDCommand.BOTH_ON.value if state else LEDCommand.ALL_OFF.value
            success = self.protocol.send_command_with_retry(command + '\n')
            
            if success:
                self.led_state = {'left': state, 'right': state}
            
            return success
        
        except Exception as e:
            logger.error(f"All LEDs control error: {e}")
            return False
    
    # ============ REWARD/MOTOR CONTROL ============
    
    def _home_motor(self) -> bool:
        """
        Move motor to home position (0)
        
        Returns:
            True if successful
        """
        try:
            # Set home position
            success = self.protocol.send_command_with_retry(
                RewardCommand.MOTOR_HOME.value,
                expected_response="ok"
            )
            
            if success:
                self.motor_position = 0
                logger.info("Motor homed successfully")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Motor homing error: {e}")
            return False
    
    def deliver_reward(self, amount: int = 1, hold_time_ms: Optional[int] = None) -> bool:
        """
        Deliver reward (juice/food)
        
        Args:
            amount: Amount of reward (1-10, mapped to motor distance)
            hold_time_ms: How long to hold (default from config)
        
        Returns:
            True if successful
        """
        if not self.is_connected:
            logger.warning("Arduino not connected")
            return False
        
        if hold_time_ms is None:
            hold_time_ms = self.reward_pulse_duration_ms
        
        try:
            # Clamp amount to valid range
            amount = max(1, min(amount, self.max_motor_position))
            
            # Calculate motor position
            motor_distance = amount  # Simple 1:1 mapping
            
            # Send motor forward command
            logger.info(f"Delivering reward: amount={amount}, distance={motor_distance}mm")
            
            command = f"G0 X{motor_distance}\n"
            success = self.protocol.send_command_with_retry(command, expected_response="ok")
            
            if success:
                self.motor_position = motor_distance
                self.reward_delivery_count += 1
                
                # Hold for specified duration
                time.sleep(hold_time_ms / 1000.0)
                
                # Return to home
                self._home_motor()
            
            return success
        
        except Exception as e:
            logger.error(f"Reward delivery error: {e}")
            self.error_count += 1
            return False
    
    def get_motor_position(self) -> int:
        """Get current motor position"""
        return self.motor_position
    
    # ============ STATISTICS & HEALTH ============
    
    def get_statistics(self) -> Dict:
        """Get usage statistics"""
        return {
            'is_connected': self.is_connected,
            'button_presses': self.button_press_count.copy(),
            'reward_deliveries': self.reward_delivery_count,
            'errors': self.error_count,
            'motor_position': self.motor_position
        }
    
    def health_check(self) -> Dict:
        """
        Perform health check on Arduino connection
        
        Returns:
            {
                'connected': bool,
                'buttons_responsive': bool,
                'motor_responsive': bool,
                'led_responsive': bool,
                'last_error': str or None
            }
        """
        health = {
            'connected': self.is_connected,
            'buttons_responsive': False,
            'motor_responsive': False,
            'led_responsive': False,
            'last_error': None
        }
        
        if not self.is_connected:
            health['last_error'] = "Not connected"
            return health
        
        try:
            # Test LED control
            if self.set_led('left', True):
                health['led_responsive'] = True
                self.set_led('left', False)
            
            # Test motor homing
            if self._home_motor():
                health['motor_responsive'] = True
            
            # Buttons are monitored continuously
            health['buttons_responsive'] = self.button_reading_active
        
        except Exception as e:
            health['last_error'] = str(e)
        
        return health
```

## 4. Abstract Interface
```python
# mnky_bx/hardware/hardware_interface.py (UPDATED)
"""
Abstract hardware interfaces for dependency injection
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Dict

class ButtonController(ABC):
    """Abstract interface for button input"""
    
    @abstractmethod
    def get_button_press(self) -> Optional[str]:
        """Get last button pressed ('left', 'right', or None)"""
        pass
    
    @abstractmethod
    def set_button_callback(self, callback: Callable) -> None:
        """Set callback for button presses"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class RewardController(ABC):
    """Abstract interface for reward delivery"""
    
    @abstractmethod
    def deliver_reward(self, amount: int = 1) -> bool:
        """Deliver reward, returns True if successful"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class LEDController(ABC):
    """Abstract interface for LED control"""
    
    @abstractmethod
    def set_led(self, button_id: str, state: bool) -> bool:
        """Control LED for a button"""
        pass
    
    @abstractmethod
    def set_all_leds(self, state: bool) -> bool:
        """Control all LEDs"""
        pass


class ArduinoController(ButtonController, RewardController, LEDController):
    """Unified Arduino controller implements all interfaces"""
    pass
```

## 5. Updated Hardware Configuration
```json
// mnky_bx/config/hardware_config.json
{
  "arduino": {
    "port": "COM4",
    "baud_rate": 115200,
    "connection_timeout_s": 5,
    "max_reward_position": 10,
    "reward_pulse_duration_ms": 500,
    "retry_attempts": 3,
    "retry_delay_ms": 500
  },
  "camera": {
    "index": 0,
    "width": 640,
    "height": 480,
    "fps": 30,
    "motion_threshold": 5000,
    "frames_to_stabilize": 30
  },
  "timeouts": {
    "motion_detection_s": 300,
    "face_detection_s": 10,
    "button_response_s": 5
  }
}
```

## 6. Updated Experiment Base Class Integration
```python
# mnky_bx/core/experiment_base.py (UPDATED SECTIONS)

from mnky_bx.hardware.arduino.arduino_uno_controller import ArduinoUnoController
from mnky_bx.hardware.hardware_interface import ArduinoController

class ExperimentBase:
    def __init__(self,
                 experiment_name,
                 subject_id,
                 kiosk_manager,
                 logger,
                 notification_manager,
                 hardware_config):
        """
        Initialize experiment with unified Arduino controller
        """
        # ... existing initialization ...
        
        # ← UPDATED: Single unified Arduino controller
        self.arduino = None
        self.setup_arduino()
    
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
    
    def cleanup(self):
        """Cleanup including Arduino disconnection"""
        # ... existing cleanup ...
        
        if self.arduino:
            stats = self.arduino.get_statistics()
            self.logger.log_hardware_event('Arduino', 
                f'Final stats: {stats}')
            self.arduino.disconnect()
        
        # ... rest of cleanup ...
```

## 7. Updated Health Monitor
```python
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
```

## 8. Integration Example
```python
# experiments/gambling_experiment/experiment.py (EXAMPLE)

from mnky_bx.core.experiment_base import ExperimentBase
import pygame

class GamblingExperiment(ExperimentBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Experiment-specific setup
    
    def wait_for_response(self):
        """Wait for button response"""
        running = True
        start_time = pygame.time.get_ticks()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    return False
            
            # Check for button press (from Arduino callback)
            if self.choice in ['left', 'right']:
                return True
            
            # Check timeout
            if pygame.time.get_ticks() - start_time > self.max_RT:
                self.choice = 'no response'
                return False
            
            pygame.time.delay(4)
        
        return True
```

## Summary of Changes
| Aspect 	| Before	| After | 
|:---|:---|:---|
| Arduino files | 	`arduino_buttons.py` + `arduino_reward.py` (separate)	| arduino_uno_controller.py (unified) | 
| Communication	| Direct serial calls scattered	| Centralized protocol handler |
| Button reading	| Blocking loop	| Background thread callback |
| LED control	| Direct Arduino writes	| Managed state tracking |
| Motor control	| Position tracking	| Homing + distance calculation |
| Error handling	| Minimal	| Comprehensive with retries |
| Health checks	| None	| Full diagnostics per component |
| Configuration	| Multiple ports	| Single port, unified config |
| Testing	| Difficult| 	Easy (mock ArduinoController) |

Benefits
- ✅ Single source of truth - One Arduino device, one controller
- ✅ Reduced complexity - No coordination between separate modules
- ✅ Better error handling - Unified fault detection
- ✅ Easier maintenance - Changes in one place
- ✅ Cleaner experiment code - Single self.arduino interface
- ✅ Thread-safe - Background button reading doesn't block trials
- ✅ Mockable - Easy to test without hardware
- ✅ Extensible - Add new Arduino features easily

### Cross-platform directory setup script for mnky_bx kiosk system

```python
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
            "mnky_bx/hardware/arduino",           # ← NEW: Unified Arduino
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
            "mnky_bx/hardware/arduino",           # ← NEW
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
        
        readmes = {
            "subjects/not_recognized/README.md": """# Not Recognized

This directory contains face images from subjects that could not be recognized by the face recognition system.

## Structure

- `raw_images/` - Original unidentified face crops
- `face_images/` - Processed face images with context
- `embeddings/` - Face embeddings for clustering analysis

## Usage

These images are useful for:
1. Discovering new subjects not yet in the system
2. Clustering analysis to identify potential new subjects
3. Training data for improving the recognition model
4. Troubleshooting recognition failures

## Cleanup

Old unrecognized images can be archived after clustering analysis.
""",
            "docs/README.md": """# Documentation

Complete documentation for the mnky_bx kiosk system.

## Contents

- `ARCHITECTURE.md` - System architecture and design
- `ORIGINAL_SCRIPT_REFERENCE.md` - Mapping from original monolithic script
- `REFACTORING_GUIDE.md` - How the refactoring was done
- `API.md` - API reference for all modules
- `original_scripts/` - Original monolithic script for reference

## Getting Started

1. Read `ARCHITECTURE.md` for overview
2. Review `original_scripts/MonkeyBoxGamblingExperiment.py` for context
3. Check `examples/` for sample implementations
4. Review module docstrings for detailed API info
""",
            "tests/README.md": """# Tests

Unit tests, integration tests, and test fixtures.

## Structure

- `test_*.py` - Individual test modules
- `fixtures/` - Test data and mock objects
  - `sample_frames/` - Sample camera frames
  - `test_subjects/` - Test subject data
  - `mock_hardware/` - Mock hardware for testing

## Running Tests

```bash
pytest tests/
pytest tests/test_camera_system.py -v
```

## Fixtures
Mock hardware and test data available in `fixtures/`.
""",
"experiments/README.md": """# Experiments

User-implemented experiment modules.

Structure
Each experiment follows this structure:

```php
experiment_name/
├── experiment.py           # Main experiment class (user implements)
├── config.json             # Experiment configuration
├── subject_params/         # Subject-specific parameters
│   ├── default.json
│   └── subject_id_*.json
├── analysis/               # Analysis scripts and results
├── data/                   # Experimental data
└── Media/                  # Media files
```
### Creating a New Experiment
1. Create directory: `experiments/my_experiment/`
2. Create config.json with experiment parameters
3. Create experiment.py and subclass ExperimentBase
4. Implement required methods (draw_stimuli, wait_for_response, etc.)
5. Add to launcher.py
See `examples/` for templates.
""",
}

```python
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
    
    placeholders = {
        "mnky_bx/hardware/arduino/protocol.py": """\"\"\"Arduino communication protocol\"\"\"
        # TODO: Implement ArduinoProtocol class
        pass
        """,
        "mnky_bx/hardware/arduino/commands.py": """"""Arduino command definitions"""
        
        # TODO: Implement command enums and mappings
        pass
        """,
        "mnky_bx/hardware/arduino/arduino_uno_controller.py": """"""Unified Arduino Uno controller"""
        
        # TODO: Implement ArduinoUnoController class
        pass
        """,
        "mnky_bx/core/experiment_base.py": """"""Base experiment class"""
        
        # TODO: Implement ExperimentBase class
        pass
        """,
        "mnky_bx/database/schemas.py": """"""Database schema definitions"""
        
        # TODO: Implement database schemas
        pass
        """,
        }
    
    for file_path, content in placeholders.items():
        self.create_file_with_content(file_path, content)

def print_summary(self) -> None:
    """Print setup summary"""
    self.print_header("Setup Complete!", "=")
    
    total_dirs = self.created_dirs + self.existing_dirs
    
    print(f"Summary:")
    print(f"  • Directories created: {self.created_dirs}")
    print(f"  • Directories existing: {self.existing_dirs}")
    print(f"  • Total directories: {total_dirs}")
    print(f"  • Files created: {self.created_files}")
    print()
    print(f"Project Structure:")
    print(f"  • Core package: mnky_bx/")
    print(f"    - Core modules, hardware (including unified Arduino), database, logging")
    print(f"    - Face recognition system, UI, utilities")
    print(f"  • Experiments: experiments/ ({len(self.experiments)} templates)")
    for exp in self.experiments:
        print(f"    - {exp}")
    print(f"  • Subjects: subjects/ ({self.num_subjects} subject directories)")
    print(f"  • Documentation: docs/")
    print(f"  • Tests: tests/")
    print(f"  • Configuration: config/")
    print()
    print(f"Next Steps:")
    print(f"  1. Review config files in config/")
    print(f"  2. Update notification_config.json with email/SMS credentials")
    print(f"  3. Update hardware port in kiosk_config.json (currently 'COM4')")
    print(f"  4. Create experiment.py files in each experiments/*/")
    print(f"  5. Add subject metadata.json files to each subject directory")
    print(f"  6. Run: pip install -r requirements.txt")
    print(f"  7. Run launcher: python mnky_bx/launcher.py")
    print()
    print(f"Key Changes in This Version:")
    print(f"  ✓ Unified Arduino controller (buttons + reward on single device)")
    print(f"  ✓ Filesystem image storage (no BLOBs in database)")
    print(f"  ✓ Face recognition system for subject identification")
    print(f"  ✓ Async video encoding support")
    print(f"  ✓ Subject-adaptive parameters")
    print(f"  ✓ Comprehensive logging and error handling")
    print(f"  ✓ Email/SMS notifications")
    print()

def run(self) -> None:
    """Execute full setup"""
    self.print_header("MNKY_BX Directory Setup Script", "=")
    
    print(f"Configuration:")
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

if name == "main":
    main()
    
    ## Usage
    
    ### Basic Usage (Windows, macOS, Linux):
    
    ```bash
    # Default: 12 subjects, 2 experiments
    python setup_directories.py
    
    # Custom number of subjects
    python setup_directories.py . 20
    
    # Custom experiments
    python setup_directories.py . 12 gambling_experiment blackjack custom_task
    
    # Custom project root
    python setup_directories.py /path/to/project 15 gambling_experiment
```
### From PowerShell (Windows):
```powershell
python setup_directories.py . 12
# or
python.exe setup_directories.py . 12
```
### From Bash (macOS/Linux):
```bash
python setup_directories.py . 12
# or
python3 setup_directories.py . 12
```

## What Gets Created
### Directory Structure
- ✓ Complete mnky_bx package with all modules 
- ✓ Unified Arduino module (new)
- ✓ All experiment directories with proper structure 
- ✓ Subject directories with face encoding paths 
- ✓ Documentation structure 
- ✓ Tests structure with fixtures
### Configuration Files
- ✓ config/kiosk_config.json - Main system configuration 
- ✓ config/face_recognition_config.json - Face recognition settings 
- ✓ config/notification_config_TEMPLATE.json - Email/SMS template 
- ✓ experiments/*/config.json - Experiment-specific configs 
- ✓ experiments/*/subject_params/default.json - Default subject parameters
### Documentation Files
- ✓ README files for key directories
- ✓ Placeholder module files (marked with TODO)
- ✓ Structure ready for full implementation

## Python Packages
- ✓ __init__.py files for all packages


## 11. Updated Directory Structure
```python
mnky_bx/
├── ui/
│   ├── __init__.py
│   ├── pygame_utils.py
│   ├── error_screen.py
│   ├── launcher_ui.py
│   ├── subject_enrollment_ui.py
│   ├── input_system.py              # ← NEW: Unified input
│   └── input_handlers/              # ← NEW: Input handlers
│       ├── __init__.py
│       ├── keyboard_handler.py
│       ├── button_handler.py
│       ├── touchscreen_handler.py
│       └── input_manager.py
│
├── hardware/
│   ├── arduino/
│   │   ├── arduino_uno_controller.py         # Full (buttons + reward)
│   │   └── reward_only_controller.py         # ← NEW: Reward only
│   └── ...
│
└── config/
    ├── kiosk_config.json            # Desktop
    └── raspi_touchscreen_config.json # ← NEW: Raspberry Pi
```

### 2. Quick Configuration Reference
Desktop (All Inputs):
```json
{
  "enabled_inputs": ["keyboard", "button", "touchscreen"],
  "touchscreen": {
    "split_screen": true
  }
}
Raspberry Pi Touchscreen Only:
json
{
  "enabled_inputs": ["touchscreen"],
  "touchscreen": {
    "screen_width": 800,
    "screen_height": 480,
    "split_screen": true
  }
}
```
Keyboard Only (Testing):
json
{
  "enabled_inputs": ["keyboard"]
}
Summary
- ✅ Unified Input System - Single interface for all input methods
- ✅ Keyboard Support - For desktop development/testing
- ✅Physical Buttons - Arduino integrated with full controller
- ✅ Touchscreen - Raspberry Pi with split-screen or custom regions
- ✅ Flexible Arduino - Can be used for buttons+reward OR reward-only
- ✅ Platform Detection - Automatically loads appropriate config
- ✅ Easy to Extend - New input types can be added easily

This architecture gives you maximum flexibility across different platforms and input methods! 🎉

there are 2 different hardware configurations. 1 uses a wired usb connection to an arduino uno. and the other uses a wireless serial/BLE connection with an adafruit feather.  so we might need an adafruit_feather_controller.py

Let me design a Strategy Pattern architecture that elegantly handles both hardware configurations.

## Hardware Abstraction Architecture
The key insight is: both controllers need the same interface but different implementations:

```python
# Common Interface (Abstract Base)
- Button input (left/right)
- LED control (feedback)
- Reward motor control (home, move, position)
- Health checks
- Statistics
```
### Strategy 1: Create a Hardware Abstraction Layer
```graphql
mnky_bx/hardware/arduino/
├── __init__.py
├── base_controller.py          # ← NEW: Abstract base class
├── protocol.py                 # ← EXISTING: Shared serial protocol
├── commands.py                 # ← EXISTING: Command enums
├── arduino_uno_controller.py    # ← IMPLEMENTATION: USB/Serial
├── adafruit_feather_controller.py  # ← NEW: BLE/Wireless
└── hardware_factory.py         # ← NEW: Factory to select controller
```
### Strategy 2: File Structure Overview
```bash
mnky_bx/hardware/
├── __init__.py
├── hardware_interface.py          # ← High-level unified interface
├── health_monitor.py
├── hardware_factory.py            # ← NEW: Instantiate correct controller
│
└── arduino/
    ├── __init__.py
    ├── base_controller.py         # ← NEW: Abstract base
    ├── protocol.py                # ← Shared serial protocol (USB or BLE)
    ├── commands.py                # ← Shared command definitions
    ├── arduino_uno_controller.py   # ← USB implementation
    └── adafruit_feather_controller.py  # ← BLE implementation
```

## Updated Arduino Module Structure
```bash
mnky_bx/hardware/arduino/
├── __init__.py
├── base_controller.py              # ← Abstract base (NEW)
├── protocol.py                      # ← Shared serial protocol
├── commands.py                      # ← Shared command enums
├── hardware_factory.py             # ← Factory (NEW)
├── arduino_uno_controller.py        # ← USB implementation
└── adafruit_feather_controller.py   # ← BLE implementation
```

## 🎯 How It Works
1. KioskManager reads config/kiosk_config.json
2. Calls HardwareFactory.create_controller(hw_config)
3. Factory detects or creates appropriate controller (Arduino Uno or Feather)
4. ExperimentBase receives controller instance and calls common interface methods
5. Both hardware types use identical command interface - experiment code doesn't care which one is connected!

## ✅ Benefits of This Design

| Aspect | Benefit | 
| --- | --- |
|  Single Interface	| Experiments work with either hardware with zero code changes | 
| Protocol Reuse	| SerialProtocol handles USB and BLE identically | 
| Command Consistency 	| Both controllers understand same commands | 
| Factory Pattern	| Auto-detection, easy to add new hardware later
| Battery Monitoring	| Feather-specific but transparent to experiments
| Thread-Safe	| Both have background button listeners
| Testable	| Can mock HardwareController for unit tests |
| 

## Revised Hardware Configuration Scenarios
```sql
Config 1: Traditional Setup (USD kiosk with enclosure)
├── Arduino Uno (USB)
│   ├── Button input (left/right)
│   ├── LED feedback
│   └── Reward motor control
└── Camera (face recognition during trial)

Config 2: Touchscreen Kiosk (Raspberry Pi with display)
├── Touchscreen (replaces physical buttons)
│   ├── Left/right tap detection
│   └── On-screen button rendering
├── Adafruit Feather (BLE wireless)
│   ├── Reward motor ONLY
│   └── Battery monitoring
└── Camera (face recognition)

Config 3: Hybrid (future expansion)
├── Touchscreen + partial Arduino fallback
```

## 📊 Hardware Configuration Summary

| Feature | Arduino Uno Full | Feather Reward Only |
| --- | --- | --- |
| Connection	| USB (wired)	| BLE (wireless) | 
| Button Input	| ✅ Yes (hardware)	| ❌ No (touchscreen) | 
| LED Feedback	| ✅ Yes (hardware)	| ❌ No (touchscreen) | 
| Reward Motor	| ✅ Yes	| ✅ Yes | 
| Battery Monitoring	| ❌ No (USB powered)	| ✅ Yes | 
| Signal Strength	| ❌ No (wired)	| ✅ Yes | 
| Setup Type	| Traditional enclosure	| Touchscreen kiosk | 
| Portability	| Limited (USB tether)	| High (wireless) | 

## 🎯 Usage Examples
### Config 1: Traditional Enclosure (Arduino Uno)
```python
config = {
    "hardware_type": "arduino_uno_full",
    "arduino_uno": {"port": "COM4"}
}

controller = HardwareFactory.create_controller(config)
controller.connect()

# Button input works
controller.start_button_listener(lambda btn, ts: print(f"Button {btn}"))

# LEDs work
controller.set_led("left", True)

# Motor works
controller.move_motor(5.0, 500)
```

### Config 2: Touchscreen Kiosk (Feather + Touchscreen)
```python
config = {
    "hardware_type": "feather_reward_only",
    "adafruit_feather": {"port": "COM3"}
}

# Hardware controller (motor only)
controller = HardwareFactory.create_controller(config)
controller.connect()

# Touchscreen handles button input
touchscreen = TouchscreenInputManager(config)
touchscreen.start_listener(lambda btn, ts: print(f"Touched {btn}"))

# LEDs rendered on touchscreen (not hardware)
touchscreen.set_button_highlight("left", True)

# Motor still works
controller.move_motor(5.0, 500)
```
## ✅ Benefits
1. Clear Separation of Concerns: Feather only does motor, touchscreen does buttons/feedback
2. Wireless Freedom: Feather can be placed in/near enclosure without tether
3. Scalability: Easy to add more hardware types
4. Error Transparency: Clear warning messages if trying to use unsupported features
5. Experiment Compatibility: Experiments work with either setup seamlessly

---

Would you like me to now create:

TouchscreenInputManager class for handling touchscreen button input?
Stub files for all missing modules?
Integration examples showing how experiments work with both setups?