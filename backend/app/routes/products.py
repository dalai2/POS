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
    sku: Optional[str] = None
    price: condecimal(max_digits=10, decimal_places=2) = 0
    cost_price: condecimal(max_digits=10, decimal_places=2) = 0
    stock: int = 0
    category: Optional[str] = None
    barcode: Optional[str] = None
    default_discount_pct: condecimal(max_digits=5, decimal_places=2) = 0
    active: bool = True


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
                    func.lower(Product.sku).like(f"%{qn}%"),
                    func.lower(Product.category).like(f"%{qn}%"),
                    func.lower(Product.barcode).like(f"%{qn}%"),
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
        sku=data.sku,
        price=data.price,
        cost_price=data.cost_price,
        stock=data.stock,
        category=data.category,
        barcode=data.barcode,
        default_discount_pct=data.default_discount_pct,
        active=data.active,
        tenant_id=tenant.id,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Friendly messages for unique constraints
        msg = str(e.orig)
        if "uq_products_tenant_sku" in msg:
            raise HTTPException(status_code=400, detail="SKU already exists for this tenant")
        if "uq_products_tenant_barcode" in msg:
            raise HTTPException(status_code=400, detail="Barcode already exists for this tenant")
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
    product.sku = data.sku
    product.price = data.price
    product.cost_price = data.cost_price
    product.stock = data.stock
    product.category = data.category
    product.barcode = data.barcode
    product.default_discount_pct = data.default_discount_pct
    product.active = data.active
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig)
        if "uq_products_tenant_sku" in msg:
            raise HTTPException(status_code=400, detail="SKU already exists for this tenant")
        if "uq_products_tenant_barcode" in msg:
            raise HTTPException(status_code=400, detail="Barcode already exists for this tenant")
        raise HTTPException(status_code=400, detail="Invalid product data")
    db.refresh(product)
    return product


@router.get("/lookup", response_model=ProductOut)
def lookup_product(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
    sku: Optional[str] = Query(None, description="Product SKU"),
    barcode: Optional[str] = Query(None, description="Product barcode"),
):
    if not sku and not barcode:
        raise HTTPException(status_code=400, detail="Provide either sku or barcode")
    query = db.query(Product).filter(Product.tenant_id == tenant.id)
    if sku and barcode:
        query = query.filter(or_(Product.sku == sku, Product.barcode == barcode))
    elif sku:
        query = query.filter(Product.sku == sku)
    else:
        query = query.filter(Product.barcode == barcode)
    product = query.first()
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


