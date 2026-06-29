"""Stripe billing webhook and checkout tests."""
import json
from unittest.mock import patch, MagicMock
from app.models import User, StripeEvent
from app.services.security import create_access_token


def test_mock_upgrade_disabled_in_production(client, db_session, monkeypatch):
    monkeypatch.setattr("app.config.settings.APP_ENV", "production")
    user = User(id="prod_user", email="prod@test.com", name="Prod")
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
    res = client.post(
        "/auth/upgrade",
        json={"plan": "Pro"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 410


@patch("stripe.Webhook.construct_event")
def test_webhook_idempotent(mock_construct, client, db_session):
    user = User(id="stripe_u", email="stripe@test.com", name="Stripe", stripe_customer_id="cus_123")
    db_session.add(user)
    db_session.commit()

    event = {
        "id": "evt_test_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": "stripe_u", "plan": "Pro"},
                "subscription": "sub_123",
                "customer": "cus_123",
            }
        },
    }
    mock_construct.return_value = event

    payload = json.dumps(event).encode()
    with patch("app.config.settings.STRIPE_WEBHOOK_SECRET", "whsec_test"):
        res1 = client.post(
            "/billing/webhook",
            content=payload,
            headers={"stripe-signature": "sig"},
        )
        assert res1.status_code == 200

        res2 = client.post(
            "/billing/webhook",
            content=payload,
            headers={"stripe-signature": "sig"},
        )
        assert res2.status_code == 200
        assert res2.json().get("duplicate") is True

    db_session.refresh(user)
    assert user.plan == "Pro"
    assert db_session.query(StripeEvent).count() == 1
