import asyncio
import logging
from pathlib import Path

from local_processor import process_local_video

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi"}


def _get_video_files(directory: Path) -> list[Path]:
    files = []
    if directory.exists():
        for f in sorted(directory.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(f)
    return files


async def main():
    input_dir = Path(__file__).parent / "input_videos"
    video_files = _get_video_files(input_dir)

    if not video_files:
        logger.info("No video files found in input_videos/")
        return

    for video_path in video_files:
        logger.info(f"Processing: {video_path.name}")
        try:
            result = await process_local_video(video_path, mode="merge")
            logger.info(f"Subtitled video saved to: {result}")
        except Exception as e:
            logger.error(f"Error processing {video_path.name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())