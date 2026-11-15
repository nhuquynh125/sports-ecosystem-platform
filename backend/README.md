# Backend — Core (Step 2)

FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL 16 · Pydantic v2 · JWT · passlib/bcrypt.
Implements the **Core** module of `docs/03-ARCHITECTURE-AND-FLOWS.md`: auth + RBAC, users,
sports, player profiles & availability, notifications, chat (REST + WebSocket), admin APIs.

## Run it

```bash
# from the repository root
cp .env.example .env                  # then set SECRET_KEY (python -c "import secrets; print(secrets.token_hex(32))")
docker compose up -d                  # PostgreSQL, wait for "healthy"

cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

alembic upgrade head                  # creates the 10 core tables + seeds the 5 roles
python scripts/seed.py                # 7 sports + 300 users (+ profiles, availability, chats)
uvicorn app.main:app --reload         # http://localhost:8000/docs
```

`python scripts/seed.py --reset` wipes and re-seeds (roles are kept). All seeded users share the
password **`Password123!`**; demo logins: `admin@example.com`, `owner@example.com`,
`organizer@example.com`, `coach@example.com`, `player@example.com`.

Tests (real PostgreSQL needed — the schema uses `citext`/`jsonb`):

```bash
createdb sports_test   # or: docker compose exec db createdb -U sports_admin sports_test
export TEST_DATABASE_URL=postgresql+psycopg2://sports_admin:change_me_in_dotenv@localhost:5432/sports_test
pytest
```

## Layout

```
backend/
├── alembic.ini
├── migrations/versions/20261114_0001_core_schema.py
├── scripts/seed.py
├── tests/
└── app/
    ├── main.py              app factory, CORS, handlers, router mounting under /api/v1
    ├── core/                config, database (naming convention), security, exceptions, utils
    ├── models/              ORM entities (ERD §3)
    ├── schemas/             Pydantic DTOs
    ├── services/            business rules + queries (router -> service; no HTTP types)
    ├── api/deps.py          get_db, get_current_user, require_role
    ├── api/v1/              routers (thin) + router.py
    └── ai/                  empty placeholders for SportScout AI
```

## Endpoints (all under `/api/v1`)

| Area | Endpoint | Access |
|------|----------|--------|
| Health | `GET /health` | public |
| Auth | `POST /auth/register`, `POST /auth/login` | public |
| Users | `GET/PATCH/DELETE /users/me`, `POST /users/me/password`, `GET /users/{id}` (public fields) | authenticated |
| Admin | `GET /admin/users` (`q`, `role`, `is_active`, paging), `GET /admin/users/{id}`, `PATCH /admin/users/{id}/status`, `PUT /admin/users/{id}/roles` | `admin` |
| Sports | `GET /sports`, `GET /sports/{id}` | public |
| Sports | `POST`, `PATCH /{id}`, `DELETE /{id}` | `admin` |
| Profiles | `POST /player-profiles` | `player` |
| Profiles | `GET /player-profiles` (search), `GET /me`, `GET/PATCH/DELETE /{id}` | authenticated (owner/admin for writes) |
| Availability | `GET/POST/PUT /player-profiles/{id}/availability`, `PATCH/DELETE …/{slot_id}` | owner/admin for writes |
| Notifications | `GET /notifications`, `GET /notifications/unread-count`, `PATCH /{id}/read`, `PATCH /read-all` | authenticated |
| Chat | `GET/POST /chat/rooms`, `GET /chat/rooms/{id}`, `GET /chat/rooms/{id}/messages` | members (admin may read) |
| Chat WS | `WS /ws/chat/{room_id}?token=<jwt>` | members |

**Lock/unlock**: `PATCH /admin/users/{id}/status` with `{"is_active": false|true}`; an empty body toggles.
An admin cannot lock themselves or the last active admin. A locked user's token stops working immediately
(roles and `is_active` are read from the DB on every request, not from the token).

### WebSocket protocol

* Connect: `ws://localhost:8000/api/v1/ws/chat/{room_id}?token=<access_token>` (or an `Authorization: Bearer` header for non-browser clients).
* Send: `{"content": "text"}` (1–2000 chars) · `{"type": "ping"}` → `{"type": "pong"}`.
* Receive (everyone in the room, sender included): `{"type": "message", "data": {id, room_id, sender_id, sender_name, content, message_type, created_at}}`.
* Invalid frames → `{"type": "error", "detail": "..."}`; the socket stays open.
* Close codes: `4401` unauthenticated/expired token, `4403` not a member / account disabled, `4404` room not found.
* Messages are saved to `chat_messages` **before** being broadcast. Membership is re-checked on every message.
* The access-token lifetime (15 min) also bounds a socket: the next frame after expiry closes it with 4401 (reconnect with a fresh token).

## Conventions honoured

* Errors are always `{"detail": ...}` (401/403/404/409/500 and framework 404/405 too). Only **422** carries a *list* of
  messages, e.g. `["email: value is not a valid email address"]`, as README §2 allows.
* Tables/columns/constraints follow the README naming rules (`uq_users_email`, `ck_player_profiles_skill_level`, `fk_…`).
* Timestamps are `timestamptz`, the DB session runs in UTC, JSON output is ISO-8601.
* Pagination: `?page=1&page_size=20` (max 100) → `{items,total,page,page_size}`.

## Decisions & deviations from the Step 1 docs (please review)

1. **Schema.** `user_roles` and `chat_room_members` are included (needed for M:N roles / chat membership) although the task
   list named only 8 tables. `refresh_tokens` is **not** created yet: Step 2 issues access tokens only (the refresh flow in
   ARCH §8.3 is still to do).
2. **Deferred FKs.** `chat_rooms.team_id` / `tournament_id` are plain unique `bigint` columns; the FKs are added by the
   SportHub / SportArena migrations when `teams` / `tournaments` exist. The `CHECK` tying room type to team/tournament is in place.
3. **ERD relaxations.** `chat_rooms.created_by` and `chat_messages.sender_id` are nullable (`ON DELETE SET NULL`) so system
   messages/rooms are possible. Added `CHECK (char_length(content) BETWEEN 1 AND 2000)` (SRS UC-SH-05).
4. **Endpoint paths.** User administration lives under `/admin/users…` (as requested) instead of `/users` + `/users/{id}/roles`
   in ARCH §6.2. Profile *area* is `player_profiles.city`; *preferred sports* = one profile per sport.
5. **RBAC.** `require_role(...)` accepts `require_role("admin","coach")` and `require_role(["admin"])`; alias `require_roles`.
   Roles are read from the DB per request (immediate revocation) — the JWT `roles` claim is informational.
6. **Account deletion.** `DELETE /users/me` anonymises and deactivates (NFR-CMP-01) rather than removing the row.
7. **Layers.** Queries live inside services (no separate repository layer yet) to keep Step 2 small; they can be extracted
   without changing routers.
8. **Not in this step:** rate limiting (NFR-SEC-06), refresh tokens, password reset / e-mail verification, notification push
   over WebSocket, multi-instance WebSocket fan-out (the in-process `ConnectionManager` needs Redis/LISTEN-NOTIFY for that).

### Doc updates to make in the same PR (README: "docs change with code")
* `docs/03` §6.2: replace `/users`, `/users/{id}/roles` with `/admin/users`, `/admin/users/{id}/status`, `/admin/users/{id}/roles`; add `/player-profiles…`, `/notifications…`, `/ws/chat/{room_id}`, `/health`.
* `docs/02` §3: note `chat_rooms.created_by` / `chat_messages.sender_id` nullable + content-length check; `refresh_tokens` and the team/tournament FKs arrive later.
* Root `README.md`: Roadmap step 2 → ✅; add the "Run it" block above.
