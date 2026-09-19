import asyncio
import shutil
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_CPU_THREADS,
    WHISPER_NUM_WORKERS,
    WHISPER_BEAM_SIZE,
    VAD_FILTER,
    VAD_PARAMETERS,
    INPUT_DIR,
    LOCAL_OUTPUT_DIR,
    OUTPUT_DIR,
)

_model: Optional[WhisperModel] = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
            cpu_threads=WHISPER_CPU_THREADS,
            num_workers=WHISPER_NUM_WORKERS,
        )
    return _model


def _format_srt_timestamp(seconds: float) -> str:
    h = int(seconds / 3600)
    m = int((seconds % 3600) / 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _generate_srt(segments) -> str:
    lines = []
    for i, segment in enumerate(segments, start=1):
        start_ts = _format_srt_timestamp(segment.start)
        end_ts = _format_srt_timestamp(segment.end)
        text = segment.text.strip()
        lines.append(f"{i}")
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


async def process_local_video(
    video_path: Path,
    mode: str,
    output_dir: Optional[Path] = None,
) -> Path:
    model = get_model()

    srt_path = video_path.with_suffix(".srt")

    segments, info = model.transcribe(
        str(video_path),
        task="translate",
        beam_size=WHISPER_BEAM_SIZE,
        vad_filter=VAD_FILTER,
        vad_parameters=VAD_PARAMETERS,
    )

    srt_content = _generate_srt(segments)
    srt_path.write_text(srt_content, encoding="utf-8")

    result_path = srt_path

    if mode == "subtitles_only":
        result_path = srt_path

    elif mode == "merge":
        if output_dir is None:
            output_dir = video_path.parent
        output_video = output_dir / f"{video_path.stem}_subtitled.mp4"
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("FFmpeg not found in PATH. Please install FFmpeg.")

        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"subtitles='{srt_path.as_posix()}':force_style='FontSize=20',",
            "-c:a",
            "copy",
            "-y",
            str(output_video),
        ]
        proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError("FFmpeg failed")
        result_path = output_video

    elif mode == "transcribe_save_srt":
        result_path = srt_path

    elif mode == "move_and_transcribe":
        if output_dir is None:
            output_dir = LOCAL_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        local_output = output_dir / video_path.name
        shutil.move(str(video_path), str(local_output))

        srt_dest = output_dir / (video_path.stem + ".srt")
        shutil.move(str(srt_path), str(srt_dest))

        result_path = local_output

    return result_path