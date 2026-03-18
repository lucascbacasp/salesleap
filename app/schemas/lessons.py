from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class LessonOut(BaseModel):
    id: UUID
    module_id: UUID
    title: str
    lesson_type: str
    content: dict
    order_index: int
    xp_reward: int
    estimated_minutes: int
    user_completed: bool = False

    model_config = {"from_attributes": True}


class CompleteLessonRequest(BaseModel):
    score: Optional[float] = None
    time_spent_sec: int = 0
    answers: Optional[List[Dict]] = None


class CompleteLessonResponse(BaseModel):
    xp_earned: int
    total_xp: int
    new_level: int
    streak_current: int
    badges_earned: List[str]
    ai_feedback: Optional[str] = None
