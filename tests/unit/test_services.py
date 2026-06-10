import smtplib

import pytest

from src.services import cloudinary_service
from src.services.auth import (
    create_access_token,
    create_email_token,
    create_reset_token,
    decode_email_token,
    decode_reset_token,
    decode_token,
)
from src.services.email import send_password_reset_email, send_verification_email


def test_token_decoders_reject_wrong_scopes():
    access_token = create_access_token("user@test.com")
    email_token = create_email_token("user@test.com")
    reset_token = create_reset_token("user@test.com")

    assert decode_token(access_token) == "user@test.com"
    assert decode_token(email_token) is None
    assert decode_email_token(reset_token) is None
    assert decode_reset_token(access_token) is None


def test_token_decoders_reject_invalid_token():
    assert decode_token("bad-token") is None
    assert decode_email_token("bad-token") is None
    assert decode_reset_token("bad-token") is None


def test_email_senders_skip_when_smtp_is_not_configured(monkeypatch):
    monkeypatch.setattr("src.services.email.settings.smtp_user", "")
    monkeypatch.setattr("src.services.email.settings.smtp_password", "")
    monkeypatch.setattr("src.services.email.settings.smtp_from", "")

    send_verification_email("user@test.com", "token")
    send_password_reset_email("user@test.com", "token")


def test_email_sender_uses_smtp_when_configured(monkeypatch):
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def starttls(self):
            sent_messages.append(("starttls", self.host, self.port))

        def login(self, user, password):
            sent_messages.append(("login", user, password))

        def sendmail(self, sender, recipients, message):
            sent_messages.append(("sendmail", sender, recipients, message))

    monkeypatch.setattr("src.services.email.settings.smtp_user", "smtp-user")
    monkeypatch.setattr("src.services.email.settings.smtp_password", "smtp-password")
    monkeypatch.setattr("src.services.email.settings.smtp_from", "noreply@test.com")
    monkeypatch.setattr("src.services.email.settings.smtp_host", "smtp.test.com")
    monkeypatch.setattr("src.services.email.settings.smtp_port", 2525)
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    send_verification_email("user@test.com", "token")

    assert sent_messages[0] == ("starttls", "smtp.test.com", 2525)
    assert sent_messages[1] == ("login", "smtp-user", "smtp-password")
    assert sent_messages[2][0] == "sendmail"


def test_upload_avatar_requires_cloudinary_configuration(monkeypatch):
    monkeypatch.setattr(cloudinary_service, "_is_configured", False)

    with pytest.raises(ValueError, match="Cloudinary is not configured"):
        cloudinary_service.upload_avatar("avatar.png", "public-id")
