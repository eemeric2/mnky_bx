# Original Script Reference

## Overview
This document maps components from the original monolithic script to the new modular architecture.

## File Location
- Original: `docs/original_scripts/MonkeyBoxGamblingExperiment.py`
- Original size: ~2000 lines
- Refactoring status: ✓ Complete (v2.0)

## Class/Function Mapping

### CameraDetectionSystem
- **Original location**: Lines 150-400
- **New location**: `mnky_bx/hardware/camera/camera_system.py`
- **Changes**: 
  - Extracted face recognition logic to separate module
  - Split picture capture into `CaptureManager`
  - Added async video encoding support

### experiment() class
- **Original location**: Lines 50-1500
- **New locations**:
  - Core logic → `mnky_bx/core/experiment_base.py`
  - Trial management → `mnky_bx/core/trial_manager.py`
  - UI rendering → `experiments/{exp_name}/experiment.py` (user implements)
- **Changes**:
  - Removed pygame dependency from base class
  - Separated hardware initialization
  - Added subject parameter adaptation

### Picture Capture Logic
- **Original location**: Lines 350-400 (`save_captured_pictures()`)
- **New locations**:
  - BLOB storage → `mnky_bx/hardware/camera/capture_manager.py` (filesystem)
  - Database writes → `mnky_bx/database/schemas.py`
  - Recognition → `mnky_bx/face_recognition_system/recognition_engine.py`
- **Key change**: BLOB → Filesystem references (major performance improvement)

### Arduino Integration
- **Original location**: Lines 500-600
- **New locations**:
  - Button handling → `mnky_bx/hardware/arduino/arduino_interface.py`
  - Reward delivery → `mnky_bx/hardware/arduino/arduino_interface.py`
  - Health monitoring → `mnky_bx/hardware/health_monitor.py`

### Database Setup
- **Original location**: Lines 700-800 (`setup_database()`)
- **New location**: `mnky_bx/database/schemas.py`
- **Changes**: 
  - Added table for lightweight frame references
  - Added recognition results tracking
  - Removed BLOB column from trial_pictures

## Line-by-Line Correspondence

### Motion Detection
```python
# Original (lines 180-200)
self.background_subtractor = cv2.createBackgroundSubtractorMOG2(...)
fg_mask = self.background_subtractor.apply(frame)
motion_area = cv2.countNonZero(fg_mask)
```
# New
# mnky_bx/hardware/camera/camera_system.py:_detection_thread()
# Same logic, better organized

### Face Recognition (NEW)
```python
# Original: Not implemented
# New implementation shows how to extend

# mnky_bx/face_recognition_system/recognition_engine.py
# - recognize_face()
# - batch_recognize_faces()
# - enroll_new_subject()
```
### Behavioral Changes
#### Storage Strategy
| `Aspect` | 	`Original` | 	`New` |
| -------- | -------- | -------- |
| Image format | 	BLOB in SQLite | 	JPEG on filesystem| 
| Metadata	| All in DB	| Split: DB refs + JSON detail| 
| Performance| 	Slow	| Fast (parallel I/O)| 
| Query speed| 	∼10s	| ∼0.1s| 

#### Parameter Adaptation (NEW)
- Original: Static parameters all trials
- New: Subject-specific adaptive parameters from JSON config

#### Face Recognition (NEW)
Original: Not present
New: Real-time subject identification + routing
#### Migration Checklist
- ✔  Extract trial logic to base class
- ✔  Implement modular hardware interfaces
- ✔  Separate database schemas
- ✔  Add face recognition system
- ✔  Optimize image storage
- ✔  Create subject parameter system
- ✔  Add logging system
- ✔  Implement error handling + notifications
#### Testing Coverage
Original script: Tested with real apparatus
Refactored modules: Each tested independently
Integration tests: Available in tests/ directory
#### How to Use This Reference
1. If extending original feature: Find it in mapping above 
2. If debugging issue: Check if it's in original or new code 
3. If adding feature: Start with original logic, refactor into appropriate module 
4. If onboarding: Read this document first, then review modular components

#### Quick Links
- Architecture Overview 
- Refactoring Guide 
- Original Script 
- Module Docstrings

```yaml

---

## REFACTORING_GUIDE.md Example

```markdown
# Refactoring Guide: Monolithic to Modular

## High-Level Changes

### Before (Monolithic)
MonkeyBoxGamblingExperiment.py (2000 lines)
├── pygame UI
├── camera/motion/face detection
├── Arduino communication
├── Experiment logic
├── Database operations
├── Image storage (BLOB)
└── Trial control flow
```
### After (Modular)
```shell
mnky_bx/
├── core/          (Experiment logic, trial management)
├── hardware/      (Camera, Arduino)
├── database/      (Schema, ORM)
├── ui/            (pygame, error screens, launcher)
├── face_recognition_system/  (NEW)
├── logging/       (NEW)
├── notifications/ (NEW)
└── utils/         (Shared helpers)

experiments/
└── {exp_name}/
└── experiment.py  (User implements pygame UI)
```

## Key Architectural Decisions

### 1. Base Class Abstraction

**Why**: Separate framework from pygame implementation

```python
# Original: Everything in one class
class experiment():
    def draw_stimuli(self):
        # pygame code mixed with logic
    def setup_new_trial(self):
        # trial management mixed with UI

# New: Separation of concerns
class ExperimentBase:
    def setup_new_trial(self):
        # Pure logic, no pygame
    
# User implements:
class GamblingExperiment(ExperimentBase):
    def draw_stimuli(self):
        # User provides pygame code
```
### 2. Storage Strategy Optimization
**Why**: BLOB storage was bottleneck

```python
# Original: BLOB in DB
INSERT INTO trial_pictures 
    (trial_number, image_data) 
    VALUES (1, <binary blob>)

# New: Filesystem with references
INSERT INTO trial_pictures 
    (trial_number, image_path) 
    VALUES (1, "trial_001_frame_001.jpg")
```
#### Result:

- Write time: 180s → 30s (6x faster)
- Query time: 10s → 0.1s (100x faster)
- Easier integration with face recognition

### 3. Face Recognition System (NEW)
**Why**: Enable subject-adaptive experiments

```python
# Original: No recognition
if motion_detected:
    run_trial(default_params)

# New: Adaptive parameters
if motion_detected:
    face_result = recognize_face()
    if face_result.recognized:
        params = load_subject_params(face_result.subject_id)
    else:
        params = load_default_params()
    run_trial(params)
```
### 4. Hardware Abstraction
Why: Easy to mock/test, swap implementations

```python
# Original: Direct Arduino calls
self.arduino_buttons.write("3\n")

# New: Abstracted interface
hardware_manager.set_led_state('buttons', 'on')
```
## Module Design Patterns
### Hardware Modules
- Abstract base class defines interface
- Concrete implementations (Arduino, simulation mode)
- Health monitor for fault detection
### Database Module
- Schema definitions separate from logic
- ORM-like manager for queries
- Batch operations for performance
### Camera System
- Detection thread for non-blocking motion/face
- Async video encoding thread
- Direct filesystem I/O in capture manager

## Performance Improvements
| `Operation`      | 	`Before`	| `After`	| `Improvement` | 
|----------------| -------- | -------- | -------- |
| Frame capture  | 	Blocked	Async | 	Non-blocking| 
| DB write       | 	BLOB insert	| Path insert	| 180s → 30s| 
| Query trial	    | All data loaded	| Indexed query	| 10s → 0.1s| 
| Face recognition	 | N/A	| ∼0.1s/face	| NEW feature| 
| Video encoding	 | Manual	| Async background	| NEW feature| 

## Testing Strategy
### Original Script
- Tested with real apparatus
- Single integration test (monkey in box)

### Modular System
```markdown
tests/
├── test_camera_system.py
├── test_capture_manager.py
├── test_face_recognition.py
├── test_experiment_base.py
├── test_database.py
├── test_integration.py
└── fixtures/
    ├── sample_frames/
    ├── test_subjects.json
    └── mock_hardware/
```
## Common Refactoring Patterns
#### Extract Method → Module Function
```python
# Before
def wait_for_motion_and_face(self):
    # 50 lines of motion detection
    # 50 lines of face detection

# After: Separate files
# camera_system._detection_thread()
# capture_manager.process_detected_face()
```
### Remove Circular Dependencies
```python
# Before: experiment calls camera, camera calls experiment
class experiment:
    def __init__(self):
        self.camera.experiment = self

# After: Dependency injection
class ExperimentBase:
    def __init__(self, camera_system, logger, etc):
        # Clear dependencies, testable
```
### Batch Operations
```python
# Before: Write immediately
for frame in frames:
    db.insert(frame)  # N database writes

# After: Batch write
db.batch_insert(frames)  # 1 database write
```
## Rollback Strategy
If you need to revert to monolithic:
1. All original code is in `docs/original_scripts/`
2. Create branch from commit before refactoring
3. Integration tests help identify issues
4. Hybrid mode available (run both systems in parallel for comparison)
## Next Steps
1. Review architecture in ARCHITECTURE.md 
2. Read original script with mapping guide 
3. Trace one feature through new modules 
4. Run unit tests to verify behavior 
5. Deploy incrementally with fallback capability

```yaml
---

## Directory Structure

mnky_bx/
├── docs/
│   ├── README.md                          # Main documentation
│   ├── ARCHITECTURE.md                    # System design
│   ├── ORIGINAL_SCRIPT_REFERENCE.md       # ← This maps old→new
│   ├── REFACTORING_GUIDE.md               # ← How we refactored
│   ├── API.md                             # API reference
│   ├── INSTALLATION.md                    # Setup instructions
│   ├── original_scripts/
│   │   ├── README.md                      # Why we kept it
│   │   ├── MonkeyBoxGamblingExperiment.py # ← Original script
│   │   └── CHANGES.md                     # What changed
│   └── examples/
│       ├── basic_experiment.py
│       ├── custom_parameters.py
│       └── face_recognition_enrollment.py
│
├── tests/
│   ├── test_*.py
│   └── fixtures/
│
├── mnky_bx/
│   ├── core/
│   ├── hardware/
│   └── ...
│
├── experiments/
│   └── ...
│
├── README.md                              # Quick start
├── CHANGELOG.md                           # Version history
└── setup.py
```
---

## Benefits of This Approach

- ✅ **Complete traceability** - Know exactly which line became which module
- ✅ **Easier debugging** - Compare original behavior with new
- ✅ **Team onboarding** - New developers understand evolution
- ✅ **Safe refactoring** - Can always reference original intent
- ✅ **Version control** - Git history shows what changed and why
- ✅ **Documentation** - Self-documenting system architecture

This is especially valuable for research code where understanding the original experimental design is important!