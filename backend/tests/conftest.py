"""Integration tests run against a REAL PostgreSQL database (the schema relies on citext/JSONB).

    export TEST_DATABASE_URL=postgresql+psycopg2://sports_admin:change_me_in_dotenv@localhost:5432/sports_test
    pytest

The database must exist and is wiped by the tests. Without TEST_DATABASE_URL every test is skipped.
"""
import os

import pytest

TEST_URL = os.environ.get("TEST_DATABASE_URL")
if TEST_URL:  # must be set BEFORE `app` is imported
    os.environ["DATABASE_URL"] = TEST_URL
    os.environ["ENVIRONMENT"] = "test"
    os.environ["BCRYPT_ROUNDS"] = "4"


def pytest_collection_modifyitems(config, items):
    if TEST_URL:
        return
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL is not set")
    for item in items:
        item.add_marker(skip)


@pytest.fixture(scope="session")
def _migrated():
    from alembic import command
    from alembic.config import Config

    from app.core.config import BACKEND_DIR

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")  # also exercises the migration itself
    yield


@pytest.fixture(autouse=True)
def _clean_db(_migrated):
    from sqlalchemy import text

    from app.core.database import engine

    with engine.begin() as conn:
        conn.execute(text(
            "TRUNCATE chat_messages, chat_room_members, chat_rooms, notifications, "
            "player_availability, player_profiles, user_roles, users, sports RESTART IDENTITY CASCADE"
        ))
    yield


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def api(client):
    """Helper bundle: register/login users and build auth headers."""
    from app.core.config import settings

    prefix = settings.API_V1_PREFIX

    class Api:
        def __init__(self):
            self.prefix = prefix
            self.client = client

        def url(self, path: str) -> str:
            return f"{self.prefix}{path}"

        def register(self, name: str, role: str = "player") -> dict:
            response = client.post(self.url("/auth/register"), json={
                "email": f"{name}@example.com", "username": name,
                "password": "Passw0rdOK", "full_name": name.title(), "role": role,
            })
            assert response.status_code == 201, response.text
            return response.json()

        def login(self, name: str) -> str:
            response = client.post(self.url("/auth/login"),
                                   json={"email": f"{name}@example.com", "password": "Passw0rdOK"})
            assert response.status_code == 200, response.text
            return response.json()["access_token"]

        def user(self, name: str, role: str = "player") -> tuple[dict, dict]:
            data = self.register(name, role)
            return data, {"Authorization": f"Bearer {self.login(name)}"}

        def make_admin(self, name: str = "root") -> dict:
            from sqlalchemy import select

            from app.core.database import SessionLocal
            from app.models import Role, UserRole

            data = self.register(name)
            with SessionLocal() as db:
                role_id = db.scalar(select(Role.id).where(Role.name == "admin"))
                db.add(UserRole(user_id=data["id"], role_id=role_id))
                db.commit()
            return {"Authorization": f"Bearer {self.login(name)}"}

    return Api()
