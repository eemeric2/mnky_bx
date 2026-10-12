# Tests

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
