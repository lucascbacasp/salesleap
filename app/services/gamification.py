"""
SalesLeap — Gamification service
XP, badges, streaks
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Badge,
    DailyStreak,
    Lesson,
    User,
    UserBadge,
    UserLessonProgress,
    ProgressStatus,
)

XP_PER_LEVEL = 500  # cada 500 XP sube un nivel


async def award_xp(db: AsyncSession, user: User, xp: int) -> None:
    user.total_xp += xp
    user.level = (user.total_xp // XP_PER_LEVEL) + 1
    user.last_activity_at = datetime.now(timezone.utc)


async def update_streak(db: AsyncSession, user: User, xp_earned: int) -> int:
    today = date.today()

    # Buscar o crear registro del día
    result = await db.execute(
        select(DailyStreak).where(DailyStreak.user_id == user.id, DailyStreak.activity_date == today)
    )
    streak_record = result.scalar_one_or_none()

    if streak_record is None:
        streak_record = DailyStreak(user_id=user.id, activity_date=today, xp_earned=xp_earned, lessons_done=1)
        db.add(streak_record)

        # Verificar si ayer hubo actividad para mantener racha
        yesterday = date.fromordinal(today.toordinal() - 1)
        yesterday_result = await db.execute(
            select(DailyStreak).where(DailyStreak.user_id == user.id, DailyStreak.activity_date == yesterday)
        )
        had_yesterday = yesterday_result.scalar_one_or_none() is not None

        if had_yesterday:
            user.streak_current += 1
        else:
            user.streak_current = 1

        if user.streak_current > user.streak_max:
            user.streak_max = user.streak_current
    else:
        streak_record.xp_earned += xp_earned
        streak_record.lessons_done += 1

    return user.streak_current


async def check_badges(
    db: AsyncSession,
    user: User,
    lesson: Lesson | None = None,
    score: float | None = None,
    time_spent: int | None = None,
) -> list[Badge]:
    """Verifica si el usuario ganó badges nuevos. Retorna los badges recién ganados."""
    new_badges: list[Badge] = []

    # Contar lecciones completadas
    lesson_count_result = await db.execute(
        select(func.count()).where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.status == ProgressStatus.completed,
        )
    )
    lessons_completed = lesson_count_result.scalar()

    # Obtener badges que el usuario aún no tiene
    existing_badge_ids = await db.execute(
        select(UserBadge.badge_id).where(UserBadge.user_id == user.id)
    )
    owned_ids = {row[0] for row in existing_badge_ids}

    all_badges_result = await db.execute(select(Badge))
    all_badges = all_badges_result.scalars().all()

    for badge in all_badges:
        if badge.id in owned_ids:
            continue

        criteria = badge.criteria or {}
        earned = False

        if "lessons_completed" in criteria and lessons_completed >= criteria["lessons_completed"]:
            earned = True
        elif "streak_days" in criteria and user.streak_current >= criteria["streak_days"]:
            earned = True
        elif "quiz_score" in criteria and score is not None and score >= criteria["quiz_score"]:
            earned = True
        elif "onboarding_done" in criteria and user.onboarding_done:
            earned = True
        elif "lesson_under_seconds" in criteria and time_spent is not None and time_spent <= criteria["lesson_under_seconds"]:
            earned = True
        elif "onboarding_lesson" in criteria and lesson is not None and lesson.title.lower() == criteria["onboarding_lesson"].lower():
            earned = True

        if earned:
            user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
            db.add(user_badge)
            # Bonus XP por badge
            if badge.xp_bonus:
                await award_xp(db, user, badge.xp_bonus)
            new_badges.append(badge)

    return new_badges
