import hashlib
import secrets
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatMessage, Contact, Conversation, Department, Notification
from app.schemas import ChatRequest, ChatResponse, ClaimRequest, PublicContactRequest
from app.services.ai_service import classify_department, classify_topic, find_article, generate_answer
from app.services.notifications import dispatch_email

router = APIRouter(prefix="/api/v1", tags=["Chat público"])

PUBLIC_PHONE = "601 743 32 00"
PUBLIC_WHATSAPP = "301 333 79 56"
PUBLIC_CONTACT_URL = "https://teinco.edu.co/contactenos/"

@router.get("/dependencies")
def list_dependencies(db: Session = Depends(get_db)):
    rows = db.scalars(select(Department).where(Department.active.is_(True)).order_by(Department.name)).all()
    counts = dict(db.execute(select(ChatMessage.department_id, func.count(ChatMessage.id)).group_by(ChatMessage.department_id)).all())
    return [{"id": row.id, "name": row.name, "contact_email": row.contact_email or None,
             "contact_phone": PUBLIC_PHONE, "contact_whatsapp": PUBLIC_WHATSAPP,
             "contact_url": PUBLIC_CONTACT_URL, "query_count": counts.get(row.id, 0)} for row in rows]

@router.post("/chat/messages", response_model=ChatResponse)
def create_message(payload: ChatRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    session_id = payload.session_id or str(uuid.uuid4())
    conversation = db.scalar(select(Conversation).where(Conversation.session_code == session_id))
    if conversation is None:
        conversation = Conversation(session_code=session_id)
        db.add(conversation)
        db.flush()
    department = classify_department(db, payload.message, payload.department_id)
    if department is None:
        raise HTTPException(status_code=503, detail="No hay dependencias activas configuradas.")
    normalized = payload.message.lower()
    explicitly_requests_human = any(
        phrase in normalized
        for phrase in ("persona", "asesor", "humano", "personal", "particular", "seguimiento")
    )
    article = None if explicitly_requests_human else find_article(db, payload.message, department.id)
    answer = None if explicitly_requests_human else generate_answer(payload.message, article)
    requires_human = not bool(answer)
    status = "HUMAN_REQUIRED" if requires_human else "AI_ANSWERED"
    claim_token = secrets.token_urlsafe(32) if requires_human else None
    message = ChatMessage(
        conversation_id=conversation.id,
        department_id=department.id,
        question=payload.message.strip(),
        topic=classify_topic(payload.message),
        ai_answer=answer if answer else "No encontré una respuesta aprobada suficiente. La consulta quedó registrada para revisión humana.",
        status=status,
        public_token_hash=hashlib.sha256(claim_token.encode()).hexdigest() if claim_token else None,
    )
    db.add(message)
    db.flush()
    if requires_human:
        notification = Notification(message_id=message.id, channel="EMAIL_DEPARTMENT", recipient=department.contact_email or None, status="PENDING" if department.contact_email else "NO_RECIPIENT")
        db.add(notification)
        db.flush()
        if department.contact_email:
            background.add_task(dispatch_email, notification.id, department.contact_email, f"Nuevo caso AsistIA #{message.id}", f"Hay una consulta pendiente para {department.name}. Ingresa al panel interno y busca el caso #{message.id}. No respondas a este correo.")
    db.commit()
    db.refresh(message)
    return ChatResponse(
        session_id=session_id, message_id=message.id, answer=message.ai_answer,
        status=message.status, requires_human=requires_human,
        case_id=message.id if requires_human else None, claim_token=claim_token,
        department_id=department.id, department_name=department.name,
        department_email=department.contact_email or None, department_phone=PUBLIC_PHONE,
        department_whatsapp=PUBLIC_WHATSAPP, department_contact_url=PUBLIC_CONTACT_URL,
    )

@router.post("/chat/cases/{case_id}/contact")
def add_contact(case_id: int, payload: PublicContactRequest, db: Session = Depends(get_db)):
    message = db.get(ChatMessage, case_id)
    expected = hashlib.sha256(payload.claim_token.encode()).hexdigest()
    if not message or message.status not in ("HUMAN_REQUIRED", "HUMAN_ANSWERED") or not message.public_token_hash or not secrets.compare_digest(message.public_token_hash, expected):
        raise HTTPException(status_code=404, detail="No se encontró el caso o el enlace ya venció.")
    if message.contact_id is not None:
        raise HTTPException(status_code=409, detail="El contacto del caso ya fue registrado.")
    contact = Contact(name=payload.contact.name, email=str(payload.contact.email).lower() if payload.contact.email else None, phone=payload.contact.phone)
    db.add(contact)
    db.flush()
    message.contact_id = contact.id
    db.commit()
    return {"status": "registered", "message": "Guardamos tu contacto para hacer seguimiento al caso."}

@router.post("/chat/cases/{case_id}/status")
def get_case_status(case_id: int, payload: ClaimRequest, db: Session = Depends(get_db)):
    message = db.get(ChatMessage, case_id)
    expected = hashlib.sha256(payload.claim_token.encode()).hexdigest()
    if not message or not message.public_token_hash or not secrets.compare_digest(message.public_token_hash, expected):
        raise HTTPException(status_code=404, detail="No se encontró el caso.")
    human_answer = message.responses[-1].answer if message.responses else None
    return {"case_id": message.id, "status": message.status, "answer": human_answer, "department": message.department.name}