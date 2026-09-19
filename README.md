# VK Subtitles Bot

## 1. Что это

Гибридная система обработки видео на Python 3 с двумя режимами работы:

**VK-бот** — требует интернет только для получения видео по ссылке и взаимодействия с VK. Локальная обработка происходит через faster-whisper и FFmpeg.

**Локальная обработка** — после предварительной установки зависимостей и наличия локальной Whisper-модели работает полностью офлайн. Не использует yt-dlp, облачные API.

Проект обрабатывает видео локально без облачных API. VK-бот и yt-dlp — единственные компоненты с интернет-доступом.

## 2. Возможности

* VK-ссылки —接受 видео ссылки через бота
* Очередь SQLite — FIFO очередь задач со статусами: queued, processing, done, failed, cancelled
* faster-whisper — распознавание речи моделью medium на CPU с int8 compute type
* Английские субтитры — translate=True переводит речь в английский
* Русские субтитры — translate=False оставляет язык исходный
* Hard-sub — FFmpeg склейка субтитров в видео
* Локальная обработка — 4 скрипта для разных режимов обработки
* Автоматическое определение языка — при source_lang=None Whisper определяет язык сам
* Максимальное качество скачивания — yt-dlp format=best
* Обработка больших файлов — видеофайлы 40 GB допустимы
* Последовательная обработка — одновременно одна задача

## 3. Требования к компьютеру

* Intel Core i3-10100 — 4 физических ядра / 8 потоков
* 16 GB DDR4 RAM
* CPU-only — NVIDIA GPU не предполагается
* faster-whisper работает только на CPU
* Модель medium с compute_type='int8' — выбрана намеренно, качество важнее скорости

Почему обработка последовательная:
* Ограничения i3-10100 — одновременнаяMultiple Whisper inference недопустима
* Архитектура предполагает одну задачу одновременно
* Модель загружается один раз и переиспользуется

## 4. Архитектура проекта

```
vk-subtitles-bot/
├── config.py          - Конфигурационный файл со всеми путями и настройками
├── queue_manager.py   - QueueManager с Job dataclass, SQLite очередь FIFO
├── downloader.py      - yt-dlp скачивание видео (best quality)
├── translator.py      - faster-whisper transcribe/translate с VAD
├── merger.py          - FFmpeg hard-sub мердж видео и субтитров
├── pipeline.py        - Pipeline VK-режима: download → transcribe → merge → cleanup
├── local_processor.py - LocalProcessor с 4 режимами обработки
├── bot.py             - VK бот: Рус→English + hard-sub (translate=True, merge=True)
├── bot_subtitles_only.py - VK бот: Рус→English SRT без hard-sub (translate=True, merge=False)
├── bot_subtitles_ru.py - VK бот: Рус→Русские субтитры + hard-sub (translate=False, merge=True)
├── local_subtitles_only.py - Local режим: SRT рядом с видео
├── local_merge.py     - Local режим: hard-sub видео рядом с оригиналом
├── local_transcribe_save_srt.py - Local режим: transcribe + SRT рядом
├── local_move_and_transcribe.py - Local режим: move original to LOCAL_OUTPUT_DIR + SRT
├── requirements.txt   - Python зависимости
├── README.md          - Эта инструкция
├── input_videos/      - Входные файлы локального режима
├── video_for_whisper/ - Временные файлы VK-режима
├── video_subtitled/   - Готовые результаты VK-режима
└── jobs.sqlite3       - SQLite база данных очереди
```

## 5. Как работает Whisper

* faster-whisper с моделью medium, device=cpu, compute_type=int8
* WHISPER_BEAM_SIZE = 5 — лучшие_beam_search
* VAD_FILTER = True с параметрами: min_silence_duration_ms=500, speech_pad_ms=200
* task="translate" если translate=True, иначе task="transcribe"
* automatic language detection при source_lang=None
* Результат всегда английский при translate=True
* target_lang сохранен для будущего расширения, но на текущем этапе — только English

## 6. Как работает очередь

* SQLite база данных jobs.sqlite3 — постоянное хранилище состояния
* Таблица jobs с полями: id, url, user_id, source_lang, target_lang, translate, merge, status, result, error, created_at
* Достимые статусы: queued, processing, done, failed, cancelled
* FIFO — ORDER BY id ASC LIMIT 1, обрабатывается строго последовательно
* Одновременно выполняется только одна задача
* Не используется asyncio.Queue как постоянное хранилище
* Worker atomicamente переводит задачу из queued в processing
* После перезапуска программа не восстанавливает старые callback-функции

## 7. VK-боты

Три альтернативных варианта, запускается только ОДИН из них одновременно:

### bot.py
* Русская речь → английские субтитры + hard-sub
* source_lang="ru", target_lang="en", translate=True, merge=True

### bot_subtitles_only.py
* Русская речь → английские субтитры без hard-sub
* source_lang="ru", target_lang="en", translate=True, merge=False

### bot_subtitles_ru.py
* Русская речь → русские субтитры + hard-sub
* source_lang="ru", target_lang="ru", translate=False, merge=True
* Логика не менять относительно этих требований

Команда /cancel отменяет только задачи текущего пользователя, находящиеся в очереди.

## 8. Локальные скрипты

Все четыре скрипта одинаково работают на Windows и Linux:

### local_subtitles_only.py
* Сканирует INPUT_DIR видео файлы (.mp4, .mkv, .webm, .avi)
* Для каждого: распознавание → перевод в английский → SRT рядом с видео
* Оригинал не удалять
* Обрабатывать строго по одному файлу

### local_merge.py
* Сканирует INPUT_DIR
* Для каждого: распознавание → перевод → SRT → hard-sub через FFmpeg → имя_subtitled.mp4
* Оригинал не удалять
* Последовательная обработка

### local_transcribe_save_srt.py
* Сканирует INPUT_DIR
* Для каждого: распознавание → перевод → SRT рядом с видео
* Оригинал не удалять
* Последовательная обработка

### local_move_and_transcribe.py
* Сканирует INPUT_DIR
* Для каждого: распознавание → перевод → SRT → shutil.move оригинала в LOCAL_OUTPUT_DIR → SRT туда же
* Оригинал ПЕРЕМЕЩАЕТСЯ из INPUT_DIR
* После выполнения INPUT_DIR не должен содержать обработанный видеофайл
* В LOCAL_OUTPUT_DIR должны быть: video.mp4 + video.srt

## 9. Установка Windows

1. Установить Python 3
2. Открыть PowerShell или CMD
3. Перейти в каталог проекта
4. Создать виртуальное окружение: `python -m venv venv`
5. Активировать: `venv\Scripts\activate`
6. Установить зависимости: `pip install -r requirements.txt`
7. Установить FFmpeg отдельно в ОС
8. Добавить FFmpeg в PATH переменные окружения системы
9. Проверить: `python --version` и `ffmpeg -version`
10. Проверить проект: `python -m py_compile *.py`
11. Подготовить Whisper-модель (см. ниже)
12. Настроить VK_TOKEN переменную окружения

## 10. Установка Linux

1. Установить Python 3
2. Создать virtual environment: `python3 -m venv venv`
3. Активировать: `source venv/bin/activate`
4. Установить зависимости: `pip install -r requirements.txt`
5. Установить FFmpeg: `sudo apt install ffmpeg` (или аналог для вашего дистрибутива)
6. Проверить: `python3 --version` и `ffmpeg -version`
7. Проверить проект: `python3 -m py_compile *.py`
8. Подготовить Whisper-модель
9. Настроить VK_TOKEN

## 11. FFmpeg

* `ffmpeg-python` — только Python-обёртка, сам FFmpeg должен быть установлен в ОС
* Python-код проверяет наличие через `shutil.which("ffmpeg")`
* Один и тот же код работает и на Linux (`ffmpeg`), и на Windows (`ffmpeg.exe`) через PATH
* Если FFmpeg не найден — выводится понятное сообщение на русском с объяснением необходимости установки

## 12. Offline-режим

После подготовки модель работает без интернета:
* Локальные скрипты не требуют интернета
* Не используются yt-dlp, cloud API
* Whisper-модель должна быть предварительно доступна локально

Первый этап подготовки модели может требовать интернета, если модель ещё не скачана.

## 13. Запуск VK-режима

```bash
python bot.py                              # Рус→English + hard-sub
python bot_subtitles_only.py               # Рус→English SRT без hard-sub
python bot_subtitles_ru.py                 # Рус→Русские субтитры + hard-sub
```

Для Linux: `python3 bot.py` и соответствующие варианты.

## 14. Запуск локального режима

1. Положить видео в `./input_videos/`
2. Поддерживаемые расширения: .mp4, .mkv, .webm, .avi
3. Запустить один из:
```bash
python local_subtitles_only.py
python local_merge.py
python local_transcribe_save_srt.py
python local_move_and_transcribe.py
```

## 15. Что происходит с оригиналом

* subtitles_only — оригинал остаётся в INPUT_DIR
* merge — оригинал остаётся в INPUT_DIR
* transcribe_save_srt — оригинал остаётся в INPUT_DIR
* move_and_transcribe — оригинал перемещается из INPUT_DIR в LOCAL_OUTPUT_DIR

Проект НЕ удаляет большие видео автоматически. Видео размером 40 GB является допустимым. Пользователь самостоятельно управляет дисковым пространством.

## 16. Где находятся результаты

* `video_for_whisper/` — временные файлы VK-режима (удаляются после pipeline)
* `video_subtitled/` — готовые результаты VK-режима (hard-sub видео)
* `input_videos/` — входные файлы локального режима
* `local_processed/` — результаты move_and_transcribe (оригинал + SRT)
* `jobs.sqlite3` — состояние VK-очереди

## 17. Примеры

### Русская речь → английские субтитры
bot.py или local_merge.py — создает видео с embedded английскими субтитрами.

### Русская речь → русские субтитры
bot_subtitles_ru.py или local_subtitles_only.py — SRT файл на русском языке.

### Локальный файл → SRT
local_subtitles_only.py — создает .srt файл рядом с видео.

### Локальный файл → hard-sub
local_merge.py — создает видео с hardcoded субтитрами.

### Локальный файл → перемещение + SRT
local_move_and_transcribe.py — видео перемещается в local_processed/, SRT рядом.

## 18. Устранение проблем

* **FFmpeg not found** — установить FFmpeg в ОС и добавить в PATH
* **Python not found** — проверить `python --version` / `python3 --version`
* **faster-whisper не может загрузить модель** — убедиться, что medium модель доступна локально в `~/.cache/whisper/` или рядом с кодом
* **Модель отсутствует локально** — скачать/подготовить модель.one раз онлайн, потом офлайн
* **Недостаточно места** — видеофайлы 40 GB допустимы, проверьте свободное место
* **VK_TOKEN не задан** — установить переменную окружения VK_TOKEN
* **yt-dlp ошибка** — проверить связь, yt-dlp обновлять
* **SRT создаётся, но видео не склеивается** — убедиться, что FFmpeg в PATH и версия поддерживает subtitles filter

## 19. Кроссплатформенность

Проект рассчитан на Windows 10/11 и Linux.

* Пути реализованы через `pathlib.Path` — кроссплатформенно
* Файловые операции используют Python API (`shutil`, `os`, `Path`)
* FFmpeg ищется через `shutil.which("ffmpeg")` — работает и на Linux, и на Windows
* Используются только кроссплатформенные команды, Linux-only shell commands не используются
* Windows-зарезервированные имена файлов (CON, PRN, AUX, NUL, COM1-9, LPT1-9) обрабатываются в санитизаторе имен
* Unicode-имена файлов поддерживаются

## 20. Безопасность и данные

* VK_TOKEN лучше хранить в переменной окружения, не публиковать его
* SQLite содержит информацию о задачах (url, user_id, статусы), не содержит содержимого видео
* Локальные видео не отправляются в облачные API (кроме yt-dlp для скачивания по ссылке)
* Whisper работает локально, модели не скачивается автоматически во время обработки
* Ошибки ограничиваются 500 символами в поле error SQLite

## 21. Используемый промт

Архитектура создавалась на основе подробного промта, содержащего:

**Основные требования исходного промта:**
* Целевое железо: Intel Core i3-10100, 16 GB RAM, CPU-only
* faster-whisper модель: medium с compute_type=int8
* SQLite очередь с FIFO обработкой
* VK-бот с тремя вариантами режимов
* Локальный offline режим после подготовки
* FFmpeg для hard-sub
* Четыре local-скрипта с разными режимами
* Три варианта VK-бота с разными настройками translate/merge
* Сохранение оригинальных видео (кроме move_and_transcribe)
* Поддержка Windows и Linux с одним кодом
* Отсутствие параллельной обработки и batch processing
* Автоматическое определение языка Whisper
* VAD фильтр для стабильности сегментов

**Рекомендуемый промт для повторного создания проекта:**
See the full prompt in the original request for complete specification.

## 22. Финальная проверка

Все `.py` файлы прошли проверку `python3 -m py_compile`.
Импортыverified. Пути verified through `Path(__file__).parent`.
FFmpeg checked via `shutil.which("ffmpeg")`.
SQLite paths verified: `BASE_DIR / "jobs.sqlite3"`.
UTF-8 encoding confirmed for SRT files.
Windows/Linux compatibility verified through pathlib usage.
Отсутствуют Linux-only команды в Python-логике.
Отсутствуют Windows-only абсолютные пути.
Все signature совпадают с требованиями.