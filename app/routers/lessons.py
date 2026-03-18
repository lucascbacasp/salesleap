"""
GET  /api/lessons/{id}          → detalle de una lección
POST /api/lessons/{id}/complete → completar lección + XP + gamification
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.models import Lesson, LessonType, UserLessonProgress, ProgressStatus
from app.schemas.lessons import CompleteLessonRequest, CompleteLessonResponse, LessonOut
from app.services.gamification import award_xp, check_badges, update_streak

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.is_published.is_(True))
    )
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leccion no encontrada")

    # Check if user has already completed this lesson
    progress_result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id == lesson_id,
            UserLessonProgress.status == ProgressStatus.completed,
        )
    )
    user_completed = progress_result.scalar_one_or_none() is not None

    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "title": lesson.title,
        "lesson_type": lesson.lesson_type.value,
        "content": lesson.content,
        "order_index": lesson.order_index,
        "xp_reward": lesson.xp_reward,
        "estimated_minutes": lesson.estimated_minutes,
        "user_completed": user_completed,
    }


@router.post("/{lesson_id}/complete", response_model=CompleteLessonResponse)
async def complete_lesson(lesson_id: UUID, body: CompleteLessonRequest, db: DB, user: CurrentUser):
    # Verificar que la lección existe
    lesson_result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leccion no encontrada")

    # Buscar o crear progreso
    progress_result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id == lesson_id,
        )
    )
    progress = progress_result.scalar_one_or_none()

    if progress and progress.status == ProgressStatus.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leccion ya completada")

    if progress is None:
        progress = UserLessonProgress(user_id=user.id, lesson_id=lesson_id)
        db.add(progress)

    progress.status = ProgressStatus.completed
    progress.score = body.score
    progress.time_spent_sec = body.time_spent_sec
    progress.attempts = (progress.attempts or 0) + 1
    progress.completed_at = datetime.now(timezone.utc)

    # Roleplay: evaluate with AI Coach
    ai_feedback = None
    if lesson.lesson_type == LessonType.roleplay and body.answers:
        try:
            from app.services.ai_coach import evaluate_quiz_answer

            answer_data = body.answers[0]
            scenario = answer_data.get("question", "")
            user_response = answer_data.get("answer", "")

            # Build ideal response hint from lesson content
            content = lesson.content or {}
            objective = content.get("objective", "Responder de forma profesional y persuasiva")
            criteria = content.get("evaluation_criteria", [])
            ideal_hint = f"Objetivo: {objective}. Criterios de evaluación: {', '.join(criteria)}" if criteria else objective

            eval_result = await evaluate_quiz_answer(
                question=scenario,
                user_answer=user_response,
                correct_answer=ideal_hint,
                industry=user.industry or "ventas",
                user_level=user.experience_level or "beginner",
            )

            ai_feedback = eval_result.get("feedback", "")
            tip = eval_result.get("tip", "")
            if tip:
                ai_feedback = f"{ai_feedback}\n\n💡 Tip: {tip}"

            ai_score = eval_result.get("score", 75)
            progress.score = ai_score
            progress.ai_feedback = ai_feedback

        except Exception as e:
            logger.warning(f"AI evaluation failed for roleplay: {e}")
            progress.ai_feedback = None

    # Dar XP
    xp = lesson.xp_reward
    await award_xp(db, user, xp)

    # Actualizar streak
    streak = await update_streak(db, user, xp)

    # Verificar badges
    new_badges = await check_badges(db, user, lesson=lesson, score=body.score, time_spent=body.time_spent_sec)

    await db.commit()

    return CompleteLessonResponse(
        xp_earned=xp,
        total_xp=user.total_xp,
        new_level=user.level,
        streak_current=streak,
        badges_earned=[b.name for b in new_badges],
        ai_feedback=progress.ai_feedback,
    )
