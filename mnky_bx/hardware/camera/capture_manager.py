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