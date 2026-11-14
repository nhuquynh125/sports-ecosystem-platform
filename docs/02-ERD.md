# Entity-Relationship Design (ERD)

**Project:** Sports Ecosystem & AI Platform
**Document ID:** `02-ERD` | **Version:** 1.0 | **Status:** Draft for review
**DBMS:** PostgreSQL 16 | **Depends on:** `01-SRS.md`

---

## Table of Contents

1. [Design Principles and Conventions](#1-design-principles-and-conventions)
2. [Conceptual Overview (all entities)](#2-conceptual-overview-all-entities)
3. [Core Schema](#3-core-schema)
4. [CourtBook Schema](#4-courtbook-schema)
5. [SportHub / Teams Schema](#5-sporthub--teams-schema)
6. [SportArena Schema](#6-sportarena-schema)
7. [SportIQ Schema](#7-sportiq-schema)
8. [SportScout AI Schema](#8-sportscout-ai-schema)
9. [Football Manager Lite Schema](#9-football-manager-lite-schema)
10. [Integrity Constraints and Business Rules](#10-integrity-constraints-and-business-rules)
11. [Index Strategy](#11-index-strategy)
12. [Enumerations](#12-enumerations)
13. [Table Catalogue and Requirement Traceability](#13-table-catalogue-and-requirement-traceability)

---

## 1. Design Principles and Conventions

| Topic | Decision |
|-------|----------|
| **Table names** | Plural `snake_case` (`users`, `player_profiles`). Football Manager Lite tables use the prefix `fm_` (`fm_clubs`). |
| **Primary keys** | `id bigint GENERATED ALWAYS AS IDENTITY`. Junction tables with a natural composite key use that composite as PK. |
| **Foreign keys** | `<singular_table>_id`; always declared with an explicit `ON DELETE` rule (`CASCADE`, `RESTRICT` or `SET NULL`). |
| **Timestamps** | `created_at` (default `now()`) and `updated_at` as `timestamptz`, stored in UTC. |
| **Soft delete** | Only where history matters (`users.is_active`, `chat_messages.deleted_at`); otherwise hard delete or status enums. |
| **Enumerations** | `varchar` + `CHECK` constraint (easier to migrate than native `ENUM`); values listed in [§12](#12-enumerations). |
| **Money** | `numeric(12,2)` in VND-compatible units; never floating point. |
| **Text search** | `citext` for case-insensitive `email` and `username`. |
| **Flexible data** | `jsonb` only for sport-specific or model-generated payloads (`stats`, `attributes`, `data`). |
| **Normalisation** | Schema is in 3NF; the only intentional denormalisations are `venues.avg_rating`, `standings.*` and `player_ratings.matches_played` (derived, maintained transactionally) for read performance. |
| **Extensions** | `btree_gist` (booking exclusion constraint), `citext` — installed by `docker/postgres/init/01-extensions.sql`. |

**Mermaid notation:** `||` exactly one · `o|` zero or one · `}o` zero or many ·
`}|` one or many. Key markers: `PK` primary key, `FK` foreign key, `UK` unique.

---

## 2. Conceptual Overview (all entities)

Relationships only (attributes are shown in the module diagrams below).

```mermaid
erDiagram
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : granted_as
    users ||--o{ refresh_tokens : owns
    users ||--o{ player_profiles : has
    sports ||--o{ player_profiles : of
    player_profiles ||--o{ player_availability : declares
    users ||--o{ notifications : receives
    users ||--o{ chat_room_members : joins
    chat_rooms ||--o{ chat_room_members : contains
    chat_rooms ||--o{ chat_messages : holds
    users ||--o{ chat_messages : sends

    users ||--o{ venues : owns
    venues ||--o{ courts : contains
    sports ||--o{ courts : played_on
    courts ||--o{ bookings : reserved_by
    users ||--o{ bookings : makes
    bookings ||--o{ payments : paid_by
    courts ||--o{ court_closures : blocked_by
    venues ||--o{ venue_reviews : rated_in
    bookings ||--o| venue_reviews : reviewed_as

    sports ||--o{ teams : of
    users ||--o{ teams : captains
    teams ||--o{ team_members : has
    users ||--o{ team_members : is
    teams |o--o| chat_rooms : discusses_in

    users ||--o{ tournaments : organizes
    sports ||--o{ tournaments : of
    tournaments ||--o{ tournament_teams : receives
    teams ||--o{ tournament_teams : registers
    tournaments ||--o{ groups : divided_into
    groups ||--o{ tournament_teams : contains
    tournaments ||--o{ matches : schedules
    groups ||--o{ matches : plays
    teams ||--o{ matches : competes
    courts |o--o{ matches : hosted_on
    groups ||--o{ standings : ranks
    teams ||--o{ standings : positioned

    matches ||--o{ match_player_stats : records
    users ||--o{ match_player_stats : performs
    users ||--o{ player_ratings : rated
    sports ||--o{ player_ratings : in
    player_ratings ||--o{ rating_history : changes
    matches ||--o{ rating_history : causes

    users ||--o{ scouting_reports : writes
    users ||--o{ scouting_reports : subject_of
    users ||--o{ scout_watchlists : keeps
    users ||--o{ scout_watchlists : watched_in

    users ||--o| fm_clubs : manages
    fm_clubs ||--o{ fm_players : employs
    users |o--o{ fm_players : seeds
    fm_seasons ||--o{ fm_fixtures : contains
    fm_clubs ||--o{ fm_fixtures : plays
    fm_fixtures ||--o{ fm_lineups : sets
    fm_players ||--o{ fm_lineups : selected_in
```

---

## 3. Core Schema

Tables: `users`, `roles`, `user_roles`, `refresh_tokens`, `sports`,
`player_profiles`, `player_availability`, `notifications`, `chat_rooms`,
`chat_room_members`, `chat_messages`.

```mermaid
erDiagram
    users {
        bigint id PK
        citext email UK "login identifier"
        citext username UK
        varchar password_hash "bcrypt or argon2"
        varchar full_name
        varchar phone
        varchar avatar_url
        date date_of_birth
        boolean is_active "false = disabled"
        boolean allow_scouting "opt-in for SportScout AI"
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
    }
    roles {
        smallint id PK
        varchar name UK "admin player venue_owner organizer coach"
        varchar description
    }
    user_roles {
        bigint user_id PK, FK
        smallint role_id PK, FK
        timestamptz assigned_at
        bigint assigned_by FK "admin who granted"
    }
    refresh_tokens {
        bigint id PK
        bigint user_id FK
        varchar token_hash UK "SHA-256 of token"
        timestamptz expires_at
        timestamptz revoked_at
        timestamptz created_at
    }
    sports {
        smallint id PK
        varchar name UK
        varchar slug UK
        varchar description
        varchar icon_url
        boolean is_active
    }
    player_profiles {
        bigint id PK
        bigint user_id FK
        smallint sport_id FK
        varchar position
        varchar skill_level "beginner intermediate advanced pro"
        varchar preferred_side "left right both"
        smallint height_cm
        smallint weight_kg
        varchar city
        text bio
        boolean is_visible
        timestamptz created_at
        timestamptz updated_at
    }
    player_availability {
        bigint id PK
        bigint player_profile_id FK
        smallint day_of_week "1 Monday to 7 Sunday"
        time start_time
        time end_time
        timestamptz created_at
    }
    notifications {
        bigint id PK
        bigint user_id FK
        varchar type "booking_confirmed registration_approved ..."
        varchar title
        text body
        jsonb data "deep-link payload"
        boolean is_read
        timestamptz read_at
        timestamptz created_at
    }
    chat_rooms {
        bigint id PK
        varchar type "direct team tournament"
        varchar name
        bigint team_id FK "nullable"
        bigint tournament_id FK "nullable"
        bigint created_by FK
        timestamptz created_at
    }
    chat_room_members {
        bigint room_id PK, FK
        bigint user_id PK, FK
        timestamptz joined_at
        timestamptz last_read_at
    }
    chat_messages {
        bigint id PK
        bigint room_id FK
        bigint sender_id FK
        text content
        varchar message_type "text image system"
        timestamptz created_at
        timestamptz edited_at
        timestamptz deleted_at
    }

    users ||--o{ user_roles : has
    roles ||--o{ user_roles : granted_as
    users ||--o{ refresh_tokens : owns
    users ||--o{ player_profiles : has
    sports ||--o{ player_profiles : of
    player_profiles ||--o{ player_availability : declares
    users ||--o{ notifications : receives
    chat_rooms ||--o{ chat_room_members : contains
    users ||--o{ chat_room_members : joins
    chat_rooms ||--o{ chat_messages : holds
    users ||--o{ chat_messages : sends
    users ||--o{ chat_rooms : creates
```

**Notes**

- `user_roles` implements the many-to-many between `users` and `roles` so one
  person can be both `player` and `coach`. The `roles` table is seeded with the
  five roles of the SRS and is read-mostly.
- `player_profiles` has `UNIQUE (user_id, sport_id)`: one profile per user and sport.
- `player_availability` has `CHECK (end_time > start_time)` and `CHECK (day_of_week BETWEEN 1 AND 7)`.
- `chat_rooms` has `CHECK` that `team` rooms carry `team_id`, `tournament` rooms carry `tournament_id`, `direct` rooms carry neither. `team_id` and `tournament_id` are `UNIQUE` (at most one room each).
- `chat_rooms.team_id` / `tournament_id` foreign keys point to `teams` and `tournaments` (shown in §5–6; omitted here to keep the diagram readable).

---

## 4. CourtBook Schema

Tables: `venues`, `courts`, `court_closures`, `bookings`, `payments`, `venue_reviews`.

```mermaid
erDiagram
    users {
        bigint id PK
    }
    sports {
        smallint id PK
    }
    venues {
        bigint id PK
        bigint owner_id FK "role venue_owner"
        varchar name
        text description
        varchar address
        varchar city
        varchar district
        numeric latitude
        numeric longitude
        varchar phone
        time open_time
        time close_time
        varchar status "pending approved rejected suspended"
        varchar rejection_reason
        numeric avg_rating "denormalised"
        integer review_count "denormalised"
        timestamptz created_at
        timestamptz updated_at
    }
    courts {
        bigint id PK
        bigint venue_id FK
        smallint sport_id FK
        varchar name
        varchar surface_type "grass turf wood hard"
        smallint capacity "players"
        numeric hourly_price
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    court_closures {
        bigint id PK
        bigint court_id FK
        timestamptz start_time
        timestamptz end_time
        varchar reason
        bigint created_by FK
        timestamptz created_at
    }
    bookings {
        bigint id PK
        varchar booking_code UK "human-readable"
        bigint court_id FK
        bigint user_id FK
        timestamptz start_time
        timestamptz end_time
        numeric total_price
        varchar status "pending confirmed cancelled completed expired"
        timestamptz expires_at "payment hold deadline"
        varchar note
        timestamptz cancelled_at
        varchar cancel_reason
        timestamptz created_at
        timestamptz updated_at
    }
    payments {
        bigint id PK
        bigint booking_id FK
        numeric amount
        varchar method "card ewallet cash"
        varchar status "initiated succeeded failed refunded"
        varchar transaction_ref UK
        timestamptz paid_at
        timestamptz created_at
    }
    venue_reviews {
        bigint id PK
        bigint venue_id FK
        bigint user_id FK
        bigint booking_id FK "UK - one review per booking"
        smallint rating "1 to 5"
        text comment
        timestamptz created_at
    }

    users ||--o{ venues : owns
    venues ||--o{ courts : contains
    sports ||--o{ courts : played_on
    courts ||--o{ court_closures : blocked_by
    courts ||--o{ bookings : reserved_by
    users ||--o{ bookings : makes
    bookings ||--o{ payments : paid_by
    venues ||--o{ venue_reviews : rated_in
    users ||--o{ venue_reviews : writes
    bookings ||--o| venue_reviews : reviewed_as
```

**Notes**

- `bookings.start_time`/`end_time` are half-open: the interval is `[start_time, end_time)`, so back-to-back bookings (10:00–11:00 and 11:00–12:00) are allowed.
- **Double-booking prevention** is enforced by an exclusion constraint (see [§10.1](#101-no-overlapping-bookings-double-booking-prevention)).
- `court_closures` have their own exclusion constraint so closures cannot overlap each other; overlap between a closure and bookings is checked in the service layer inside the booking transaction.
- `venues`: `CHECK (close_time > open_time)`; `courts`: `CHECK (hourly_price >= 0)`.
- `venue_reviews`: `UNIQUE (booking_id)`, `CHECK (rating BETWEEN 1 AND 5)`.

---

## 5. SportHub / Teams Schema

Tables: `teams`, `team_members` (player profile and chat tables are in §3).

```mermaid
erDiagram
    users {
        bigint id PK
    }
    sports {
        smallint id PK
    }
    teams {
        bigint id PK
        smallint sport_id FK
        varchar name
        varchar logo_url
        varchar city
        text description
        bigint captain_id FK "users.id"
        bigint coach_id FK "users.id - nullable"
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    team_members {
        bigint id PK
        bigint team_id FK
        bigint user_id FK
        varchar status "invited active declined left removed"
        varchar position
        smallint jersey_number
        bigint invited_by FK
        timestamptz joined_at
        timestamptz created_at
        timestamptz updated_at
    }
    chat_rooms {
        bigint id PK
        bigint team_id FK
    }

    sports ||--o{ teams : of
    users ||--o{ teams : captains
    users |o--o{ teams : coaches
    teams ||--o{ team_members : has
    users ||--o{ team_members : is
    teams |o--o| chat_rooms : discusses_in
```

**Notes**

- `teams`: `UNIQUE (sport_id, name)`.
- `team_members`: `UNIQUE (team_id, user_id)`; partial unique index `(team_id, jersey_number) WHERE status = 'active'`.
- The captain is also inserted as an `active` member; service logic keeps `teams.captain_id` and membership consistent (captain cannot leave without transferring).

---

## 6. SportArena Schema

Tables: `tournaments`, `tournament_teams`, `groups`, `matches`, `standings`.

```mermaid
erDiagram
    users {
        bigint id PK
    }
    teams {
        bigint id PK
    }
    courts {
        bigint id PK
    }
    tournaments {
        bigint id PK
        bigint organizer_id FK "role organizer"
        smallint sport_id FK
        varchar name
        text description
        varchar format "round_robin knockout group_knockout"
        varchar location
        timestamptz registration_start
        timestamptz registration_end
        date start_date
        date end_date
        smallint max_teams
        smallint min_players_per_team
        numeric entry_fee
        varchar status "draft open closed ongoing completed cancelled"
        timestamptz created_at
        timestamptz updated_at
    }
    groups {
        bigint id PK
        bigint tournament_id FK
        varchar name "A B C ..."
        timestamptz created_at
    }
    tournament_teams {
        bigint id PK
        bigint tournament_id FK
        bigint team_id FK
        bigint group_id FK "nullable until draw"
        varchar status "pending approved rejected withdrawn"
        bigint registered_by FK "captain"
        bigint reviewed_by FK "organizer - nullable"
        timestamptz reviewed_at
        varchar reject_reason
        smallint seed
        timestamptz registered_at
        timestamptz updated_at
    }
    matches {
        bigint id PK
        bigint tournament_id FK
        bigint group_id FK "nullable for knockout"
        varchar stage "group round_of_16 quarter semi final"
        smallint round_number
        bigint home_team_id FK
        bigint away_team_id FK
        bigint court_id FK "nullable - CourtBook link"
        timestamptz scheduled_at
        smallint home_score
        smallint away_score
        smallint home_penalty
        smallint away_penalty
        bigint winner_team_id FK "nullable"
        varchar status "scheduled live finished postponed cancelled"
        timestamptz created_at
        timestamptz updated_at
    }
    standings {
        bigint id PK
        bigint tournament_id FK
        bigint group_id FK
        bigint team_id FK
        smallint played
        smallint won
        smallint drawn
        smallint lost
        smallint goals_for
        smallint goals_against
        smallint points
        timestamptz updated_at
    }

    users ||--o{ tournaments : organizes
    tournaments ||--o{ groups : divided_into
    tournaments ||--o{ tournament_teams : receives
    teams ||--o{ tournament_teams : registers
    groups |o--o{ tournament_teams : contains
    users ||--o{ tournament_teams : registers_by
    tournaments ||--o{ matches : schedules
    groups |o--o{ matches : plays
    teams ||--o{ matches : home_or_away
    courts |o--o{ matches : hosted_on
    groups ||--o{ standings : ranks
    teams ||--o{ standings : positioned
    tournaments ||--o{ standings : summarises
```

**Notes**

- `tournament_teams`: `UNIQUE (tournament_id, team_id)`. The *registration approval workflow* is the `status` column: `pending → approved | rejected`, and `withdrawn` from `pending`/`approved`.
- `groups`: `UNIQUE (tournament_id, name)`.
- `standings`: `UNIQUE (group_id, team_id)`; ranking = `points DESC, goal_difference DESC, goals_for DESC`.
- `matches`: `CHECK (home_team_id <> away_team_id)`; scores are `NULL` until `finished`.
- `tournaments`: `CHECK (registration_end > registration_start)`, `CHECK (start_date >= registration_end::date)`, `CHECK (max_teams >= 2)`.
- Capacity rule (`approved` count ≤ `max_teams`) is enforced in the approval transaction under a row lock on the tournament (see [§10.3](#103-tournament-capacity)).

---

## 7. SportIQ Schema

Tables: `match_player_stats`, `player_ratings`, `rating_history`.

```mermaid
erDiagram
    users {
        bigint id PK
    }
    sports {
        smallint id PK
    }
    matches {
        bigint id PK
    }
    teams {
        bigint id PK
    }
    match_player_stats {
        bigint id PK
        bigint match_id FK
        bigint user_id FK "player"
        bigint team_id FK
        smallint minutes_played
        smallint points_scored "goals or points"
        smallint assists
        smallint yellow_cards
        smallint red_cards
        numeric performance_score "0 to 10"
        jsonb stats "sport-specific metrics"
        bigint recorded_by FK
        timestamptz created_at
        timestamptz updated_at
    }
    player_ratings {
        bigint id PK
        bigint user_id FK
        smallint sport_id FK
        integer rating_value "Elo - default 1000"
        integer matches_played
        timestamptz updated_at
    }
    rating_history {
        bigint id PK
        bigint player_rating_id FK
        bigint match_id FK
        integer old_rating
        integer new_rating
        integer delta
        timestamptz created_at
    }

    matches ||--o{ match_player_stats : records
    users ||--o{ match_player_stats : performs
    teams ||--o{ match_player_stats : for_team
    users ||--o{ player_ratings : rated
    sports ||--o{ player_ratings : in
    player_ratings ||--o{ rating_history : changes
    matches ||--o{ rating_history : causes
```

**Notes**

- `match_player_stats`: `UNIQUE (match_id, user_id)`; `CHECK (minutes_played >= 0)`.
- `player_ratings`: `UNIQUE (user_id, sport_id)`.
- `rating_history`: `UNIQUE (player_rating_id, match_id)` makes the Elo update **idempotent** (re-processing a match cannot double-apply).
- `rating_history.delta = new_rating - old_rating` (`CHECK`).

---

## 8. SportScout AI Schema

Tables: `scouting_reports`, `scout_watchlists`.

```mermaid
erDiagram
    users {
        bigint id PK
    }
    sports {
        smallint id PK
    }
    scouting_reports {
        bigint id PK
        bigint coach_id FK "report author"
        bigint player_id FK "subject - users.id"
        smallint sport_id FK
        numeric ai_score "0 to 100"
        jsonb attributes "pace shooting passing ..."
        jsonb top_factors "explanation of score"
        text summary
        varchar model_version
        integer matches_considered
        timestamptz generated_at
    }
    scout_watchlists {
        bigint id PK
        bigint coach_id FK
        bigint player_id FK "users.id"
        smallint sport_id FK
        text notes
        timestamptz created_at
        timestamptz updated_at
    }

    users ||--o{ scouting_reports : writes
    users ||--o{ scouting_reports : subject_of
    sports ||--o{ scouting_reports : in
    users ||--o{ scout_watchlists : keeps
    users ||--o{ scout_watchlists : watched_in
    sports ||--o{ scout_watchlists : in
```

**Notes**

- `scout_watchlists`: `UNIQUE (coach_id, player_id, sport_id)`.
- `scouting_reports`: `CHECK (ai_score BETWEEN 0 AND 100)`, `CHECK (coach_id <> player_id)`. Reports are **immutable** snapshots (re-scoring creates a new row) so that history and model version are auditable.
- A report may only be created if the subject has `users.allow_scouting = true` and enough `match_player_stats`.

---

## 9. Football Manager Lite Schema

Tables: `fm_clubs`, `fm_players`, `fm_seasons`, `fm_fixtures`, `fm_lineups`.

```mermaid
erDiagram
    users {
        bigint id PK
    }
    fm_clubs {
        bigint id PK
        bigint user_id FK "UK - one club per manager"
        varchar name UK
        varchar crest_url
        numeric budget
        varchar default_formation "4-4-2"
        timestamptz created_at
        timestamptz updated_at
    }
    fm_players {
        bigint id PK
        bigint club_id FK "nullable - free agent"
        bigint source_user_id FK "nullable - seeded from real player"
        varchar name
        varchar position "GK DF MF FW"
        smallint age
        smallint pace
        smallint shooting
        smallint passing
        smallint defending
        smallint stamina
        smallint overall "derived 1 to 99"
        numeric market_value
        timestamptz created_at
        timestamptz updated_at
    }
    fm_seasons {
        bigint id PK
        varchar name UK
        varchar status "upcoming active finished"
        date start_date
        date end_date
        timestamptz created_at
    }
    fm_fixtures {
        bigint id PK
        bigint season_id FK
        smallint round_number
        bigint home_club_id FK
        bigint away_club_id FK
        smallint home_goals
        smallint away_goals
        varchar status "scheduled played"
        bigint random_seed "reproducible simulation"
        jsonb events "goals cards minutes"
        timestamptz simulated_at
        timestamptz created_at
    }
    fm_lineups {
        bigint id PK
        bigint fixture_id FK
        bigint club_id FK
        bigint player_id FK
        varchar slot_position "e.g. LB CM ST"
        boolean is_starter
        timestamptz created_at
    }

    users ||--o| fm_clubs : manages
    fm_clubs |o--o{ fm_players : employs
    users |o--o{ fm_players : seeds
    fm_seasons ||--o{ fm_fixtures : contains
    fm_clubs ||--o{ fm_fixtures : home
    fm_clubs ||--o{ fm_fixtures : away
    fm_fixtures ||--o{ fm_lineups : sets
    fm_clubs ||--o{ fm_lineups : fielded_by
    fm_players ||--o{ fm_lineups : selected_in
```

**Notes**

- `fm_players`: `CHECK` that each attribute and `overall` is between 1 and 99.
- `fm_fixtures`: `CHECK (home_club_id <> away_club_id)`, `UNIQUE (season_id, round_number, home_club_id)`.
- `fm_lineups`: `UNIQUE (fixture_id, player_id)`; exactly 11 starters per club and fixture is validated in the service layer (a deferred constraint trigger may be added later).
- The league table is **derived** from `fm_fixtures` (view/query) — no stored table is needed.
- `fm_players.source_user_id` links to a real player only when that player has `allow_scouting = true` (consent reuse).

---

## 10. Integrity Constraints and Business Rules

### 10.1 No overlapping bookings (double-booking prevention)

The guarantee is delegated to PostgreSQL so that it holds under **any**
concurrency level and regardless of which code path writes the row.

```sql
-- Requires: CREATE EXTENSION btree_gist;
ALTER TABLE bookings
  ADD CONSTRAINT ex_bookings_no_overlap
  EXCLUDE USING gist (
      court_id WITH =,
      tstzrange(start_time, end_time, '[)') WITH &&
  )
  WHERE (status IN ('pending', 'confirmed'));

ALTER TABLE bookings
  ADD CONSTRAINT ck_bookings_time_order CHECK (end_time > start_time);
```

How it works:

- Two rows conflict when they have the **same `court_id`** *and* their time ranges **overlap** (`&&`).
- The `WHERE` clause makes only `pending` and `confirmed` rows "active"; `cancelled`, `expired` and `completed` rows never block a slot, so cancelling or expiring a booking frees it automatically.
- `'[)'` (closed start, open end) allows adjacent bookings.
- A conflicting `INSERT`/`UPDATE` raises SQLSTATE `23P01` (`exclusion_violation`), which the API maps to **HTTP 409** `{ "detail": "Time slot is already booked" }`.
- Of two simultaneous transactions inserting overlapping rows, one commits and the other fails — no check-then-insert race window exists.

### 10.2 Other key constraints

| Table | Constraint | Purpose |
|-------|-----------|---------|
| `users` | `UNIQUE (email)`, `UNIQUE (username)` (citext) | Case-insensitive identity |
| `user_roles` | `PRIMARY KEY (user_id, role_id)` | No duplicate role grants |
| `player_profiles` | `UNIQUE (user_id, sport_id)` | One profile per sport |
| `bookings` | `ex_bookings_no_overlap`, `ck_bookings_time_order`, `UNIQUE (booking_code)` | Integrity of reservations |
| `court_closures` | `EXCLUDE USING gist (court_id WITH =, tstzrange(start_time,end_time,'[)') WITH &&)` | Closures cannot overlap |
| `venue_reviews` | `UNIQUE (booking_id)`, `CHECK (rating BETWEEN 1 AND 5)` | One review per booking |
| `teams` | `UNIQUE (sport_id, name)` | No duplicate team names per sport |
| `team_members` | `UNIQUE (team_id, user_id)` | Single membership row per player and team |
| `tournament_teams` | `UNIQUE (tournament_id, team_id)` | A team registers once per tournament |
| `groups` | `UNIQUE (tournament_id, name)` | Unique group labels |
| `matches` | `CHECK (home_team_id <> away_team_id)` | A team cannot play itself |
| `match_player_stats` | `UNIQUE (match_id, user_id)` | One stat line per player and match |
| `rating_history` | `UNIQUE (player_rating_id, match_id)` | Idempotent Elo updates |
| `scout_watchlists` | `UNIQUE (coach_id, player_id, sport_id)` | No duplicate watch entries |
| `fm_clubs` | `UNIQUE (user_id)` | One club per user |

### 10.3 Tournament capacity

`approved` registrations ≤ `tournaments.max_teams` is checked while holding a
row lock on the tournament:

```sql
BEGIN;
SELECT max_teams FROM tournaments WHERE id = :tid FOR UPDATE;   -- serialises approvals
SELECT count(*) FROM tournament_teams
 WHERE tournament_id = :tid AND status = 'approved';            -- compare with max_teams
UPDATE tournament_teams SET status = 'approved', reviewed_by = :uid, reviewed_at = now()
 WHERE id = :rid AND status = 'pending';
COMMIT;
```

### 10.4 Referential actions

| Relationship | `ON DELETE` | Rationale |
|--------------|-------------|-----------|
| `user_roles.user_id`, `refresh_tokens.user_id`, `notifications.user_id` | `CASCADE` | Dependent data has no meaning without the user |
| `player_availability.player_profile_id` | `CASCADE` | Owned by the profile |
| `courts.venue_id` | `RESTRICT` | Venue with courts cannot be deleted — deactivate instead |
| `bookings.court_id`, `bookings.user_id` | `RESTRICT` | Preserve financial and historical records |
| `payments.booking_id` | `RESTRICT` | Audit trail |
| `team_members.team_id` | `CASCADE` | Membership belongs to the team |
| `tournament_teams.team_id`, `matches.*_team_id` | `RESTRICT` | Keep tournament history intact |
| `matches.court_id`, `tournament_teams.group_id` | `SET NULL` | Optional links |
| `chat_messages.room_id` | `CASCADE` | Messages belong to the room |
| `fm_players.club_id` | `SET NULL` | Player becomes a free agent |

---

## 11. Index Strategy

| Table | Index | Supports |
|-------|-------|----------|
| `users` | `uq_users_email`, `uq_users_username` (unique, citext) | Login, uniqueness |
| `refresh_tokens` | `ix_refresh_tokens_user_id`, `uq_refresh_tokens_token_hash` | Rotation and revocation |
| `venues` | `ix_venues_city_status (city, status)` | FR-CB-04 search |
| `courts` | `ix_courts_venue_id`, `ix_courts_sport_id` | Venue pages, sport filter |
| `bookings` | GiST index created by `ex_bookings_no_overlap`; `ix_bookings_user_id_start_time`; `ix_bookings_court_id_start_time`; partial `ix_bookings_pending_expires_at (expires_at) WHERE status = 'pending'` | Overlap check, "my bookings", calendar, expiry job |
| `player_profiles` | `ix_player_profiles_sport_city_level (sport_id, city, skill_level)` | FR-SH-03 search |
| `player_availability` | `ix_player_availability_profile_day (player_profile_id, day_of_week)` | Availability overlap |
| `notifications` | `ix_notifications_user_unread (user_id, is_read, created_at DESC)` | Notification centre |
| `chat_messages` | `ix_chat_messages_room_created (room_id, created_at DESC)` | Paginated history |
| `tournament_teams` | `ix_tournament_teams_tournament_status (tournament_id, status)` | Pending list, capacity count |
| `matches` | `ix_matches_tournament_scheduled (tournament_id, scheduled_at)` | Fixture lists |
| `standings` | `uq_standings_group_team` | Table updates |
| `match_player_stats` | `ix_match_player_stats_user_id` | Personal dashboard |
| `player_ratings` | `ix_player_ratings_sport_rating (sport_id, rating_value DESC)` | Leaderboards |
| `scouting_reports` | `ix_scouting_reports_player_generated (player_id, generated_at DESC)` | Latest report |
| `fm_fixtures` | `ix_fm_fixtures_season_round (season_id, round_number)` | Season views |

---

## 12. Enumerations

| Column | Allowed values |
|--------|----------------|
| `roles.name` | `admin`, `player`, `venue_owner`, `organizer`, `coach` |
| `player_profiles.skill_level` | `beginner`, `intermediate`, `advanced`, `pro` |
| `chat_rooms.type` | `direct`, `team`, `tournament` |
| `chat_messages.message_type` | `text`, `image`, `system` |
| `venues.status` | `pending`, `approved`, `rejected`, `suspended` |
| `bookings.status` | `pending`, `confirmed`, `cancelled`, `completed`, `expired` |
| `payments.status` | `initiated`, `succeeded`, `failed`, `refunded` |
| `team_members.status` | `invited`, `active`, `declined`, `left`, `removed` |
| `tournaments.format` | `round_robin`, `knockout`, `group_knockout` |
| `tournaments.status` | `draft`, `open`, `closed`, `ongoing`, `completed`, `cancelled` |
| `tournament_teams.status` | `pending`, `approved`, `rejected`, `withdrawn` |
| `matches.status` | `scheduled`, `live`, `finished`, `postponed`, `cancelled` |
| `fm_seasons.status` | `upcoming`, `active`, `finished` |
| `fm_fixtures.status` | `scheduled`, `played` |

### State machines

```mermaid
stateDiagram-v2
    direction LR
    [*] --> pending: create booking
    pending --> confirmed: payment succeeded
    pending --> expired: hold timeout
    pending --> cancelled: user cancels
    confirmed --> cancelled: cancel before cutoff
    confirmed --> completed: end_time passed
    expired --> [*]
    cancelled --> [*]
    completed --> [*]
```

```mermaid
stateDiagram-v2
    direction LR
    [*] --> pending: captain registers
    pending --> approved: organizer approves
    pending --> rejected: organizer rejects
    pending --> withdrawn: captain withdraws
    approved --> withdrawn: captain withdraws
    rejected --> [*]
    withdrawn --> [*]
```

---

## 13. Table Catalogue and Requirement Traceability

| # | Table | Module | Main purpose | Key requirements |
|---|-------|--------|--------------|------------------|
| 1 | `users` | Core | Accounts and credentials | FR-CORE-01…07 |
| 2 | `roles` | Core | Role catalogue | FR-CORE-05, 07 |
| 3 | `user_roles` | Core | User ↔ role assignment (M:N) | FR-CORE-05, 07 |
| 4 | `refresh_tokens` | Core | Revocable refresh tokens | FR-CORE-04, NFR-SEC-03 |
| 5 | `sports` | Core | Sports catalogue | FR-CORE-08 |
| 6 | `player_profiles` | Core / SportHub | Per-sport player profile | FR-SH-01 |
| 7 | `player_availability` | Core / SportHub | Weekly availability | FR-SH-02, 03 |
| 8 | `notifications` | Core | In-app notifications | FR-CORE-09, 12 |
| 9 | `chat_rooms` | Core / SportHub | Direct, team, tournament rooms | FR-SH-07 |
| 10 | `chat_room_members` | Core / SportHub | Room membership | FR-SH-07, 08 |
| 11 | `chat_messages` | Core / SportHub | Messages | FR-SH-08, 10 |
| 12 | `venues` | CourtBook | Facilities | FR-CB-01, 03, 04 |
| 13 | `courts` | CourtBook | Bookable courts | FR-CB-02, 08 |
| 14 | `court_closures` | CourtBook | Maintenance / blocked time | FR-CB-11 |
| 15 | `bookings` | CourtBook | Reservations (exclusion constraint) | FR-CB-06…10 |
| 16 | `payments` | CourtBook | Payment records | FR-CB-09, 14 |
| 17 | `venue_reviews` | CourtBook | Ratings and comments | FR-CB-13 |
| 18 | `teams` | SportHub | Teams | FR-SH-04, 06 |
| 19 | `team_members` | SportHub | Team membership and invitations | FR-SH-05, 06 |
| 20 | `tournaments` | SportArena | Tournaments | FR-SA-01…03 |
| 21 | `tournament_teams` | SportArena | Registrations and approval | FR-SA-04…08 |
| 22 | `groups` | SportArena | Tournament groups | FR-SA-09 |
| 23 | `matches` | SportArena | Fixtures and results | FR-SA-10, 11 |
| 24 | `standings` | SportArena | Group tables | FR-SA-11, 12 |
| 25 | `match_player_stats` | SportIQ | Per-player match stats | FR-SIQ-01, 02 |
| 26 | `player_ratings` | SportIQ | Current Elo per sport | FR-SIQ-03, 06 |
| 27 | `rating_history` | SportIQ | Elo audit trail | FR-SIQ-04 |
| 28 | `scouting_reports` | SportScout AI | AI report snapshots | FR-SC-01, 02, 06 |
| 29 | `scout_watchlists` | SportScout AI | Coach watchlist | FR-SC-04 |
| 30 | `fm_clubs` | Football Manager Lite | Virtual clubs | FR-FM-01 |
| 31 | `fm_players` | Football Manager Lite | Virtual players | FR-FM-02, 03 |
| 32 | `fm_seasons` | Football Manager Lite | Seasons | FR-FM-06 |
| 33 | `fm_fixtures` | Football Manager Lite | Fixtures and simulation results | FR-FM-05…07 |
| 34 | `fm_lineups` | Football Manager Lite | Lineup per fixture | FR-FM-04 |

**Total: 34 tables** (11 core, 6 CourtBook, 2 teams, 5 SportArena, 3 SportIQ, 2 SportScout AI, 5 Football Manager Lite).

> Schema is implemented in Step 2 by versioned migrations; this document is
> the single source of truth until then. Any later schema change must update
> this file in the same pull request.
