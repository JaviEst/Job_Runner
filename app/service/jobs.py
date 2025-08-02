from datetime import datetime
import json
import uuid

import jsonpatch

from app.constants import DEFAULT_JOB_STATUS, DEFAULT_CPU, DEFAULT_MEM
from app.db import jobs as db_jobs
from app.models import jobs as models_jobs
from app.routes import jobs as routes_jobs

ALLOWED_PATCH_FIELDS = {"status", "message"}


async def create_job(new_job: models_jobs.JobCreate) -> models_jobs.JobRead:
    new_job_dict = {
        "id": str(uuid.uuid4()),
        "image": new_job.image,
        "command": new_job.command,
        "cpu": new_job.cpu or DEFAULT_CPU,
        "memory": new_job.memory or DEFAULT_MEM,
        "status": DEFAULT_JOB_STATUS,
        "message": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    await db_jobs.create_job(new_job_dict)
    created_job = await get_job(new_job_dict.get("id"))

    for queue in routes_jobs.job_event_subscribers:
        await queue.put(created_job.dict())

    return created_job


async def patch_job(
    job_id: str,
    patch_ops: list[models_jobs.JSONPatchOperation],
) -> models_jobs.JobRead:

    current_job = await get_job(job_id)
    if current_job is None:
        raise KeyError("Job not found")
    
    if not patch_ops:
        return await get_job(job_id)
    
    for patch in patch_ops:
        if patch.op != "replace":
            raise ValueError(f"Unsupported operation: {patch.op}")

        field = patch.path.lstrip("/")
        if field not in ALLOWED_PATCH_FIELDS:
            raise ValueError(f"Cannot patch field: {field}")

    patch_ops.append(
        models_jobs.JSONPatchOperation(
            op="replace",
            path="/updated_at",
            value=datetime.utcnow(),
        )
    )

    job_dict = current_job.dict()
    patch_list = [op.dict(exclude_unset=True) for op in patch_ops]

    try:
        patch = jsonpatch.JsonPatch(patch_list)
        patched_job_dict = patch.apply(job_dict)

        # Only keep the keys that were modified
        updated_fields = {}
        for op in patch.patch:
            path = op.get("path").lstrip("/")
            if path in patched_job_dict:
                updated_fields[path] = patched_job_dict[path]

    except jsonpatch.JsonPatchException as e:
        raise ValueError(f"Invalid patch: {e}")

    await db_jobs.update_job(job_id, updated_fields)
    return await get_job(job_id)


async def list_jobs() -> list[models_jobs.JobRead]:
    jobs = await db_jobs.list_jobs()
    return [models_jobs.JobRead(**job) for job in jobs]


async def get_job(job_id: str) -> models_jobs.JobRead:
    job = await db_jobs.get_job(job_id)
    if not job:
        return None
    return models_jobs.JobRead(**job)
