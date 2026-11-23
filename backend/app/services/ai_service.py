import logging
import re
import unicodedata
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Department, KnowledgeArticle

log = logging.getLogger(__name__)

STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "del", "un", "una",
    "por", "para", "con", "sobre", "que", "como", "cual", "cuales", "donde",
    "cuando", "quien", "es", "son", "mi", "mis", "tu", "su", "me", "se",
    "lo", "al", "o", "u", "si", "no", "quiero", "necesito", "informacion",
    "saber", "puedo", "solicito", "hacer", "tengo",
}

TOPIC_DEPARTMENT_MAP = {
    "admisiones": "Admisiones y Comercial",
    "registro": "Registro y Control",
    "bienestar": "Bienestar Institucional",
    "coordinacion": "Coordinación Académica",
    "tesoreria": "Tesorería y Facturación",
    "investigacion": "Investigación y Opciones de Grado",
    "general": "Atención General",
}


def _normalize(text: str) -> str:
    clean = unicodedata.normalize("NFD", text.lower())
    clean = "".join(ch for ch in clean if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", clean)


def _stem_word(w: str) -> str:
    if len(w) > 4 and w.endswith("es"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s"):
        return w[:-1]
    return w


def search_tokens(text: str) -> set[str]:
    words = _normalize(text).split()
    tokens = set()
    for w in words:
        if len(w) > 2 and w not in STOPWORDS:
            tokens.add(w)
            stem = _stem_word(w)
            if len(stem) > 2:
                tokens.add(stem)
    return tokens


def classify_topic(question: str) -> str:
    q = _normalize(question)
    if any(k in q for k in ("admi", "inscrip", "aspirante", "carrera", "programa", "beca")):
        return "admisiones"
    if any(k in q for k in ("certific", "constancia", "nota", "calific", "homolog", "matricula", "carne", "registro")):
        return "registro"
    if any(k in q for k in ("bienestar", "psicolog", "deporte", "cultura", "enfermeria", "apoyo")):
        return "bienestar"
    if any(k in q for k in ("horario", "clase", "docente", "profesor", "asignatura", "materia", "semestre", "cancelacion")):
        return "coordinacion"
    if any(k in q for k in ("pago", "factura", "recibo", "financ", "credito", "cuota", "tesoreria", "descuento")):
        return "tesoreria"
    if any(k in q for k in ("grado", "tesis", "investig", "semillero", "diplomado", "practica", "pasantia")):
        return "investigacion"
    return "general"


def classify_department(db: Session, question: str, department_id: int | None = None) -> Department | None:
    if department_id is not None:
        dept = db.scalar(
            select(Department).where(Department.id == department_id, Department.active.is_(True))
        )
        if dept is not None:
            return dept

    topic = classify_topic(question)
    target_name = TOPIC_DEPARTMENT_MAP.get(topic, "Atención General")
    dept = db.scalar(
        select(Department).where(Department.name == target_name, Department.active.is_(True))
    )
    if dept is not None:
        return dept

    fallback = db.scalar(
        select(Department).where(Department.name == "Atención General", Department.active.is_(True))
    )
    if fallback is not None:
        return fallback

    return db.scalar(select(Department).where(Department.active.is_(True)).order_by(Department.id))


def find_article(db: Session, question: str, department_id: int) -> KnowledgeArticle | None:
    all_rows = db.scalars(
        select(KnowledgeArticle).where(KnowledgeArticle.active.is_(True))
    ).all()
    if not all_rows:
        return None

    dept_rows = [
        r for r in all_rows if r.department_id == department_id or r.department_id is None
    ]
    tokens = search_tokens(question)
    if not tokens:
        return None

    def best_match(candidates: list[KnowledgeArticle]) -> tuple[KnowledgeArticle | None, float]:
        best, best_score = None, 0.0
        for row in candidates:
            candidate_tokens = search_tokens(f"{row.question} {row.answer}")
            score = len(tokens & candidate_tokens) / len(tokens)
            if score > best_score:
                best, best_score = row, score
        return best, best_score

    best, best_score = best_match(dept_rows)
    if best_score < 0.65:
        best, best_score = best_match(all_rows)
    return best if best_score >= 0.65 else None


def generate_answer(question: str, article: KnowledgeArticle | None = None) -> str | None:
    provider = settings.ai_provider.strip().casefold()
    api_key = settings.gemini_api_key.strip()
    if provider != "gemini":
        return article.answer if article else None

    if (
        not api_key
        or "tu_clave_de_google_ai_studio" in api_key.casefold()
        or api_key.casefold() in {"your_api_key", "your_api_key_here"}
    ):
        log.warning("Gemini está seleccionado, pero GEMINI_API_KEY no contiene una clave válida.")
        return article.answer if article else None

    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1)
        ),
    )

    if article:
        sys_inst = (
            "Eres AsistIA, el asistente académico virtual de TEINCO. Responde en español de forma clara, amable y concisa "
            "usando la información aprobada. Menciona la fuente cuando sea útil. "
            "Solo si el usuario pide explícitamente hablar con un asesor humano, escribe exactamente [DERIVAR]."
        )
        prompt_input = (
            f"Artículo aprobado:\n"
            f"Pregunta guía: {article.question}\n"
            f"Respuesta: {article.answer}\n\n"
            f"Fuente: {article.source or 'Información institucional TEINCO'}\n\n"
            f"Pregunta del usuario: {question}"
        )
    else:
        sys_inst = (
            "Eres AsistIA, el asistente académico virtual de TEINCO (Corporación Tecnológica Industrial Colombiana). "
            "Responde en español de forma clara, amable y concisa orientando al estudiante sobre trámites y servicios académicos "
            "(certificados, admisiones, horarios, bienestar, tesorería u opciones de grado). "
            "Explica los pasos habituales sin inventar tarifas exactas ni fechas específicas, y sugiere confirmar los detalles "
            "con la dependencia correspondiente (teléfono 601 743 32 00 o WhatsApp 301 333 79 56). "
            "Solo si el usuario solicita explícitamente atención humana o un asesor, escribe exactamente [DERIVAR]."
        )
        prompt_input = f"Pregunta del usuario: {question}"

    models_to_try = [settings.gemini_model.strip()]
    for fallback in ("gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite"):
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    for model_name in models_to_try:
        try:
            config_kwargs = {
                "system_instruction": sys_inst,
                "max_output_tokens": 1024,
            }
            if model_name.startswith("gemini-3"):
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="low")

            response = client.models.generate_content(
                model=model_name,
                contents=prompt_input,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            answer = (response.text or "").strip()
            if not answer or "[DERIVAR]" in answer.upper():
                return None
            return answer
        except Exception as exc:
            log.warning("El modelo %s no estuvo disponible (%s), intentando respaldo...", model_name, exc)
            continue

    log.warning("Ningún modelo de Gemini respondió; usando artículo oficial de respaldo.")
    return article.answer if article else None