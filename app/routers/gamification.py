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
    """Returns ALL badges in the system, with earned=True/False for the current user."""
    # Get all system badges
    all_badges_result = await db.execute(select(Badge).order_by(Badge.category, Badge.name))
    all_badges = all_badges_result.scalars().all()

    # Get badges already earned by the user
    earned_result = await db.execute(
        select(UserBadge)
        .where(UserBadge.user_id == user.id)
        .options(selectinload(UserBadge.badge))
    )
    earned_map = {ub.badge_id: ub.earned_at for ub in earned_result.scalars().all()}

    return [
        BadgeOut(
            id=b.id,
            name=b.name,
            description=b.description,
            icon=b.icon,
            category=b.category,
            rarity=b.rarity,
            xp_bonus=b.xp_bonus,
            earned=b.id in earned_map,
            earned_at=earned_map.get(b.id),
        )
        for b in all_badges
    ]
