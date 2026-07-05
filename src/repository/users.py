from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import User


def get_user_by_email(email: str, db: Session) -> User | None:
    """Return user by email or None."""

    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(user_id: int, db: Session) -> User | None:
    """Return user by id or None."""

    return db.get(User, user_id)


def create_user(email: str, hashed_password: str, db: Session, role: str = "user") -> User:
    """Create user with hashed password."""

    user = User(email=email, hashed_password=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def confirm_user_email(email: str, db: Session) -> None:
    """Mark user email as confirmed."""

    user = get_user_by_email(email, db)
    if user:
        user.is_confirmed = True
        db.commit()


def update_user_avatar(email: str, avatar_url: str, db: Session) -> User | None:
    """Update user avatar URL."""

    user = get_user_by_email(email, db)
    if user is None:
        return None
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user


def update_user_password(email: str, hashed_password: str, db: Session) -> User | None:
    """Update user password hash."""

    user = get_user_by_email(email, db)
    if user is None:
        return None
    user.hashed_password = hashed_password
    db.commit()
    db.refresh(user)
    return user


def update_user_role(user_id: int, role: str, db: Session) -> User | None:
    """Update user role by id."""

    user = get_user_by_id(user_id, db)
    if user is None:
        return None
    user.role = role
    db.commit()
    db.refresh(user)
    return user
