"""
GET /api/paths → rutas disponibles (filtrado por industria/nivel)
"""
from typing import List, Optional

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.models import LearningPath
from app.schemas.paths import PathOut

router = APIRouter()


@router.get("/", response_model=List[PathOut])
async def list_paths(
    db: DB,
    user: CurrentUser,
    industry: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
):
    query = select(LearningPath).where(
        LearningPath.is_published.is_(True),
        # Paths globales o de la empresa del usuario
        (LearningPath.company_id.is_(None)) | (LearningPath.company_id == user.company_id),
    ).order_by(LearningPath.order_index)

    if industry:
        query = query.where(LearningPath.industry == industry)
    if level:
        query = query.where(LearningPath.level == level)

    result = await db.execute(query)
    return result.scalars().all()
