"""
Servicio centralizado para gestión de tickets.
Maneja el guardado y recuperación de tickets HTML generados.
"""
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.ticket import Ticket
from app.models.tenant import Tenant


def save_ticket(
    db: Session,
    tenant_id: int,
    html: str,
    kind: str = "sale",
    sale_id: Optional[int] = None,
    venta_contado_id: Optional[int] = None,
    apartado_id: Optional[int] = None,
    pedido_id: Optional[int] = None
) -> Ticket:
    """
    Guarda o actualiza un ticket en la base de datos.
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        html: HTML del ticket
        kind: Tipo de ticket ('sale', 'payment', 'pedido', etc.)
        sale_id: ID de venta legacy (opcional, para compatibilidad)
        venta_contado_id: ID de venta de contado (opcional)
        apartado_id: ID de apartado (opcional)
        pedido_id: ID de pedido (opcional)
    
    Returns:
        Ticket guardado o actualizado
    """
    # Buscar ticket existente
    existing = None
    
    if venta_contado_id is not None:
        existing = db.query(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            Ticket.venta_contado_id == venta_contado_id,
            Ticket.kind == kind
        ).first()
    elif apartado_id is not None:
        existing = db.query(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            Ticket.apartado_id == apartado_id,
            Ticket.kind == kind
        ).first()
    elif pedido_id is not None:
        existing = db.query(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            Ticket.pedido_id == pedido_id,
            Ticket.kind == kind
        ).first()
    elif sale_id is not None:
        existing = db.query(Ticket).filter(
            Ticket.tenant_id == tenant_id,
            Ticket.sale_id == sale_id,
            Ticket.kind == kind
        ).first()
    
    if existing:
        # Actualizar ticket existente
        existing.html = html
        db.commit()
        db.refresh(existing)
        return existing
    
    # Crear nuevo ticket
    ticket = Ticket(
        tenant_id=tenant_id,
        sale_id=sale_id,
        venta_contado_id=venta_contado_id,
        apartado_id=apartado_id,
        pedido_id=pedido_id,
        kind=kind,
        html=html
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_tickets_by_venta_contado(
    db: Session,
    tenant_id: int,
    venta_contado_id: int
) -> List[Ticket]:
    """
    Obtiene todos los tickets asociados a una venta de contado.
    """
    return db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.venta_contado_id == venta_contado_id
    ).order_by(Ticket.created_at.asc()).all()


def get_tickets_by_apartado(
    db: Session,
    tenant_id: int,
    apartado_id: int
) -> List[Ticket]:
    """
    Obtiene todos los tickets asociados a un apartado.
    """
    return db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.apartado_id == apartado_id
    ).order_by(Ticket.created_at.asc()).all()


def get_tickets_by_pedido(
    db: Session,
    tenant_id: int,
    pedido_id: int
) -> List[Ticket]:
    """
    Obtiene todos los tickets asociados a un pedido.
    """
    return db.query(Ticket).filter(
        Ticket.tenant_id == tenant_id,
        Ticket.pedido_id == pedido_id
    ).order_by(Ticket.created_at.asc()).all()

