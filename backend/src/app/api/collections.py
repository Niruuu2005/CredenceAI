import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Collection, CollectionItem, User
from app.services.security import get_current_user
from app.services.quota_service import check_collection_quota
from app.schemas import CollectionCreate, CollectionResponse

router = APIRouter(prefix="/collections", tags=["Collections"])


class CollectionItemCreate(BaseModel):
    result_id: str | None = None
    title: str
    url: str | None = None
    snippet: str | None = None
    source: str | None = None
    job_id: str | None = None


class CollectionItemResponse(BaseModel):
    id: str
    collection_id: str
    result_id: str | None
    title: str
    url: str | None
    snippet: str | None
    source: str | None
    job_id: str | None

    class Config:
        from_attributes = True


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


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_user_collection(db, collection_id, current_user.id)


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


@router.get("/{collection_id}/items", response_model=List[CollectionItemResponse])
def list_collection_items(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_user_collection(db, collection_id, current_user.id)
    return (
        db.query(CollectionItem)
        .filter(CollectionItem.collection_id == collection_id)
        .order_by(CollectionItem.created_at.desc())
        .all()
    )


@router.post("/{collection_id}/items", response_model=CollectionItemResponse, status_code=201)
def add_collection_item(
    collection_id: str,
    body: CollectionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    coll = _get_user_collection(db, collection_id, current_user.id)
    item_id = f"ci_{uuid.uuid4().hex[:10]}"
    item = CollectionItem(
        id=item_id,
        collection_id=collection_id,
        result_id=body.result_id,
        title=body.title,
        url=body.url,
        snippet=body.snippet,
        source=body.source,
        job_id=body.job_id,
    )
    db.add(item)
    coll.items_count = (coll.items_count or 0) + 1
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{collection_id}/items/{item_id}")
def remove_collection_item(
    collection_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    coll = _get_user_collection(db, collection_id, current_user.id)
    item = (
        db.query(CollectionItem)
        .filter(CollectionItem.id == item_id, CollectionItem.collection_id == collection_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    coll.items_count = max(0, (coll.items_count or 1) - 1)
    db.commit()
    return {"message": "Item removed"}
