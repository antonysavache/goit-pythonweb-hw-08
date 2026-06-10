from src.database.models import User
from src.repository.users import (
    confirm_user_email,
    create_user,
    get_user_by_email,
    update_user_avatar,
    update_user_password,
)


def test_create_and_get_user(db_session):
    user = create_user("new@test.com", "hashed", db_session)
    fetched = get_user_by_email("new@test.com", db_session)
    assert fetched is not None
    assert fetched.id == user.id


def test_confirm_email_and_update_profile_fields(db_session):
    create_user("profile@test.com", "hashed", db_session)

    confirm_user_email("profile@test.com", db_session)
    user = get_user_by_email("profile@test.com", db_session)
    assert user.is_confirmed is True

    update_user_avatar("profile@test.com", "http://example.com/avatar.png", db_session)
    user = get_user_by_email("profile@test.com", db_session)
    assert user.avatar_url == "http://example.com/avatar.png"

    update_user_password("profile@test.com", "newhash", db_session)
    user = get_user_by_email("profile@test.com", db_session)
    assert user.hashed_password == "newhash"
