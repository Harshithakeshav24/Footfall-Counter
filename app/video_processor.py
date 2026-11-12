import logging
import threading
import time

import cv2
from ultralytics import YOLO

from app import database
from app.line_counter import LineCounter

logger = logging.getLogger(__name__)

PERSON_CLASS_ID = 0  # "person" is class 0 in the COCO dataset that YOLOv8 is trained on


class VideoProcessor:
    """Reads the video in a background thread, runs YOLOv8 tracking and counts line crossings."""

    def __init__(self, source, model_path, line_position=0.5, confidence=0.4, frame_step=1):
        self.source = source
        self.model_path = model_path
        self.line_position = line_position
        self.confidence = confidence
        self.frame_step = max(1, frame_step)

        self.counter = None
        self.status = "not started"
        self.frames_processed = 0
        self.latest_jpeg = None  # last annotated frame, used by GET /frame

        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

    def get_counts(self):
        with self.lock:
            if self.counter is None:
                return {"total_count": 0, "entered": 0, "exited": 0}
            return {
                "total_count": self.counter.total,
                "entered": self.counter.entered,
                "exited": self.counter.exited,
            }

    def get_latest_frame(self):
        with self.lock:
            return self.latest_jpeg

    def _run(self):
        try:
            self._process_video()
        except Exception as e:
            logger.exception("Video processing failed")
            self.status = f"error: {e}"

    def _process_video(self):
        # "0" means webcam, everything else is a file path or stream url
        source = int(self.source) if self.source.isdigit() else self.source
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source}")

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        line_y = int(height * self.line_position)

        with self.lock:
            self.counter = LineCounter(line_y)

        self.status = "loading model"
        model = YOLO(self.model_path)

        self.status = "running"
        logger.info("Processing %s (line at y=%d)", self.source, line_y)
        frame_time = self.frame_step / fps

        while not self.stop_event.is_set():
            started = time.time()

            # skip frames if FRAME_STEP > 1 (grab() does not decode, so it is cheap)
            for _ in range(self.frame_step - 1):
                cap.grab()

            ok, frame = cap.read()
            if not ok:
                break

            # persist=True keeps the tracker state between frames so IDs stay the same
            results = model.track(
                frame,
                persist=True,
                classes=[PERSON_CLASS_ID],
                conf=self.confidence,
                verbose=False,
            )
            boxes = results[0].boxes

            if boxes.id is not None:
                for box, track_id in zip(boxes.xyxy.tolist(), boxes.id.int().tolist()):
                    x1, y1, x2, y2 = map(int, box)
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    with self.lock:
                        direction = self.counter.update(track_id, cy)
                        counts = (self.counter.entered, self.counter.exited, self.counter.total)

                    if direction:
                        logger.info("Person %d crossed the line (%s). Total = %d", track_id, direction, counts[2])
                        database.save_event(direction, *counts)

                    self._draw_person(frame, x1, y1, x2, y2, cx, cy, track_id)

            self._draw_line_and_counts(frame, line_y)

            ok, jpeg = cv2.imencode(".jpg", frame)
            with self.lock:
                self.frames_processed += 1
                if ok:
                    self.latest_jpeg = jpeg.tobytes()

            # do not play faster than the real video speed
            elapsed = time.time() - started
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)

        cap.release()
        self.status = "stopped" if self.stop_event.is_set() else "finished"
        logger.info("Processing %s. Final counts: %s", self.status, self.get_counts())

    def _draw_person(self, frame, x1, y1, x2, y2, cx, cy, track_id):
        with self.lock:
            counted = track_id in self.counter.counted_ids
        color = (0, 0, 255) if counted else (0, 255, 0)  # red once counted, green before
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, (cx, cy), 4, color, -1)
        cv2.putText(frame, f"ID {track_id}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def _draw_line_and_counts(self, frame, line_y):
        width = frame.shape[1]
        cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 255), 2)

        counts = self.get_counts()
        text = f"In: {counts['entered']}  Out: {counts['exited']}  Total: {counts['total_count']}"
        cv2.rectangle(frame, (10, 10), (330, 45), (0, 0, 0), -1)
        cv2.putText(frame, text, (18, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
