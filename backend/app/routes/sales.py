from typing import List
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, condecimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.payment import Payment


router = APIRouter()


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int
    discount_pct: condecimal(max_digits=5, decimal_places=2) | None = Decimal("0")
class PaymentIn(BaseModel):
    method: str
    amount: condecimal(max_digits=10, decimal_places=2)



class SaleOutItem(BaseModel):
    name: str
    sku: str | None
    quantity: int
    unit_price: condecimal(max_digits=10, decimal_places=2)
    discount_pct: condecimal(max_digits=5, decimal_places=2) | None = Decimal("0")
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = Decimal("0")
    total_price: condecimal(max_digits=10, decimal_places=2)

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: int
    subtotal: condecimal(max_digits=10, decimal_places=2) | None = None
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = None
    tax_rate: condecimal(max_digits=5, decimal_places=2) | None = None
    tax_amount: condecimal(max_digits=10, decimal_places=2) | None = None
    total: condecimal(max_digits=10, decimal_places=2)
    items: List[SaleOutItem]
    created_at: datetime | None = None

    class Config:
        from_attributes = True


@router.post("/", response_model=SaleOut)
def create_sale(
    items: List[SaleItemIn],
    payments: List[PaymentIn] | None = None,
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = Decimal("0"),
    tax_rate: condecimal(max_digits=5, decimal_places=2) | None = Decimal("15"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    if not items:
        raise HTTPException(status_code=400, detail="No hay artículos en la venta")

    # Load products and compute totals, validating stock
    product_map: dict[int, Product] = {}
    for it in items:
        p = db.query(Product).filter(Product.id == it.product_id, Product.tenant_id == tenant.id, Product.active == True).first()
        if not p:
            raise HTTPException(status_code=400, detail=f"Producto inválido: {it.product_id}")
        product_map[it.product_id] = p

    sale = Sale(tenant_id=tenant.id, user_id=user.id, total=Decimal("0"))
    db.add(sale)
    db.flush()

    subtotal = Decimal("0")
    for it in items:
        p = product_map[it.product_id]
        q = max(1, int(it.quantity))
        if p.stock is not None and p.stock < q:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {p.name}")
        unit = Decimal(str(p.price))
        line_subtotal = unit * q
        line_disc_pct = Decimal(str(getattr(it, 'discount_pct', Decimal('0')) or 0))
        line_disc_amount = (line_subtotal * line_disc_pct / Decimal('100')).quantize(Decimal('0.01'))
        line_total = line_subtotal - line_disc_amount
        subtotal += line_total
        db.add(SaleItem(
            sale_id=sale.id,
            product_id=p.id,
            name=p.name,
            sku=p.sku,
            quantity=q,
            unit_price=unit,
            discount_pct=line_disc_pct,
            discount_amount=line_disc_amount,
            total_price=line_total,
        ))
        # decrement stock
        if p.stock is not None:
            p.stock = int(p.stock) - q

    sale.subtotal = subtotal
    sale.discount_amount = Decimal(str(discount_amount or 0))
    sale.tax_rate = Decimal(str(tax_rate or 0))
    taxable = max(Decimal("0"), sale.subtotal - sale.discount_amount)
    sale.tax_amount = (taxable * sale.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    sale.total = (taxable + sale.tax_amount).quantize(Decimal("0.01"))
    # Save payments (optional)
    if payments:
        paid = Decimal("0")
        for p in payments:
            amt = Decimal(str(p.amount))
            paid += amt
            db.add(Payment(sale_id=sale.id, method=p.method, amount=amt))
        if paid < sale.total:
            raise HTTPException(status_code=400, detail="Pago insuficiente")
    db.commit()
    db.refresh(sale)
    return sale


@router.post("/{sale_id}/return", response_model=SaleOut)
def return_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    orig = db.query(Sale).filter(Sale.id == sale_id, Sale.tenant_id == tenant.id).first()
    if not orig:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    # Create a negative sale as return
    ret = Sale(
        tenant_id=tenant.id,
        user_id=user.id,
        return_of_id=orig.id,
        subtotal=-orig.subtotal,
        discount_amount=-orig.discount_amount,
        tax_rate=orig.tax_rate,
        tax_amount=-orig.tax_amount,
        total=-orig.total,
    )
    db.add(ret)
    db.flush()
    # Add negative items and restock
    for it in db.query(SaleItem).filter(SaleItem.sale_id == orig.id).all():
        db.add(SaleItem(
            sale_id=ret.id,
            product_id=it.product_id,
            name=it.name,
            sku=it.sku,
            quantity=-it.quantity,
            unit_price=it.unit_price,
            total_price=-it.total_price,
        ))
        if it.product_id:
            p = db.query(Product).filter(Product.id == it.product_id, Product.tenant_id == tenant.id).first()
            if p and p.stock is not None:
                p.stock = int(p.stock) + int(it.quantity)
    db.commit()
    db.refresh(ret)
    return ret


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.tenant_id == tenant.id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="No encontrado")
    return sale


class SaleSummary(BaseModel):
    id: int
    total: condecimal(max_digits=10, decimal_places=2)
    created_at: datetime | None = None
    user_id: int | None = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SaleSummary])
def list_sales(
    skip: int = 0,
    limit: int = 50,
    date_from: str | None = None,
    date_to: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    q = db.query(Sale).filter(Sale.tenant_id == tenant.id)
    if user_id is not None:
        q = q.filter(Sale.user_id == user_id)
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            q = q.filter(Sale.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            q = q.filter(Sale.created_at <= dt)
        except Exception:
            pass
    q = q.order_by(Sale.created_at.desc())
    return q.offset(skip).limit(min(200, max(1, limit))).all()


@router.get("/export")
def export_sales_csv(
    date_from: str | None = None,
    date_to: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    q = db.query(Sale).filter(Sale.tenant_id == tenant.id)
    if user_id is not None:
        q = q.filter(Sale.user_id == user_id)
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            q = q.filter(Sale.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            q = q.filter(Sale.created_at <= dt)
        except Exception:
            pass
    q = q.order_by(Sale.created_at.desc())

    import csv
    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "created_at", "user_id", "total"]) 
    for s in q.all():
        writer.writerow([
            s.id,
            s.created_at.isoformat() if s.created_at else "",
            s.user_id or "",
            f"{s.total}",
        ])
    csv_data = buf.getvalue()
    headers = {
        "Content-Disposition": "attachment; filename=ventas.csv",
        "Content-Type": "text/csv; charset=utf-8",
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)


