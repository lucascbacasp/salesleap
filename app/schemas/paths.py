from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PathOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    industry: str
    level: str
    company_id: Optional[UUID] = None
    cover_url: Optional[str] = None
    xp_reward: int
    order_index: int
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: UUID
    path_id: UUID
    title: str
    description: Optional[str] = None
    order_index: int
    xp_reward: int
    estimated_minutes: int

    model_config = {"from_attributes": True}
