import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app import db
from app.main import job_runner_app


@pytest.fixture(scope="session")
def test_db_file():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    yield f"sqlite:///{db_path}"
    os.close(db_fd)
    os.remove(db_path)


@pytest.fixture(scope="function")
def test_client(test_db_file):
    test_engine = create_engine(
        test_db_file, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    db.engine = test_engine
    db.metadata.bind = test_engine
    db.metadata.drop_all(test_engine)
    db.metadata.create_all(test_engine)

    with TestClient(job_runner_app) as client:
        yield client


def test_create_job(test_client):
    job_payload = {
        "image": "alpine",
        "command": ["echo", "hello world"],
        "cpu": "100m",
        "memory": "64Mi",
    }

    response = test_client.post("/jobs", json=job_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["image"] == "alpine"
    assert data["status"] == "queued"
    assert data["command"] == ["echo", "hello world"]


def test_create_job_missing_fields(test_client):
    response = test_client.post("/jobs", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_job_invalid_command_type(test_client):
    payload = {
        "image": "alpine",
        "command": "echo hello",  # should be list, not string
        "cpu": "100m",
        "memory": "128Mi",
    }
    response = test_client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_create_job_empty_command(test_client):
    payload = {
        "image": "alpine",
        "command": [],
        "cpu": "100m",
        "memory": "128Mi",
    }
    response = test_client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_create_job_field_length_exceeded(test_client):
    payload = {
        "image": "a" * 300,
        "command": ["echo", "test"],
        "cpu": "100m",
        "memory": "64Mi",
    }
    response = test_client.post("/jobs", json=payload)
    assert response.status_code == 422


def test_get_job_by_id(test_client):
    job_payload = {"image": "ubuntu", "command": ["ls", "/"], "cpu": "150m", "memory": "128Mi"}
    create_resp = test_client.post("/jobs", json=job_payload)
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    response = test_client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["image"] == "ubuntu"


def test_get_job_not_found(test_client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = test_client.get(f"/jobs/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_get_job_invalid_uuid_format(test_client):
    response = test_client.get("/jobs/not-a-valid-uuid")
    assert response.status_code == 422  # Pydantic validation
    assert "detail" in response.json()


def test_list_jobs(test_client):
    job_payload = {
        "image": "busybox",
        "command": ["sleep", "1"],
        "cpu": "50m",
        "memory": "32Mi",
    }
    test_client.post("/jobs", json=job_payload)

    response = test_client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1
    assert any(job["image"] == "busybox" for job in jobs)
