import smtplib
from email.mime.text import MIMEText

from src.config import settings


def send_verification_email(email: str, token: str) -> None:
    if not settings.smtp_user or not settings.smtp_password or not settings.smtp_from:
        return

    verify_link = f"{settings.app_base_url}/auth/confirmed_email/{token}"
    body = f"Verify your email by opening this link: {verify_link}"

    msg = MIMEText(body)
    msg["Subject"] = "Email verification"
    msg["From"] = settings.smtp_from
    msg["To"] = email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from, [email], msg.as_string())
