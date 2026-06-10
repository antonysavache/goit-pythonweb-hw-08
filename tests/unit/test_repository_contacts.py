from datetime import date, timedelta

from src.database.models import Contact, User
from src.repository.contacts import (
    create_contact,
    delete_contact,
    get_contact,
    get_contacts,
    get_upcoming_birthdays,
    update_contact,
)
from src.schemas.contact import ContactCreate, ContactUpdate


def test_create_contact(db_session):
    user = User(email="u@test.com", hashed_password="x", is_confirmed=True, role="user")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    body = ContactCreate(
        first_name="Ann",
        last_name="Lee",
        email="ann@test.com",
        phone_number="1234567",
        birthday=date(2000, 1, 1),
        extra_data="friend",
    )
    created = create_contact(body, db_session, user)

    assert created.id is not None
    assert created.user_id == user.id


def test_get_update_delete_contact(db_session):
    user = User(email="u2@test.com", hashed_password="x", is_confirmed=True, role="user")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    contact = Contact(
        user_id=user.id,
        first_name="Tom",
        last_name="Fox",
        email="tom@test.com",
        phone_number="999",
        birthday=date(1999, 2, 2),
        extra_data=None,
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)

    found = get_contact(contact.id, db_session, user)
    assert found is not None

    updated = update_contact(
        contact.id,
        ContactUpdate(
            first_name="Thomas",
            last_name="Fox",
            email="tom@test.com",
            phone_number="999",
            birthday=date(1999, 2, 2),
            extra_data="updated",
        ),
        db_session,
        user,
    )
    assert updated.first_name == "Thomas"

    all_contacts = get_contacts(db_session, user)
    assert len(all_contacts) == 1

    deleted = delete_contact(contact.id, db_session, user)
    assert deleted is not None
    assert get_contact(contact.id, db_session, user) is None


def test_get_contacts_filters_and_upcoming_birthdays(db_session):
    user = User(email="u3@test.com", hashed_password="x", is_confirmed=True, role="user")
    other_user = User(email="other@test.com", hashed_password="x", is_confirmed=True, role="user")
    db_session.add_all([user, other_user])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(other_user)

    today = date.today()
    soon = today + timedelta(days=3)
    later = today + timedelta(days=20)
    contacts = [
        Contact(
            user_id=user.id,
            first_name="Alice",
            last_name="Smith",
            email="alice@test.com",
            phone_number="111",
            birthday=date(1990, soon.month, soon.day),
            extra_data=None,
        ),
        Contact(
            user_id=user.id,
            first_name="Bob",
            last_name="Brown",
            email="bob@test.com",
            phone_number="222",
            birthday=date(1991, later.month, later.day),
            extra_data=None,
        ),
        Contact(
            user_id=other_user.id,
            first_name="Alice",
            last_name="Other",
            email="alice-other@test.com",
            phone_number="333",
            birthday=date(1992, soon.month, soon.day),
            extra_data=None,
        ),
    ]
    db_session.add_all(contacts)
    db_session.commit()

    filtered = get_contacts(db_session, user, first_name="ali")
    upcoming = get_upcoming_birthdays(db_session, user)

    assert [contact.email for contact in filtered] == ["alice@test.com"]
    assert [contact.email for contact in upcoming] == ["alice@test.com"]
