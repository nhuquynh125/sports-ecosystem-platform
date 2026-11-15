from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession, OptionalUser, require_role
from app.core.exceptions import AuthenticationError, PermissionDenied
from app.models.enums import ROLE_ADMIN
from app.schemas.sport import SportCreate, SportRead, SportUpdate
from app.services import sport_service

router = APIRouter(prefix="/sports", tags=["Sports"])

AdminOnly = Depends(require_role(ROLE_ADMIN))


@router.get("", response_model=list[SportRead], summary="List sports (public)")
def list_sports(
    db: DbSession,
    viewer: OptionalUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
    include_inactive: Annotated[bool, Query(description="Admins only")] = False,
):
    if include_inactive:
        if viewer is None:
            raise AuthenticationError("Not authenticated")
        if ROLE_ADMIN not in viewer.role_names:
            raise PermissionDenied()
    return sport_service.list_sports(db, include_inactive=include_inactive, q=q)


@router.get("/{sport_id}", response_model=SportRead, summary="Get a sport (public)")
def get_sport(sport_id: int, db: DbSession):
    return sport_service.get_sport(db, sport_id, active_only=True)


@router.post(
    "",
    response_model=SportRead,
    status_code=201,
    dependencies=[AdminOnly],
    summary="Create a sport (admin)",
)
def create_sport(payload: SportCreate, db: DbSession):
    return sport_service.create_sport(db, payload)


@router.patch(
    "/{sport_id}",
    response_model=SportRead,
    dependencies=[AdminOnly],
    summary="Update a sport (admin)",
)
def update_sport(sport_id: int, payload: SportUpdate, db: DbSession):
    return sport_service.update_sport(db, sport_id, payload)


@router.delete(
    "/{sport_id}",
    status_code=204,
    response_class=Response,
    dependencies=[AdminOnly],
    summary="Delete an unused sport (admin)",
)
def delete_sport(sport_id: int, db: DbSession):
    sport_service.delete_sport(db, sport_id)
    return Response(status_code=204)
