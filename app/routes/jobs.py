import asyncio
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models import jobs as models_jobs
from app.service import jobs as service_jobs

router = APIRouter()


@router.post(
    "/jobs",
    response_model=models_jobs.JobRead,
    summary="Create a job",
    tags=["Jobs"],
)
async def create_job(job: models_jobs.JobCreate) -> models_jobs.JobRead:
    return await service_jobs.create_job(job)


@router.patch(
    "/jobs/{job_id}",
    response_model=models_jobs.JobRead,
    summary="Patch a job using JSON Patch",
    tags=["Jobs"],
)
async def patch_job(
    job_id: UUID,
    request: models_jobs.JobPatchRequest,
) -> models_jobs.JobRead:

    try:
        return await service_jobs.patch_job(str(job_id), request.patch)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.get(
    "/jobs",
    response_model=list[models_jobs.JobRead],
    summary="Get a list of jobs",
    tags=["Jobs"],
)
async def list_jobs() -> list[models_jobs.JobRead]:
    return await service_jobs.list_jobs()


@router.get(
    "/jobs/{job_id}",
    response_model=models_jobs.JobRead,
    summary="Get a single job by its UUID",
    tags=["Jobs"],
)
async def get_job(job_id: UUID) -> models_jobs.JobRead:
    job = await service_jobs.get_job(str(job_id))  # convert UUID to str for DB lookup
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# A shared list of queues — each queue is for one connected client
job_event_subscribers: list[asyncio.Queue] = []

@router.get("/stream/jobs", summary="Stream job events via SSE", tags=["Jobs"])
async def stream_jobs(request: Request) -> StreamingResponse:
    queue = asyncio.Queue()
    job_event_subscribers.append(queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                # Disconnect cleanly if client goes away
                if await request.is_disconnected():
                    break

                try:
                    # Wait for new job data or timeout to send heartbeat
                    job_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {job_data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"  # comment-style keep-alive ping
        finally:
            # Always remove the queue from subscribers when done
            job_event_subscribers.remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
