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
from app.models.cash_sale import VentasContado, ItemVentaContado
from app.models.apartado import Apartado, ItemApartado


router = APIRouter()


def _serialize_decimal(value):
    if value is None:
        return None
    return float(value)


def _serialize_datetime(value):
    if value is None:
        return None
    return value.isoformat()


def build_product_snapshot(product: Product) -> dict:
    return {
        "id": product.id,
        "tenant_id": product.tenant_id,
        "name": product.name,
        "modelo": getattr(product, "modelo", None),
        "marca": getattr(product, "marca", None),
        "color": getattr(product, "color", None),
        "quilataje": getattr(product, "quilataje", None),
        "base": getattr(product, "base", None),
        "tipo_joya": getattr(product, "tipo_joya", None),
        "talla": getattr(product, "talla", None),
        "codigo": product.codigo,
        "price": _serialize_decimal(product.price),
        "cost_price": _serialize_decimal(product.cost_price),
        "stock": product.stock,
        "category": product.category,
        "default_discount_pct": _serialize_decimal(product.default_discount_pct),
        "active": product.active,
        "peso_gramos": _serialize_decimal(product.peso_gramos),
        "descuento_porcentaje": _serialize_decimal(getattr(product, "descuento_porcentaje", None)),
        "precio_manual": _serialize_decimal(getattr(product, "precio_manual", None)),
        "costo": _serialize_decimal(getattr(product, "costo", None)),
        "precio_venta": _serialize_decimal(getattr(product, "precio_venta", None)),
        "created_at": _serialize_datetime(product.created_at),
    }


def build_description_from_product_data(product_data: dict) -> str:
    desc_parts = []
    name = product_data.get("name")
    modelo = product_data.get("modelo")
    color = product_data.get("color")
    quilataje = product_data.get("quilataje")
    peso_gramos = product_data.get("peso_gramos")
    talla = product_data.get("talla")
    if name:
        desc_parts.append(name)
    if modelo and modelo != name:
        desc_parts.append(modelo)
    if color:
        desc_parts.append(color)
    if quilataje:
        desc_parts.append(quilataje)
    if peso_gramos:
        peso = float(peso_gramos)
        if peso == int(peso):
            peso_formatted = f"{peso:.0f}"
        else:
            peso_formatted = f"{peso:.3f}".rstrip('0').rstrip('.')
        desc_parts.append(f"{peso_formatted}g")
    if talla:
        desc_parts.append(talla)
    return '-'.join(desc_parts) if desc_parts else (name or "")


def serialize_sale_items_with_snapshot(db: Session, tenant_id: int, sale_items: List[SaleItem]) -> List[dict]:
    product_cache: dict[int, dict | None] = {}
    serialized_items: List[dict] = []
    for item in sale_items:
        product_data = None
        if item.product_id:
            if item.product_id not in product_cache:
                product = db.query(Product).filter(
                    Product.id == item.product_id,
                    Product.tenant_id == tenant_id
                ).first()
                product_cache[item.product_id] = build_product_snapshot(product) if product else None
            product_data = product_cache.get(item.product_id)
        if product_data is None and item.product_snapshot:
            product_data = item.product_snapshot

        description = build_description_from_product_data(product_data) if product_data else item.name
        if product_data and product_data.get("codigo"):
            codigo = product_data.get("codigo")
        else:
            codigo = item.codigo

        serialized_items.append({
            "name": description or item.name,
            "codigo": codigo,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "discount_pct": item.discount_pct,
            "discount_amount": item.discount_amount,
            "total_price": item.total_price,
            "product_snapshot": product_data or item.product_snapshot
        })
    return serialized_items

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
    product_snapshot: dict | None = None

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
    folio_apartado: str | None = None  # Folio único para apartados

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

    # Calcularemos totales e inventario; luego insertaremos en tabla según tipo_venta

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
        # decrement stock
        if p.stock is not None:
            p.stock = int(p.stock) - q

    subtotal_val = subtotal.quantize(Decimal("0.01"))
    discount_val = Decimal(str(discount_amount or 0)).quantize(Decimal("0.01"))
    tax_rate_val = Decimal(str(tax_rate or 0)).quantize(Decimal("0.01"))
    taxable = max(Decimal("0"), subtotal_val - discount_val).quantize(Decimal("0.01"))
    tax_amount_val = (taxable * tax_rate_val / Decimal("100")).quantize(Decimal("0.01"))
    total_val = (taxable + tax_amount_val).quantize(Decimal("0.01"))

    # Save payments (optional)
    paid = Decimal("0")
    if payments:
        for p in payments:
            amt = Decimal(str(p.amount)).quantize(Decimal("0.01"))
            paid += amt

    # Para contado: validar que el pago cubre total si se envía
    if (tipo_venta or "contado") == "contado" and payments and paid < total_val:
        raise HTTPException(status_code=400, detail=f"Pago insuficiente: {paid} < {total_val}")
    
    # Para credito: validar anticipo > 0
    if (tipo_venta or "contado") == "credito" and paid <= Decimal("0"):
        raise HTTPException(
            status_code=400, 
            detail="El anticipo inicial debe ser mayor a 0 para apartados"
        )

    # Insertar según tipo_venta
    if (tipo_venta or "contado") == "contado":
        venta = VentasContado(
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
        )
        db.add(venta)
        db.flush()
        for it in items:
            p = product_map[it.product_id]
            q = max(1, int(it.quantity))
            unit = Decimal(str(p.price)).quantize(Decimal("0.01"))
            line_subtotal = (unit * q).quantize(Decimal("0.01"))
            line_disc_pct = Decimal(str(getattr(it, 'discount_pct', Decimal('0')) or 0)).quantize(Decimal("0.01"))
            line_disc_amount = (line_subtotal * line_disc_pct / Decimal('100')).quantize(Decimal('0.01'))
            line_total = (line_subtotal - line_disc_amount).quantize(Decimal('0.01'))
            db.add(ItemVentaContado(
                venta_id=venta.id,
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
        # Guardar pagos de contado
        payments_list = []
        if payments:
            for p_in in payments:
                amt = Decimal(str(p_in.amount)).quantize(Decimal("0.01"))
                db.add(Payment(venta_contado_id=venta.id, method=p_in.method, amount=amt))
                payments_list.append({"method": p_in.method, "amount": float(amt)})
        db.commit()
        db.refresh(venta)
        # Respuesta
        sale_items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id == venta.id).all()
        items_out = serialize_sale_items_with_snapshot(db, tenant.id, sale_items)  # uses similar fields
        return SaleOut(
            id=venta.id,
            user_id=venta.user_id,
            subtotal=venta.subtotal,
            discount_amount=venta.discount_amount,
            tax_rate=venta.tax_rate,
            tax_amount=venta.tax_amount,
            total=venta.total,
            items=items_out,
            created_at=venta.created_at,
            tipo_venta="contado",
            vendedor_id=venta.vendedor_id,
            utilidad=venta.utilidad,
            total_cost=venta.total_cost,
            amount_paid=paid,
            payments=payments_list
        )
    else:
        # credito (apartado)
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
        )
        db.add(apartado)
        db.flush()
        apartado.folio_apartado = f"APT-{str(apartado.id).zfill(6)}"
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
                    amount=amt,
                    payment_method=p_in.method,
                    user_id=user.id,
                    notes="Anticipo inicial"
                )
                db.add(cp)
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
        return SaleOut(
            id=apartado.id,
            user_id=apartado.user_id,
            subtotal=apartado.subtotal,
            discount_amount=apartado.discount_amount,
            tax_rate=apartado.tax_rate,
            tax_amount=apartado.tax_amount,
            total=apartado.total,
            items=items_out,
            created_at=apartado.created_at,
            tipo_venta="credito",
            vendedor_id=apartado.vendedor_id,
            utilidad=apartado.utilidad,
            total_cost=apartado.total_cost,
            folio_apartado=apartado.folio_apartado,
            customer_name=apartado.customer_name,
            customer_phone=apartado.customer_phone,
            customer_address=apartado.customer_address,
            amount_paid=apartado.amount_paid,
            credit_status=apartado.credit_status,
            payments=payments_list
        )


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
            product_snapshot=it.product_snapshot
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
    # Unir contado y apartados
    cont_q = db.query(VentasContado).filter(VentasContado.tenant_id == tenant.id)
    ap_q = db.query(Apartado).filter(Apartado.tenant_id == tenant.id)
    from sqlalchemy import and_
    if user_id is not None:
        cont_q = cont_q.filter(
            or_(VentasContado.vendedor_id == user_id, and_(VentasContado.vendedor_id == None, VentasContado.user_id == user_id))
        )
        ap_q = ap_q.filter(
            or_(Apartado.vendedor_id == user_id, and_(Apartado.vendedor_id == None, Apartado.user_id == user_id))
        )
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            cont_q = cont_q.filter(VentasContado.created_at >= df)
            ap_q = ap_q.filter(Apartado.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            cont_q = cont_q.filter(VentasContado.created_at <= dt)
            ap_q = ap_q.filter(Apartado.created_at <= dt)
        except Exception:
            pass
    cont_q = cont_q.order_by(VentasContado.created_at.desc())
    ap_q = ap_q.order_by(Apartado.created_at.desc())

    import csv
    from io import StringIO

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "created_at", "user_id", "total", "tipo_venta"]) 
    for s in cont_q.all():
        writer.writerow([
            s.id,
            s.created_at.isoformat() if s.created_at else "",
            s.user_id or "",
            f"{s.total}",
            "contado",
        ])
    for s in ap_q.all():
        writer.writerow([
            s.id,
            s.created_at.isoformat() if s.created_at else "",
            s.user_id or "",
            f"{s.total}",
            "abono",
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
    cont = db.query(VentasContado).filter(VentasContado.id == sale_id, VentasContado.tenant_id == tenant.id).first()
    if cont:
        payments = db.query(Payment).filter(Payment.venta_contado_id == cont.id).all()
        payments_list = [{"method": p.method, "amount": float(p.amount)} for p in payments] if payments else []
        sale_items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id == cont.id).all()
        items_out = serialize_sale_items_with_snapshot(db, tenant.id, sale_items)
        return SaleOut(
            id=cont.id,
            user_id=cont.user_id,
            subtotal=cont.subtotal,
            discount_amount=cont.discount_amount,
            tax_rate=cont.tax_rate,
            tax_amount=cont.tax_amount,
            total=cont.total,
            items=items_out,
            created_at=cont.created_at,
            tipo_venta="contado",
            vendedor_id=cont.vendedor_id,
            utilidad=cont.utilidad,
            total_cost=cont.total_cost,
            payments=payments_list
        )
    ap = db.query(Apartado).filter(Apartado.id == sale_id, Apartado.tenant_id == tenant.id).first()
    if ap:
        payments = db.query(CreditPayment).filter(CreditPayment.apartado_id == ap.id).all()
        payments_list = [{"method": p.payment_method, "amount": float(p.amount)} for p in payments] if payments else []
        sale_items = db.query(ItemApartado).filter(ItemApartado.apartado_id == ap.id).all()
        items_out = serialize_sale_items_with_snapshot(db, tenant.id, sale_items)
        return SaleOut(
            id=ap.id,
            user_id=ap.user_id,
            subtotal=ap.subtotal,
            discount_amount=ap.discount_amount,
            tax_rate=ap.tax_rate,
            tax_amount=ap.tax_amount,
            total=ap.total,
            items=items_out,
            created_at=ap.created_at,
            tipo_venta="credito",
            vendedor_id=ap.vendedor_id,
            utilidad=ap.utilidad,
            total_cost=ap.total_cost,
            folio_apartado=ap.folio_apartado,
            customer_name=ap.customer_name,
            customer_phone=ap.customer_phone,
            customer_address=ap.customer_address,
            amount_paid=ap.amount_paid,
            credit_status=ap.credit_status,
            payments=payments_list
        )
    raise HTTPException(status_code=404, detail="No encontrado")


class SaleSummary(BaseModel):
    id: int
    total: condecimal(max_digits=10, decimal_places=2)
    created_at: datetime | None = None
    user_id: int | None = None
    vendedor_id: int | None = None
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
    from sqlalchemy import or_, and_
    cont_q = db.query(VentasContado).filter(VentasContado.tenant_id == tenant.id)
    ap_q = db.query(Apartado).filter(Apartado.tenant_id == tenant.id)
    if user_id is not None:
        cont_q = cont_q.filter(or_(VentasContado.vendedor_id == user_id, and_(VentasContado.vendedor_id == None, VentasContado.user_id == user_id)))
        ap_q = ap_q.filter(or_(Apartado.vendedor_id == user_id, and_(Apartado.vendedor_id == None, Apartado.user_id == user_id)))
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            cont_q = cont_q.filter(VentasContado.created_at >= df)
            ap_q = ap_q.filter(Apartado.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            cont_q = cont_q.filter(VentasContado.created_at <= dt)
            ap_q = ap_q.filter(Apartado.created_at <= dt)
        except Exception:
            pass
    cont_q = cont_q.order_by(VentasContado.created_at.desc())
    ap_q = ap_q.order_by(Apartado.created_at.desc())

    sales_cont = cont_q.offset(skip).limit(min(200, max(1, limit))).all()
    sales_ap = ap_q.offset(skip).limit(min(200, max(1, limit))).all()

    result = []
    # contado
    for s in sales_cont:
        user_info = None
        if s.user_id:
            u = db.query(User).filter(User.id == s.user_id).first()
            if u:
                user_info = {"email": u.email}
        result.append({
            "id": s.id,
            "total": s.total,
            "created_at": s.created_at,
            "user_id": s.user_id,
            "vendedor_id": s.vendedor_id,
            "tipo_venta": "contado",
            "user": user_info
        })
    # apartados
    for s in sales_ap:
        user_info = None
        if s.user_id:
            u = db.query(User).filter(User.id == s.user_id).first()
            if u:
                user_info = {"email": u.email}
        result.append({
            "id": s.id,
            "total": s.total,
            "created_at": s.created_at,
            "user_id": s.user_id,
            "vendedor_id": s.vendedor_id,
            "tipo_venta": "abono",
            "user": user_info
        })
    # Ordenar por fecha desc
    result.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)
    return result



