from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.database.models import Contact
from src.schemas.contact import ContactCreate, ContactUpdate


def create_contact(body: ContactCreate, db: Session) -> Contact:
    contact = Contact(**body.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contacts(
    db: Session,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    stmt = select(Contact)
    filters = []

    if first_name:
        filters.append(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        filters.append(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        filters.append(Contact.email.ilike(f"%{email}%"))

    if filters:
        stmt = stmt.where(or_(*filters))

    return list(db.scalars(stmt).all())


def get_contact(contact_id: int, db: Session) -> Contact | None:
    stmt = select(Contact).where(Contact.id == contact_id)
    return db.scalar(stmt)


def update_contact(contact_id: int, body: ContactUpdate, db: Session) -> Contact | None:
    contact = get_contact(contact_id, db)
    if contact is None:
        return None

    for key, value in body.model_dump().items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(contact_id: int, db: Session) -> Contact | None:
    contact = get_contact(contact_id, db)
    if contact is None:
        return None

    db.delete(contact)
    db.commit()
    return contact


def get_upcoming_birthdays(db: Session) -> list[Contact]:
    today = date.today()
    end_date = today + timedelta(days=7)
    contacts = list(db.scalars(select(Contact)).all())
    result: list[Contact] = []

    for contact in contacts:
        birthday_this_year = _safe_birthday(today.year, contact.birthday.month, contact.birthday.day)
        next_birthday = birthday_this_year if birthday_this_year >= today else _safe_birthday(
            today.year + 1, contact.birthday.month, contact.birthday.day
        )

        if today <= next_birthday <= end_date:
            result.append(contact)

    return result


def _safe_birthday(year: int, month: int, day: int) -> date:
    if month == 2 and day == 29:
        try:
            return date(year, month, day)
        except ValueError:
            return date(year, 2, 28)
    return date(year, month, day)
