import logging
import smtplib
from email.message import EmailMessage
from app.config import settings
from app.database import SessionLocal
from app.models import Notification

log = logging.getLogger(__name__)

def dispatch_email(notification_id: int, recipient: str, subject: str, body: str) -> None:
    with SessionLocal() as db:
        notice = db.get(Notification, notification_id)
        if not notice:
            return
        if not settings.smtp_host or not settings.smtp_from or recipient.endswith(".invalid"):
            notice.status = "SIMULATED"
            log.info("Correo simulado: notificación %s", notification_id)
            db.commit()
            return
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from
            msg["To"] = recipient
            msg.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
            notice.status = "SENT"
        except Exception:
            log.exception("No se pudo enviar la notificación %s", notification_id)
            notice.status = "FAILED"
        db.commit()
