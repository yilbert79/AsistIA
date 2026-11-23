from typing import Literal
from pydantic import BaseModel, EmailStr, Field, model_validator

class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, min_length=8, max_length=64)
    message: str = Field(min_length=2, max_length=2000)
    department_id: int | None = None

class ChatResponse(BaseModel):
    session_id: str
    message_id: int
    answer: str
    status: str
    requires_human: bool
    case_id: int | None = None
    claim_token: str | None = None
    department_id: int
    department_name: str
    department_email: str | None = None
    department_phone: str
    department_whatsapp: str
    department_contact_url: str

class ContactInput(BaseModel):
    name: str | None = Field(default=None, max_length=140)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    consent: bool

    @model_validator(mode="after")
    def validate_contact(self):
        if not self.consent:
            raise ValueError("Debes aceptar el uso de tus datos para solicitar seguimiento.")
        if bool(self.email) == bool(self.phone):
            raise ValueError("Ingresa un correo electrónico o un número de teléfono.")
        return self

class PublicContactRequest(BaseModel):
    claim_token: str = Field(min_length=20, max_length=100)
    contact: ContactInput

class ClaimRequest(BaseModel):
    claim_token: str = Field(min_length=20, max_length=100)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=140)
    password: str = Field(min_length=10, max_length=200)
    role: Literal["DIVISION_AGENT", "DIVISION_LEADER", "SUPERADMIN"]
    department_id: int | None = None

    @model_validator(mode="after")
    def require_department(self):
        if self.role != "SUPERADMIN" and self.department_id is None:
            raise ValueError("El personal de división debe tener una dependencia asignada.")
        return self

class HumanResponseInput(BaseModel):
    answer: str = Field(min_length=2, max_length=5000)

class ReviewInput(BaseModel):
    decision: Literal["APPROVED", "CORRECTED", "REJECTED"]
    corrected_answer: str | None = Field(default=None, max_length=5000)
    comment: str | None = Field(default=None, max_length=2000)

class CaseOutput(BaseModel):
    id: int
    question: str
    ai_answer: str | None
    status: str
    topic: str
    department: str
    created_at: str
    contact_email: str | None
    contact_phone: str | None

class KnowledgeArticleInput(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    answer: str = Field(min_length=2, max_length=10000)
    source: str = Field(min_length=2, max_length=240)
    department_id: int | None = None

class KnowledgeArticleUpdate(BaseModel):
    question: str | None = Field(default=None, min_length=2, max_length=2000)
    answer: str | None = Field(default=None, min_length=2, max_length=10000)
    source: str | None = Field(default=None, min_length=2, max_length=240)
    department_id: int | None = None
    active: bool | None = None
