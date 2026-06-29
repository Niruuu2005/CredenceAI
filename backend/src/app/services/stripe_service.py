"""Stripe billing integration."""
import logging
from typing import Optional
import stripe
from sqlalchemy.orm import Session
from app.config import settings
from app.models import User

logger = logging.getLogger(__name__)

PLAN_QUOTAS = {"Free": 50, "Pro": 500, "Enterprise": 5000}
PRICE_TO_PLAN = {}


def _configure_stripe() -> None:
    if settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    if settings.STRIPE_PRICE_ID_PRO:
        PRICE_TO_PLAN[settings.STRIPE_PRICE_ID_PRO] = "Pro"
    if settings.STRIPE_PRICE_ID_ENTERPRISE:
        PRICE_TO_PLAN[settings.STRIPE_PRICE_ID_ENTERPRISE] = "Enterprise"


def stripe_configured() -> bool:
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)


def get_or_create_customer(db: Session, user: User) -> str:
    _configure_stripe()
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        name=user.name or user.email,
        metadata={"user_id": user.id},
    )
    user.stripe_customer_id = customer.id
    db.commit()
    return customer.id


def create_checkout_session(db: Session, user: User, plan: str) -> str:
    _configure_stripe()
    if plan not in ("Pro", "Enterprise"):
        raise ValueError("Invalid plan for checkout")
    price_id = (
        settings.STRIPE_PRICE_ID_PRO
        if plan == "Pro"
        else settings.STRIPE_PRICE_ID_ENTERPRISE
    )
    if not price_id:
        raise ValueError(f"Stripe price not configured for {plan}")

    customer_id = get_or_create_customer(db, user)
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL or "http://localhost:3000/app/billing?success=1",
        cancel_url=settings.STRIPE_CANCEL_URL or "http://localhost:3000/app/billing?canceled=1",
        metadata={"user_id": user.id, "plan": plan},
    )
    return session.url


def create_portal_session(user: User) -> str:
    _configure_stripe()
    if not user.stripe_customer_id:
        raise ValueError("No Stripe customer on file")
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=settings.STRIPE_SUCCESS_URL or "http://localhost:3000/app/billing",
    )
    return session.url


def apply_plan_to_user(user: User, plan: str, subscription_id: Optional[str] = None, status: Optional[str] = None):
    user.plan = plan
    user.search_quota_limit = PLAN_QUOTAS.get(plan, 50)
    if subscription_id:
        user.subscription_id = subscription_id
    if status:
        user.subscription_status = status


def handle_checkout_completed(db: Session, session: dict) -> None:
    user_id = (session.get("metadata") or {}).get("user_id")
    plan = (session.get("metadata") or {}).get("plan", "Pro")
    if not user_id:
        logger.warning("checkout.session.completed missing user_id metadata")
        return
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    sub_id = session.get("subscription")
    apply_plan_to_user(user, plan, subscription_id=sub_id, status="active")
    db.commit()


def handle_subscription_updated(db: Session, subscription: dict) -> None:
    customer_id = subscription.get("customer")
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        return
    status = subscription.get("status")
    user.subscription_status = status
    user.subscription_id = subscription.get("id")
    period_end = subscription.get("current_period_end")
    if period_end:
        import datetime
        user.current_period_end = datetime.datetime.fromtimestamp(period_end, tz=datetime.timezone.utc)

    items = (subscription.get("items") or {}).get("data") or []
    if items:
        price_id = items[0].get("price", {}).get("id")
        plan = PRICE_TO_PLAN.get(price_id)
        if plan:
            apply_plan_to_user(user, plan, status=status)
    if status in ("canceled", "unpaid", "incomplete_expired"):
        apply_plan_to_user(user, "Free", status=status)
    db.commit()
