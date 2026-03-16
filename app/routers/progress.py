"""
GET /api/progress/me              → progreso del usuario actual
GET /api/progress/company/{id}    → progreso de la empresa
"""
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import DB, CurrentUser
from app.models.models import User, UserLessonProgress, ProgressStatus

router = APIRouter()


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


@router.get("/company/{company_id}")
async def get_company_progress(company_id: UUID, db: DB, user: CurrentUser):
    # Usuarios de la empresa
    users_result = await db.execute(
        select(User).where(User.company_id == company_id, User.is_active.is_(True))
    )
    users = users_result.scalars().all()
    user_ids = [u.id for u in users]

    if not user_ids:
        return {"company_id": str(company_id), "total_users": 0, "stats": []}

    # Contar lecciones completadas por usuario
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
