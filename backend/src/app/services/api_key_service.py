import secrets
import hashlib
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import ApiKey

def generate_api_key() -> str:
    raw = secrets.token_hex(32)
    return f"cred_sk_{raw}"

def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()

def create_api_key(
    db: Session,
    owner: str,
    label: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    raw_key = generate_api_key()
    hashed = hash_key(raw_key)
    
    db_key = ApiKey(
        key_hash=hashed,
        owner=owner,
        user_id=user_id or owner,
        label=label,
        revoked=False,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    
    return {
        "key": raw_key,
        "owner": db_key.owner,
        "label": db_key.label,
        "created_at": db_key.created_at
    }

def validate_api_key(db: Session, raw_key: str) -> Optional[ApiKey]:
    hashed = hash_key(raw_key)
    db_key = db.query(ApiKey).filter(ApiKey.key_hash == hashed, ApiKey.revoked == False).first()
    return db_key

def update_key_last_used(key_id: int):
    """Updates last_used_at timestamp in a separate session for background tasks."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        db.query(ApiKey).filter(ApiKey.id == key_id).update({"last_used_at": datetime.datetime.now(datetime.timezone.utc)})
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
