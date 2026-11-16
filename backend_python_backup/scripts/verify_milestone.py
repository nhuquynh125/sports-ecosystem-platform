"""
Milestone verification: starts embedded PostgreSQL, runs alembic upgrade head,
then runs scripts.seed. Used when Docker/native Postgres is unavailable.
"""
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

logging.basicConfig(level=logging.WARNING)  # suppress embedded-postgres noise

BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../backend


def run(cmd: list[str], env: dict) -> int:
    print(f">>> {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env)
    return result.returncode


def main() -> None:
    from embedded_postgres import PostgresServer

    tmpdir = tempfile.mkdtemp(prefix="sports_pgdata_")
    pgdata = Path(tmpdir) / "pgdata"
    pgdata.mkdir()

    print("⏳ Starting embedded PostgreSQL…")
    pg = PostgresServer(pgdata, cleanup_mode="delete")
    db_url = pg.get_uri(database="postgres")

    # Alembic needs psycopg2+postgresql schema
    db_url_alchemy = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    print(f"   DB URL: {db_url_alchemy}\n")

    env = {**os.environ, "DATABASE_URL": db_url_alchemy}

    # --- alembic upgrade head ------------------------------------------------
    code = run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
    if code != 0:
        print("\n❌  alembic upgrade head FAILED")
        sys.exit(code)
    print("✅  alembic upgrade head OK\n")

    # --- python -m scripts.seed ---------------------------------------------
    code = run([sys.executable, "-m", "scripts.seed"], env)
    if code != 0:
        print("\n❌  python -m scripts.seed FAILED")
        sys.exit(code)
    print("✅  python -m scripts.seed OK\n")

    print("🎉 Backend milestone verification PASSED")


if __name__ == "__main__":
    main()
