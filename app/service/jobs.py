from uuid import UUID

from app.db import jobs as db_jobs
from app.models import jobs as models_jobs


def create_job(job_data: models_jobs.JobCreate) -> models_jobs.JobRead:
    job_dict = db_jobs.create_job(job_data.dict())
    return models_jobs.JobRead(**job_dict)


def get_job(job_id: UUID) -> models_jobs.JobRead:
    job = db_jobs.get_job(str(job_id))
    if not job:
        return None
    return models_jobs.JobRead(**job)


def list_jobs() -> list[models_jobs.JobRead]:
    jobs = db_jobs.list_jobs()
    return [models_jobs.JobRead(**job) for job in jobs]
