import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ForensicDomain = Literal["digital", "medico_legal", "financeiro"]
CaseStatus = Literal["aberto", "em_investigacao", "em_revisao", "fechado", "arquivado"]
ConfidentialityLevel = Literal["normal", "reservado", "confidencial", "secreto"]


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    forensic_domain: ForensicDomain
    confidentiality: ConfidentialityLevel = "normal"
    tags: list[str] = Field(default_factory=list)
    domain_metadata: dict = Field(default_factory=dict)


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    confidentiality: ConfidentialityLevel | None = None
    tags: list[str] | None = None
    domain_metadata: dict | None = None


class CaseTransitionRequest(BaseModel):
    to_status: CaseStatus
    justification: str | None = Field(default=None, max_length=2000)


class CaseResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    case_number: str
    title: str
    description: str | None
    forensic_domain: ForensicDomain
    status: CaseStatus
    confidentiality: ConfidentialityLevel
    owner_id: uuid.UUID
    tags: list[str]
    domain_metadata: dict
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    archived_at: datetime | None


class CaseListFilters(BaseModel):
    status: CaseStatus | None = None
    forensic_domain: ForensicDomain | None = None
    owner_id: uuid.UUID | None = None
    search: str | None = Field(default=None, max_length=500)
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
