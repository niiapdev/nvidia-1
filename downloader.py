import asyncio
import os
import re
import shutil
from pathlib import Path
from typing import Tuple

import yt_dlp


def _sanitize_filename(filename: str) -> str:
    """Санитизирует имя файла для кроссплатформенной совместимости.

    Заменяет недопустимые символы Windows (<>:"/\\|?>*), обрабатывает
    зарезервированные имена Windows, удаляет пробелы/точки в конце,
    ограничивает длину, сохраняя Unicode-символы."""
    # Заменяем символы, которые невозможны в Windows-imposed
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Удаляем пробелы и точки в конце имени (до расширения)
    # Разделяем имя и расширение
    base, ext = os.path.splitext(filename)
    # Удаляем пробелы и точки в конце базового имени
    base = base.rstrip('. ')
    # Защита от зарезервированных имен Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    reserved_pattern = r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$'
    if re.match(reserved_pattern, base, re.IGNORECASE):
        base = '_' + base
    # Ограничиваем общую длину до 255 символов (макс для Windows),
    # но оставляем достаточно места для расширения
    max_total = 255
    if len(filename) > max_total:
        # Пересчитываем: базовое имя + расширение должно поместиться
        if len(ext) > max_total:
            ext = ext[-5:]  # Оставляем последние 5 симв. расширения
        available_for_base = max_total - len(ext)
        if len(base) > available_for_base:
            base = base[:available_for_base]
        filename = base + ext
    return filename


async def download_video(
    url: str,
    progress_coro=None,
) -> Tuple[Path, str]:
    ydl_opts = {
        "format": "best",
        "outtmpl": str(WORK_DIR / "%(title)s.%(ext)s"),
        "retries": 3,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    loop = asyncio.get_event_loop()

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_filename = ydl.prepare_filename(info)
            # Санитизируем имя
            safe_name = _sanitize_filename(raw_filename)
            raw_path = Path(raw_filename)
            safe_path = Path(safe_name)

            # Если имя изменилось — переименовываем файл на диске
            if raw_path != safe_path and raw_path.exists():
                try:
                    raw_path.rename(safe_path)
                except OSError:
                    # Если переименование не удалось (например, разные диски),
                    # используем санитизированное имя как опорное
                    pass

            # Возвращаем путь к файлу (сейчас может быть как raw, так и safe)
            # Для последующей работы используем safe имя
            return safe_path, info.get("title", "unknown")

    try:
        result_path, title = await loop.run_in_executor(None, _download)
        return result_path, title
    except Exception as exc:
        error_msg = str(exc)[:500]
        raise RuntimeError(error_msg)