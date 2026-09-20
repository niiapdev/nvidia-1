from pathlib import Path
import os

BASE_DIR = Path(__file__).parent
BASE_DIR.mkdir(parents=True, exist_ok=True)

WORK_DIR = BASE_DIR / "video_for_whisper"
OUTPUT_DIR = BASE_DIR / "video_subtitled"
INPUT_DIR = BASE_DIR / "input_videos"
LOCAL_OUTPUT_DIR = BASE_DIR / "local_processed"
DB_PATH = BASE_DIR / "jobs.sqlite3"

VK_TOKEN = os.environ.get("VK_TOKEN", "YOUR_TOKEN_HERE")

WHISPER_MODEL = "medium"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_CPU_THREADS = 8
WHISPER_NUM_WORKERS = 1
WHISPER_BEAM_SIZE = 5

VAD_FILTER = True

VAD_PARAMETERS = {
    "min_silence_duration_ms": 500,
    "speech_pad_ms": 200,
}