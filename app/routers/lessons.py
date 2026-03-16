"""
GET  /api/lessons/{id}          → detalle de una lección
POST /api/lessons/{id}/complete → completar lección + XP + gamification
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.models import Lesson, UserLessonProgress, ProgressStatus
from app.schemas.lessons import CompleteLessonRequest, CompleteLessonResponse, LessonOut
from app.services.gamification import award_xp, check_badges, update_streak

router = APIRouter()


@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.is_published.is_(True))
    )
    lesson = result.scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leccion no encontrada")
    return lesson


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
    progress.attempts += 1
    progress.completed_at = datetime.now(timezone.utc)

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
