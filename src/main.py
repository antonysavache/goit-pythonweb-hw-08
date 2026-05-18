import os
import tempfile

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.config import settings
from src.database.db import Base, engine
from src.database.deps import get_db
from src.database.models import User
from src.repository.contacts import (
    create_contact,
    delete_contact,
    get_contact,
    get_contacts,
    get_upcoming_birthdays,
    update_contact,
)
from src.repository.users import confirm_user_email, create_user, get_user_by_email, update_user_avatar
from src.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from src.schemas.user import RequestEmail, Token, UserCreate, UserResponse
from src.services.auth import (
    create_access_token,
    create_email_token,
    decode_email_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from src.services.cloudinary_service import upload_avatar
from src.services.email import send_verification_email

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Contacts API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = ["*"] if settings.cors_origins.strip() == "*" else [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Contacts API is running"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    email = decode_token(token)
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = get_user_by_email(body.email, db)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

    user = create_user(body.email, get_password_hash(body.password), db)
    verification_token = create_email_token(user.email)
    background_tasks.add_task(send_verification_email, user.email, verification_token)
    return user


@app.post("/auth/login", response_model=Token, status_code=status.HTTP_201_CREATED)
def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = get_user_by_email(body.username, db)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")

    return Token(access_token=create_access_token(user.email))


@app.get("/auth/confirmed_email/{token}")
def confirmed_email(token: str, db: Session = Depends(get_db)) -> dict[str, str]:
    email = decode_email_token(token)
    if email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    user = get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.is_confirmed:
        return {"message": "Your email is already confirmed"}

    confirm_user_email(email, db)
    return {"message": "Email confirmed"}


@app.post("/auth/request_email")
def request_email(body: RequestEmail, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, str]:
    user = get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_confirmed:
        return {"message": "Your email is already confirmed"}

    verification_token = create_email_token(user.email)
    background_tasks.add_task(send_verification_email, user.email, verification_token)
    return {"message": "Check your email for confirmation"}


@app.get("/users/me", response_model=UserResponse)
@limiter.limit("5/minute")
def me(request: Request, current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@app.patch("/users/avatar", response_model=UserResponse)
def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        avatar_url = upload_avatar(tmp_path, f"ContactsApp/{current_user.email}")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    user = update_user_avatar(current_user.email, avatar_url, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact_endpoint(
    body: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    try:
        return create_contact(body, db, current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")


@app.get("/contacts", response_model=list[ContactResponse])
def get_contacts_endpoint(
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ContactResponse]:
    return get_contacts(db, current_user, first_name, last_name, email)


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact_endpoint(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    contact = get_contact(contact_id, db, current_user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact_endpoint(
    contact_id: int,
    body: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    try:
        contact = update_contact(contact_id, body, db, current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact_endpoint(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContactResponse:
    contact = delete_contact(contact_id, db, current_user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@app.get("/contacts/upcoming/birthdays", response_model=list[ContactResponse])
def upcoming_birthdays_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ContactResponse]:
    return get_upcoming_birthdays(db, current_user)
