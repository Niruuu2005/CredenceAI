import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Collection, User
from app.services.security import get_current_user
from app.services.quota_service import check_collection_quota
from app.schemas import CollectionCreate, CollectionResponse

router = APIRouter(prefix="/collections", tags=["Collections"])


def _get_user_collection(db: Session, collection_id: str, user_id: str) -> Collection:
    coll = (
        db.query(Collection)
        .filter(Collection.id == collection_id, Collection.user_id == user_id)
        .first()
    )
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    return coll


@router.get("", response_model=List[CollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Collection)
        .filter(Collection.user_id == current_user.id)
        .order_by(Collection.created_at.desc())
        .all()
    )


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(
    request: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_collection_quota(db, current_user)

    collection_id = f"coll-{uuid.uuid4().hex[:8]}"
    db_collection = Collection(
        id=collection_id,
        user_id=current_user.id,
        name=request.name,
        description=request.description or "A collection of research intelligence.",
        items_count=0,
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    return db_collection


@router.delete("/{collection_id}")
def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_collection = _get_user_collection(db, collection_id, current_user.id)
    db.delete(db_collection)
    db.commit()
    return {"message": "Collection deleted successfully"}
