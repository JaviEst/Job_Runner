import os
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.constants import DEFAULT_JOB_STATUS
from app.db import jobs
from app.main import job_runner_app


@pytest.fixture(scope="session")
def test_db_file():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    yield f"sqlite+aiosqlite:///{db_path}"
    os.close(db_fd)
    os.remove(db_path)


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db_file):
    test_engine = create_async_engine(
        test_db_file,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    jobs.engine = test_engine
    jobs.metadata.bind = test_engine

    async with test_engine.begin() as conn:
        # Run sync DDL operations within an async context
        await conn.run_sync(jobs.metadata.drop_all)
        await conn.run_sync(jobs.metadata.create_all)

    transport = ASGITransport(app=job_runner_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_job(test_client):
    job_payload = {
        "image": "alpine",
        "command": ["echo", "hello world"],
        "cpu": "100m",
        "memory": "64Mi",
    }

    response = await test_client.post("/jobs", json=job_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["image"] == job_payload.get("image")
    assert data["status"] == DEFAULT_JOB_STATUS
    assert data["command"] == job_payload.get("command")
    assert data["cpu"] == job_payload.get("cpu")
    assert data["memory"] == job_payload.get("memory")


@pytest.mark.asyncio
async def test_create_job_missing_fields(test_client):
    response = await test_client.post("/jobs", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_job_invalid_command_type(test_client):
    payload = {
        "image": "alpine",
        "command": "echo hello",  # should be list, not string
        "cpu": "100m",
        "memory": "128Mi",
    }
    response = await test_client.post("/jobs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_job_empty_command(test_client):
    payload = {
        "image": "alpine",
        "command": [],
        "cpu": "100m",
        "memory": "128Mi",
    }
    response = await test_client.post("/jobs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_job_field_length_exceeded(test_client):
    payload = {
        "image": "a" * 300,
        "command": ["echo", "test"],
        "cpu": "100m",
        "memory": "64Mi",
    }
    response = await test_client.post("/jobs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_job_by_id(test_client):
    job_payload = {
        "image": "ubuntu",
        "command": ["ls", "/"],
        "cpu": "150m",
        "memory": "128Mi",
    }
    create_resp = await test_client.post("/jobs", json=job_payload)
    assert create_resp.status_code == 200
    job_id = create_resp.json().get("id")

    response = await test_client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["image"] == job_payload.get("image")
    assert data["status"] == DEFAULT_JOB_STATUS
    assert data["command"] == job_payload.get("command")
    assert data["cpu"] == job_payload.get("cpu")
    assert data["memory"] == job_payload.get("memory")


@pytest.mark.asyncio
async def test_get_job_not_found(test_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await test_client.get(f"/jobs/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_invalid_uuid_format(test_client):
    response = await test_client.get("/jobs/not-a-valid-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_jobs(test_client):
    job_payload = {
        "image": "busybox",
        "command": ["sleep", "1"],
        "cpu": "50m",
        "memory": "32Mi",
    }
    await test_client.post("/jobs", json=job_payload)

    response = await test_client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1
    assert any(job["image"] == "busybox" for job in jobs)


@pytest.mark.asyncio
async def test_list_jobs_empty(test_client):
    response = await test_client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) == 0


@pytest.mark.asyncio
async def test_patch_job(test_client):
    job_payload = {
        "image": "busybox",
        "command": ["sleep", "1"],
        "cpu": "50m",
        "memory": "32Mi",
    }
    create_resp = await test_client.post("/jobs", json=job_payload)
    assert create_resp.status_code == 200
    job_id = create_resp.json().get("id")

    response = await test_client.get(f"/jobs/{job_id}")
    assert response.status_code == 200

    new_status = "scheduled"
    patch_op = {"patch": [{"op": "replace", "path": "/status", "value": new_status}]}
    patch_resp = await test_client.patch(f"/jobs/{job_id}", json=patch_op)
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["status"] == new_status


@pytest.mark.asyncio
async def test_patch_job_not_found(test_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    patch_op = {"patch": [{"op": "replace", "path": "/status", "value": "scheduled"}]}
    patch_resp = await test_client.patch(f"/jobs/{fake_id}", json=patch_op)
    response = patch_resp.json()
    assert patch_resp.status_code == 404
    assert response["detail"] == f"Job {fake_id} not found"


@pytest.mark.asyncio
async def test_patch_job_invalid_operation(test_client):
    job_payload = {
        "image": "busybox",
        "command": ["sleep", "1"],
        "cpu": "50m",
        "memory": "32Mi",
    }
    create_resp = await test_client.post("/jobs", json=job_payload)
    assert create_resp.status_code == 200
    job_id = create_resp.json().get("id")

    response = await test_client.get(f"/jobs/{job_id}")
    assert response.status_code == 200

    new_status = "scheduled"
    patch_op = {"patch": [{"op": "invalid", "path": "/status", "value": new_status}]}
    patch_resp = await test_client.patch(f"/jobs/{job_id}", json=patch_op)
    response = patch_resp.json()
    assert patch_resp.status_code == 400
    assert response["detail"] == "Unsupported operation: invalid"


@pytest.mark.asyncio
async def test_patch_job_not_allowed_path(test_client):
    job_payload = {
        "image": "busybox",
        "command": ["sleep", "1"],
        "cpu": "50m",
        "memory": "32Mi",
    }
    create_resp = await test_client.post("/jobs", json=job_payload)
    assert create_resp.status_code == 200
    job_id = create_resp.json().get("id")

    response = await test_client.get(f"/jobs/{job_id}")
    assert response.status_code == 200

    patch_op = {"patch": [{"op": "replace", "path": "/image", "value": "ubuntu"}]}
    patch_resp = await test_client.patch(f"/jobs/{job_id}", json=patch_op)
    response = patch_resp.json()
    assert patch_resp.status_code == 400
    assert response["detail"] == "Cannot patch field: image"


# TODO: add tests for stream jobs endpoint
# @pytest.mark.asyncio
# async def test_stream_jobs(test_client):
#     job_payload = {
#         "image": "busybox",
#         "command": ["sleep", "1"],
#         "cpu": "50m",
#         "memory": "32Mi",
#     }

#     async def listen_for_event():
#         async with test_client.stream("GET", "/stream/jobs") as response:
#             assert response.status_code == 200
#             async for line in response.aiter_lines():
#                 if not line or line.startswith(":"):
#                     continue
#                 if line.startswith("data:"):
#                     return json.loads(line[len("data: "):])
#         return None

#     listener_task = asyncio.create_task(listen_for_event())
#     await asyncio.sleep(3)
#     await test_client.post("/jobs", json=job_payload)

#     job_event = await asyncio.wait_for(listener_task, timeout=5.0)
#     assert job_event is not None
#     assert job_event.get("image") == job_payload.get("image")
#     assert job_event.get("status") == DEFAULT_JOB_STATUS
#     assert job_event.get("command") == job_payload.get("command")
#     assert job_event.get("cpu") == job_payload.get("cpu")
#     assert job_event.get("memory") == job_payload.get("memory")
