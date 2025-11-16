from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_serializer
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.ticket import Ticket

router = APIRouter()


class TicketCreate(BaseModel):
    sale_id: Optional[int] = None
    pedido_id: Optional[int] = None
    kind: str = "sale"
    html: str


class TicketOut(BaseModel):
    id: int
    sale_id: Optional[int]
    pedido_id: Optional[int]
    kind: str
    html: str
    created_at: datetime

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat() if value else ""

    class Config:
        from_attributes = True


def _ensure_ticket_table(db: Session) -> None:
    try:
        Ticket.__table__.create(bind=db.get_bind(), checkfirst=True)
    except Exception:
        pass


@router.post("/tickets", response_model=TicketOut)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user=Depends(get_current_user),
):
    _ensure_ticket_table(db)

    # Upsert logic: replace if already exists
    existing = None
    
    # Check for existing ticket by sale_id
    if payload.sale_id is not None:
        existing = (
            db.query(Ticket)
            .filter(
                Ticket.tenant_id == tenant.id, 
                Ticket.sale_id == payload.sale_id, 
                Ticket.kind == payload.kind
            )
            .first()
        )
    # Check for existing ticket by pedido_id
    elif payload.pedido_id is not None:
        existing = (
            db.query(Ticket)
            .filter(
                Ticket.tenant_id == tenant.id, 
                Ticket.pedido_id == payload.pedido_id, 
                Ticket.kind == payload.kind
            )
            .first()
        )
    
    if existing:
        existing.html = payload.html
        db.commit()
        db.refresh(existing)
        return existing

    ticket = Ticket(
        tenant_id=tenant.id, 
        sale_id=payload.sale_id, 
        pedido_id=payload.pedido_id,
        kind=payload.kind, 
        html=payload.html
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user=Depends(get_current_user),
):
    _ensure_ticket_table(db)
    t = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.tenant_id == tenant.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return t


@router.get("/tickets/by-sale/{sale_id}", response_model=List[TicketOut])
def get_tickets_by_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user=Depends(get_current_user),
):
    _ensure_ticket_table(db)
    tickets = (
        db.query(Ticket)
        .filter(Ticket.tenant_id == tenant.id, Ticket.sale_id == sale_id)
        .order_by(Ticket.created_at.asc())
        .all()
    )
    return tickets


@router.get("/tickets/by-pedido/{pedido_id}", response_model=List[TicketOut])
def get_tickets_by_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user=Depends(get_current_user),
):
    _ensure_ticket_table(db)
    tickets = (
        db.query(Ticket)
        .filter(Ticket.tenant_id == tenant.id, Ticket.pedido_id == pedido_id)
        .order_by(Ticket.created_at.asc())
        .all()
    )
    return tickets


