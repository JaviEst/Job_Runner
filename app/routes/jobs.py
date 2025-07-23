from uuid import UUID

from fastapi import APIRouter, HTTPException

from app import db, models

router = APIRouter()


@router.post("/jobs", response_model=models.JobRead, tags=["Jobs"])
def create_job(job: models.JobCreate):
    job_dict = db.create_job(job.dict())
    return job_dict


@router.get("/jobs", response_model=list[models.JobRead], tags=["Jobs"])
def list_jobs():
    return db.list_jobs()


@router.get("/jobs/{job_id}", response_model=models.JobRead, tags=["Jobs"])
def get_job(job_id: UUID):
    job = db.get_job(str(job_id))  # convert UUID to str for DB lookup
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
