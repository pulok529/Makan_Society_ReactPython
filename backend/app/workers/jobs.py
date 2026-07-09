from app.db.session import SessionLocal
from app.modules.jobs.service import JobService


def process_background_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        service = JobService(db)
        job = service.get_job(job_id)
        if job.status == "pending":
            service.process_next_pending_job()
    finally:
        db.close()


def process_next_pending_job() -> bool:
    db = SessionLocal()
    try:
        return JobService(db).process_next_pending_job()
    finally:
        db.close()
