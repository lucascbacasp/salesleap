from typing import Dict, List

from pydantic import BaseModel


class CoachChatRequest(BaseModel):
    message: str
    conversation_history: List[Dict] = []


class CoachChatResponse(BaseModel):
    response: str


class CoachEvaluateRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str


class CoachEvaluateResponse(BaseModel):
    is_correct: bool
    is_partial: bool
    score: float
    feedback: str
    tip: str
