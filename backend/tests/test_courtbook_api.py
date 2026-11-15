"""Integration tests for CourtBook API (venues and bookings).

Run with:
    export TEST_DATABASE_URL=postgresql+psycopg2://sports_admin:change_me@localhost:5432/sports_test
    pytest tests/test_courtbook_api.py -v
"""
from datetime import date, time, timedelta

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_venue_and_court(sport_id: int, owner_id: int) -> tuple[int, int]:
    """Insert a Venue + one Court directly in the DB; return (venue_id, court_id)."""
    from app.core.database import SessionLocal
    from app.models.venue import Court, Venue

    with SessionLocal() as db:
        venue = Venue(
            owner_id=owner_id,
            name="Test Venue",
            address="1 Test Street",
            city="Test City",
            open_time=time(6, 0),
            close_time=time(22, 0),
            is_active=True,
        )
        db.add(venue)
        db.flush()
        court = Court(
            venue_id=venue.id,
            sport_id=sport_id,
            name="Court A",
            hourly_price=200000,
            is_active=True,
        )
        db.add(court)
        db.commit()
        return venue.id, court.id


def _ensure_sport(db) -> int:
    """Return the id of the first Sport row (creates one if none exist)."""
    from sqlalchemy import select
    from app.models.sport import Sport

    sport = db.scalar(select(Sport).limit(1))
    if sport is None:
        sport = Sport(name="Badminton", slug="badminton")
        db.add(sport)
        db.commit()
        db.refresh(sport)
    return sport.id


def _ensure_role(db, role_name: str) -> int:
    from sqlalchemy import select
    from app.models.user import Role

    role = db.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name, description=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
    return role.id


def _make_venue_owner(api, db) -> tuple[dict, dict, int]:
    """Register a venue_owner user and patch the DB so they have the role."""
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models.user import Role, User, UserRole

    data, _ = api.user("vowner", "player")
    with SessionLocal() as s:
        role_id = _ensure_role(s, "venue_owner")
        user_id = s.scalar(select(User.id).where(User.username == "vowner"))
        s.add(UserRole(user_id=user_id, role_id=role_id))
        s.commit()
    token = api.login("vowner")
    hdrs = {"Authorization": f"Bearer {token}"}
    return data, hdrs, data["id"]


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        yield session


@pytest.fixture()
def sport_id(db):
    return _ensure_sport(db)


@pytest.fixture()
def owner_setup(api, db):
    """Returns (owner_headers, owner_id, venue_id, court_id)."""
    _ensure_role(db, "venue_owner")
    data, hdrs, owner_id = _make_venue_owner(api, db)
    venue_id, court_id = _make_venue_and_court(_ensure_sport(db), owner_id)
    return hdrs, owner_id, venue_id, court_id


# ---------------------------------------------------------------------------
# Tests: venue listing
# ---------------------------------------------------------------------------

class TestVenueListing:
    def test_list_venues_empty(self, client, api):
        _, hdrs = api.user("lister", "player")
        resp = client.get(api.url("/venues"))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body

    def test_list_venues_with_data(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        _make_venue_and_court(sport_id, owner_id)
        resp = client.get(api.url("/venues"))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert len(body["items"]) >= 1
        # Spot-check fields
        item = body["items"][0]
        assert "id" in item
        assert "name" in item
        assert "city" in item

    def test_list_venues_filter_by_sport(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        _make_venue_and_court(sport_id, owner_id)
        resp = client.get(api.url(f"/venues?sport_id={sport_id}"))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_list_venues_keyword_search(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        _make_venue_and_court(sport_id, owner_id)
        resp = client.get(api.url("/venues?q=Test"))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Tests: venue detail
# ---------------------------------------------------------------------------

class TestVenueDetail:
    def test_get_venue(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, _ = _make_venue_and_court(sport_id, owner_id)
        resp = client.get(api.url(f"/venues/{venue_id}"))
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == venue_id
        assert "courts" in body

    def test_get_venue_not_found(self, client, api):
        resp = client.get(api.url("/venues/999999"))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: availability
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_availability_structure(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, _ = _make_venue_and_court(sport_id, owner_id)
        future_date = (date.today() + timedelta(days=5)).isoformat()
        resp = client.get(api.url(f"/venues/{venue_id}/availability?date={future_date}"))
        assert resp.status_code == 200
        body = resp.json()
        assert body["venue_id"] == venue_id
        assert body["date"] == future_date
        assert "courts" in body
        assert len(body["courts"]) >= 1
        # check slot structure
        court_avail = body["courts"][0]
        assert "court" in court_avail
        assert "slots" in court_avail
        assert len(court_avail["slots"]) > 0
        slot = court_avail["slots"][0]
        assert "start_time" in slot
        assert "end_time" in slot
        assert "status" in slot
        assert slot["status"] in ("available", "booked", "past")
        assert "price" in slot

    def test_availability_missing_date(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, _ = _make_venue_and_court(sport_id, owner_id)
        resp = client.get(api.url(f"/venues/{venue_id}/availability"))
        assert resp.status_code == 422  # date is required


# ---------------------------------------------------------------------------
# Tests: booking creation + double-booking
# ---------------------------------------------------------------------------

class TestBookings:
    def _book(self, client, api, court_id: int, bdate: date, slot: str, user_name: str):
        _, hdrs = api.user(user_name, "player")
        return client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": slot},
            headers=hdrs,
        )

    def test_create_booking_success(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        bdate = date.today() + timedelta(days=3)
        _, player_hdrs = api.user("player1_ok", "player")
        resp = client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "08:00"},
            headers=player_hdrs,
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["court_id"] == court_id
        assert body["status"] == "confirmed"
        assert "booking_code" in body
        assert "venue_id" in body
        assert "venue_name" in body

    def test_double_booking_returns_409(self, client, api, db, sport_id):
        """Booking the same (court, date, time_slot) twice → 409."""
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        bdate = date.today() + timedelta(days=4)

        _, h1 = api.user("dbplayer1", "player")
        _, h2 = api.user("dbplayer2", "player")

        payload = {"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "09:00"}
        r1 = client.post(api.url("/bookings"), json=payload, headers=h1)
        assert r1.status_code == 201, r1.text

        r2 = client.post(api.url("/bookings"), json=payload, headers=h2)
        assert r2.status_code == 409, r2.text
        assert r2.json()["detail"] == "Time slot is already booked"

    def test_booking_requires_auth(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        bdate = date.today() + timedelta(days=5)
        resp = client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "10:00"},
        )
        assert resp.status_code == 401

    def test_booking_past_slot_rejected(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        past_date = date.today() - timedelta(days=1)
        _, player_hdrs = api.user("past_booker", "player")
        resp = client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": past_date.isoformat(), "time_slot": "08:00"},
            headers=player_hdrs,
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Tests: GET /bookings/me
# ---------------------------------------------------------------------------

class TestMyBookings:
    def test_my_bookings_empty(self, client, api):
        _, hdrs = api.user("nobody_booked", "player")
        resp = client.get(api.url("/bookings/me"), headers=hdrs)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_my_bookings_shows_own(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        bdate = date.today() + timedelta(days=6)
        _, player_hdrs = api.user("mybooker", "player")
        client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "11:00"},
            headers=player_hdrs,
        )
        resp = client.get(api.url("/bookings/me"), headers=player_hdrs)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["court_id"] == court_id

    def test_my_bookings_requires_auth(self, client, api):
        resp = client.get(api.url("/bookings/me"))
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests: cancel booking
# ---------------------------------------------------------------------------

class TestCancelBooking:
    def test_cancel_own_booking(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        # Use a slot far in the future to avoid cutoff
        bdate = date.today() + timedelta(days=10)
        _, player_hdrs = api.user("canceller", "player")
        r = client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "14:00"},
            headers=player_hdrs,
        )
        assert r.status_code == 201, r.text
        booking_id = r.json()["id"]
        # Cancel
        rc = client.delete(api.url(f"/bookings/{booking_id}"), headers=player_hdrs)
        assert rc.status_code == 204, rc.text
        # Slot should now be available again (can book it again)
        _, p2_hdrs = api.user("rebooker", "player")
        r2 = client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "14:00"},
            headers=p2_hdrs,
        )
        assert r2.status_code == 201

    def test_cancel_others_booking_forbidden(self, client, api, db, sport_id):
        _, hdrs, owner_id = _make_venue_owner(api, db)
        venue_id, court_id = _make_venue_and_court(sport_id, owner_id)
        bdate = date.today() + timedelta(days=11)
        _, p1_hdrs = api.user("owner_cancel1", "player")
        _, p2_hdrs = api.user("thief_cancel", "player")
        r = client.post(
            api.url("/bookings"),
            json={"court_id": court_id, "booking_date": bdate.isoformat(), "time_slot": "15:00"},
            headers=p1_hdrs,
        )
        assert r.status_code == 201, r.text
        booking_id = r.json()["id"]
        rc = client.delete(api.url(f"/bookings/{booking_id}"), headers=p2_hdrs)
        assert rc.status_code == 403

    def test_cancel_nonexistent_booking(self, client, api):
        _, hdrs = api.user("ghost_canceller", "player")
        resp = client.delete(api.url("/bookings/999999"), headers=hdrs)
        assert resp.status_code == 404
