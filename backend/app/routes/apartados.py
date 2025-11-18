"""
Rutas para gestión de apartados (ventas a crédito).
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, condecimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant, require_admin
from app.core.folio_service import generate_folio
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.apartado import Apartado, ItemApartado
from app.models.credit_payment import CreditPayment
from app.routes.status_history import create_status_history
from app.routes.ventas import (
    build_product_snapshot,
    serialize_sale_items_with_snapshot,
    SaleItemIn,
    PaymentIn
)
from app.services.customer_service import upsert_customer

router = APIRouter()


class ApartadoOut(BaseModel):
    id: int
    user_id: int | None
    subtotal: float
    discount_amount: float
    tax_rate: float
    tax_amount: float
    total: float
    items: List[dict]
    created_at: datetime
    vendedor_id: int | None
    utilidad: float | None
    total_cost: float | None
    folio_apartado: str | None
    customer_name: str | None
    customer_phone: str | None
    customer_address: str | None
    notas_cliente: str | None
    amount_paid: float | None
    credit_status: str | None
    payments: List[dict]

    class Config:
        from_attributes = True


class ApartadoUpdate(BaseModel):
    """Modelo para actualizar apartados - solo campos básicos, sin tocar lógica de negocio"""
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    credit_status: Optional[str] = None
    notas_cliente: Optional[str] = None


@router.post("/", response_model=ApartadoOut)
async def create_apartado_route(
    request: Request,
    items: List[SaleItemIn],
    payments: List[PaymentIn] | None = None,
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = Decimal("0"),
    tax_rate: condecimal(max_digits=5, decimal_places=2) | None = Decimal("0"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """
    Crea un apartado (venta a crédito).
    Requiere un anticipo inicial mayor a 0.
    """
    # Get the raw JSON data from request body
    body = await request.json()
    vendedor_id = body.get('vendedor_id') or user.id
    utilidad = body.get('utilidad')
    total_cost = body.get('total_cost')
    customer_name = body.get('customer_name')
    customer_phone = body.get('customer_phone')
    customer_address = body.get('customer_address')

    if not items:
        raise HTTPException(status_code=400, detail="No hay artículos en el apartado")

    # Load products and compute totals, validating stock
    product_map: dict[int, Product] = {}
    for it in items:
        p = db.query(Product).filter(
            Product.id == it.product_id,
            Product.tenant_id == tenant.id,
            Product.active == True
        ).first()
        if not p:
            raise HTTPException(status_code=400, detail=f"Producto inválido: {it.product_id}")
        product_map[it.product_id] = p

    # Calculate totals
    subtotal = Decimal("0")
    for it in items:
        p = product_map[it.product_id]
        q = max(1, int(it.quantity))
        if p.stock is not None and p.stock < q:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {p.name}")
        unit = Decimal(str(p.price)).quantize(Decimal("0.01"))
        line_subtotal = (unit * q).quantize(Decimal("0.01"))
        line_disc_pct = Decimal(str(getattr(it, 'discount_pct', Decimal('0')) or 0)).quantize(Decimal("0.01"))
        line_disc_amount = (line_subtotal * line_disc_pct / Decimal('100')).quantize(Decimal('0.01'))
        line_total = (line_subtotal - line_disc_amount).quantize(Decimal('0.01'))
        subtotal += line_total
        # Decrement stock
        if p.stock is not None:
            p.stock = int(p.stock) - q

    subtotal_val = subtotal.quantize(Decimal("0.01"))
    discount_val = Decimal(str(discount_amount or 0)).quantize(Decimal("0.01"))
    tax_rate_val = Decimal(str(tax_rate or 0)).quantize(Decimal("0.01"))
    taxable = max(Decimal("0"), subtotal_val - discount_val).quantize(Decimal("0.01"))
    tax_amount_val = (taxable * tax_rate_val / Decimal("100")).quantize(Decimal("0.01"))
    total_val = (taxable + tax_amount_val).quantize(Decimal("0.01"))

    # Save payments (required for apartado)
    paid = Decimal("0")
    if payments:
        for p in payments:
            amt = Decimal(str(p.amount)).quantize(Decimal("0.01"))
            paid += amt

    # Validar anticipo > 0
    if paid <= Decimal("0"):
        raise HTTPException(
            status_code=400,
            detail="El anticipo inicial debe ser mayor a 0 para apartados"
        )

    # Generar folio ANTES de crear el apartado (no depende del ID)
    folio_apartado = generate_folio(db, tenant.id, "APARTADO")
    # Crear apartado
    apartado = Apartado(
        tenant_id=tenant.id,
        user_id=user.id,
        subtotal=subtotal_val,
        discount_amount=discount_val,
        tax_rate=tax_rate_val,
        tax_amount=tax_amount_val,
        total=total_val,
        vendedor_id=vendedor_id,
        utilidad=Decimal(str(utilidad)) if utilidad is not None else None,
        total_cost=Decimal(str(total_cost)) if total_cost is not None else None,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        amount_paid=paid,
        credit_status="pendiente",
        folio_apartado=folio_apartado,  # Asignar folio al crear
    )
    db.add(apartado)
    upsert_customer(db, tenant.id, customer_name, customer_phone)
    db.flush()
    
    for it in items:
        p = product_map[it.product_id]
        q = max(1, int(it.quantity))
        unit = Decimal(str(p.price)).quantize(Decimal("0.01"))
        line_subtotal = (unit * q).quantize(Decimal("0.01"))
        line_disc_pct = Decimal(str(getattr(it, 'discount_pct', Decimal('0')) or 0)).quantize(Decimal("0.01"))
        line_disc_amount = (line_subtotal * line_disc_pct / Decimal('100')).quantize(Decimal('0.01'))
        line_total = (line_subtotal - line_disc_amount).quantize(Decimal('0.01'))
        db.add(ItemApartado(
            apartado_id=apartado.id,
            product_id=p.id,
            name=p.name,
            codigo=p.codigo,
            quantity=q,
            unit_price=unit,
            discount_pct=line_disc_pct,
            discount_amount=line_disc_amount,
            total_price=line_total,
            product_snapshot=build_product_snapshot(p)
        ))
    
    # Registrar pago inicial como CreditPayment
    payments_list = []
    if payments:
        for p_in in payments:
            amt = Decimal(str(p_in.amount)).quantize(Decimal("0.01"))
            cp = CreditPayment(
                tenant_id=tenant.id,
                apartado_id=apartado.id,
                sale_id=None,  # Explicitly set to None for new apartados
                amount=amt,
                payment_method=p_in.method,
                user_id=user.id,
                notes="Anticipo inicial"
            )
            db.add(cp)
            db.flush()  # Flush after each payment to avoid bulk insert issues
            payments_list.append({"method": p_in.method, "amount": float(amt)})
    
    db.commit()
    db.refresh(apartado)
    
    create_status_history(
        db=db,
        tenant_id=tenant.id,
        entity_type="sale",
        entity_id=apartado.id,
        old_status=None,
        new_status=apartado.credit_status,
        user_id=user.id,
        user_email=user.email,
        notes=f"Venta a crédito creada - Monto inicial pagado: ${float(apartado.amount_paid or 0):.2f}"
    )
    
    sale_items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
    items_out = serialize_sale_items_with_snapshot(db, tenant.id, sale_items)
    
    return ApartadoOut(
        id=apartado.id,
        user_id=apartado.user_id,
        subtotal=apartado.subtotal,
        discount_amount=apartado.discount_amount,
        tax_rate=apartado.tax_rate,
        tax_amount=apartado.tax_amount,
        total=apartado.total,
        items=items_out,
        created_at=apartado.created_at,
        vendedor_id=apartado.vendedor_id,
        utilidad=apartado.utilidad,
        total_cost=apartado.total_cost,
        folio_apartado=apartado.folio_apartado,
        customer_name=apartado.customer_name,
        customer_phone=apartado.customer_phone,
        customer_address=apartado.customer_address,
        notas_cliente=apartado.notas_cliente,
        amount_paid=apartado.amount_paid,
        credit_status=apartado.credit_status,
        payments=payments_list
    )


@router.put("/{apartado_id}", response_model=ApartadoOut)
def update_apartado(
    apartado_id: int,
    apartado_update: ApartadoUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """
    Actualizar un apartado - solo campos básicos.
    NO modifica items, pagos, o totales (lógica de negocio).
    """
    apartado = db.query(Apartado).filter(
        Apartado.id == apartado_id,
        Apartado.tenant_id == tenant.id
    ).first()
    
    if not apartado:
        raise HTTPException(status_code=404, detail="Apartado no encontrado")
    
    # Guardar estado anterior si se va a actualizar
    old_status = apartado.credit_status if 'credit_status' in apartado_update.dict(exclude_unset=True) else None
    
    # Actualizar solo campos permitidos (sin tocar lógica de negocio)
    update_data = apartado_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(apartado, field, value)
    
    # Registrar cambio de estado si cambió
    if old_status is not None and old_status != apartado.credit_status:
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="sale",  # Mantener compatibilidad con historial existente
            entity_id=apartado.id,
            old_status=old_status,
            new_status=apartado.credit_status,
            user_id=user.id,
            user_email=user.email,
            notes=f"Estado cambiado manualmente de {old_status} a {apartado.credit_status}"
        )
    
    # Actualizar cliente si cambió información
    if 'customer_name' in update_data or 'customer_phone' in update_data:
        upsert_customer(db, tenant.id, apartado.customer_name, apartado.customer_phone)
    
    db.commit()
    db.refresh(apartado)
    
    # Serializar respuesta (mismo código que get_apartado)
    payments = db.query(CreditPayment).filter(CreditPayment.apartado_id == apartado.id).all()
    payments_list = [{"method": p.payment_method, "amount": float(p.amount)} for p in payments] if payments else []
    sale_items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
    items_out = serialize_sale_items_with_snapshot(db, tenant.id, sale_items)
    
    return ApartadoOut(
        id=apartado.id,
        user_id=apartado.user_id,
        subtotal=apartado.subtotal,
        discount_amount=apartado.discount_amount,
        tax_rate=apartado.tax_rate,
        tax_amount=apartado.tax_amount,
        total=apartado.total,
        items=items_out,
        created_at=apartado.created_at,
        vendedor_id=apartado.vendedor_id,
        utilidad=apartado.utilidad,
        total_cost=apartado.total_cost,
        folio_apartado=apartado.folio_apartado,
        customer_name=apartado.customer_name,
        customer_phone=apartado.customer_phone,
        customer_address=apartado.customer_address,
        notas_cliente=apartado.notas_cliente,
        amount_paid=apartado.amount_paid,
        credit_status=apartado.credit_status,
        payments=payments_list
    )


@router.get("/{apartado_id}", response_model=ApartadoOut)
def get_apartado(
    apartado_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """Obtiene un apartado por ID"""
    apartado = db.query(Apartado).filter(
        Apartado.id == apartado_id,
        Apartado.tenant_id == tenant.id
    ).first()
    
    if not apartado:
        raise HTTPException(status_code=404, detail="Apartado no encontrado")
    
    payments = db.query(CreditPayment).filter(CreditPayment.apartado_id == apartado.id).all()
    payments_list = [{"method": p.payment_method, "amount": float(p.amount)} for p in payments] if payments else []
    
    sale_items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
    items_out = serialize_sale_items_with_snapshot(db, tenant.id, sale_items)
    
    return ApartadoOut(
        id=apartado.id,
        user_id=apartado.user_id,
        subtotal=apartado.subtotal,
        discount_amount=apartado.discount_amount,
        tax_rate=apartado.tax_rate,
        tax_amount=apartado.tax_amount,
        total=apartado.total,
        items=items_out,
        created_at=apartado.created_at,
        vendedor_id=apartado.vendedor_id,
        utilidad=apartado.utilidad,
        total_cost=apartado.total_cost,
        folio_apartado=apartado.folio_apartado,
        customer_name=apartado.customer_name,
        customer_phone=apartado.customer_phone,
        customer_address=apartado.customer_address,
        notas_cliente=apartado.notas_cliente,
        amount_paid=apartado.amount_paid,
        credit_status=apartado.credit_status,
        payments=payments_list
    )

