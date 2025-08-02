from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
    insert,
    update,
    select,
)

from sqlalchemy.ext.asyncio import create_async_engine


from app.config import settings
from app.constants import DEFAULT_CPU, DEFAULT_MEM

engine = create_async_engine(
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


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


async def create_job(data: dict[str, Any]) -> None:
    stmt = insert(jobs).values(
        id=data.get("id"),
        image=data.get("image"),
        command=data.get("command"),
        cpu=data.get("cpu") or DEFAULT_CPU,
        memory=data.get("memory") or DEFAULT_MEM,
        status=data.get("status"),
        message=data.get("message"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )
    async with engine.begin() as conn:
        await conn.execute(stmt)
    return None


async def update_job(job_id: str, patched_job_dict: dict[str, Any]) -> None:
    stmt = update(jobs).where(jobs.c.id == job_id).values(**patched_job_dict)
    async with engine.begin() as conn:
        await conn.execute(stmt)
    return None


async def list_jobs(limit: int = 100) -> list[dict[str, Any]]:
    stmt = select(jobs).order_by(jobs.c.created_at.desc()).limit(limit)
    async with engine.begin() as conn:
        result = await conn.execute(stmt)
        rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


async def get_job(job_id: str) -> dict[str, Any] | None:
    stmt = select(jobs).where(jobs.c.id == job_id)
    async with engine.begin() as conn:
        result = await conn.execute(stmt)
        row = result.first()
    if row:
        return dict(row._mapping)
    return None
