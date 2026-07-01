# Mini Social Network API (Django REST Framework)

REST API for a mini social network featuring user registration with email verification, publications, comments, likes, and a grouped chronological feed.

## Tech Stack

- **Backend:** Django 5.0, Django REST Framework (DRF)
- **Auth:** JWT (SimpleJWT) with 15m access token & 7d refresh token TTL
- **Cryptography:** Argon2id (`argon2-cffi` integrated natively in `PASSWORD_HASHERS`)
- **Database:** PostgreSQL 15 (with custom composite indexes & constraints)
- **Background Tasks:** Celery, Celery Beat, Redis (for scheduled cleanups)
- **Documentation:** `drf-spectacular` (interactive Swagger UI / ReDoc)
- **Testing:** `pytest`, `pytest-django`, `httpx`

## Features

- **User Authentication & Verification:** Account registration, JWT login (supporting username or email), and activation via email links (valid for 24 hours).
- **Publications (Posts):** Create, read, update, and delete posts (restricted to the post's author, who must have a verified email).
- **Comments:** Comment on publications and delete comments (restricted to the comment's author).
- **Likes:** Like and unlike posts (allowed for both verified and unverified users, excluding self-liking and duplicate liking).
- **Grouped Feed:** A chronological feed of posts grouped by author username with support for search keywords, date range filters, and offset pagination.
- **Auto-Cleanup Tasks:** Background Celery tasks to automatically delete unverified users older than 24 hours and posts older than 30 days.

## Project Structure

```
social_network_drf/
├── app/
│   ├── apps.py
│   ├── models.py          # DB Schemas: User, VerificationToken, Post, Comment, Like
│   ├── serializers.py     # DRF input validations and output serializers
│   ├── tasks.py           # Celery background tasks (cleanup routines)
│   ├── urls.py            # API routing patterns
│   └── views/             # API views split by domain: auth.py, social.py, users.py
├── root/
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py          # Celery app initialization
│   ├── settings.py        # Django core settings (Argon2, SimpleJWT, espectacular config)
│   ├── urls.py            # Main URL dispatcher (admin panel, api router, Swagger docs)
│   └── wsgi.py
├── shared/
│   ├── permissions.py     # Custom DRF Permission check classes (IsEmailVerified)
│   └── utils.py           # Reusable utils (e.g., developer console mock email logger)
├── tests/
│   ├── conftest.py        # Pytest setup and global APIClient fixtures
│   ├── test_auth.py       # Authentication integration tests
│   ├── test_cleanup.py    # Celery periodic tasks integration tests
│   └── test_social.py     # Social features integration tests (feed, likes, comments, permissions)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── pyproject.toml
└── README.md
```

## Quick Start

### Using Docker (recommended)

1. Copy env parameters:
   ```bash
   cp .env.example .env
   ```
2. Build and start containers:
   ```bash
   docker compose up --build
   ```
3. The API will be available at `http://localhost:8000/`
4. Interactive Swagger documentation is available at `http://localhost:8000/api/docs/`
5. ReDoc is available at `http://localhost:8000/api/redoc/`

### Local Development

1. Create and activate a python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```
2. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment settings:
   ```bash
   cp .env.example .env
   ```
4. Start database and cache containers (PostgreSQL and Redis) on host ports:
   ```bash
   docker compose up -d db redis
   ```
5. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the local server:
   ```bash
   python manage.py runserver
   ```

---

## API Endpoints

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | Open | Create new account (sends verification link) |
| POST | `/auth/login` | Open | Authenticate credentials, returns JWT tokens |
| GET | `/auth/verify-email` | Open | Verify email address using query token parameter |
| GET | `/auth/me` | JWT | Retrieve current user profile details |

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| PATCH | `/users/me` | JWT | Partial update user profile (username / full name) |

### Publications & Socials

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/posts` | Open | Get paginated list of flat posts |
| POST | `/posts` | JWT (Verified) | Publish a new post |
| GET | `/posts/{id}` | Open | Get detailed post along with its comments |
| PATCH | `/posts/{id}` | JWT (Verified) | Partial update a post (author only) |
| DELETE | `/posts/{id}` | JWT (Verified) | Delete a post (author only) |
| POST | `/posts/{id}/comments` | JWT (Verified) | Add a comment to a post |
| DELETE | `/posts/{post_id}/comments/{comment_id}` | JWT (Verified) | Delete a comment (author only) |
| POST | `/posts/{id}/like` | JWT (Any) | Like a post (self-liking and duplicates blocked) |
| DELETE | `/posts/{id}/like` | JWT (Any) | Remove like from a post |
| GET | `/feed` | Open | Retrieve chronological posts grouped by author |

---

## Running Tests

Tests run inside a temporary, isolated database. Ensure PostgreSQL database service is running before executing tests.

```bash
python -m pytest -v
```

All 10 integration test cases will run:
```
tests/test_auth.py::test_successful_auth_flow PASSED
tests/test_auth.py::test_duplicate_registration_fails PASSED
tests/test_auth.py::test_login_validation PASSED
tests/test_cleanup.py::test_cleanup_unverified_users_task PASSED
tests/test_cleanup.py::test_cleanup_expired_posts_task PASSED
tests/test_social.py::test_access_rules_for_unverified_users PASSED
tests/test_social.py::test_post_crud_and_permissions PASSED
tests/test_social.py::test_comments_flow PASSED
tests/test_social.py::test_likes_constraints PASSED
tests/test_social.py::test_feed_filters_pagination_and_format PASSED
```

---

## Architectural Decisions

- **Argon2id Hashing:** Standard PBKDF2 is substituted with Argon2 (via `argon2-cffi` package) inside settings `PASSWORD_HASHERS` to satisfy the ТЗ's high cryptography guidelines.
- **Service Layer (decoupled business rules):** Following a clean architecture style, views contain no DB creation logic. All domain validations (such as blocking self-likes or double-likes) reside inside service classes.
- **Prevent N+1 Query Issue:** Eager loading (`select_related` and `prefetch_related`) is applied on database queries for posts, comments, and feed retrievals.
- **DB Constraints & Indexes:** Composite database indexes are set on the `created_at` field (descending order) of the Post model to boost feed performance. A unique constraint is set on User-Post pairings on the Like model to guarantee single-like integrity on the DB level.
- **Transactional Beat Cleanup:** Worker database requests are safely configured. The cleanup tasks explicitly invoke `connection.close()` (skipped inside testing transaction blocks using `connection.in_atomic_block`) to avoid celery worker thread pool connection exhaustion.
