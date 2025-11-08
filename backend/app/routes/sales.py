from typing import List
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, condecimal
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant, require_admin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.payment import Payment
from app.models.credit_payment import CreditPayment
from app.routes.status_history import create_status_history


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
    codigo: str | None
    quantity: int
    unit_price: condecimal(max_digits=10, decimal_places=2)
    discount_pct: condecimal(max_digits=5, decimal_places=2) | None = Decimal("0")
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = Decimal("0")
    total_price: condecimal(max_digits=10, decimal_places=2)

    class Config:
        from_attributes = True


class PaymentOut(BaseModel):
    method: str
    amount: float


class SaleOut(BaseModel):
    id: int
    user_id: int | None = None
    subtotal: condecimal(max_digits=10, decimal_places=2) | None = None
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = None
    tax_rate: condecimal(max_digits=5, decimal_places=2) | None = None
    tax_amount: condecimal(max_digits=10, decimal_places=2) | None = None
    total: condecimal(max_digits=10, decimal_places=2)
    items: List[SaleOutItem]
    created_at: datetime | None = None

    # Jewelry store fields
    tipo_venta: str | None = None
    vendedor_id: int | None = None
    utilidad: condecimal(max_digits=10, decimal_places=2) | None = None
    total_cost: condecimal(max_digits=10, decimal_places=2) | None = None

    # Credit sale fields
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_address: str | None = None
    amount_paid: condecimal(max_digits=10, decimal_places=2) | None = None
    credit_status: str | None = None
    
    # Payment information
    payments: List[PaymentOut] | None = None

    class Config:
        from_attributes = True


@router.post("/", response_model=SaleOut)
async def create_sale(
    request: Request,
    items: List[SaleItemIn],
    payments: List[PaymentIn] | None = None,
    discount_amount: condecimal(max_digits=10, decimal_places=2) | None = Decimal("0"),
    tax_rate: condecimal(max_digits=5, decimal_places=2) | None = Decimal("0"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    # Get the raw JSON data from request body
    body = await request.json()
    tipo_venta = body.get('tipo_venta')
    vendedor_id = body.get('vendedor_id')
    utilidad = body.get('utilidad')
    total_cost = body.get('total_cost')
    customer_name = body.get('customer_name')
    customer_phone = body.get('customer_phone')
    customer_address = body.get('customer_address')

    if not items:
        raise HTTPException(status_code=400, detail="No hay artículos en la venta")

    # Load products and compute totals, validating stock
    product_map: dict[int, Product] = {}
    for it in items:
        p = db.query(Product).filter(Product.id == it.product_id, Product.tenant_id == tenant.id, Product.active == True).first()
        if not p:
            raise HTTPException(status_code=400, detail=f"Producto inválido: {it.product_id}")
        product_map[it.product_id] = p

    # Create sale object first
    sale = Sale(tenant_id=tenant.id, user_id=user.id)
    db.add(sale)
    db.flush()  # Get the sale.id

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
        
        # Build full description from product fields
        descParts = []
        if p.name: descParts.append(p.name)
        if p.modelo: descParts.append(p.modelo)
        if p.color: descParts.append(p.color)
        if p.quilataje: descParts.append(p.quilataje)
        if p.peso_gramos: 
            # Format weight to avoid unnecessary decimals
            peso = float(p.peso_gramos)
            if peso == int(peso):
                peso_formatted = f"{peso:.0f}"
            else:
                # Remove trailing zeros
                peso_formatted = f"{peso:.3f}".rstrip('0').rstrip('.')
            descParts.append(f"{peso_formatted}g")
        if p.talla: descParts.append(p.talla)
        full_description = '-'.join(descParts) if descParts else p.name
        
        db.add(SaleItem(
            sale_id=sale.id,
            product_id=p.id,
            name=full_description,
            codigo=p.codigo,
            quantity=q,
            unit_price=unit,
            discount_pct=line_disc_pct,
            discount_amount=line_disc_amount,
            total_price=line_total,
        ))
        # decrement stock
        if p.stock is not None:
            p.stock = int(p.stock) - q

    sale.subtotal = subtotal.quantize(Decimal("0.01"))
    sale.discount_amount = Decimal(str(discount_amount or 0)).quantize(Decimal("0.01"))
    sale.tax_rate = Decimal(str(tax_rate or 0)).quantize(Decimal("0.01"))
    taxable = max(Decimal("0"), sale.subtotal - sale.discount_amount).quantize(Decimal("0.01"))
    sale.tax_amount = (taxable * sale.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    sale.total = (taxable + sale.tax_amount).quantize(Decimal("0.01"))

    # Set additional fields if provided in request
    if tipo_venta is not None:
        sale.tipo_venta = tipo_venta
        # Set credit status for credit sales
        if tipo_venta == "abono":
            sale.credit_status = "pendiente"
    if vendedor_id is not None:
        sale.vendedor_id = vendedor_id
    if utilidad is not None:
        sale.utilidad = Decimal(str(utilidad))
    if total_cost is not None:
        sale.total_cost = Decimal(str(total_cost))

    # Set customer info if provided
    if customer_name is not None:
        sale.customer_name = customer_name
    if customer_phone is not None:
        sale.customer_phone = customer_phone
    if customer_address is not None:
        sale.customer_address = customer_address

    # Save payments (optional)
    paid = Decimal("0")
    if payments:
        for p in payments:
            amt = Decimal(str(p.amount)).quantize(Decimal("0.01"))
            paid += amt
            db.add(Payment(sale_id=sale.id, method=p.method, amount=amt))

    # Update amount_paid for the sale
    sale.amount_paid = paid

    # For contado sales, verify payment is sufficient only if payments were provided
    if sale.tipo_venta == "contado" and payments and paid < sale.total:
        raise HTTPException(status_code=400, detail=f"Pago insuficiente: {paid} < {sale.total}")

    db.commit()
    db.refresh(sale)
    
    # Registrar estado inicial para ventas a crédito
    if sale.credit_status:  # Si tiene credit_status, es una venta a crédito
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="sale",
            entity_id=sale.id,
            old_status=None,  # Estado inicial
            new_status=sale.credit_status,
            user_id=user.id,
            user_email=user.email,
            notes=f"Venta a crédito creada - Monto inicial pagado: ${float(sale.amount_paid or 0):.2f}"
        )
    
    # Get payments for this sale
    payments_list = []
    if payments:
        payments_list = [{"method": p.method, "amount": float(p.amount)} for p in payments]
    
    # Convert sale to SaleOut with payments
    sale_out = SaleOut(
        id=sale.id,
        user_id=sale.user_id,
        subtotal=sale.subtotal,
        discount_amount=sale.discount_amount,
        tax_rate=sale.tax_rate,
        tax_amount=sale.tax_amount,
        total=sale.total,
        items=db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all(),
        created_at=sale.created_at,
        tipo_venta=sale.tipo_venta,
        vendedor_id=sale.vendedor_id,
        utilidad=sale.utilidad,
        total_cost=sale.total_cost,
        customer_name=sale.customer_name,
        customer_phone=sale.customer_phone,
        customer_address=sale.customer_address,
        amount_paid=sale.amount_paid,
        credit_status=sale.credit_status,
        payments=payments_list
    )
    
    return sale_out


@router.post("/{sale_id}/return", response_model=SaleOut)
def return_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(require_admin),
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
            codigo=it.codigo,
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
    writer.writerow(["id", "created_at", "user_id", "total", "tipo_venta"]) 
    for s in q.all():
        writer.writerow([
            s.id,
            s.created_at.isoformat() if s.created_at else "",
            s.user_id or "",
            f"{s.total}",
            "abono" if s.tipo_venta == "credito" else (s.tipo_venta or ""),
        ])
    csv_data = buf.getvalue()
    headers = {
        "Content-Disposition": "attachment; filename=ventas.csv",
        "Content-Type": "text/csv; charset=utf-8",
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)


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
    
    # Get payments for this sale (both Payment and CreditPayment)
    payments_list = []
    payments = db.query(Payment).filter(Payment.sale_id == sale.id).all()
    if payments:
        payments_list = [{"method": p.method, "amount": float(p.amount)} for p in payments]
    
    # Also get credit payments (abonos)
    credit_payments = db.query(CreditPayment).filter(CreditPayment.sale_id == sale.id).all()
    if credit_payments:
        for cp in credit_payments:
            payments_list.append({"method": cp.payment_method, "amount": float(cp.amount)})
    
    # Build items with full description
    sale_items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
    items_with_description = []
    for item in sale_items:
        # If item has product relationship, build full description
        if item.product_id:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                descParts = []
                if product.name: descParts.append(product.name)
                if product.modelo: descParts.append(product.modelo)
                if product.color: descParts.append(product.color)
                if product.quilataje: descParts.append(product.quilataje)
                if product.peso_gramos: 
                    # Format weight to avoid unnecessary decimals
                    peso = float(product.peso_gramos)
                    if peso == int(peso):
                        peso_formatted = f"{peso:.0f}"
                    else:
                        # Remove trailing zeros
                        peso_formatted = f"{peso:.3f}".rstrip('0').rstrip('.')
                    descParts.append(f"{peso_formatted}g")
                if product.talla: descParts.append(product.talla)
                full_description = '-'.join(descParts) if descParts else product.name
                # Create a copy of the item with updated name
                item_dict = {
                    "name": full_description,
                    "codigo": item.codigo,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "discount_pct": item.discount_pct,
                    "discount_amount": item.discount_amount,
                    "total_price": item.total_price
                }
                items_with_description.append(item_dict)
            else:
                items_with_description.append(item)
        else:
            items_with_description.append(item)
    
    # Return sale with payments
    sale_out = SaleOut(
        id=sale.id,
        user_id=sale.user_id,
        subtotal=sale.subtotal,
        discount_amount=sale.discount_amount,
        tax_rate=sale.tax_rate,
        tax_amount=sale.tax_amount,
        total=sale.total,
        items=items_with_description,
        created_at=sale.created_at,
        tipo_venta=sale.tipo_venta,
        vendedor_id=sale.vendedor_id,
        utilidad=sale.utilidad,
        total_cost=sale.total_cost,
        customer_name=sale.customer_name,
        customer_phone=sale.customer_phone,
        customer_address=sale.customer_address,
        amount_paid=sale.amount_paid,
        credit_status=sale.credit_status,
        payments=payments_list
    )
    
    return sale_out


class SaleSummary(BaseModel):
    id: int
    total: condecimal(max_digits=10, decimal_places=2)
    created_at: datetime | None = None
    user_id: int | None = None
    tipo_venta: str | None = None
    user: dict | None = None

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
    sales = q.offset(skip).limit(min(200, max(1, limit))).all()
    
    # Build response with user information
    result = []
    for sale in sales:
        user_info = None
        if sale.user_id:
            user = db.query(User).filter(User.id == sale.user_id).first()
            if user:
                user_info = {"email": user.email}
        
        result.append({
            "id": sale.id,
            "total": sale.total,
            "created_at": sale.created_at,
            "user_id": sale.user_id,
            "tipo_venta": "abono" if sale.tipo_venta == "credito" else sale.tipo_venta,
            "user": user_info
        })
    
    return result



