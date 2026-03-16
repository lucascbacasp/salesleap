"""
GET /api/gamification/leaderboard → ranking
GET /api/gamification/badges      → badges del usuario
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.models import Badge, User, UserBadge
from app.schemas.gamification import BadgeOut, LeaderboardEntry

router = APIRouter()


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    db: DB,
    user: CurrentUser,
    company_id: Optional[UUID] = Query(None),
    limit: int = Query(20, le=100),
):
    query = select(User).where(User.is_active.is_(True)).order_by(User.total_xp.desc()).limit(limit)

    if company_id:
        query = query.where(User.company_id == company_id)

    result = await db.execute(query)
    users = result.scalars().all()

    return [
        LeaderboardEntry(
            user_id=u.id,
            full_name=u.full_name,
            avatar_url=u.avatar_url,
            total_xp=u.total_xp,
            level=u.level,
            rank=idx + 1,
        )
        for idx, u in enumerate(users)
    ]


@router.get("/badges", response_model=List[BadgeOut])
async def get_my_badges(db: DB, user: CurrentUser):
    result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user.id)
        .options(selectinload(UserBadge.badge))
    )
    user_badges = result.scalars().all()

    return [
        BadgeOut(
            id=ub.badge.id,
            name=ub.badge.name,
            description=ub.badge.description,
            icon=ub.badge.icon,
            category=ub.badge.category,
            rarity=ub.badge.rarity,
            earned_at=ub.earned_at,
        )
        for ub in user_badges
    ]
