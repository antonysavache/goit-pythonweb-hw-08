# Homework 12 - Contacts REST API (Testing, Docs, Redis, Roles)

Repository name for submission: `goit-pythonweb-hw-12`.

## Implemented

- Authentication and JWT authorization (`access_token`)
- Email verification and password reset flow
- Role model (`user`, `admin`) with admin bootstrap and admin-only role management
- Access to contacts only for owner
- `/users/me` rate limit (`5/minute`)
- CORS support
- Avatar upload to Cloudinary (admin-only)
- Redis cache for `get_current_user`
- Unit tests for repository modules
- Integration tests for API routes
- Sphinx documentation from docstrings

## Environment variables

Use `.env` (see `.env.example`):

- `DATABASE_URL`
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXP_MINUTES`
- `CORS_ORIGINS`
- `APP_BASE_URL`
- SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- Cloudinary: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- `ADMIN_EMAILS` - comma-separated emails that receive the `admin` role on registration
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`, `REDIS_CACHE_TTL`

## Admin role management

The first admin can be created without direct database edits:

1. Add the admin email to `.env` before registration:

```env
ADMIN_EMAILS=admin@example.com
```

2. Register with that email through `POST /auth/register`.
3. Confirm the email and log in.
4. Use the admin token to assign roles:

```http
PATCH /users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{"role": "admin"}
```

Only authenticated users with role `admin` can update user roles.

## Run with Docker Compose

```bash
docker compose up -d --build
```

API docs:

- `http://127.0.0.1:8000/docs`

## Tests and coverage

```bash
pytest
```

Coverage threshold is configured in `pytest.ini` and set to `75%`.

## Build Sphinx docs

```bash
sphinx-build -b html docs docs/_build
```
