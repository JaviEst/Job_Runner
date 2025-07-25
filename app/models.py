from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, conlist


class JobCreate(BaseModel):
    image: str = Field(..., max_length=255)
    command: conlist(str, min_length=1)
    cpu: str | None = Field(None, max_length=32)
    memory: str | None = Field(None, max_length=32)


class JobRead(BaseModel):
    id: UUID
    image: str
    command: list[str]
    cpu: str | None
    memory: str | None
    status: str
    message: str | None
    created_at: datetime
    updated_at: datetime
