"""
GET /api/users/me          → perfil del usuario actual
PUT /api/users/me          → actualizar perfil
GET /api/users/{id}/stats  → estadísticas de un usuario
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.deps import DB, CurrentUser
from app.models.models import User, UserBadge, UserLessonProgress, ProgressStatus
from app.schemas.users import UserOut, UserStats, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUser):
    return user


@router.put("/me", response_model=UserOut)
async def update_me(body: UserUpdate, db: DB, user: CurrentUser):
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    if body.industry is not None:
        user.industry = body.industry
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(user_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    lessons_result = await db.execute(
        select(func.count()).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == ProgressStatus.completed,
        )
    )
    badges_result = await db.execute(
        select(func.count()).where(UserBadge.user_id == user_id)
    )

    return UserStats(
        total_xp=target.total_xp,
        level=target.level,
        streak_current=target.streak_current,
        streak_max=target.streak_max,
        lessons_completed=lessons_result.scalar(),
        badges_count=badges_result.scalar(),
    )
