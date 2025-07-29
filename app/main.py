from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.db import jobs as db_jobs
from app.routes import jobs as route_jobs

db_jobs.init_db()

job_runner_app = FastAPI(
    title="Job Runner API",
    description="Submit and track jobs running on a Raspberry Pi K8s cluster.",
    version="0.1.0",
)

job_runner_app.include_router(route_jobs.router)

instrumentator = Instrumentator().instrument(job_runner_app)


@job_runner_app.on_event("startup")
async def _startup():
    instrumentator.expose(job_runner_app)
