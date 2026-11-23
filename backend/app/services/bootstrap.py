from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.models import AdminUser, Department, KnowledgeArticle
from app.security import hash_password

DEPARTMENTS = [
    ("Atención General", ""),
    ("Admisiones y Comercial", "admisiones@teinco.edu.co"),
    ("Registro y Control", "coordinacionregistroycontrol@teinco.edu.co"),
    ("Bienestar Institucional", "bienestar@teinco.edu.co"),
    ("Coordinación Académica", ""),
    ("Tesorería y Facturación", ""),
    ("Investigación y Opciones de Grado", ""),
]

APPROVED_ARTICLES = [
    (
        "Atención General",
        "¿Dónde queda la sede de TEINCO y cuál es el horario de atención?",
        "La sede principal de TEINCO se encuentra ubicada en Bogotá en la Calle 42 # 13-19 (Teusaquillo). El horario de atención administrativa es de lunes a viernes de 8:00 a.m. a 6:00 p.m. y sábados de 8:00 a.m. a 12:00 m. Teléfono: 601 743 32 00, WhatsApp: 301 333 79 56.",
        "Información institucional TEINCO.",
    ),
    (
        "Atención General",
        "¿Cuáles son los canales oficiales de contacto y atención?",
        "Puedes comunicarte con TEINCO a través de:\n- PBX / Teléfono: 601 743 32 00\n- WhatsApp institucional: 301 333 79 56\n- Portal web: https://teinco.edu.co/contactenos/\n- Sede presencial: Calle 42 # 13-19, Bogotá.",
        "Información institucional TEINCO.",
    ),
    (
        "Admisiones y Comercial",
        "Quiero información sobre admisiones e inscripciones",
        "Para iniciar tu proceso de admisión e inscripción en TEINCO, sigue estos pasos:\n1. Consulta los programas disponibles y diligencia el formulario de inscripción en línea.\n2. Adjunta tu documento de identidad, diploma o acta de bachiller y resultados de pruebas Saber 11 (ICFES).\n3. Recibe la liquidación de matrícula.\nPara asesoría personalizada comunícate con Admisiones: admisiones@teinco.edu.co o WhatsApp 301 333 79 56.",
        "Información institucional aprobada TEINCO.",
    ),
    (
        "Admisiones y Comercial",
        "¿Cómo puedo inscribirme o solicitar admisión?",
        "Para iniciar una inscripción, consulta el programa académico disponible, revisa el perfil del aspirante y diligencia el formulario de admisión publicado por TEINCO. Confirma requisitos, fechas y costos vigentes con Admisiones y Comercial.",
        "Información institucional aprobada TEINCO.",
    ),
    (
        "Admisiones y Comercial",
        "¿Qué programas académicos o carreras ofrece TEINCO?",
        "TEINCO ofrece programas de educación superior en ciclos propedéuticos (técnicos profesionales y tecnólogos) en áreas de ingeniería de software, sistemas, telecomunicaciones, electromecánica, gestión administrativa y contable. Para conocer el plan de estudios y pensum vigente, escribe a admisiones@teinco.edu.co.",
        "Catálogo de programas académicos TEINCO.",
    ),
    (
        "Admisiones y Comercial",
        "¿Cuáles son los requisitos de ingreso para estudiantes nuevos?",
        "Los requisitos para estudiantes nuevos son:\n1. Documento de identidad vigente.\n2. Fotocopia de diploma de bachiller o acta de grado.\n3. Resultados de la prueba Saber 11 (ICFES).\n4. Certificado de afiliación a salud (EPS o SISBÉN).\n5. Formulario de inscripción diligenciado.",
        "Reglamento de Admisiones TEINCO.",
    ),
    (
        "Registro y Control",
        "¿Cómo solicito un certificado académico o constancia de estudios?",
        "Para solicitar un certificado académico o constancia de estudios, ingresa al canal autorizado de Registro y Control indicando tus nombres completos, documento de identidad y tipo de certificado requerido. Confirma el tiempo de entrega y si aplica derecho pecuniario.",
        "Guía institucional de Registro y Control.",
    ),
    (
        "Registro y Control",
        "¿Cómo puedo homologar una asignatura o realizar transferencia externa?",
        "Para homologar asignaturas provenientes de otra universidad o del SENA, radica ante Registro y Control el certificado oficial de notas y los contenidos programáticos firmados de la institución de origen para evaluación del comité curricular.",
        "Reglamento académico TEINCO.",
    ),
    (
        "Registro y Control",
        "¿Cómo solicito el carné estudiantil o un duplicado?",
        "Para la expedición del carné o reposición por pérdida o deterioro, comunícate con Registro y Control (coordinacionregistroycontrol@teinco.edu.co). En caso de duplicado, presenta el denuncio por pérdida o el comprobante de pago de derechos de reposición.",
        "Registro y Control TEINCO.",
    ),
    (
        "Registro y Control",
        "¿Cómo consulto mis notas o calificaciones del semestre?",
        "Puedes consultar tus calificaciones parciales y finales ingresando al portal académico con tu usuario estudiantil. Si tienes alguna duda con una nota registrada, solicita la revisión con tu docente dentro de los plazos del calendario académico.",
        "Reglamento estudiantil TEINCO.",
    ),
    (
        "Registro y Control",
        "¿Cómo solicito la cancelación o retiro de una asignatura?",
        "La cancelación de asignaturas debe solicitarse formalmente dentro de las fechas fijadas en el calendario académico del semestre a través del sistema institucional o enviando el formato a Registro y Control y Coordinación Académica.",
        "Calendario y normativa académica.",
    ),
    (
        "Bienestar Institucional",
        "¿Qué servicios ofrece Bienestar Institucional?",
        "Bienestar Institucional orienta sobre acompañamiento estudiantil, actividades deportivas, culturales y atención psicológica. Para solicitar una cita o conocer la disponibilidad, contacta directamente al área de Bienestar.",
        "Catálogo vigente de servicios de Bienestar.",
    ),
    (
        "Bienestar Institucional",
        "¿Cómo solicito cita de atención psicológica o apoyo estudiantil?",
        "El área de Bienestar ofrece orientación psicopedagógica y apoyo emocional gratuito y confidencial. Para agendar una cita, escribe a bienestar@teinco.edu.co indicando tu nombre, documento de identidad, número de contacto y programa académico.",
        "Bienestar Institucional TEINCO.",
    ),
    (
        "Bienestar Institucional",
        "¿Qué actividades deportivas y culturales hay disponibles?",
        "Bienestar Institucional organiza torneos de fútbol, microfútbol, baloncesto, tenis de mesa, grupos de danzas, música y talleres extracurriculares. Las inscripciones se abren al inicio de cada semestre mediante convocatoria de Bienestar.",
        "Bienestar Institucional TEINCO.",
    ),
    (
        "Coordinación Académica",
        "¿Cómo consulto el horario de clase?",
        "Para consultar tu horario de clase, revisa el medio académico habilitado por TEINCO con tu usuario estudiantil o solicita la orientación correspondiente a Coordinación Académica. Confirma cambios o cruces de horario con tu coordinación.",
        "Procedimiento de Coordinación Académica.",
    ),
    (
        "Coordinación Académica",
        "Necesito consultar información sobre horarios de clase",
        "Para consultar tus horarios de clase, asignaturas o docentes asignados, ingresa al portal académico con tus credenciales estudiantiles o comunícate con Coordinación Académica para verificar cruces de horario o novedades de calendario.",
        "Información institucional aprobada TEINCO.",
    ),
    (
        "Coordinación Académica",
        "¿Cómo solicito un examen supletorio o habilitación?",
        "Si no pudiste presentar una prueba evaluativa por causa justificada o necesitas presentar examen de habilitación, debes radicar la solicitud ante Coordinación Académica dentro de los 3 días hábiles siguientes, adjuntando soporte y el respectivo recibo de pago.",
        "Reglamento académico TEINCO.",
    ),
    (
        "Coordinación Académica",
        "¿Qué debo hacer si tengo un cruce de horarios en mis materias?",
        "Si presentas cruce de horarios entre dos asignaturas inscritas, acércate o escribe a la Coordinación Académica de tu programa para solicitar el cambio de grupo o reajuste de horario según los cupos disponibles.",
        "Coordinación Académica TEINCO.",
    ),
    (
        "Tesorería y Facturación",
        "¿Cómo puedo pagar matrícula o consultar una factura?",
        "Para consultar el estado de una factura, los medios de pago o información sobre matrícula, comunícate con Tesorería y Facturación. Conserva el comprobante de pago y verifica el valor, fecha límite y referencia antes de realizar el pago.",
        "Canales de Tesorería TEINCO.",
    ),
    (
        "Tesorería y Facturación",
        "¿Qué convenios de financiación y créditos educativos están disponibles?",
        "TEINCO ofrece opciones de financiación como crédito educativo ICETEX, cooperativas y entidades financieras aliadas, además de facilidades de pago directo institucional. Comunícate con Tesorería para recibir asesoría sobre planes de pago.",
        "Tesorería y Facturación TEINCO.",
    ),
    (
        "Tesorería y Facturación",
        "¿Existen becas o descuentos en la matrícula?",
        "TEINCO dispone de estímulos económicos por pronto pago, convenios empresariales, rendimiento académico destacado y descuentos para hermanos. Consulta las condiciones y fechas de postulación con Tesorería y Admisiones.",
        "Políticas de beneficios TEINCO.",
    ),
    (
        "Investigación y Opciones de Grado",
        "¿Cuáles son las opciones de grado disponibles?",
        "TEINCO orienta sobre opciones de grado como proyecto productivo de grado, coterminal, semillero de investigación, diplomado de profundización o práctica profesional según el programa académico. Consulta los requisitos con Investigación y Opciones de Grado.",
        "Normativa de Grados TEINCO.",
    ),
    (
        "Investigación y Opciones de Grado",
        "¿Cómo es el proceso de postulación a grados y ceremonia de graduación?",
        "Para postularte a grado debes haber aprobado el 100% del plan de estudios y la opción de grado, contar con paz y salvo integral (académico, biblioteca y financiero), presentar el requisito de prueba Saber TyT/Pro e idioma, y radicar los derechos de grado en las fechas fijadas.",
        "Guía de Graduación TEINCO.",
    ),
]

def seed_demo_data(db: Session) -> None:
    if not settings.seed_demo_data:
        return
    for name, email in DEPARTMENTS:
        if not db.scalar(select(Department).where(Department.name == name)):
            db.add(Department(name=name, contact_email=email, context="Dependencia de demostración. Confirma la información con TEINCO antes de publicarla."))
        elif email:
            existing = db.scalar(select(Department).where(Department.name == name))
            if not existing.contact_email or existing.contact_email.endswith(".invalid"):
                existing.contact_email = email
        else:
            existing = db.scalar(select(Department).where(Department.name == name))
            if existing.contact_email.endswith(".invalid"):
                existing.contact_email = ""
    db.flush()
    if not db.scalar(select(AdminUser).where(AdminUser.email == settings.dev_admin_email.lower())):
        db.add(AdminUser(email=settings.dev_admin_email.lower(), full_name="Administrador de demostración", password_hash=hash_password(settings.dev_admin_password), role="SUPERADMIN"))
    if not db.scalar(select(KnowledgeArticle).where(KnowledgeArticle.question == "¿Qué es AsistIA?")):
        db.add(KnowledgeArticle(question="¿Qué es AsistIA?", answer="AsistIA es un prototipo de asistente conversacional para orientar consultas sobre TEINCO. Esta respuesta de demostración no contiene información oficial de trámites. Sustituye el contenido de ejemplo por información validada antes de usarlo con la comunidad.", source="Dato de demostración; reemplazar por fuente institucional aprobada."))
    for department_name, question, answer, source in APPROVED_ARTICLES:
        department = db.scalar(select(Department).where(Department.name == department_name))
        if not db.scalar(select(KnowledgeArticle).where(KnowledgeArticle.question == question)):
            db.add(KnowledgeArticle(
                department_id=department.id if department else None,
                question=question,
                answer=answer,
                source=source,
                active=True,
            ))
    db.commit()
