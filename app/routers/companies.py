"""
CRUD empresas + subida de documentos
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.core.deps import DB, CurrentUser
from app.models.models import Company, CompanyDocument
from app.schemas.companies import CompanyCreate, CompanyOut, DocumentUploadResponse

router = APIRouter()


@router.get("/", response_model=list[CompanyOut])
async def list_companies(db: DB, user: CurrentUser):
    result = await db.execute(select(Company).where(Company.is_active.is_(True)))
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    return company


@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(body: CompanyCreate, db: DB, user: CurrentUser):
    company = Company(**body.model_dump())
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.post("/{company_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(company_id: UUID, file: UploadFile, db: DB, user: CurrentUser):
    # Verificar que la empresa existe
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")

    # TODO: subir archivo a S3 y obtener URL
    file_url = f"s3://salesleap-docs/{company_id}/{file.filename}"

    doc = CompanyDocument(
        company_id=company_id,
        uploaded_by=user.id,
        title=file.filename or "Documento",
        file_url=file_url,
        file_type=file.content_type,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # TODO: disparar tarea Celery para procesar el documento
    # process_document.delay(str(doc.id))

    return DocumentUploadResponse(
        document_id=doc.id,
        status="pending",
        message="Documento subido. Se procesara en breve.",
    )
