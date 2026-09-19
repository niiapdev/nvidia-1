import sqlite3
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS jobs ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "url TEXT,"
        "user_id INTEGER,"
        "source_lang TEXT,"
        "target_lang TEXT,"
        "translate BOOLEAN,"
        "merge BOOLEAN,"
        "status TEXT,"
        "result TEXT,"
        "error TEXT,"
        "created_at DATETIME"
        ")"
    )
    conn.commit()
    return conn


@dataclass
class Job:
    id: int
    url: str
    user_id: int
    source_lang: str
    target_lang: str
    translate: bool
    merge: bool
    status: str = "queued"
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = ""


class QueueManager:
    def __init__(self):
        self.conn = get_connection()
        self._notify_coro = None
        self._progress_coro = None

    def submit(
        self,
        url: str,
        user_id: int,
        source_lang: str,
        target_lang: str,
        translate: bool,
        merge: bool,
        notify_coro,
        progress_coro,
    ) -> Job:
        job = Job(
            url=url,
            user_id=user_id,
            source_lang=source_lang,
            target_lang=target_lang,
            translate=translate,
            merge=merge,
        )
        self.conn.execute(
            "INSERT INTO jobs (url, user_id, source_lang, target_lang, translate, merge, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'queued', datetime('now'))",
            (url, user_id, source_lang, target_lang, translate, merge),
        )
        self.conn.commit()
        # Store callbacks for later use by worker
        self._notify_coro = notify_coro
        self._progress_coro = progress_coro
        # Re-fetch the id
        cursor = self.conn.execute(
            "SELECT id FROM jobs WHERE url=? AND user_id=? ORDER BY id DESC LIMIT 1", (url, user_id)
        )
        job.id = cursor.fetchone()[0]
        return job

    def cancel_user_jobs(self, user_id: int) -> int:
        self.conn.execute(
            "UPDATE jobs SET status='cancelled' WHERE user_id=? AND status='queued'", (user_id,)
        )
        self.conn.commit()
        cursor = self.conn.execute(
            "SELECT changes()"
        )
        return cursor.fetchone()[0]

    def get_next_queued(self):
        cursor = self.conn.execute(
            "SELECT id, url, user_id, source_lang, target_lang, translate, merge FROM jobs WHERE status='queued' ORDER BY id ASC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return Job(
                id=row[0],
                url=row[1],
                user_id=row[2],
                source_lang=row[3],
                target_lang=row[4],
                translate=bool(row[5]),
                merge=bool(row[6]),
            )
        return None

    def set_processing(self, job_id: int) -> bool:
        self.conn.execute("UPDATE jobs SET status='processing' WHERE id=? AND status='queued'", (job_id,))
        self.conn.commit()
        cursor = self.conn.execute("SELECT changes()")
        return cursor.fetchone()[0] > 0

    def set_done(self, job_id: int, result: str):
        self.conn.execute("UPDATE jobs SET status='done', result=? WHERE id=?", (result, job_id))
        self.conn.commit()

    def set_failed(self, job_id: int, error: str):
        self.conn.execute(
            "UPDATE jobs SET status='failed', error=? WHERE id=?",
            (str(error)[:500], job_id),
        )
        self.conn.commit()

    async def worker_loop(self):
        """Process jobs sequentially from the queue."""
        while True:
            job = self.get_next_queued()
            if job is None:
                await asyncio.sleep(0.5)
                continue

            # Atomically move to processing
            if not self.set_processing(job.id):
                await asyncio.sleep(0.1)
                continue

            try:
                from pipeline import run_pipeline
                result = await run_pipeline(
                    url=job.url,
                    user_id=job.user_id,
                    source_lang=job.source_lang,
                    target_lang=job.target_lang,
                    translate=job.translate,
                    merge=job.merge,
                    notify_coro=self._notify_coro,
                    progress_coro=self._progress_coro,
                )

                if result["status"] == "done":
                    self.set_done(job.id, result["result"])
                else:
                    self.set_failed(job.id, result["error"])
            except Exception as exc:
                self.set_failed(job.id, str(exc)[:500])
            finally:
                # Reset callbacks - they'll be set on next submit
                pass

    def close(self):
        self.conn.close()