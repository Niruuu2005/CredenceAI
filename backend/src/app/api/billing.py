import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, StripeEvent
from app.services.security import get_current_user
from app.services.quota_service import count_user_jobs_in_period
from app.services import stripe_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


class CheckoutRequest(BaseModel):
    plan: str


class CheckoutResponse(BaseModel):
    url: str


@router.post("/checkout-session", response_model=CheckoutResponse)
def create_checkout(
    body: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.plan not in ("Pro", "Enterprise"):
        raise HTTPException(status_code=400, detail="Invalid plan for checkout.")
    if not stripe_service.stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured.")
    try:
        url = stripe_service.create_checkout_session(db, current_user, body.plan)
        return CheckoutResponse(url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal-session", response_model=CheckoutResponse)
def create_portal(
    current_user: User = Depends(get_current_user),
):
    if not stripe_service.stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe is not configured.")
    try:
        url = stripe_service.create_portal_session(current_user)
        return CheckoutResponse(url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def billing_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    used = count_user_jobs_in_period(db, current_user)
    return {
        "plan": current_user.plan,
        "search_quota_limit": current_user.search_quota_limit,
        "search_used": used,
        "subscription_status": current_user.subscription_status,
        "current_period_end": current_user.current_period_end,
        "stripe_configured": stripe_service.stripe_configured(),
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    import stripe

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured.")

    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.warning("Stripe webhook verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    existing = db.query(StripeEvent).filter(StripeEvent.id == event["id"]).first()
    if existing:
        return {"received": True, "duplicate": True}

    db.add(StripeEvent(id=event["id"], event_type=event["type"]))
    db.commit()

    data = event.get("data", {}).get("object", {})
    if event["type"] == "checkout.session.completed":
        stripe_service.handle_checkout_completed(db, data)
    elif event["type"] in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        stripe_service.handle_subscription_updated(db, data)
    elif event["type"] == "invoice.payment_failed":
        customer_id = data.get("customer")
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user:
            user.subscription_status = "past_due"
            db.commit()

    return {"received": True}
