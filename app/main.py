from fastapi import FastAPI

from app import db
from app.routes import jobs

db.init_db()

job_runner_app = FastAPI(
    title="Job Runner API",
    description="Submit and track jobs running on a Raspberry Pi Kubernetes cluster.",
    version="0.1.0",
)

job_runner_app.include_router(jobs.router)
