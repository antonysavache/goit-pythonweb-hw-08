from datetime import date

from src.config import settings
from src.database.models import User
from src.services.auth import create_reset_token


def _register(client, email: str = "user@test.com", password: str = "secret12"):
    return client.post("/auth/register", json={"email": email, "password": password})


def _confirm_user(db_session, email: str):
    user = db_session.query(User).filter(User.email == email).first()
    user.is_confirmed = True
    db_session.commit()


def _login(client, email: str = "user@test.com", password: str = "secret12"):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_register_and_login_flow(client, db_session):
    reg = _register(client)
    assert reg.status_code == 201

    _confirm_user(db_session, "user@test.com")

    login = _login(client)
    assert login.status_code == 201
    assert "access_token" in login.json()


def test_me_requires_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_contacts_crud(client, db_session):
    _register(client)
    _confirm_user(db_session, "user@test.com")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/contacts",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@ex.com",
            "phone_number": "12345",
            "birthday": str(date(1990, 1, 1)),
            "extra_data": "note",
        },
        headers=headers,
    )
    assert created.status_code == 201
    cid = created.json()["id"]

    listed = client.get("/contacts", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = client.delete(f"/contacts/{cid}", headers=headers)
    assert deleted.status_code == 200


def test_reset_password_flow(client, db_session):
    _register(client)
    user = db_session.query(User).filter(User.email == "user@test.com").first()
    token = create_reset_token(user.email)

    reset = client.post("/auth/reset_password", json={"token": token, "new_password": "newpass123"})
    assert reset.status_code == 200


def test_avatar_forbidden_for_non_admin(client, db_session):
    _register(client)
    _confirm_user(db_session, "user@test.com")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.patch(
        "/users/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"fake", "image/png")},
    )
    assert resp.status_code == 403


def test_admin_bootstrap_and_role_assignment(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "admin@test.com")

    admin_reg = _register(client, "admin@test.com")
    user_reg = _register(client, "member@test.com")

    assert admin_reg.status_code == 201
    assert admin_reg.json()["role"] == "admin"
    assert user_reg.status_code == 201
    assert user_reg.json()["role"] == "user"

    _confirm_user(db_session, "admin@test.com")
    _confirm_user(db_session, "member@test.com")

    member = db_session.query(User).filter(User.email == "member@test.com").first()
    member_token = _login(client, "member@test.com").json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    forbidden = client.patch(f"/users/{member.id}/role", json={"role": "admin"}, headers=member_headers)
    assert forbidden.status_code == 403

    admin_token = _login(client, "admin@test.com").json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    promoted = client.patch(f"/users/{member.id}/role", json={"role": "admin"}, headers=admin_headers)
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"
