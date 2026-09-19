import asyncio
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List

from config import BASE_DIR

logger = logging.getLogger(__name__)


def cleanup_files(*paths: Path):
    for path in paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


async def merge_video_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    progress_coro=None,
) -> Path:
    if progress_coro is not None:
        await progress_coro("⏳ Склейка видео с субтитрами...")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg not found in PATH. Please install FFmpeg.")

    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vf",
        f"subtitles='{srt_path}':force_style='FontSize=20',",
        "-c:a",
        "copy",
        "-y",
        str(output_path),
    ]

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg failed with code {process.returncode}")

    return output_path


def cleanup_temp_files(*paths: Path):
    for path in paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass