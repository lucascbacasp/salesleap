from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: UUID
    name: str
    slug: str
    email_domain: Optional[str] = None
    logo_url: Optional[str] = None
    industry: str
    plan: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    name: str
    slug: str
    email_domain: Optional[str] = None
    industry: str


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str
    message: str
