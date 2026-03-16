from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class BadgeOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    category: str
    rarity: str
    earned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    user_id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    total_xp: int
    level: int
    rank: int


class ProgressOut(BaseModel):
    user_id: UUID
    path_id: UUID
    status: str
    xp_earned: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
