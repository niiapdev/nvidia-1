import asyncio
from pathlib import Path

from downloader import download_video
from translator import transcribe_video
from merger import merge_video_subtitles, cleanup_temp_files


async def run_pipeline(
    url: str,
    user_id: int,
    source_lang: str | None,
    target_lang: str,
    translate: bool,
    merge: bool,
    notify_coro,
    progress_coro,
) -> dict:
    result_info = {"status": "failed", "result": None, "error": None}
    video_path = None
    srt_path = None

    try:
        await progress_coro("📥 Скачивание видео...", user_id)
        video_path, title = await download_video(url, progress_coro=progress_coro)

        await progress_coro("⏳ Распознавание речи...", user_id)
        srt_path = await transcribe_video(
            video_path,
            source_lang=source_lang,
            target_lang=target_lang,
            translate=translate,
            progress_coro=progress_coro,
        )

        if merge:
            await progress_coro("⏳ Склейка видео с субтитрами...", user_id)
            output_path = video_path.parent / (video_path.stem + "_subtitled.mp4")
            await merge_video_subtitles(video_path, srt_path, output_path, progress_coro=progress_coro)
            result_info["result"] = str(output_path)
        else:
            result_info["result"] = str(srt_path)

        result_info["status"] = "done"

    except Exception as exc:
        result_info["error"] = str(exc)[:500]
        result_info["status"] = "failed"

    finally:
        if video_path and srt_path:
            cleanup_temp_files(video_path)

    return result_info