````markdown
# VK Subtitles Bot

Гибридная система обработки видео на Python 3:

- **VK-режим** — принимает ссылки на видео через VK-бота, ставит задачи в SQLite-очередь, скачивает видео через `yt-dlp`, распознаёт речь через `faster-whisper` и при необходимости встраивает субтитры через FFmpeg.
- **Локальный режим** — обрабатывает видео из `./input_videos/` без VK и без `yt-dlp`. После предварительной подготовки Whisper-модели может работать полностью офлайн.

Проект рассчитан прежде всего на:

- Intel Core i3-10100
- 16 GB RAM
- CPU-only
- без NVIDIA GPU
- последовательную обработку — только одна задача одновременно
- модель Whisper `medium`
- `compute_type="int8"`

---

# 1. Первый запуск — сделать по шагам

Если вы только скачали проект, **не нужно сначала разбираться во всей архитектуре**.

Для первого запуска выполните следующие шаги.

## Шаг 1. Перейдите в папку проекта

Структура должна выглядеть примерно так:

```text
vk-subtitles-bot/
├── config.py
├── queue_manager.py
├── downloader.py
├── translator.py
├── merger.py
├── pipeline.py
├── local_processor.py
│
├── bot.py
├── bot_subtitles_only.py
├── bot_subtitles_ru.py
│
├── local_subtitles_only.py
├── local_merge.py
├── local_transcribe_save_srt.py
├── local_move_and_transcribe.py
│
├── requirements.txt
└── README.md
````

Откройте терминал именно в этой папке.

---

# 2. Установка Python

## Windows

Откройте PowerShell или CMD и проверьте:

```powershell
python --version
```

Если команда не найдена, установите Python 3.

После установки снова выполните:

```powershell
python --version
```

---

## Linux

Проверьте:

```bash
python3 --version
```

Если Python 3 отсутствует, установите его средствами вашего дистрибутива.

Для Debian/Ubuntu это обычно:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

---

# 3. Создание виртуального окружения

Использование `venv` рекомендуется, чтобы зависимости проекта не смешивались с системным Python.

## Windows

В папке проекта:

```powershell
python -m venv venv
```

Активировать:

```powershell
.\venv\Scripts\Activate.ps1
```

Если PowerShell не позволяет выполнить скрипт, можно использовать CMD:

```cmd
venv\Scripts\activate.bat
```

После активации в терминале должно появиться:

```text
(venv)
```

---

## Linux

```bash
python3 -m venv venv
```

Активировать:

```bash
source venv/bin/activate
```

После активации:

```text
(venv)
```

---

# 4. Установка Python-зависимостей

После активации `venv`.

## Windows

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Linux

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Основные Python-зависимости:

```text
vkbottle
yt-dlp
faster-whisper
ffmpeg-python
```

---

# 5. Установка FFmpeg

Это **обязательный отдельный шаг**.

Важно:

```text
ffmpeg-python
```

из `requirements.txt` — это только Python-обёртка.

Она **не устанавливает сам FFmpeg**.

Сам исполняемый файл FFmpeg должен быть установлен в операционной системе и находиться в `PATH`.

После установки проверьте:

```bash
ffmpeg -version
```

Если выводится информация о версии FFmpeg — всё хорошо.

Проект ищет FFmpeg через:

```python
shutil.which("ffmpeg")
```

Поэтому не требуется прописывать путь вроде:

```text
C:\ffmpeg\bin\ffmpeg.exe
```

или:

```text
/usr/bin/ffmpeg
```

---

# 6. Проверка проекта перед запуском

После установки зависимостей рекомендуется проверить Python-файлы.

## Windows PowerShell

```powershell
python -m py_compile config.py queue_manager.py downloader.py translator.py merger.py pipeline.py local_processor.py bot.py bot_subtitles_only.py bot_subtitles_ru.py local_subtitles_only.py local_merge.py local_transcribe_save_srt.py local_move_and_transcribe.py
```

## Linux

```bash
python3 -m py_compile config.py queue_manager.py downloader.py translator.py merger.py pipeline.py local_processor.py bot.py bot_subtitles_only.py bot_subtitles_ru.py local_subtitles_only.py local_merge.py local_transcribe_save_srt.py local_move_and_transcribe.py
```

Если команда завершилась без ошибок — синтаксис Python-файлов корректен.

---

# 7. Whisper-модель

Проект использует:

```text
faster-whisper
model: medium
device: cpu
compute_type: int8
beam_size: 5
```

Это сделано намеренно.

Проект **не переключается автоматически на `small` или `base`**.

NVIDIA GPU не требуется.

Whisper работает на CPU.

## Важно про первый запуск

При первом использовании модель может потребовать загрузку, если она ещё не доступна локально.

Поэтому:

* первый запуск подготовки модели может потребовать интернет;
* после того как модель доступна локально, локальный режим может работать без интернета.

Точное расположение кэша модели зависит от версии `faster-whisper` и способа загрузки модели. Не следует считать конкретный путь вроде `~/.cache/whisper/` обязательным.

---

# 8. Первый тест — локальный режим

Перед настройкой VK рекомендуется сначала проверить локальную обработку.

Это позволяет отдельно проверить:

* Python;
* зависимости;
* faster-whisper;
* Whisper-модель;
* FFmpeg;
* файловые пути;
* создание SRT.

Создайте каталог:

```text
input_videos/
```

Проект также может создать его автоматически.

Положите туда небольшое тестовое видео:

```text
input_videos/test.mp4
```

Поддерживаются:

```text
.mp4
.mkv
.webm
.avi
```

---

# 9. Первый тест: создать SRT

Запустите:

## Windows

```powershell
python local_subtitles_only.py
```

## Linux

```bash
python3 local_subtitles_only.py
```

Скрипт:

1. найдёт видео в `input_videos/`;
2. распознает речь;
3. переведёт речь на английский;
4. создаст SRT;
5. оставит оригинальное видео.

Результат:

```text
input_videos/
├── test.mp4
└── test.srt
```

Если `test.srt` появился и содержит субтитры — базовая локальная обработка работает.

---

# 10. Первый тест: hard-sub

Для проверки FFmpeg запустите:

## Windows

```powershell
python local_merge.py
```

## Linux

```bash
python3 local_merge.py
```

Результат будет создан рядом с оригиналом.

Например:

```text
input_videos/
├── test.mp4
├── test.srt
└── test_subtitled.mp4
```

Оригинал:

```text
test.mp4
```

не удаляется.

---

# 11. Если локальный тест работает

Если:

```text
local_subtitles_only.py
```

создал SRT, а:

```text
local_merge.py
```

создал видео с hard-sub, значит основные локальные компоненты работают:

```text
Python
  ↓
faster-whisper
  ↓
SRT
  ↓
FFmpeg
  ↓
готовое видео
```

Теперь можно переходить к VK-режиму.

---

# 12. Переменные конфигурации

Основные настройки находятся в:

```text
config.py
```

В проекте используются относительные пути на основе:

```python
BASE_DIR = Path(__file__).parent
```

Основные каталоги:

```text
input_videos/
video_for_whisper/
video_subtitled/
local_processed/
```

SQLite:

```text
jobs.sqlite3
```

---

# 13. Структура проекта

```text
vk-subtitles-bot/
│
├── config.py
│
├── queue_manager.py
├── downloader.py
├── translator.py
├── merger.py
├── pipeline.py
├── local_processor.py
│
├── bot.py
├── bot_subtitles_only.py
├── bot_subtitles_ru.py
│
├── local_subtitles_only.py
├── local_merge.py
├── local_transcribe_save_srt.py
├── local_move_and_transcribe.py
│
├── requirements.txt
├── README.md
│
├── input_videos/
├── video_for_whisper/
├── video_subtitled/
├── local_processed/
│
└── jobs.sqlite3
```

## Назначение файлов

### `config.py`

Общие настройки:

* пути;
* VK token;
* Whisper;
* SQLite;
* директории;
* параметры VAD;
* параметры CPU.

---

### `queue_manager.py`

SQLite-очередь задач.

Содержит:

* `Job`;
* добавление задач;
* отмену задач пользователя;
* FIFO worker;
* статусы задач.

---

### `downloader.py`

Скачивание видео через `yt-dlp`.

Используется:

```text
format = best
```

То есть проект намеренно выбирает максимально доступное качество согласно настройкам downloader.

---

### `translator.py`

Распознавание речи через `faster-whisper`.

Отвечает за:

* загрузку Whisper-модели;
* распознавание;
* перевод в английский;
* определение языка;
* VAD;
* генерацию SRT.

Модель загружается лениво и переиспользуется между задачами.

---

### `merger.py`

Работа с FFmpeg.

Используется для hard-sub:

```text
video + SRT
      ↓
FFmpeg
      ↓
video with embedded subtitles
```

---

### `pipeline.py`

Основной pipeline VK:

```text
download
   ↓
transcribe / translate
   ↓
SRT
   ↓
optional merge
   ↓
cleanup temporary files
   ↓
result
```

---

### `local_processor.py`

Общая логика четырёх локальных режимов.

---

### `bot.py`

VK:

```text
русский
   ↓
английский перевод
   ↓
hard-sub
```

---

### `bot_subtitles_only.py`

VK:

```text
русский
   ↓
английский перевод
   ↓
SRT
```

Видео не встраивает субтитры.

---

### `bot_subtitles_ru.py`

VK:

```text
русский
   ↓
русские субтитры
   ↓
hard-sub
```

---

# 14. VK-режим

VK-режим требует интернет.

Интернет используется для:

* взаимодействия с VK;
* получения ссылки;
* скачивания видео через `yt-dlp`.

Само распознавание выполняется локально:

```text
VK
 ↓
yt-dlp
 ↓
локальный файл
 ↓
faster-whisper
 ↓
SRT
 ↓
FFmpeg
 ↓
результат
```

Облачный API распознавания речи не используется.

---

# 15. Настройка VK_TOKEN

Токен VK не следует записывать непосредственно в исходный код и нельзя публиковать в GitHub.

Проект читает:

```text
VK_TOKEN
```

из переменной окружения.

## Windows PowerShell

Для текущего окна PowerShell:

```powershell
$env:VK_TOKEN="ВАШ_VK_TOKEN"
```

Проверить:

```powershell
echo $env:VK_TOKEN
```

Для постоянной пользовательской переменной:

```powershell
[Environment]::SetEnvironmentVariable("VK_TOKEN","ВАШ_VK_TOKEN","User")
```

После этого откройте новый терминал.

---

## Linux

Для текущей сессии:

```bash
export VK_TOKEN="ВАШ_VK_TOKEN"
```

Проверить:

```bash
echo $VK_TOKEN
```

---

# 16. Запуск VK-бота

В проекте три альтернативных бота.

Одновременно запускается только **один**.

---

## Вариант 1 — русский → английский + hard-sub

Файл:

```text
bot.py
```

Запуск Windows:

```powershell
python bot.py
```

Linux:

```bash
python3 bot.py
```

Настройки:

```text
source_lang = ru
target_lang = en
translate = True
merge = True
```

Pipeline:

```text
русская речь
      ↓
Whisper
      ↓
английский перевод
      ↓
SRT
      ↓
FFmpeg
      ↓
видео с английскими субтитрами
```

---

# 17. VK-бот только с английским SRT

Файл:

```text
bot_subtitles_only.py
```

Windows:

```powershell
python bot_subtitles_only.py
```

Linux:

```bash
python3 bot_subtitles_only.py
```

Настройки:

```text
source_lang = ru
target_lang = en
translate = True
merge = False
```

Получается английский SRT без hard-sub.

---

# 18. VK-бот с русскими субтитрами

Файл:

```text
bot_subtitles_ru.py
```

Windows:

```powershell
python bot_subtitles_ru.py
```

Linux:

```bash
python3 bot_subtitles_ru.py
```

Настройки:

```text
source_lang = ru
target_lang = ru
translate = False
merge = True
```

Результат:

```text
русская речь
      ↓
русское распознавание
      ↓
русский SRT
      ↓
FFmpeg
      ↓
видео с русскими субтитрами
```

---

# 19. Как пользоваться VK-ботом

После запуска одного из:

```text
bot.py
bot_subtitles_only.py
bot_subtitles_ru.py
```

бот начинает принимать сообщения.

Отправьте ему ссылку на видео.

Поддерживается ссылка, начинающаяся с:

```text
http://
```

или:

```text
https://
```

После получения ссылки задача помещается в SQLite.

Пользователь получает сообщение:

```text
Ссылка принята! Встало в очередь...
```

---

# 20. Очередь VK

Очередь хранится в:

```text
jobs.sqlite3
```

SQLite является постоянным хранилищем состояния очереди.

Статусы:

```text
queued
processing
done
failed
cancelled
```

Обработка:

```text
queued
   ↓
processing
   ↓
done
```

При ошибке:

```text
processing
   ↓
failed
```

Очередь FIFO:

```text
ORDER BY id ASC
```

Одновременно обрабатывается только одна задача.

`asyncio.Queue` не используется как постоянное хранилище.

---

# 21. Команда /cancel

Пользователь может отправить:

```text
/cancel
```

Это отменяет его задачи, находящиеся в очереди.

Задачи других пользователей команда не отменяет.

---

# 22. Прогресс обработки

Pipeline может передавать сообщения о текущем этапе через runtime callback.

Например:

```text
Скачивание...
Распознавание...
Создание субтитров...
Обработка FFmpeg...
Готово!
```

Callbacks не записываются в SQLite.

В SQLite хранится только состояние самой задачи.

---

# 23. Локальный режим

Локальный режим не использует VK.

Не используются:

```text
VK
yt-dlp
облачные API
```

Видео берётся непосредственно из:

```text
input_videos/
```

---

# 24. Локальный скрипт №1

## `local_subtitles_only.py`

Назначение:

```text
видео
 ↓
распознавание
 ↓
перевод на английский
 ↓
SRT
```

Оригинал остаётся на месте.

Пример:

```text
input_videos/
├── video.mp4
└── video.srt
```

Запуск Windows:

```powershell
python local_subtitles_only.py
```

Linux:

```bash
python3 local_subtitles_only.py
```

---

# 25. Локальный скрипт №2

## `local_merge.py`

Назначение:

```text
видео
 ↓
распознавание
 ↓
английский SRT
 ↓
FFmpeg
 ↓
hard-sub видео
```

Оригинал остаётся.

Пример:

```text
input_videos/
├── video.mp4
└── video_subtitled.mp4
```

Запуск:

```bash
python local_merge.py
```

Linux:

```bash
python3 local_merge.py
```

---

# 26. Локальный скрипт №3

## `local_transcribe_save_srt.py`

Назначение:

```text
видео
 ↓
распознавание
 ↓
английский SRT
```

SRT сохраняется рядом с видео.

Оригинал не удаляется.

---

# 27. Локальный скрипт №4

## `local_move_and_transcribe.py`

Этот режим отличается от остальных.

Pipeline:

```text
input_videos/video.mp4
        ↓
распознавание
        ↓
SRT
        ↓
shutil.move()
        ↓
local_processed/
```

После обработки:

```text
input_videos/
```

больше не содержит обработанное видео.

В:

```text
local_processed/
```

находятся:

```text
video.mp4
video.srt
```

Это единственный локальный режим, который перемещает оригинал.

---

# 28. Что происходит с оригинальными видео

## `local_subtitles_only.py`

Оригинал сохраняется.

## `local_merge.py`

Оригинал сохраняется.

## `local_transcribe_save_srt.py`

Оригинал сохраняется.

## `local_move_and_transcribe.py`

Оригинал перемещается:

```text
input_videos/
        ↓
local_processed/
```

Проект не удаляет большие видео автоматически.

Видео размером 40 GB допустимы при наличии достаточного свободного места.

Удаление файлов пользователь контролирует самостоятельно.

---

# 29. Где находятся результаты

## `input_videos/`

Входные видео локального режима.

---

## `video_for_whisper/`

Временные файлы VK pipeline.

После успешного завершения временные файлы могут удаляться.

---

## `video_subtitled/`

Готовые результаты VK hard-sub.

Эта директория автоматически не очищается.

---

## `local_processed/`

Результаты:

```text
local_move_and_transcribe.py
```

---

## `jobs.sqlite3`

SQLite база задач VK.

---

# 30. Поддерживаемые видео

Локальные скрипты обрабатывают:

```text
.mp4
.mkv
.webm
.avi
```

VK-режим зависит от того, какой формат в результате отдаёт `yt-dlp`/FFmpeg.

---

# 31. Распознавание и перевод

Функция распознавания поддерживает два основных режима.

## `translate=True`

Используется Whisper:

```text
task="translate"
```

Результат — английский.

Например:

```text
Русская речь
      ↓
Whisper translate
      ↓
English subtitles
```

---

## `translate=False`

Используется:

```text
task="transcribe"
```

Речь распознаётся без перевода.

Например:

```text
Русская речь
      ↓
Whisper transcribe
      ↓
Русские субтитры
```

---

# 32. Определение языка

Если:

```python
source_lang=None
```

Whisper может автоматически определить язык.

Если язык указан явно:

```python
source_lang="ru"
```

он передаётся Whisper как исходный язык.

Текущая архитектура оставляет:

```text
target_lang
```

для будущего расширения.

В текущей реализации перевод через Whisper ориентирован на английский.

---

# 33. VAD

В проекте включён:

```text
VAD_FILTER = True
```

Параметры:

```text
min_silence_duration_ms = 500
speech_pad_ms = 200
```

VAD помогает определять участки речи и отсекать продолжительные участки тишины.

Он не является гарантией идеальной точности каждого таймкода.

---

# 34. Таймкоды и SRT

SRT создаётся из сегментов Whisper.

Используется временная точность с миллисекундами.

Файлы SRT записываются в:

```text
UTF-8
```

Это позволяет сохранять Unicode, включая:

* русский;
* английский;
* другие поддерживаемые языки.

---

# 35. Производительность

Целевая конфигурация:

```text
CPU:
Intel Core i3-10100

RAM:
16 GB

GPU:
не требуется

Whisper:
medium

compute:
int8

beam_size:
5

workers:
1
```

Обработка намеренно последовательная.

То есть:

```text
video 1
   ↓
Whisper
   ↓
done
   ↓
video 2
   ↓
Whisper
   ↓
done
```

А не:

```text
video 1 ─┐
video 2 ─┼→ одновременно
video 3 ─┘
```

Это сделано для ограничения нагрузки на CPU и RAM.

---

# 36. Модель Whisper загружается один раз

Whisper-модель не должна создаваться заново для каждого видео.

Используется lazy initialization.

Схема:

```text
первое видео
    ↓
загрузка medium
    ↓
обработка
    ↓
модель остаётся в памяти
    ↓
второе видео
    ↓
используется та же модель
```

Это уменьшает лишние расходы времени и памяти.

---

# 37. Большие видео

Проект допускает большие видеофайлы, включая файлы порядка десятков гигабайт.

Например:

```text
40 GB
```

не является специальным запретным размером.

Однако необходимо учитывать:

* свободное место на диске;
* дополнительное место для временных файлов;
* место для результата FFmpeg;
* время обработки;
* скорость диска.

Проект не удаляет такие файлы автоматически.

---

# 38. Кроссплатформенность

Проект рассчитан на:

```text
Windows 10/11
Linux
```

Используются:

```python
pathlib.Path
shutil
os
subprocess
sqlite3
```

Пути не должны быть привязаны к:

```text
/home/user/...
C:\Users\...
/tmp/...
```

Проект использует:

```python
BASE_DIR = Path(__file__).parent
```

FFmpeg определяется через:

```python
shutil.which("ffmpeg")
```

---

# 39. Windows-safe имена файлов

Названия, полученные из внешних источников, например из названий видео в yt-dlp, могут содержать символы, запрещённые Windows.

Проект должен обрабатывать такие имена.

Проблемные символы:

```text
< > : " / \ | ? *
```

Также учитываются зарезервированные Windows-имена:

```text
CON
PRN
AUX
NUL
COM1
COM2
...
COM9
LPT1
LPT2
...
LPT9
```

Unicode в именах сохраняется.

---

# 40. yt-dlp

VK downloader использует Python API `yt-dlp`.

Используется формат:

```text
best
```

Проект не требует:

```text
wget
curl
aria2c
```

для скачивания.

Это позволяет использовать одну Python-архитектуру на Windows и Linux.

---

# 41. FFmpeg и hard-sub

Для hard-sub используется FFmpeg.

Общая схема:

```text
video.mp4
    +
video.srt
    ↓
FFmpeg
    ↓
video_subtitled.mp4
```

Hard-sub означает, что субтитры становятся частью изображения.

Их нельзя отключить как отдельную дорожку.

---

# 42. Offline-режим

После установки зависимостей и подготовки модели локальная обработка может работать без интернета.

Для локального режима не требуются:

```text
VK
yt-dlp
VK_TOKEN
облачные API
```

Необходимы только локальные компоненты:

```text
Python
faster-whisper
Whisper model
FFmpeg
```

Если модель ещё не подготовлена, для её первоначальной загрузки может потребоваться интернет.

---

# 43. Что НЕ является offline

VK-режим не является полностью офлайн.

Он требует интернет для:

```text
VK
yt-dlp
```

Сама обработка после скачивания видео выполняется локально.

---

# 44. Безопасность

## VK_TOKEN

Никогда не публикуйте:

```text
VK_TOKEN
```

в GitHub.

Не помещайте настоящий токен в:

```text
README.md
```

или публичный исходный код.

Используйте переменную окружения.

---

## Видео

Локальные видео не отправляются в облачные API распознавания.

Whisper работает локально.

---

## SQLite

SQLite содержит данные о задачах:

```text
id
url
user_id
source_lang
target_lang
translate
merge
status
result
error
created_at
```

Содержимое самого видео в SQLite не хранится.

---

# 45. Обработка ошибок

Ошибки записываются в поле:

```text
error
```

Длина ошибки ограничивается 500 символами.

Статус задачи при ошибке:

```text
failed
```

---

# 46. Временные файлы

VK pipeline может создавать временные файлы в:

```text
video_for_whisper/
```

После успешного завершения временные файлы могут удаляться.

Готовые результаты в:

```text
video_subtitled/
```

автоматически не удаляются.

Оригинальные локальные видео также не удаляются автоматически, кроме специального
режима:

```text
local_move_and_transcribe.py
```

который именно перемещает файл.

---

# 47. Перезапуск программы

SQLite хранит состояние очереди.

При запуске worker работает с задачами:

```text
queued
```

Runtime callbacks не сохраняются в SQLite.

Проект не предназначен для сохранения Python callback-функций между перезапусками.

Если процесс был принудительно остановлен во время обработки, необходимо учитывать,
что текущая задача могла не завершиться.

---

# 48. Типичный сценарий использования

## Локальное видео → английские субтитры

```text
1. Положить video.mp4 в input_videos/
2. Запустить local_subtitles_only.py
3. Дождаться завершения
4. Получить video.srt
```

---

## Локальное видео → английские hard-sub

```text
1. Положить video.mp4 в input_videos/
2. Запустить local_merge.py
3. Дождаться завершения
4. Получить video_subtitled.mp4
```

---

## VK → английские hard-sub

```text
1. Установить VK_TOKEN
2. Запустить bot.py
3. Отправить боту ссылку
4. Задача попадает в SQLite
5. yt-dlp скачивает видео
6. Whisper распознаёт и переводит речь
7. FFmpeg встраивает субтитры
8. Готовый файл сохраняется в video_subtitled/
```

---

# 49. Устранение проблем

## `python: command not found`

На Linux попробуйте:

```bash
python3 --version
```

Если Python установлен, используйте:

```bash
python3
```

---

## `No module named ...`

Убедитесь, что активирован `venv`.

Должно быть:

```text
(venv)
```

Затем:

```bash
python -m pip install -r requirements.txt
```

---

## `ffmpeg not found`

Проверьте:

```bash
ffmpeg -version
```

Если команда не существует, установите FFmpeg и добавьте его в `PATH`.

---

## Whisper не может загрузить модель

Проверьте:

1. установлен ли `faster-whisper`;
2. доступна ли модель;
3. хватает ли свободного места;
4. был ли интернет при первоначальной загрузке модели.

---

## VK_TOKEN не найден

Windows:

```powershell
echo $env:VK_TOKEN
```

Linux:

```bash
echo $VK_TOKEN
```

Если переменная пустая — задайте её.

---

## yt-dlp не может скачать видео

Проверьте:

* интернет;
* доступность исходной ссылки;
* актуальность `yt-dlp`;
* наличие свободного места.

Можно обновить:

```bash
python -m pip install --upgrade yt-dlp
```

---

## SRT создаётся, но hard-sub не работает

Проверьте:

```bash
ffmpeg -version
```

Затем убедитесь, что FFmpeg доступен из того же терминала, в котором запускается Python.

---

## Закончилось место на диске

Проект может работать с очень большими видео.

Проверьте свободное место.

Помните, что при hard-sub может потребоваться дополнительное место для:

```text
оригинала
+
временного файла
+
готового результата
```

---

# 50. Команды запуска — краткая памятка

## Windows

Активировать окружение:

```powershell
.\venv\Scripts\Activate.ps1
```

Локальные режимы:

```powershell
python local_subtitles_only.py
python local_merge.py
python local_transcribe_save_srt.py
python local_move_and_transcribe.py
```

VK:

```powershell
python bot.py
python bot_subtitles_only.py
python bot_subtitles_ru.py
```

---

## Linux

Активировать:

```bash
source venv/bin/activate
```

Локальные режимы:

```bash
python3 local_subtitles_only.py
python3 local_merge.py
python3 local_transcribe_save_srt.py
python3 local_move_and_transcribe.py
```

VK:

```bash
python3 bot.py
python3 bot_subtitles_only.py
python3 bot_subtitles_ru.py
```

---

# 51. Какой режим выбрать

| Задача                               | Скрипт                         |
| ------------------------------------ | ------------------------------ |
| Видео → английский SRT               | `local_subtitles_only.py`      |
| Видео → английские hard-sub          | `local_merge.py`               |
| Видео → распознавание + SRT          | `local_transcribe_save_srt.py` |
| Видео → перемещение + SRT            | `local_move_and_transcribe.py` |
| VK → русский → английский + hard-sub | `bot.py`                       |
| VK → русский → английский SRT        | `bot_subtitles_only.py`        |
| VK → русский → русский + hard-sub    | `bot_subtitles_ru.py`          |

---

# 52. Полная архитектура

Общая архитектура:

```text
                         ┌─────────────────┐
                         │     VK Bot      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ SQLite Queue    │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    yt-dlp       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ faster-whisper  │
                         │     medium      │
                         │    CPU/int8     │
                         └────────┬────────┘
                                  │
                                  ▼
                              SRT file
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     FFmpeg      │
                         └────────┬────────┘
                                  │
                                  ▼
                           Final video
```

Локальный pipeline:

```text
input_videos/
      │
      ▼
local_processor.py
      │
      ▼
faster-whisper
      │
      ▼
SRT
      │
      ├──────────────► SRT only
      │
      ▼
    FFmpeg
      │
      ▼
hard-sub video
```

---

# 53. Основные проектные решения

## Почему SQLite

SQLite используется как постоянное состояние очереди.

Преимущества:

* не требуется отдельный сервер;
* данные сохраняются на диске;
* очередь переживает обычный перезапуск процесса;
* легко просматривать состояние задач;
* подходит для последовательной обработки.

---

## Почему нет `asyncio.Queue`

`asyncio.Queue` хорошо подходит для runtime-очереди, но не является постоянным хранилищем.

Проекту необходимо сохранять задачи в SQLite.

Поэтому:

```text
SQLite = состояние очереди
```

а Python worker только читает и обрабатывает это состояние.

---

## Почему одна задача одновременно

Whisper `medium` на CPU достаточно тяжёлый.

Для Intel Core i3-10100 и 16 GB RAM проект сознательно использует:

```text
одна задача
один Whisper inference
num_workers = 1
```

---

## Почему `medium`

Модель `medium` выбрана намеренно.

Проект не пытается автоматически заменить её на более лёгкую модель ради скорости.

---

# 54. Ограничения проекта

Проект не является:

* облачным сервисом;
* GPU-ориентированной системой;
* многопоточным batch-processing сервером;
* системой автоматического удаления старых видео;
* системой хранения видео в SQLite.

Основная задача проекта:

```text
локальная обработка видео
+
необязательный VK-интерфейс
+
локальное распознавание Whisper
+
локальный FFmpeg
```

---

# 55. Кроссплатформенная реализация

Проект должен работать на:

```text
Windows 10/11
Linux
```

Для путей используется:

```python
Path(__file__).parent
```

Для файловых операций:

```python
pathlib
shutil
```

Для поиска FFmpeg:

```python
shutil.which("ffmpeg")
```

Для перемещения файлов:

```python
shutil.move()
```

Не используются Linux-only операции типа:

```text
rm
mv
chmod
bash
```

для основной Python-логики.

Не используются жёстко заданные пути:

```text
/home/...
/usr/bin/ffmpeg
C:\Users\...
```

---

# 56. Важное замечание о тестировании Windows/Linux

Проверка отсутствия Linux-only и Windows-only конструкций не является заменой реального запуска на обеих операционных системах.

Если проект был проверен только на одной ОС, корректно говорить:

```text
Код подготовлен с учётом Windows/Linux совместимости.
```

а не:

```text
Проект фактически протестирован на Windows и Linux.
```

Фактическое тестирование каждой ОС требует запуска проекта на соответствующей ОС.

---

# 57. Проверка перед публикацией на GitHub

Перед публикацией убедитесь, что в GitHub не попали:

```text
VK_TOKEN
```

или другие секреты.

Не рекомендуется публиковать:

```text
venv/
__pycache__/
*.pyc
```

Также проверьте:

```text
git status
```

Перед первым push.

---

# 58. Рекомендуемый `.gitignore`

Для GitHub можно использовать:

```gitignore
venv/
.venv/
__pycache__/
*.pyc
*.pyo

.env

jobs.sqlite3

video_for_whisper/*
video_subtitled/*
input_videos/*
local_processed/*

*.mp4
*.mkv
*.webm
*.avi
*.srt
```

Если необходимо хранить пустые каталоги в Git, добавьте в них `.gitkeep`.

---

# 59. Быстрый старт

Если всё уже установлено:

## Локальная обработка

```text
1. Положить видео в input_videos/
2. Активировать venv
3. Запустить local_subtitles_only.py
4. Получить SRT
```

## Hard-sub

```text
1. Положить видео в input_videos/
2. Запустить local_merge.py
3. Получить video_subtitled.mp4
```

## VK

```text
1. Установить VK_TOKEN
2. Запустить один bot*.py
3. Отправить ссылку боту
4. Дождаться обработки
5. Забрать результат
```

---

# 60. Исходные требования проекта

Архитектура проекта основана на следующих требованиях:

* Python 3;
* Windows + Linux;
* Intel Core i3-10100;
* 16 GB DDR4;
* CPU-only;
* faster-whisper;
* Whisper `medium`;
* `compute_type="int8"`;
* `beam_size=5`;
* VAD;
* автоматическое определение языка при `source_lang=None`;
* английский перевод через `task="translate"`;
* исходный язык через `task="transcribe"`;
* SQLite queue;
* FIFO;
* одна задача одновременно;
* VK-bot;
* yt-dlp;
* FFmpeg;
* четыре локальных режима;
* три альтернативных VK-бота;
* сохранение оригиналов;
* отдельный режим перемещения оригинала;
* Unicode;
* Windows-safe filenames;
* относительные пути через `Path(__file__).parent`;
* отсутствие облачного распознавания;
* возможность локальной offline-обработки;
* отсутствие автоматического удаления больших видео.

---

# 61. Полный промт для повторного создания проекта

Ниже приведена краткая спецификация, которой должен придерживаться AI-агент при повторном создании проекта.

Создать гибридный проект обработки видео на Python 3 с двумя режимами:

**A. VK-бот**

Бот принимает ссылки, записывает задачи в SQLite и обрабатывает их
последовательно.

Pipeline:

```text
VK URL
→ SQLite queue
→ yt-dlp
→ faster-whisper
→ SRT
→ optional FFmpeg hard-sub
→ result
```

**B. Local**

Видео помещаются в:

```text
./input_videos/
```

и обрабатываются локально четырьмя отдельными скриптами.

Общие требования:

```text
Intel Core i3-10100
16 GB RAM
CPU-only
Whisper medium
int8
beam_size=5
VAD enabled
one task at a time
```

Использовать:

```text
vkbottle
yt-dlp
faster-whisper
ffmpeg-python
SQLite
FFmpeg
```

Постоянное состояние очереди хранить только в SQLite.

Таблица:

```text
jobs:
id
url
user_id
source_lang
target_lang
translate
merge
status
result
error
created_at
```

Статусы:

```text
queued
processing
done
failed
cancelled
```

FIFO:

```text
ORDER BY id ASC
```

Не использовать `asyncio.Queue` как постоянное хранилище.

Whisper:

```text
model = medium
device = cpu
compute_type = int8
beam_size = 5
```

Модель загружать один раз и переиспользовать.

При:

```text
translate=True
```

использовать:

```text
task="translate"
```

для английского.

При:

```text
translate=False
```

использовать:

```text
task="transcribe"
```

для исходного языка.

При:

```text
source_lang=None
```

разрешить автоматическое определение языка.

SRT:

```text
UTF-8
millisecond timestamps
```

VAD:

```text
min_silence_duration_ms = 500
speech_pad_ms = 200
```

Пути:

```python
BASE_DIR = Path(__file__).parent
```

Не использовать абсолютные пути.

FFmpeg искать через:

```python
shutil.which("ffmpeg")
```

Не использовать Linux-only shell commands.

yt-dlp использовать через Python API.

Обрабатывать Windows-недопустимые символы в именах файлов:

```text
< > : " / \ | ? *
```

учитывать Windows reserved names:

```text
CON
PRN
AUX
NUL
COM1-COM9
LPT1-LPT9
```

Сохранять Unicode.

Создать три VK-бота:

```text
bot.py
    ru → en + hard-sub

bot_subtitles_only.py
    ru → en SRT

bot_subtitles_ru.py
    ru → ru + hard-sub
```

Создать четыре local-скрипта:

```text
local_subtitles_only.py
local_merge.py
local_transcribe_save_srt.py
local_move_and_transcribe.py
```

Оригиналы не удалять в первых трёх режимах.

В `local_move_and_transcribe.py` использовать:

```python
shutil.move()
```

и перемещать оригинал в:

```text
local_processed/
```

Не удалять автоматически большие видео.

Создать:

```text
README.md
```

на русском языке с:

* первым запуском;
* Windows;
* Linux;
* Python;
* venv;
* requirements;
* FFmpeg;
* Whisper;
* VK_TOKEN;
* VK-ботами;
* локальными скриптами;
* offline режимом;
* структурой проекта;
* очередью;
* результатами;
* FAQ;
* кроссплатформенностью;
* безопасностью;
* ограничениями;
* архитектурой.

Перед завершением проверить все `.py` через:

```text
python -m py_compile
```

или соответствующий Python 3 executable.

Не утверждать о фактическом тестировании Windows/Linux, если запуск на обеих ОС реально не выполнялся.

---

# 62. Итог

Проект предназначен для следующего рабочего процесса:

```text
                 ┌───────────────────────┐
                 │       VK режим        │
                 │                       │
                 │ VK → yt-dlp → Whisper │
                 │       → SRT → FFmpeg  │
                 └───────────┬───────────┘
                             │
                             ▼
                       готовое видео


                 ┌───────────────────────┐
                 │     Local режим       │
                 │                       │
                 │ input_videos/         │
                 │       ↓               │
                 │ faster-whisper        │
                 │       ↓               │
                 │ SRT / FFmpeg          │
                 └───────────────────────┘
```

Главный принцип проекта:

```text
Whisper и FFmpeg работают локально.
VK и yt-dlp используются только там, где нужен интернет.
```

Для обычного первого запуска достаточно:

```text
1. Python
2. FFmpeg
3. venv
4. pip install -r requirements.txt
5. Whisper medium
6. test.mp4 → input_videos/
7. python local_subtitles_only.py
```

После успешного локального теста можно настраивать VK-бота.

```
```
