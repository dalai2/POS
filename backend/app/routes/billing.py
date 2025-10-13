import os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant, require_owner
from app.core.database import get_db
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


class CheckoutSessionCreate(BaseModel):
    price_id: str  # Stripe Price ID


@router.post("/checkout-session", dependencies=[Depends(require_owner)])
def create_checkout_session(
    data: CheckoutSessionCreate,
    request: Request,
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    try:
        import stripe as stripe_lib
    except ImportError:
        raise HTTPException(status_code=500, detail="Stripe not installed")
    stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_secret:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe_lib.api_key = stripe_secret
    origin = request.headers.get("origin", "http://localhost:5173")
    session = stripe_lib.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": data.price_id, "quantity": 1}],
        success_url=f"{origin}/billing?success=true",
        cancel_url=f"{origin}/billing?canceled=true",
        metadata={"tenant_slug": tenant.slug},
    )
    return {"id": session.id, "url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        import stripe as stripe_lib
    except ImportError:
        # Allow noop webhook if stripe not installed in dev
        return {"received": True}
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_lib.api_key = stripe_secret
    event = None
    try:
        if endpoint_secret:
            event = stripe_lib.Webhook.construct_event(payload, sig_header, endpoint_secret)
        else:
            # Unsafe parse for dev only
            event = stripe_lib.Event.construct_from(request.json(), stripe_lib.api_key)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    if event and event["type"] in {"checkout.session.completed", "customer.subscription.updated"}:
        data = event["data"]["object"]
        tenant_slug = data.get("metadata", {}).get("tenant_slug")
        if tenant_slug:
            tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
            if tenant:
                tenant.is_active = True
                tenant.plan = "paid"
                tenant.stripe_customer_id = data.get("customer")
                tenant.stripe_subscription_id = data.get("subscription") or tenant.stripe_subscription_id
                db.commit()
    return {"received": True}


@router.get("/plans")
def list_plans():
    # Plans can be configured via env vars; fallback demo values
    plans = [
        {
            "key": "basic",
            "name": "Basic",
            "price_month": os.getenv("STRIPE_PRICE_BASIC", "price_basic_demo"),
            "amount": int(os.getenv("PLAN_BASIC_AMOUNT", "990")),
            "currency": os.getenv("PLAN_CURRENCY", "mxn"),
            "interval": "month",
        },
        {
            "key": "pro",
            "name": "Pro",
            "price_month": os.getenv("STRIPE_PRICE_PRO", "price_pro_demo"),
            "amount": int(os.getenv("PLAN_PRO_AMOUNT", "1990")),
            "currency": os.getenv("PLAN_CURRENCY", "mxn"),
            "interval": "month",
        },
    ]
    return {"plans": plans}


@router.get("/status")
def subscription_status(tenant: Tenant = Depends(get_tenant)):
    return {
        "tenant": tenant.slug,
        "is_active": tenant.is_active,
        "plan": tenant.plan,
        "stripe_customer_id": tenant.stripe_customer_id,
        "stripe_subscription_id": tenant.stripe_subscription_id,
    }


