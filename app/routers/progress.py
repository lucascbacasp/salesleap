"""
GET /api/progress/me              → progreso del usuario actual
GET /api/progress/mission         → misión diaria (3 lecciones/día)
GET /api/progress/company/{id}    → progreso de la empresa
"""
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import DB, CurrentUser
from app.models.models import (
    DailyStreak, LearningPath, Module, Lesson, OnboardingResult,
    User, UserLessonProgress, UserPathProgress, ProgressStatus,
)

router = APIRouter()

DAILY_MISSION_TARGET = 3


@router.get("/me")
async def get_my_progress(db: DB, user: CurrentUser):
    result = await db.execute(
        select(UserLessonProgress).where(UserLessonProgress.user_id == user.id)
    )
    progress_list = result.scalars().all()

    completed = [p for p in progress_list if p.status == ProgressStatus.completed]
    in_progress = [p for p in progress_list if p.status == ProgressStatus.in_progress]

    return {
        "total_lessons_started": len(progress_list),
        "total_lessons_completed": len(completed),
        "total_lessons_in_progress": len(in_progress),
        "total_xp": user.total_xp,
        "level": user.level,
        "streak": user.streak_current,
    }


@router.get("/mission")
async def get_daily_mission(db: DB, user: CurrentUser):
    """Returns today's daily mission status + the user's assigned path."""
    today = date.today()

    # Get today's lessons done from daily_streaks
    streak_result = await db.execute(
        select(DailyStreak).where(
            DailyStreak.user_id == user.id,
            DailyStreak.activity_date == today,
        )
    )
    streak = streak_result.scalar_one_or_none()
    lessons_today = streak.lessons_done if streak else 0

    # Get the user's assigned path (most recent in_progress or last started)
    path_progress_result = await db.execute(
        select(UserPathProgress).where(
            UserPathProgress.user_id == user.id,
        ).order_by(UserPathProgress.started_at.desc()).limit(1)
    )
    path_progress = path_progress_result.scalar_one_or_none()

    assigned_path = None
    next_lesson = None

    if path_progress:
        # Get path details
        path_result = await db.execute(
            select(LearningPath).where(LearningPath.id == path_progress.path_id)
        )
        path = path_result.scalar_one_or_none()

        if path:
            # Count total lessons in path
            total_result = await db.execute(
                select(func.count())
                .select_from(Lesson)
                .join(Module, Lesson.module_id == Module.id)
                .where(Module.path_id == path.id, Lesson.is_published.is_(True))
            )
            total_lessons = total_result.scalar() or 0

            # Count completed lessons in this path
            completed_result = await db.execute(
                select(func.count())
                .select_from(UserLessonProgress)
                .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
                .join(Module, Lesson.module_id == Module.id)
                .where(
                    Module.path_id == path.id,
                    UserLessonProgress.user_id == user.id,
                    UserLessonProgress.status == ProgressStatus.completed,
                )
            )
            completed_lessons = completed_result.scalar() or 0

            assigned_path = {
                "id": str(path.id),
                "title": path.title,
                "description": path.description,
                "level": path.level,
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "progress_pct": round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0),
            }

            # Find the next uncompleted lesson
            completed_ids_result = await db.execute(
                select(UserLessonProgress.lesson_id).where(
                    UserLessonProgress.user_id == user.id,
                    UserLessonProgress.status == ProgressStatus.completed,
                )
            )
            completed_ids = set(completed_ids_result.scalars().all())

            next_result = await db.execute(
                select(Lesson)
                .join(Module, Lesson.module_id == Module.id)
                .where(
                    Module.path_id == path.id,
                    Lesson.is_published.is_(True),
                )
                .order_by(Module.order_index, Lesson.order_index)
            )
            all_lessons = next_result.scalars().all()
            for l in all_lessons:
                if l.id not in completed_ids:
                    next_lesson = {
                        "id": str(l.id),
                        "title": l.title,
                        "lesson_type": l.lesson_type.value,
                        "xp_reward": l.xp_reward,
                        "estimated_minutes": l.estimated_minutes,
                    }
                    break

    completed = lessons_today >= DAILY_MISSION_TARGET

    return {
        "target": DAILY_MISSION_TARGET,
        "completed_today": min(lessons_today, DAILY_MISSION_TARGET),
        "is_completed": completed,
        "assigned_path": assigned_path,
        "next_lesson": next_lesson,
    }


@router.get("/company/{company_id}")
async def get_company_progress(company_id: UUID, db: DB, user: CurrentUser):
    users_result = await db.execute(
        select(User).where(User.company_id == company_id, User.is_active.is_(True))
    )
    users = users_result.scalars().all()
    user_ids = [u.id for u in users]

    if not user_ids:
        return {"company_id": str(company_id), "total_users": 0, "stats": []}

    stats = []
    for u in users:
        count_result = await db.execute(
            select(func.count()).where(
                UserLessonProgress.user_id == u.id,
                UserLessonProgress.status == ProgressStatus.completed,
            )
        )
        stats.append({
            "user_id": str(u.id),
            "full_name": u.full_name,
            "total_xp": u.total_xp,
            "level": u.level,
            "lessons_completed": count_result.scalar(),
        })

    return {
        "company_id": str(company_id),
        "total_users": len(users),
        "stats": sorted(stats, key=lambda x: x["total_xp"], reverse=True),
    }
