"""
SalesLeap — Document processing service
Procesa PDFs empresariales → genera módulos con Claude
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CompanyDocument, LearningPath, Lesson, Module
from app.services import ai_coach


async def process_document(db: AsyncSession, document_id: UUID) -> None:
    """Procesa un documento y genera un módulo de aprendizaje."""
    result = await db.execute(select(CompanyDocument).where(CompanyDocument.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        return

    doc.status = "processing"
    await db.commit()

    try:
        # TODO: descargar y extraer texto del PDF desde S3 (doc.file_url)
        # Por ahora se usa source_text placeholder
        document_text = f"Contenido del documento: {doc.title}"

        # Obtener industria de la empresa
        company = doc.company
        industry = company.industry if company else "ventas"

        # Generar módulo con Claude
        module_data = await ai_coach.generate_module_from_document(
            document_text=document_text,
            industry=industry,
            module_title=doc.title,
        )

        # Crear o reusar learning path para docs de la empresa
        path_result = await db.execute(
            select(LearningPath).where(
                LearningPath.company_id == doc.company_id,
                LearningPath.title.ilike(f"%{industry}%custom%"),
            )
        )
        path = path_result.scalar_one_or_none()

        if path is None:
            path = LearningPath(
                title=f"Capacitación {industry} - {company.name if company else 'Custom'}",
                description="Módulos generados a partir de documentos de la empresa",
                industry=industry,
                company_id=doc.company_id,
                is_published=True,
            )
            db.add(path)
            await db.flush()

        # Crear módulo
        module = Module(
            path_id=path.id,
            title=doc.title,
            description=module_data.get("description", ""),
            source_document=doc.file_url,
            is_published=True,
        )
        db.add(module)
        await db.flush()

        # Crear lecciones
        for idx, lesson_data in enumerate(module_data.get("lessons", [])):
            lesson = Lesson(
                module_id=module.id,
                title=lesson_data["title"],
                lesson_type=lesson_data.get("type", "theory"),
                content=lesson_data.get("content", {}),
                order_index=idx,
                xp_reward=lesson_data.get("xp_reward", 20),
                estimated_minutes=lesson_data.get("estimated_minutes", 5),
                is_published=True,
            )
            db.add(lesson)

        doc.status = "done"
        doc.generated_path_id = path.id
        doc.processed_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception:
        doc.status = "error"
        await db.commit()
        raise
