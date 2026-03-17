from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class OnboardingAnswer(BaseModel):
    question: str
    answer: str


class OnboardingQuizRequest(BaseModel):
    industry: str
    experience_years: int
    answers: List[OnboardingAnswer]


class AssignedPathOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    level: str
    xp_reward: int
    total_modules: int = 0
    total_lessons: int = 0

    model_config = {"from_attributes": True}


class OnboardingQuizResponse(BaseModel):
    level: str
    strengths: List[str]
    gaps: List[str]
    priority_topics: List[str]
    explanation: str
    quick_win_tip: str
    suggested_path_ids: List[UUID]
    assigned_path: Optional[AssignedPathOut] = None
