import asyncio
import logging
import re
from pathlib import Path

from vkbottle import Bot
from vkbottle.framework.framework.exceptions import MessageTooLong

from config import VK_TOKEN
from queue_manager import QueueManager
from pipeline import run_pipeline

logger = logging.getLogger(__name__)

bot = Bot(VK_TOKEN)
queue_manager = QueueManager()


async def _notify_done(job: "Job"):
    try:
        await bot.api.messages.send(
            peer_id=job.user_id,
            random_id=0,
            message=f"✅ Готово! Файл: {job.result}",
        )
    except Exception as exc:
        logger.error(f"Failed to send notify_done: {exc}")


async def _notify_progress(message: str, user_id: int = None):
    try:
        if user_id is None:
            user_id = message.from_user.id if hasattr(message, 'from_user.id') else message.user_id
        await bot.api.messages.send(
            peer_id=user_id,
            random_id=0,
            message=message,
        )
    except Exception as exc:
        logger.error(f"Failed to send notify_progress: {exc}")


@bot.on.message(text=lambda text: text and (text.startswith("http://") or text.startswith("https://")))
async def handle_link(message):
    url = message.text.strip()
    job = queue_manager.submit(
        url=url,
        user_id=message.from_user.id,
        source_lang=None,
        target_lang="en",
        translate=True,
        merge=True,
        notify_coro=_notify_progress,
        progress_coro=_notify_progress,
    )
    await message.answer(f"✅ Ссылка принята! Встало в очередь...")


@bot.on.message(text="/cancel")
async def handle_cancel(message):
    deleted = queue_manager.cancel_user_jobs(message.from_user.id)
    if deleted > 0:
        await message.answer(f"❌ Ваши задачи в очереди отменены")
    else:
        await message.answer("❌ У вас нет активных задач в очереди")


async def start_bot():
    await bot.run_polling()


if __name__ == "__main__":
    asyncio.run(start_bot())