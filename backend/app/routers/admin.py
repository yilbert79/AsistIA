from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AdminUser, ChatMessage, Department, DepartmentResponse, KnowledgeArticle, Notification, Validation
from app.schemas import HumanResponseInput, KnowledgeArticleInput, KnowledgeArticleUpdate, ReviewInput, UserCreate
from app.security import get_current_admin, hash_password, require_roles
from app.services.notifications import dispatch_email
from fastapi import BackgroundTasks

router = APIRouter(prefix="/api/v1", tags=["Administración"])

def check_scope(user: AdminUser, message: ChatMessage) -> None:
    if user.role != "SUPERADMIN" and user.department_id != message.department_id:
        raise HTTPException(status_code=404, detail="No se encontró el caso.")

@router.get("/admin/cases")
def list_cases(status: str = "HUMAN_REQUIRED", db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    stmt = select(ChatMessage).where(ChatMessage.status == status).order_by(ChatMessage.created_at.desc())
    if user.role != "SUPERADMIN":
        stmt = stmt.where(ChatMessage.department_id == user.department_id)
    rows = db.scalars(stmt).all()
    return [{"id":m.id,"question":m.question,"ai_answer":m.ai_answer,"status":m.status,"topic":m.topic,"department":m.department.name,"created_at":m.created_at.isoformat(),"contact_email":m.contact.email if m.contact else None,"contact_phone":m.contact.phone if m.contact else None} for m in rows]

@router.post("/admin/cases/{case_id}/responses")
def answer_case(case_id: int, payload: HumanResponseInput, background: BackgroundTasks, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    message = db.get(ChatMessage, case_id)
    if not message:
        raise HTTPException(status_code=404, detail="No se encontró el caso.")
    check_scope(user, message)
    if message.status != "HUMAN_REQUIRED":
        raise HTTPException(status_code=409, detail="El caso ya no está pendiente de respuesta.")
    response = DepartmentResponse(message_id=message.id, author_id=user.id, answer=payload.answer.strip())
    db.add(response)
    message.status = "HUMAN_ANSWERED"
    db.flush()
    contact = message.contact
    notification = Notification(message_id=message.id, channel="EMAIL_USER", recipient=contact.email if contact else None, status="PENDING" if contact and contact.email else ("NO_EMAIL_CHANNEL" if contact else "NO_CONTACT"))
    db.add(notification)
    db.commit()
    if contact and contact.email:
        background.add_task(dispatch_email, notification.id, contact.email, f"Respuesta a tu consulta AsistIA #{message.id}", f"La dependencia {message.department.name} respondió tu consulta:\n\n{payload.answer.strip()}\n\nEste mensaje corresponde al caso #{message.id}.")
    return {"status":"saved","message":"La respuesta quedó registrada.","case_id":message.id}

@router.get("/admin/reviews")
def list_reviews(db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    stmt = select(ChatMessage).where(ChatMessage.status.in_(["AI_ANSWERED","HUMAN_ANSWERED"])).order_by(ChatMessage.created_at.desc()).limit(100)
    if user.role not in ("SUPERADMIN", "DIVISION_LEADER"):
        raise HTTPException(status_code=403, detail="Solo un líder puede revisar respuestas.")
    if user.role != "SUPERADMIN":
        stmt = stmt.where(ChatMessage.department_id == user.department_id)
    rows = db.scalars(stmt).all()
    result=[]
    for m in rows:
        human=m.responses[-1].answer if m.responses else None
        result.append({"id":m.id,"question":m.question,"ai_answer":m.ai_answer,"human_answer":human,"status":m.status,"department":m.department.name})
    return result

@router.post("/admin/reviews/{message_id}")
def review_message(message_id: int, payload: ReviewInput, db: Session = Depends(get_db), user: AdminUser = Depends(require_roles("SUPERADMIN","DIVISION_LEADER"))):
    message=db.get(ChatMessage,message_id)
    if not message:
        raise HTTPException(status_code=404, detail="No se encontró la respuesta.")
    check_scope(user,message)
    if payload.decision == "CORRECTED" and not (payload.corrected_answer or "").strip():
        raise HTTPException(status_code=422, detail="Escribe la respuesta corregida.")
    validation=Validation(message_id=message.id,validator_id=user.id,decision=payload.decision,corrected_answer=payload.corrected_answer.strip() if payload.corrected_answer else None,comment=payload.comment)
    db.add(validation)
    db.flush()
    if payload.decision in ("APPROVED","CORRECTED"):
        answer=payload.corrected_answer.strip() if payload.decision == "CORRECTED" else (message.responses[-1].answer if message.responses else message.ai_answer)
        if answer:
            db.add(KnowledgeArticle(department_id=message.department_id,question=message.question,answer=answer,source=f"Validación interna #{validation.id}",approved_by=user.id))
    db.commit()
    return {"status":"saved","decision":payload.decision,"validation_id":validation.id}

@router.get("/reports/dashboard")
def dashboard(start: date | None = None, end: date | None = None, db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    if user.role not in ("SUPERADMIN","DIVISION_LEADER"):
        raise HTTPException(status_code=403, detail="No tienes permiso para consultar reportes.")
    filters=[]
    if start: filters.append(ChatMessage.created_at >= datetime.combine(start,time.min))
    if end: filters.append(ChatMessage.created_at < datetime.combine(end + timedelta(days=1),time.min))
    scoped=select(ChatMessage)
    if filters: scoped=scoped.where(*filters)
    if user.role != "SUPERADMIN": scoped=scoped.where(ChatMessage.department_id == user.department_id)
    ids=scoped.subquery()
    total=db.scalar(select(func.count()).select_from(ids)) or 0
    by_status=db.execute(select(ids.c.status,func.count()).group_by(ids.c.status)).all()
    by_topic=db.execute(select(ids.c.topic,func.count()).group_by(ids.c.topic).order_by(func.count().desc()).limit(5)).all()
    dept_query=select(Department.name,func.count(ids.c.id)).select_from(Department).outerjoin(ids,ids.c.department_id==Department.id).group_by(Department.id,Department.name).order_by(func.count(ids.c.id).desc())
    if user.role != "SUPERADMIN": dept_query=dept_query.where(Department.id==user.department_id)
    by_department=db.execute(dept_query).all()
    return {"total":total,"by_status":[{"status":s,"count":c} for s,c in by_status],"by_topic":[{"topic":t,"count":c} for t,c in by_topic],"by_department":[{"department":n,"count":c} for n,c in by_department]}

@router.post("/admin/users", status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), user: AdminUser = Depends(require_roles("SUPERADMIN"))):
    email=str(payload.email).lower()
    if db.scalar(select(AdminUser).where(AdminUser.email==email)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo.")
    if payload.department_id and not db.get(Department,payload.department_id):
        raise HTTPException(status_code=422, detail="La dependencia no existe.")
    created=AdminUser(email=email,full_name=payload.full_name,password_hash=hash_password(payload.password),role=payload.role,department_id=payload.department_id)
    db.add(created); db.commit(); db.refresh(created)
    return {"id":created.id,"email":created.email,"name":created.full_name,"role":created.role,"department_id":created.department_id}

@router.get("/admin/departments")
def list_admin_departments(db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    stmt = select(Department).where(Department.active.is_(True)).order_by(Department.name)
    if user.role == "DIVISION_LEADER":
        stmt = stmt.where(Department.id == user.department_id)
    elif user.role not in ("SUPERADMIN", "DIVISION_LEADER"):
        raise HTTPException(status_code=403, detail="No tienes permiso para consultar las dependencias.")
    rows = db.scalars(stmt).all()
    return [{"id": row.id, "name": row.name} for row in rows]

@router.get("/admin/knowledge")
def list_knowledge(db: Session = Depends(get_db), user: AdminUser = Depends(get_current_admin)):
    stmt = select(KnowledgeArticle).order_by(KnowledgeArticle.active.desc(), KnowledgeArticle.created_at.desc())
    if user.role == "DIVISION_LEADER":
        stmt = stmt.where(or_(KnowledgeArticle.department_id == user.department_id, KnowledgeArticle.department_id.is_(None)))
    elif user.role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="No tienes permiso para consultar el conocimiento.")
    rows = db.scalars(stmt).all()
    result = []
    for article in rows:
        department = db.get(Department, article.department_id) if article.department_id else None
        result.append({
            "id": article.id,
            "question": article.question,
            "answer": article.answer,
            "source": article.source,
            "department_id": article.department_id,
            "department_name": department.name if department else "Todas las dependencias",
            "active": article.active,
        })
    return result

@router.post("/admin/knowledge")
def create_knowledge(payload: KnowledgeArticleInput, db: Session = Depends(get_db), user: AdminUser = Depends(require_roles("SUPERADMIN", "DIVISION_LEADER"))):
    if payload.department_id is not None:
        department = db.get(Department, payload.department_id)
        if not department or not department.active:
            raise HTTPException(status_code=422, detail="La dependencia seleccionada no existe.")
        if user.role == "DIVISION_LEADER" and payload.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Solo puedes agregar conocimiento a tu dependencia.")
    elif user.role != "SUPERADMIN":
        raise HTTPException(status_code=403, detail="Solo el superadministrador puede agregar conocimiento global.")
    if db.scalar(select(KnowledgeArticle).where(
        KnowledgeArticle.active.is_(True),
        KnowledgeArticle.question == payload.question.strip(),
        KnowledgeArticle.department_id == payload.department_id,
    )):
        raise HTTPException(status_code=409, detail="Ya existe una respuesta aprobada para esa pregunta y alcance.")
    article = KnowledgeArticle(
        department_id=payload.department_id,
        question=payload.question.strip(),
        answer=payload.answer.strip(),
        source=payload.source.strip(),
        approved_by=user.id,
        active=True,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return {"status": "saved", "id": article.id, "message": "La respuesta aprobada quedó disponible."}

@router.patch("/admin/knowledge/{article_id}")
def update_knowledge(article_id: int, payload: KnowledgeArticleUpdate, db: Session = Depends(get_db), user: AdminUser = Depends(require_roles("SUPERADMIN", "DIVISION_LEADER"))):
    article = db.get(KnowledgeArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="No se encontró el artículo.")
    if user.role == "DIVISION_LEADER" and article.department_id != user.department_id:
        raise HTTPException(status_code=404, detail="No se encontró el artículo de tu dependencia.")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Indica al menos un campo para actualizar.")
    if any(changes.get(field) is None for field in ("question", "answer", "source", "active") if field in changes):
        raise HTTPException(status_code=422, detail="Pregunta, respuesta, fuente y estado no pueden ser nulos.")

    target_department_id = changes.get("department_id", article.department_id)
    if target_department_id is not None:
        department = db.get(Department, target_department_id)
        if not department or not department.active:
            raise HTTPException(status_code=422, detail="La dependencia seleccionada no existe.")
    if user.role == "DIVISION_LEADER" and target_department_id != user.department_id:
        raise HTTPException(status_code=403, detail="Solo puedes asignar conocimiento a tu dependencia.")

    target_question = changes.get("question", article.question).strip()
    if changes.get("active", article.active):
        duplicate = db.scalar(select(KnowledgeArticle).where(
            KnowledgeArticle.id != article.id,
            KnowledgeArticle.active.is_(True),
            KnowledgeArticle.question == target_question,
            KnowledgeArticle.department_id == target_department_id,
        ))
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe una respuesta activa para esa pregunta y alcance.")

    for field in ("question", "answer", "source"):
        if field in changes:
            changes[field] = changes[field].strip()
            setattr(article, field, changes[field])
    if "department_id" in changes:
        article.department_id = target_department_id
    if "active" in changes:
        article.active = changes["active"]
    article.approved_by = user.id
    db.commit()
    return {"status": "saved", "id": article.id, "active": article.active, "message": "El artículo fue actualizado."}
