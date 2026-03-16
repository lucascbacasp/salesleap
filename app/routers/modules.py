"""
GET /api/modules/{id} → detalle de un módulo con sus lecciones
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DB, CurrentUser
from app.models.models import Module
from app.schemas.paths import ModuleOut

router = APIRouter()


@router.get("/{module_id}")
async def get_module(module_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(
        select(Module)
        .where(Module.id == module_id)
        .options(selectinload(Module.lessons))
    )
    module = result.scalar_one_or_none()
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modulo no encontrado")

    return {
        "id": module.id,
        "path_id": module.path_id,
        "title": module.title,
        "description": module.description,
        "order_index": module.order_index,
        "xp_reward": module.xp_reward,
        "estimated_minutes": module.estimated_minutes,
        "lessons": [
            {
                "id": l.id,
                "title": l.title,
                "lesson_type": l.lesson_type.value,
                "order_index": l.order_index,
                "xp_reward": l.xp_reward,
                "estimated_minutes": l.estimated_minutes,
            }
            for l in module.lessons
        ],
    }
