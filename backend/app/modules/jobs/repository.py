from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.jobs.models import BackgroundJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_job(self, job: BackgroundJob) -> BackgroundJob:
        self.db.add(job)
        self.db.flush()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> BackgroundJob | None:
        return self.db.get(BackgroundJob, job_id)

    def list_jobs(self, limit: int = 20) -> list[BackgroundJob]:
        statement = select(BackgroundJob).order_by(BackgroundJob.created_at.desc(), BackgroundJob.id.desc()).limit(limit)
        return list(self.db.scalars(statement))

    def get_next_pending_job(self) -> BackgroundJob | None:
        statement = (
            select(BackgroundJob)
            .where(BackgroundJob.status == "pending")
            .order_by(BackgroundJob.created_at.asc(), BackgroundJob.id.asc())
            .limit(1)
        )
        return self.db.scalar(statement)
