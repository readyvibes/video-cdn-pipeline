import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Local storage paths (not tracked by Git)
INPUT_DIR = os.path.join(BASE_DIR, ".local", "raw_uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, ".local", "processed")

# Create directories if they don't exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# FFmpeg configurations
SEGMENT_TIME = 2
FPS = 30
GOP = FPS * SEGMENT_TIME  # Ensures I-frame alignment