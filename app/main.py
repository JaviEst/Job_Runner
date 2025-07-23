from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app import db
from app.routes import jobs

db.init_db()

job_runner_app = FastAPI(
    title="Job Runner API",
    description="Submit and track jobs running on a Raspberry Pi K8s cluster.",
    version="0.1.0",
)

job_runner_app.include_router(jobs.router)

instrumentator = Instrumentator().instrument(job_runner_app)


@job_runner_app.on_event("startup")
async def _startup():
    instrumentator.expose(job_runner_app)
