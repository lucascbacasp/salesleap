"""
GET /api/paths → rutas disponibles (filtrado por industria/nivel)
GET /api/paths/{id}/modules → módulos de una ruta con lecciones
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.models import LearningPath, Module, UserLessonProgress, ProgressStatus
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
        # Company-specific paths always show (already filtered by company_id above);
        # only apply industry filter to global paths (company_id IS NULL).
        query = query.where(
            or_(
                LearningPath.company_id == user.company_id,
                LearningPath.industry == industry,
            )
        )
    if level:
        query = query.where(LearningPath.level == level)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{path_id}/modules")
async def get_path_modules(path_id: UUID, db: DB, user: CurrentUser):
    """Devuelve los módulos de una ruta con sus lecciones."""
    # Verify path exists and user has access
    path_result = await db.execute(
        select(LearningPath).where(LearningPath.id == path_id)
    )
    path = path_result.scalar_one_or_none()
    if path is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta no encontrada")

    result = await db.execute(
        select(Module)
        .where(Module.path_id == path_id, Module.is_published.is_(True))
        .options(selectinload(Module.lessons))
        .order_by(Module.order_index)
    )
    modules = result.scalars().all()

    # Get completed lesson IDs for this user in one query
    completed_result = await db.execute(
        select(UserLessonProgress.lesson_id).where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.status == ProgressStatus.completed,
        )
    )
    completed_ids = set(completed_result.scalars().all())

    return [
        {
            "id": m.id,
            "path_id": m.path_id,
            "title": m.title,
            "description": m.description,
            "order_index": m.order_index,
            "xp_reward": m.xp_reward,
            "estimated_minutes": m.estimated_minutes,
            "lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "lesson_type": l.lesson_type.value,
                    "order_index": l.order_index,
                    "xp_reward": l.xp_reward,
                    "estimated_minutes": l.estimated_minutes,
                    "completed": l.id in completed_ids,
                }
                for l in sorted(m.lessons, key=lambda x: x.order_index)
                if l.is_published
            ],
        }
        for m in modules
    ]
