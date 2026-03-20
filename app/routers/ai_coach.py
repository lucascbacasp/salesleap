"""
POST /api/coach/chat     → chat libre con el coach IA (restringido al dominio del usuario)
POST /api/coach/evaluate → evaluar respuesta de quiz
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.models import (
    Lesson, LearningPath, Module,
    UserLessonProgress, UserPathProgress,
    ProgressStatus,
)
from app.schemas.ai_coach import (
    CoachChatRequest, CoachChatResponse,
    CoachEvaluateRequest, CoachEvaluateResponse,
)
from app.services import ai_coach

router = APIRouter()


async def _build_user_context(user, db) -> dict:
    """
    Construye el contexto del usuario para el coach:
    datos básicos + path actual + última lección completada.
    """
    # Path activo (in_progress más reciente)
    path_result = await db.execute(
        select(LearningPath)
        .join(UserPathProgress, UserPathProgress.path_id == LearningPath.id)
        .where(
            UserPathProgress.user_id == user.id,
            UserPathProgress.status == ProgressStatus.in_progress,
        )
        .order_by(UserPathProgress.started_at.desc())
        .limit(1)
    )
    active_path = path_result.scalar_one_or_none()

    # Última lección completada
    last_lesson_result = await db.execute(
        select(Lesson)
        .join(UserLessonProgress, UserLessonProgress.lesson_id == Lesson.id)
        .where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.status == ProgressStatus.completed,
        )
        .order_by(UserLessonProgress.completed_at.desc())
        .limit(1)
    )
    last_lesson = last_lesson_result.scalar_one_or_none()

    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "industry": user.industry or "",
        "total_xp": user.total_xp,
        "level": user.level,
        "streak_current": user.streak_current,
        "current_path": active_path.title if active_path else None,
        "last_lesson": last_lesson.title if last_lesson else None,
    }


@router.post("/chat", response_model=CoachChatResponse)
async def coach_chat(body: CoachChatRequest, user: CurrentUser, db: DB):
    try:
        user_context = await _build_user_context(user, db)
        response = await ai_coach.coach_chat(
            user_message=body.message,
            conversation_history=body.conversation_history,
            user_context=user_context,
        )
        return CoachChatResponse(response=response)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el coach: {str(e)}",
        )


@router.post("/evaluate", response_model=CoachEvaluateResponse)
async def evaluate_answer(body: CoachEvaluateRequest, user: CurrentUser, db: DB):
    try:
        user_context = await _build_user_context(user, db)
        result = await ai_coach.evaluate_answer(
            question=body.question,
            user_answer=body.user_answer,
            correct_answer=body.correct_answer,
            user_context=user_context,
        )
        return CoachEvaluateResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al evaluar respuesta: {str(e)}",
        )
