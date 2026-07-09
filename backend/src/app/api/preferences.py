import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, UserPreferences
from app.services.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/preferences", tags=["Preferences"])


class PreferencesResponse(BaseModel):
    min_citations: int = 2
    scholarly_focus: str = "balanced"
    api_logging_enabled: bool = True

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    min_citations: int | None = Field(default=None, ge=1, le=10)
    scholarly_focus: str | None = None
    api_logging_enabled: bool | None = None


def _get_or_create_prefs(db: Session, user_id: str) -> UserPreferences:
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("", response_model=PreferencesResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = _get_or_create_prefs(db, current_user.id)
    return PreferencesResponse(
        min_citations=prefs.min_citations,
        scholarly_focus=prefs.scholarly_focus,
        api_logging_enabled=prefs.api_logging_enabled,
    )


@router.put("", response_model=PreferencesResponse)
def update_preferences(
    body: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = _get_or_create_prefs(db, current_user.id)
    if body.min_citations is not None:
        prefs.min_citations = body.min_citations
    if body.scholarly_focus is not None:
        prefs.scholarly_focus = body.scholarly_focus
    if body.api_logging_enabled is not None:
        prefs.api_logging_enabled = body.api_logging_enabled
    db.commit()
    db.refresh(prefs)
    return PreferencesResponse(
        min_citations=prefs.min_citations,
        scholarly_focus=prefs.scholarly_focus,
        api_logging_enabled=prefs.api_logging_enabled,
    )
