from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.models import jobs as models_jobs
from app.service import jobs as service_jobs

router = APIRouter()


@router.post("/jobs", response_model=models_jobs.JobRead, tags=["Jobs"])
def create_job(job: models_jobs.JobCreate):
    job_dict = service_jobs.create_job(job)
    return job_dict


@router.get("/jobs", response_model=list[models_jobs.JobRead], tags=["Jobs"])
def list_jobs() -> list[models_jobs.JobRead]:
    return service_jobs.list_jobs()


@router.get("/jobs/{job_id}", response_model=models_jobs.JobRead, tags=["Jobs"])
def get_job(job_id: UUID) -> models_jobs.JobRead:
    job = service_jobs.get_job(str(job_id))  # convert UUID to str for DB lookup
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
