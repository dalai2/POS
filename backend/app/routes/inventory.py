from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product

router = APIRouter()


class InventoryMovementCreate(BaseModel):
    product_id: int
    movement_type: str  # "entrada" or "salida"
    quantity: int
    cost: Optional[float] = None
    notes: Optional[str] = None


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    movement_type: str
    quantity: int
    cost: Optional[float]
    notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/product/{product_id}", response_model=List[InventoryMovementResponse])
def get_product_movements(
    product_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all inventory movements for a specific product"""
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.tenant_id == tenant.id,
        InventoryMovement.product_id == product_id
    ).order_by(InventoryMovement.created_at.desc()).all()
    return movements


@router.post("", response_model=InventoryMovementResponse)
def create_movement(
    data: InventoryMovementCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Create an inventory movement (entrada or salida)"""
    # Verify product exists
    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.tenant_id == tenant.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate movement type
    if data.movement_type not in ["entrada", "salida"]:
        raise HTTPException(status_code=400, detail="Invalid movement type. Must be 'entrada' or 'salida'")
    
    # Create movement
    movement = InventoryMovement(
        tenant_id=tenant.id,
        product_id=data.product_id,
        user_id=current_user.id,
        movement_type=data.movement_type,
        quantity=data.quantity,
        cost=data.cost,
        notes=data.notes
    )
    db.add(movement)
    
    # Update product stock
    if data.movement_type == "entrada":
        product.stock += data.quantity
        # Update cost if provided
        if data.cost is not None:
            product.cost_price = data.cost
            product.costo = data.cost
    else:  # salida
        if product.stock < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.stock -= data.quantity
    
    db.commit()
    db.refresh(movement)
    return movement


@router.get("", response_model=List[InventoryMovementResponse])
def get_all_movements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all inventory movements for the tenant"""
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.tenant_id == tenant.id
    ).order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()
    return movements

