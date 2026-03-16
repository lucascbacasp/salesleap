from typing import List
from uuid import UUID

from pydantic import BaseModel


class OnboardingAnswer(BaseModel):
    question: str
    answer: str


class OnboardingQuizRequest(BaseModel):
    industry: str
    experience_years: int
    answers: List[OnboardingAnswer]


class OnboardingQuizResponse(BaseModel):
    level: str
    strengths: List[str]
    gaps: List[str]
    priority_topics: List[str]
    explanation: str
    quick_win_tip: str
    suggested_path_ids: List[UUID]
