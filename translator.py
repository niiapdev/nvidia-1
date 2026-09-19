import asyncio
import logging
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


def _generate_srt(segments, model_lang: str) -> str:
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


async def transcribe_video(
    video_path: Path,
    source_lang: str | None = None,
    target_lang: str = "en",
    translate: bool = False,
    progress_coro=None,
) -> Path:
    if progress_coro is not None:
        await progress_coro("⏳ Распознавание речи...")

    model = get_model()

    task = "translate" if translate else "transcribe"

    kwargs = {
        "task": task,
        "beam_size": WHISPER_BEAM_SIZE,
        "vad_filter": VAD_FILTER,
        "vad_parameters": VAD_PARAMETERS,
    }

    if source_lang is not None:
        kwargs["language"] = source_lang

    segments, info = model.transcribe(str(video_path), **kwargs)

    srt_content = _generate_srt(segments, info.language)

    srt_path = video_path.with_suffix(".srt")
    srt_path.write_text(srt_content, encoding="utf-8")

    return srt_path