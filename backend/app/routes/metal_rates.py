from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user, require_admin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.metal_rate import MetalRate
from app.models.product import Product

router = APIRouter()


class MetalRateCreate(BaseModel):
    metal_type: str  # Any metal type (e.g., "14k", "Plata Gold", "Oro Italiano")
    rate_per_gram: float


class MetalRateUpdate(BaseModel):
    metal_type: str | None = None
    rate_per_gram: float | None = None
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        # Check if metal_type is provided and not empty string
        metal_type_provided = self.metal_type is not None and self.metal_type != ''
        rate_per_gram_provided = self.rate_per_gram is not None
        
        if not metal_type_provided and not rate_per_gram_provided:
            raise ValueError('At least one field must be provided')
        return self


class MetalRateResponse(BaseModel):
    id: int
    metal_type: str
    rate_per_gram: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[MetalRateResponse])
def get_metal_rates(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all metal rates for the current tenant"""
    rates = db.query(MetalRate).filter(MetalRate.tenant_id == tenant.id).all()
    return rates


@router.post("", response_model=MetalRateResponse)
def create_metal_rate(
    data: MetalRateCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
):
    """Create a new metal rate"""
    # Check if rate already exists for this metal type
    existing = db.query(MetalRate).filter(
        MetalRate.tenant_id == tenant.id,
        MetalRate.metal_type == data.metal_type
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Metal rate already exists for this type. Use update instead.")
    
    rate = MetalRate(
        tenant_id=tenant.id,
        metal_type=data.metal_type,
        rate_per_gram=data.rate_per_gram
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.put("/{rate_id}", response_model=MetalRateResponse)
def update_metal_rate(
    rate_id: int,
    data: MetalRateUpdate,
    recalculate_prices: bool = True,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
):
    """Update a metal rate and optionally recalculate product prices"""
    rate = db.query(MetalRate).filter(
        MetalRate.id == rate_id,
        MetalRate.tenant_id == tenant.id
    ).first()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Metal rate not found")
    
    # Update metal_type if provided and not empty
    if data.metal_type is not None and data.metal_type != '':
        rate.metal_type = data.metal_type
    
    # Update rate_per_gram if provided
    if data.rate_per_gram is not None:
        rate.rate_per_gram = data.rate_per_gram
    
    # Recalculate prices for all products using this metal type
    if recalculate_prices:
        products = db.query(Product).filter(
            Product.tenant_id == tenant.id,
            Product.quilataje == rate.metal_type,
            Product.precio_manual == None,  # Only auto-calculate if no manual override
            Product.peso_gramos != None
        ).all()
        
        for product in products:
            # Calculate: (metal_rate × weight_grams) - discount% (redondeado a entero)
            base_price = round(float(rate.rate_per_gram) * float(product.peso_gramos))
            if product.descuento_porcentaje:
                discount = base_price * (float(product.descuento_porcentaje) / 100)
                final_price = round(base_price - discount)
            else:
                final_price = base_price

            product.price = final_price
            product.precio_venta = final_price
    
    db.commit()
    db.refresh(rate)
    return rate


@router.delete("/{rate_id}")
def delete_metal_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
):
    """Delete a metal rate"""
    rate = db.query(MetalRate).filter(
        MetalRate.id == rate_id,
        MetalRate.tenant_id == tenant.id
    ).first()
    
    if not rate:
        raise HTTPException(status_code=404, detail="Metal rate not found")
    
    db.delete(rate)
    db.commit()
    return {"message": "Metal rate deleted successfully"}

