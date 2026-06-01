import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

CaseRole = Literal["responsavel", "investigador", "supervisor", "consultor"]


class CaseMemberAssign(BaseModel):
    user_id: uuid.UUID
    role: CaseRole


class CaseMemberResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    role: CaseRole
    assigned_by: uuid.UUID
    assigned_at: datetime
    removed_at: datetime | None
    removed_by: uuid.UUID | None


class CaseMemberRemove(BaseModel):
    user_id: uuid.UUID
