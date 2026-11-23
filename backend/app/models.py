from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Department(Base):
    __tablename__ = "dependencias"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(180), default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    context: Mapped[str] = mapped_column(Text, default="", nullable=False)

class AdminUser(Base):
    __tablename__ = "usuarios_admin"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(140), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(180), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="DIVISION_AGENT", nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("dependencias.id", ondelete="SET NULL"))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    department: Mapped[Department | None] = relationship()

class Conversation(Base):
    __tablename__ = "conversaciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

class Contact(Base):
    __tablename__ = "contactos_usuario"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(140))
    email: Mapped[str | None] = mapped_column(String(180))
    phone: Mapped[str | None] = mapped_column(String(40))
    consent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

class ChatMessage(Base):
    __tablename__ = "mensajes_chat"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversaciones.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contactos_usuario.id", ondelete="SET NULL"))
    department_id: Mapped[int] = mapped_column(ForeignKey("dependencias.id"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(120), default="general", index=True)
    ai_answer: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="PROCESSING", index=True)
    public_token_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    department: Mapped[Department] = relationship()
    contact: Mapped[Contact | None] = relationship()
    responses: Mapped[list["DepartmentResponse"]] = relationship(back_populates="message", cascade="all, delete-orphan")

class DepartmentResponse(Base):
    __tablename__ = "respuestas_division"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("mensajes_chat.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("usuarios_admin.id"))
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    message: Mapped[ChatMessage] = relationship(back_populates="responses")
    author: Mapped[AdminUser] = relationship()

class Validation(Base):
    __tablename__ = "validaciones_lider"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("mensajes_chat.id", ondelete="CASCADE"), index=True)
    validator_id: Mapped[int] = mapped_column(ForeignKey("usuarios_admin.id"))
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    corrected_answer: Mapped[str | None] = mapped_column(Text)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    validator: Mapped[AdminUser] = relationship()

class KnowledgeArticle(Base):
    __tablename__ = "base_conocimiento"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("dependencias.id", ondelete="SET NULL"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios_admin.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

class Notification(Base):
    __tablename__ = "notificaciones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("mensajes_chat.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(24), nullable=False)
    recipient: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(24), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
