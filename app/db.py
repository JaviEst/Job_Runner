import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    insert,
    select,
)

from app.config import settings
from app.constants import DEFAULT_CPU, DEFAULT_MEM

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo="debug",
    pool_size=15,
    pool_timeout=30,
)
metadata = MetaData()

jobs = Table(
    "jobs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("image", String(255), nullable=False),
    Column("command", JSON, nullable=False),
    Column("cpu", String(32), default=DEFAULT_CPU),
    Column("memory", String(32), default=DEFAULT_MEM),
    Column("status", String(32), nullable=False, default="queued"),
    Column("message", Text),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)


def init_db() -> None:
    metadata.create_all(engine)


def create_job(data: dict[str, Any]) -> dict[str, Any] | None:
    now = datetime.utcnow()
    job_id = str(uuid.uuid4())
    stmt = insert(jobs).values(
        id=job_id,
        image=data.get("image"),
        command=data.get("command"),
        cpu=data.get("cpu") or DEFAULT_CPU,
        memory=data.get("memory") or DEFAULT_MEM,
        status="queued",
        message=None,
        created_at=now,
        updated_at=now,
    )
    with engine.begin() as conn:
        conn.execute(stmt)
    return get_job(job_id)


def get_job(job_id: str) -> dict[str, Any] | None:
    stmt = select(jobs).where(jobs.c.id == job_id)
    with engine.begin() as conn:
        result = conn.execute(stmt).first()
    if result:
        return dict(result._mapping)
    return None


def list_jobs(limit: int = 100) -> list[dict[str, Any]]:
    stmt = select(jobs).order_by(jobs.c.created_at.desc()).limit(limit)
    with engine.begin() as conn:
        result = conn.execute(stmt).fetchall()
    return [dict(row._mapping) for row in result]
