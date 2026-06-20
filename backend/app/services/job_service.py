from datetime import datetime

from app.repositories.sqlite_repo import SQLiteRepository


class JobService:
    def __init__(self, repo: SQLiteRepository | None = None) -> None:
        self.repo = repo or SQLiteRepository()

    def create_daily_job(self) -> dict:
        now = datetime.now().isoformat(timespec="seconds")
        job_id = self.repo.execute(
            """
            INSERT INTO job_execution(job_name, status, progress, started_at, message)
            VALUES ('daily_update', 'QUEUED', 0, ?, '任务已创建，等待执行')
            """,
            (now,),
        )
        return {"job_id": job_id, "status": "QUEUED"}

    def latest_jobs(self) -> list[dict]:
        return self.repo.fetch_all("SELECT * FROM job_execution ORDER BY id DESC LIMIT 20")

