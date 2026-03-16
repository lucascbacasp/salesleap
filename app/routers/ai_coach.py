"""
POST /api/coach/chat     → chat libre con el coach IA
POST /api/coach/evaluate → evaluar respuesta de quiz
"""
from fastapi import APIRouter

from app.core.deps import DB, CurrentUser
from app.schemas.ai_coach import CoachChatRequest, CoachChatResponse, CoachEvaluateRequest, CoachEvaluateResponse
from app.services import ai_coach

router = APIRouter()


@router.post("/chat", response_model=CoachChatResponse)
async def coach_chat(body: CoachChatRequest, user: CurrentUser):
    user_context = {
        "name": user.full_name,
        "industry": user.industry or "ventas",
        "level": user.experience_level,
        "total_xp": user.total_xp,
        "streak": user.streak_current,
    }

    response = await ai_coach.coach_chat(
        user_message=body.message,
        conversation_history=body.conversation_history,
        user_context=user_context,
    )

    return CoachChatResponse(response=response)


@router.post("/evaluate", response_model=CoachEvaluateResponse)
async def evaluate_answer(body: CoachEvaluateRequest, user: CurrentUser):
    result = await ai_coach.evaluate_quiz_answer(
        question=body.question,
        user_answer=body.user_answer,
        correct_answer=body.correct_answer,
        industry=user.industry or "ventas",
        user_level=user.experience_level,
    )

    return CoachEvaluateResponse(**result)
