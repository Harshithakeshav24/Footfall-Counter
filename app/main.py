import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response

from app import config, database
from app.video_processor import VideoProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class SkipFrameRequests(logging.Filter):
    # the home page asks for /frame many times per second, no need to log all of them
    def filter(self, record):
        return "GET /frame" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(SkipFrameRequests())

processor = VideoProcessor(
    source=config.VIDEO_SOURCE,
    model_path=config.MODEL_PATH,
    line_position=config.LINE_POSITION,
    confidence=config.CONFIDENCE,
    frame_step=config.FRAME_STEP,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # start counting in the background as soon as the server starts
    database.init_db()
    processor.start()
    yield
    processor.stop()


app = FastAPI(
    title="Footfall Counter API",
    description="Counts people crossing a line in a video using YOLOv8 + OpenCV",
    lifespan=lifespan,
)


@app.get("/footfall")
def get_footfall():
    """Current number of people that crossed the line."""
    return processor.get_counts()


@app.get("/footfall/history")
def get_footfall_history(limit: int = Query(20, ge=1, le=500)):
    """Latest crossing events saved in SQLite (newest first)."""
    return database.get_history(limit)


@app.get("/status")
def get_status():
    return {
        "status": processor.status,
        "frames_processed": processor.frames_processed,
        "video_source": config.VIDEO_SOURCE,
    }


@app.get("/frame")
def get_frame():
    """Latest processed frame (with boxes and the line) as a JPEG image."""
    jpeg = processor.get_latest_frame()
    if jpeg is None:
        raise HTTPException(status_code=404, detail="No frame processed yet")
    return Response(content=jpeg, media_type="image/jpeg")


@app.get("/")
def home():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
