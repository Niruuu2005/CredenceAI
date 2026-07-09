import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EnterpriseContact

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enterprise", tags=["Enterprise"])


class EnterpriseContactRequest(BaseModel):
    email: EmailStr
    message: str = Field(min_length=10, max_length=5000)


class EnterpriseContactResponse(BaseModel):
    id: str
    message: str


@router.post("/contact", response_model=EnterpriseContactResponse, status_code=201)
def submit_enterprise_contact(
    body: EnterpriseContactRequest,
    db: Session = Depends(get_db),
):
    contact_id = f"ent-{uuid.uuid4().hex[:10]}"
    record = EnterpriseContact(
        id=contact_id,
        email=body.email,
        message=body.message,
        status="new",
    )
    db.add(record)
    db.commit()
    logger.info("Enterprise contact submitted id=%s email=%s", contact_id, body.email)
    return EnterpriseContactResponse(
        id=contact_id,
        message="Thank you. Our team will contact you within 2 business days.",
    )
