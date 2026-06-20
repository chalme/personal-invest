from datetime import datetime
from threading import Thread

from app.repositories.sqlite_repo import SQLiteRepository


def _run_daily_job(job_id: int) -> None:
    from worker.daily_job import run

    run(job_id=job_id)


class JobService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def create_daily_job(self) -> dict:
        running = self.repo.fetch_one(
            """
            SELECT * FROM job_execution
            WHERE job_name = 'daily_update' AND status IN ('QUEUED', 'RUNNING')
            ORDER BY id DESC LIMIT 1
            """
        )
        if running:
            return {"job_id": running["id"], "status": running["status"], "message": running.get("message")}

        now = datetime.now().isoformat(timespec="seconds")
        job_id = self.repo.execute(
            """
            INSERT INTO job_execution(job_name, status, progress, started_at, message)
            VALUES ('daily_update', 'QUEUED', 0, ?, '任务已创建，准备执行')
            """,
            (now,),
        )
        thread = Thread(target=_run_daily_job, args=(job_id,), daemon=True)
        thread.start()
        return {"job_id": job_id, "status": "QUEUED", "message": "每日更新已启动"}

    def get_job(self, job_id: int) -> dict | None:
        return self.repo.fetch_one("SELECT * FROM job_execution WHERE id = ?", (job_id,))

    def latest_jobs(self) -> list[dict]:
        return self.repo.fetch_all("SELECT * FROM job_execution ORDER BY id DESC LIMIT 20")

