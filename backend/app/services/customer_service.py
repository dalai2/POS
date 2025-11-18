from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.customer import Customer


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def upsert_customer(
    db: Session,
    tenant_id: int,
    name: Optional[str],
    phone: Optional[str],
) -> Optional[Customer]:
    """
    Ensure there is a Customer record for the given tenant/phone (or name when phone absent).
    - Phone is the primary grouping key (unique per tenant).
    - When phone is missing, fall back to name+NULL phone grouping.
    """
    normalized_name = _normalize_text(name)
    normalized_phone = _normalize_text(phone)

    if not normalized_name and not normalized_phone:
        return None

    base_query = db.query(Customer).filter(Customer.tenant_id == tenant_id)

    if normalized_phone:
        customer = base_query.filter(Customer.phone == normalized_phone).first()
    else:
        customer = (
            base_query.filter(
                Customer.phone.is_(None),
                Customer.name == normalized_name,
            )
            .first()
        )

    if customer:
        updated = False
        if normalized_name and customer.name != normalized_name:
            customer.name = normalized_name
            updated = True
        if normalized_phone and customer.phone != normalized_phone:
            customer.phone = normalized_phone
            updated = True
        if updated:
            customer.updated_at = datetime.utcnow()
        return customer

    customer = Customer(
        tenant_id=tenant_id,
        name=normalized_name or "Cliente Sin Nombre",
        phone=normalized_phone,
    )
    db.add(customer)
    return customer


