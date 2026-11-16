"""FastAPI application factory.  Run: ``uvicorn app.main:app --reload`` (from backend/)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

DESCRIPTION = """
Core backend of the **Sports Ecosystem & AI Platform** (Step 2): identity & RBAC, sports
catalogue, player profiles and availability, notifications and chat.

* All endpoints live under `/api/v1`; errors are always `{ "detail": ... }`.
* Click **Authorize** and paste the `access_token` returned by `POST /api/v1/auth/login`.
* Real-time chat is a WebSocket (not shown in this page): `/api/v1/ws/chat/{room_id}?token=...`
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=DESCRIPTION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"name": settings.PROJECT_NAME, "docs": "/docs", "api": settings.API_V1_PREFIX}

    return app


app = create_app()
