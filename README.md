# Sports Ecosystem & AI Platform

Capstone Project — **Đồ án Cơ sở 2**, Faculty of Computer Science.

An integrated platform that connects players, venues, organizers and coaches
through six cooperating modules sharing one identity system and one database.

| # | Module | Purpose |
|---|--------|---------|
| 1 | **CourtBook** | Venue discovery, court availability and online booking |
| 2 | **SportHub** | Player profiles, availability, teams, matchmaking and chat |
| 3 | **SportIQ** | Match statistics, player ratings and leaderboards |
| 4 | **SportArena** | Tournament creation, registration, groups, fixtures and standings |
| 5 | **SportScout AI** | AI-assisted talent evaluation and recommendations for coaches |
| 6 | **Football Manager Lite** | Club-management simulation game seeded from real player data |

> Development follows a **documentation-first** workflow: all analysis and
> design artifacts in [`docs/`](./docs) must be reviewed before implementation.

---

## Repository Structure

```text
sports-ecosystem-platform/
├── frontend/              # Web client (SPA)
├── backend/               # REST API (modular monolith)
├── docs/                  # System analysis & design documentation
│   ├── 01-SRS.md                        # Software Requirements Specification
│   ├── 02-ERD.md                        # Entity-Relationship Diagram & data dictionary
│   └── 03-ARCHITECTURE-AND-FLOWS.md     # Architecture + sequence diagrams
├── docker/
│   └── postgres/init/     # One-time DB initialisation scripts (extensions)
├── docker-compose.yml     # PostgreSQL (persistent volume + healthcheck)
├── .env.example           # Environment template
├── .gitignore
└── README.md
```

## Documentation Index

| Document | Content |
|----------|---------|
| [01-SRS.md](./docs/01-SRS.md) | Scope, actors/roles, functional & non-functional requirements, use-case specifications for all 6 modules |
| [02-ERD.md](./docs/02-ERD.md) | Mermaid ER diagrams (core + per-module), constraints, data dictionary |
| [03-ARCHITECTURE-AND-FLOWS.md](./docs/03-ARCHITECTURE-AND-FLOWS.md) | System architecture, RBAC matrix, sequence diagrams (Auth/RBAC, Booking, Tournament registration) |

Mermaid diagrams render natively on GitHub, GitLab and in VS Code
(extension: *Markdown Preview Mermaid Support*).

---

## Getting Started

**Prerequisites:** Docker and Docker Compose v2.

```bash
# 1. Create your local environment file
cp .env.example .env

# 2. Start PostgreSQL
docker compose up -d

# 3. Check health (STATUS should become "healthy")
docker compose ps

# 4. Stop (data is kept)            |  Stop and DELETE all data
docker compose down                 |  docker compose down -v
```

Connection string (default values):
`postgresql://sports_admin:change_me_in_dotenv@localhost:5432/sports_ecosystem`

---

## Project Conventions

These conventions are **binding for every module** and every team member.

### 1. API

| Rule | Convention |
|------|-----------|
| **Base prefix** | All endpoints are served under **`/api/v1`** (e.g. `POST /api/v1/auth/login`) |
| **Resource naming** | Plural, lowercase, kebab-case nouns: `/api/v1/venues`, `/api/v1/tournaments/{id}/registrations` |
| **Format** | JSON request and response bodies (`Content-Type: application/json`) |
| **Authentication** | `Authorization: Bearer <access_token>` (JWT) |
| **Time** | ISO-8601 in UTC, e.g. `2026-11-20T18:00:00Z` |
| **Versioning** | Breaking changes ⇒ new prefix `/api/v2`; `/api/v1` stays stable |

### 2. Error Response Format

Every error — validation, authentication, authorization, not found, conflict,
server — returns the **same envelope**:

```json
{ "detail": "Human-readable description of the problem" }
```

| Status | Meaning | Example `detail` |
|--------|---------|------------------|
| 400 | Bad request / business rule violated | `"Booking must be at least 30 minutes long"` |
| 401 | Missing, invalid or expired token | `"Could not validate credentials"` |
| 403 | Authenticated but role not allowed | `"Insufficient permissions"` |
| 404 | Resource not found | `"Court not found"` |
| 409 | Conflict (duplicate / overlap) | `"Time slot is already booked"` |
| 422 | Request body failed schema validation | `"Invalid value for field 'email'"` (a list of messages is allowed for 422 only) |
| 500 | Unexpected server error | `"Internal server error"` |

### 3. Database Naming

| Element | Rule | Example |
|---------|------|---------|
| Tables | **Plural `snake_case`** | `users`, `player_profiles`, `tournament_teams` |
| Columns | Singular `snake_case` | `full_name`, `start_time` |
| Primary key | `id` (`bigint` identity) | `bookings.id` |
| Foreign key | `<singular_table>_id` | `bookings.court_id → courts.id` |
| Junction tables | Plural of both entities or a domain noun | `user_roles`, `team_members` |
| Timestamps | `created_at`, `updated_at` as `timestamptz` (UTC) | — |
| Booleans | Prefix `is_` / `has_` | `is_active` |
| Indexes / constraints | `ix_<table>_<cols>`, `uq_<table>_<cols>`, `ck_<table>_<rule>`, `fk_<table>_<ref>` | `uq_users_email` |
| Module-specific prefix | Only for Football Manager Lite, to avoid clashing with real-world entities | `fm_clubs`, `fm_players` |

### 4. Git Workflow

- Branches: `main` (stable) ← `develop` ← `feature/<module>-<short-name>`
  (e.g. `feature/courtbook-booking-api`).
- Commits follow **Conventional Commits**: `feat(courtbook): add overlap check`,
  `fix(auth): refresh token rotation`, `docs(erd): update bookings`.
- Every change reaches `develop` through a Pull Request with at least one review.
- Documentation changes that alter requirements, schema or flows must update
  the matching file in `docs/` in the **same** PR.

### 5. Secrets

Never commit `.env`. Only `.env.example` (with placeholder values) is tracked.

---

## Roadmap

| Step | Deliverable | Status |
|------|-------------|--------|
| 1 | Monorepo setup + System Analysis & Design documentation | ✅ This commit |
| 2 | Backend foundation: core schema migrations, auth, RBAC | ⏳ |
| 3 | Module implementation (CourtBook → SportHub → SportArena → …) | ⏳ |
| 4 | Frontend, integration, testing, final report | ⏳ |
