from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    company_id: Optional[UUID] = None
    industry: Optional[str] = None
    experience_level: str
    total_xp: int
    level: int
    streak_current: int
    streak_max: int
    onboarding_done: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    industry: Optional[str] = None


class UserStats(BaseModel):
    total_xp: int
    level: int
    streak_current: int
    streak_max: int
    lessons_completed: int
    badges_count: int
