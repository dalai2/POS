from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, condecimal
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant, require_admin
from app.models.product import Product
from app.models.tenant import Tenant
from app.models.user import User


router = APIRouter()


class ProductBase(BaseModel):
    name: str
    price: condecimal(max_digits=10, decimal_places=2) = 0
    cost_price: condecimal(max_digits=10, decimal_places=2) = 0
    stock: int = 0
    category: Optional[str] = None
    default_discount_pct: condecimal(max_digits=5, decimal_places=2) = 0
    active: bool = True
    
    # Jewelry-specific fields
    codigo: Optional[str] = None  # Single code field (replaces sku and barcode)
    marca: Optional[str] = None
    modelo: Optional[str] = None
    color: Optional[str] = None
    quilataje: Optional[str] = None
    base: Optional[str] = None
    tipo_joya: Optional[str] = None
    talla: Optional[str] = None
    peso_gramos: Optional[condecimal(max_digits=10, decimal_places=3)] = None
    descuento_porcentaje: Optional[condecimal(max_digits=5, decimal_places=2)] = None
    precio_manual: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    costo: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    precio_venta: Optional[condecimal(max_digits=10, decimal_places=2)] = None


class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
    q: Optional[str] = Query(None, description="Search by name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active: Optional[bool] = Query(None, description="Filter by active status"),
):
    logging.getLogger(__name__).info("list_products q=%s skip=%s limit=%s", q, skip, limit)
    query = db.query(Product).filter(Product.tenant_id == tenant.id)
    if q:
        qn = q.strip().lower()
        if qn:
            query = query.filter(
                or_(
                    func.lower(Product.name).like(f"%{qn}%"),
                    func.lower(Product.codigo).like(f"%{qn}%"),
                    func.lower(Product.category).like(f"%{qn}%"),
                )
            )
    if active is not None:
        query = query.filter(Product.active == active)
    items = query.offset(skip).limit(limit).all()
    return items


@router.post("/", response_model=ProductOut, dependencies=[Depends(require_admin)])
def create_product(
    data: ProductBase,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    product = Product(
        name=data.name,
        price=data.price,
        cost_price=data.cost_price,
        stock=data.stock,
        category=data.category,
        default_discount_pct=data.default_discount_pct,
        active=data.active,
        tenant_id=tenant.id,
        # Jewelry fields
        codigo=data.codigo,
        marca=data.marca,
        modelo=data.modelo,
        color=data.color,
        quilataje=data.quilataje,
        base=data.base,
        tipo_joya=data.tipo_joya,
        talla=data.talla,
        peso_gramos=data.peso_gramos,
        descuento_porcentaje=data.descuento_porcentaje,
        precio_manual=data.precio_manual,
        costo=data.costo,
        precio_venta=data.precio_venta,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Friendly messages for unique constraints
        msg = str(e.orig)
        if "uq_products_tenant_codigo" in msg:
            raise HTTPException(status_code=400, detail="Código already exists for this tenant")
        raise HTTPException(status_code=400, detail="Invalid product data")
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    return product


@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(
    product_id: int,
    data: ProductBase,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    product.name = data.name
    product.price = data.price
    product.cost_price = data.cost_price
    product.stock = data.stock
    product.category = data.category
    product.default_discount_pct = data.default_discount_pct
    product.active = data.active
    # Jewelry fields
    product.codigo = data.codigo
    product.marca = data.marca
    product.modelo = data.modelo
    product.color = data.color
    product.quilataje = data.quilataje
    product.base = data.base
    product.tipo_joya = data.tipo_joya
    product.talla = data.talla
    product.peso_gramos = data.peso_gramos
    product.descuento_porcentaje = data.descuento_porcentaje
    product.precio_manual = data.precio_manual
    product.costo = data.costo
    product.precio_venta = data.precio_venta
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig)
        if "uq_products_tenant_codigo" in msg:
            raise HTTPException(status_code=400, detail="Código already exists for this tenant")
        raise HTTPException(status_code=400, detail="Invalid product data")
    db.refresh(product)
    return product


@router.get("/lookup", response_model=ProductOut)
def lookup_product(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
    codigo: Optional[str] = Query(None, description="Product code"),
):
    if not codigo:
        raise HTTPException(status_code=400, detail="Provide codigo")
    product = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.codigo == codigo
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    return product


@router.post("/{product_id}/archive", response_model=ProductOut, dependencies=[Depends(require_admin)])
def archive_product(
    product_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    product.active = False
    db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/unarchive", response_model=ProductOut, dependencies=[Depends(require_admin)])
def unarchive_product(
    product_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    product.active = True
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id, Product.tenant_id == tenant.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(product)
    db.commit()
    return {"ok": True}


