# Frontend — Core (Step 3)

Vite · React 19 · TypeScript · Tailwind CSS 3 · shadcn/ui-style components (Radix) · React Router 6 · TanStack Query 5 ·
React Hook Form + Zod · Axios. Talks to the Step 2 backend under `/api/v1`.

## Run it

```bash
# 1. backend + database running (see backend/README.md), API on http://localhost:8000
cd frontend
npm install
npm run dev          # http://localhost:5173  (Vite proxies /api -> http://localhost:8000)
```

Checks: `npm run build` (type-check + production build) · `npm run lint` (ESLint, zero warnings expected).
Needs Node 20.19+ (Vite 7).

Dev logins (after `python scripts/seed.py`): the login page shows one-click buttons for
`admin@ / player@ / coach@ / organizer@ / owner@example.com`, password `Password123!` (development builds only).

Configuration (`.env`, see `.env.example`): `VITE_PROXY_TARGET` (dev proxy target), `VITE_API_BASE_URL`
(set only when the API lives on another origin in production; the backend `CORS_ORIGINS` must then allow it).

## Structure

```
src/
├── api/            axios client (JWT + error envelope), types, React Query hooks per resource
├── config/         roles, role-aware navigation
├── context/        AuthProvider (token, /users/me, login/logout) + context object
├── hooks/          useAuth, useToast
├── lib/            utils, time helpers, toast store, query client, form helpers
├── routes/         ProtectedRoute (role guard), GuestRoute
├── components/
│   ├── ui/         shadcn-style primitives (button, input, dialog, popover, tabs, table, ...)
│   └── shared/     Navbar, Sidebar, NotificationBell, DataTable, Modal/ConfirmDialog,
│                   Toast, ScheduleGrid, Field, AppLayout, AuthLayout, ...
└── pages/          Login, Register, Dashboard, Profile (+ profile/*), admin/AdminUsersPage
```

## How the main pieces behave

* **API client** (`api/client.ts`): attaches `Authorization: Bearer <token>`; every failure becomes an `ApiError`
  built from `{ "detail": ... }` (a 422 list is also split per field: `"email: ..."` -> `fieldErrors.email`).
  A 401, or 403 `Account is disabled`, ends the session (token cleared, redirect to `/login`, toast).
* **Global errors** (`lib/query-client.ts`): failed mutations raise an error toast unless the mutation sets
  `meta: { silent: true }` (forms do this and show inline errors instead). Failed *background* refetches toast;
  initial load failures are shown inline by the page.
* **Roles** come from `GET /users/me` (not the JWT claim), refetched on window focus and when the bell opens, so
  a role change or lock by an admin takes effect quickly.
* **Route guards**: `<ProtectedRoute />` (signed in) and `<ProtectedRoute roles={['admin']} />` (shows a 403 page).
  Add new module routes the same way, e.g. `roles={['venue_owner', 'admin']}`.
* **DataTable**: server-driven search (350 ms debounce) and pagination; sorting is client-side on the loaded page
  (the backend has no sort parameter yet — the footer says so when more pages exist).
* **ScheduleGrid**: generic Mon–Sun time grid fed with `{ id, day, start, end }`; used for player availability,
  intended to be reused for court / match schedules. There is no separate month `Calendar` yet.
* **Notifications**: the bell polls `/notifications/unread-count` every 30 s; the list loads when opened.
  Items with `data.deep_link` navigate there.

## Known limits (by design for this step)

* Access tokens last 15 minutes and there is no refresh endpoint yet, so users are signed out when the token expires.
* No WebSocket push for notifications or chat UI yet (backend supports chat WS; UI comes with SportHub).
* Sidebar entries for CourtBook / SportHub / SportArena / Scouting are visible but disabled ("Soon").
* No dark mode. Availability `PUT` (replace whole week) is not used by the UI.
