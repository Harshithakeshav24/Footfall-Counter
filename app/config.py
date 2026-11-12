import os

# Settings are read from environment variables so the same code
# works on my machine and inside Docker without editing files.

VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "videos/store-aisle.mp4")  # file path, RTSP url or "0" for webcam
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")  # downloaded automatically on first run

# Position of the counting line as a fraction of frame height (0 = top, 1 = bottom)
LINE_POSITION = float(os.getenv("LINE_POSITION", "0.5"))

# Minimum detection confidence for a person
CONFIDENCE = float(os.getenv("CONFIDENCE", "0.4"))

# Run detection on every Nth frame. 1 = every frame.
# The sample video is 60 fps, so 2 (= 30 fps) is enough for tracking
# and halves the processing time on CPU.
FRAME_STEP = int(os.getenv("FRAME_STEP", "2"))

DB_PATH = os.getenv("DB_PATH", "data/footfall.db")
