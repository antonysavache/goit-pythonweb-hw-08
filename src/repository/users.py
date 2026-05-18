from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import User


def get_user_by_email(email: str, db: Session) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(email: str, hashed_password: str, db: Session) -> User:
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def confirm_user_email(email: str, db: Session) -> None:
    user = get_user_by_email(email, db)
    if user:
        user.is_confirmed = True
        db.commit()


def update_user_avatar(email: str, avatar_url: str, db: Session) -> User | None:
    user = get_user_by_email(email, db)
    if user is None:
        return None
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user
