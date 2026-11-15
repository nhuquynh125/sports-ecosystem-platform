"""Aggregates every v1 router. Mounted by app.main under settings.API_V1_PREFIX."""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    chat,
    health,
    notifications,
    player_profiles,
    sports,
    users,
    ws,
)
from app.api.v1.endpoints import bookings as bookings_ep, venues as venues_ep
from app.api.v1.endpoints import teams as teams_ep, tournaments as tournaments_ep
from app.api.v1.endpoints import pickup_matches as pickup_matches_ep
from app.schemas.common import ErrorResponse

_errors = {
    401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"},
    403: {"model": ErrorResponse, "description": "Insufficient permissions"},
}

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router, responses=_errors)
api_router.include_router(admin.router, responses=_errors)
api_router.include_router(sports.router)
api_router.include_router(player_profiles.router, responses=_errors)
api_router.include_router(notifications.router, responses=_errors)
api_router.include_router(chat.router, responses=_errors)
api_router.include_router(ws.router)
api_router.include_router(venues_ep.router, responses=_errors)
api_router.include_router(bookings_ep.router, responses=_errors)
api_router.include_router(teams_ep.router, responses=_errors)
api_router.include_router(tournaments_ep.router, responses=_errors)
api_router.include_router(pickup_matches_ep.router, responses=_errors)
