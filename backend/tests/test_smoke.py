import uuid

def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_demo_knowledge_answer(client):
    response = client.post("/api/v1/chat/messages", json={"session_id":str(uuid.uuid4()),"message":"¿Qué es AsistIA?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AI_ANSWERED"
    assert data["requires_human"] is False

def test_unknown_question_creates_human_case(client):
    response = client.post("/api/v1/chat/messages", json={"session_id":str(uuid.uuid4()),"message":"Necesito revisar un asunto personal de mi matrícula"})
    assert response.status_code == 200
    data = response.json()
    assert data["requires_human"] is True
    assert data["case_id"] is not None
    assert data["claim_token"]

def test_case_contact_and_human_reply_flow(client):
    case = client.post("/api/v1/chat/messages", json={"session_id":str(uuid.uuid4()),"message":"Necesito ayuda con un caso excepcional de beca"}).json()
    contact = client.post(f"/api/v1/chat/cases/{case['case_id']}/contact", json={
        "claim_token":case["claim_token"],
        "contact":{"name":"Usuario de prueba","email":"estudiante@example.com","consent":True}
    })
    assert contact.status_code == 200, contact.text
    login = client.post("/api/v1/auth/login", json={"email":"admin@asistia.example.com","password":"AsistIA-demo-2026"})
    assert login.status_code == 200
    headers={"Authorization":f"Bearer {login.json()['access_token']}"}
    reply=client.post(f"/api/v1/admin/cases/{case['case_id']}/responses",headers=headers,json={"answer":"Respuesta de prueba del área."})
    assert reply.status_code == 200 
    status=client.post(f"/api/v1/chat/cases/{case['case_id']}/status",json={"claim_token":case["claim_token"]})
    assert status.status_code == 200
    assert status.json()["answer"] == "Respuesta de prueba del área."

def test_case_contact_accepts_phone_or_email_but_not_both(client):
    case = client.post("/api/v1/chat/messages", json={
        "session_id":str(uuid.uuid4()),
        "message":"Necesito seguimiento humano para una consulta particular"
    }).json()
    url = f"/api/v1/chat/cases/{case['case_id']}/contact"
    phone = client.post(url, json={
        "claim_token":case["claim_token"],
        "contact":{"phone":"+57 300 123 4567","consent":True}
    })
    assert phone.status_code == 200

    case = client.post("/api/v1/chat/messages", json={
        "session_id":str(uuid.uuid4()),
        "message":"Necesito seguimiento humano para otra consulta particular"
    }).json()
    url = f"/api/v1/chat/cases/{case['case_id']}/contact"
    missing = client.post(url, json={
        "claim_token":case["claim_token"],
        "contact":{"consent":True}
    })
    assert missing.status_code == 422
    both = client.post(url, json={
        "claim_token":case["claim_token"],
        "contact":{"email":"estudiante@example.com","phone":"3001234567","consent":True}
    })
    assert both.status_code == 422


def test_public_directory_exposes_verified_channels_and_aggregate_counts(client):
    response = client.get("/api/v1/dependencies")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 7
    registration = next(row for row in rows if row["name"] == "Registro y Control")
    assert registration["contact_email"] == "coordinacionregistroycontrol@teinco.edu.co"
    assert registration["contact_phone"] == "601 743 32 00"
    assert registration["contact_whatsapp"] == "301 333 79 56"
    assert isinstance(registration["query_count"], int)
    assert all("example.invalid" not in (row["contact_email"] or "") for row in rows)

def test_chat_response_includes_assigned_department_channels(client):
    response = client.post("/api/v1/chat/messages", json={"session_id":str(uuid.uuid4()),"message":"documentos necesito homologacion asignatura"})
    assert response.status_code == 200
    data = response.json()
    assert data["department_name"] == "Registro y Control"
    assert data["department_email"] == "coordinacionregistroycontrol@teinco.edu.co"
    assert data["department_whatsapp"] == "301 333 79 56"

def test_audit_dependencies_and_knowledge_are_available(client):
    login = client.post("/api/v1/auth/login", json={"email":"admin@asistia.example.com","password":"AsistIA-demo-2026"})
    assert login.status_code == 200
    headers={"Authorization":f"Bearer {login.json()['access_token']}"}
    departments = client.get("/api/v1/admin/departments", headers=headers)
    assert departments.status_code == 200
    assert len(departments.json()) == 7
    knowledge = client.get("/api/v1/admin/knowledge", headers=headers)
    assert knowledge.status_code == 200
    assert any(article["question"] == "¿Qué es AsistIA?" for article in knowledge.json())

def test_approved_article_answers_certificate_question(client):
    login = client.post("/api/v1/auth/login", json={"email":"admin@asistia.example.com","password":"AsistIA-demo-2026"})
    headers={"Authorization":f"Bearer {login.json()['access_token']}"}
    articles = client.get("/api/v1/admin/knowledge", headers=headers).json()
    article = next(item for item in articles if "certificado académico" in item["question"])
    client.patch(f"/api/v1/admin/knowledge/{article['id']}", headers=headers, json={
        "answer":"Para solicitar el certificado académico, contacta a Registro y Control.",
        "active":True,
    })
    response = client.post("/api/v1/chat/messages", json={
        "session_id":str(uuid.uuid4()),
        "message":"¿Cómo solicito un certificado académico?",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["department_name"] == "Registro y Control"
    assert data["status"] == "AI_ANSWERED"
    assert "Registro y Control" in data["answer"]

def test_admin_can_update_and_deactivate_knowledge_article(client):
    login = client.post("/api/v1/auth/login", json={"email":"admin@asistia.example.com","password":"AsistIA-demo-2026"})
    headers={"Authorization":f"Bearer {login.json()['access_token']}"}
    articles = client.get("/api/v1/admin/knowledge", headers=headers).json()
    article = next(item for item in articles if "certificado académico" in item["question"])

    updated = client.patch(f"/api/v1/admin/knowledge/{article['id']}", headers=headers, json={
        "answer":"Procedimiento actualizado: solicita el certificado en Registro y Control y confirma los requisitos vigentes.",
        "source":"Procedimiento institucional actualizado",
        "active":True,
    })
    assert updated.status_code == 200
    assert updated.json()["active"] is True

    response = client.post("/api/v1/chat/messages", json={
        "session_id":str(uuid.uuid4()),
        "message":"¿Cómo solicito un certificado académico?",
    }).json()
    assert "Procedimiento actualizado" in response["answer"]

    deactivated = client.patch(f"/api/v1/admin/knowledge/{article['id']}", headers=headers, json={"active":False})
    assert deactivated.status_code == 200
    active_articles = client.get("/api/v1/admin/knowledge", headers=headers).json()
    assert next(item for item in active_articles if item["id"] == article["id"])["active"] is False
    no_longer_answered = client.post("/api/v1/chat/messages", json={
        "session_id":str(uuid.uuid4()),
        "message":"¿Cómo solicito un certificado académico?",
    }).json()
    assert no_longer_answered["status"] == "HUMAN_REQUIRED"
