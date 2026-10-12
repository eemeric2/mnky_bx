# Not Recognized

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
