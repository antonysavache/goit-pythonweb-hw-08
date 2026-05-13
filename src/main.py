from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.db import Base, engine
from src.database.deps import get_db
from src.repository.contacts import (
    create_contact,
    delete_contact,
    get_contact,
    get_contacts,
    get_upcoming_birthdays,
    update_contact,
)
from src.schemas.contact import ContactCreate, ContactResponse, ContactUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Contacts API is running"}


@app.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact_endpoint(body: ContactCreate, db: Session = Depends(get_db)) -> ContactResponse:
    try:
        return create_contact(body, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")


@app.get("/contacts", response_model=list[ContactResponse])
def get_contacts_endpoint(
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ContactResponse]:
    return get_contacts(db, first_name, last_name, email)


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact_endpoint(contact_id: int, db: Session = Depends(get_db)) -> ContactResponse:
    contact = get_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact_endpoint(
    contact_id: int, body: ContactUpdate, db: Session = Depends(get_db)
) -> ContactResponse:
    try:
        contact = update_contact(contact_id, body, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact_endpoint(contact_id: int, db: Session = Depends(get_db)) -> ContactResponse:
    contact = delete_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@app.get("/contacts/upcoming/birthdays", response_model=list[ContactResponse])
def upcoming_birthdays_endpoint(db: Session = Depends(get_db)) -> list[ContactResponse]:
    return get_upcoming_birthdays(db)
