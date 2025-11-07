from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..core.deps import get_db, get_current_user, get_tenant
from ..models.tasa_metal_pedido import TasaMetalPedido
from ..models.tenant import Tenant
from ..models.user import User

router = APIRouter()

# Pydantic schemas
class TasaMetalPedidoBase(BaseModel):
    metal_type: str
    rate_per_gram: float

class TasaMetalPedidoCreate(TasaMetalPedidoBase):
    pass

class TasaMetalPedidoUpdate(TasaMetalPedidoBase):
    pass

class TasaMetalPedidoOut(TasaMetalPedidoBase):
    id: int
    tenant_id: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TasaMetalPedidoOut])
def list_tasas_pedido(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user)
):
    """Listar todas las tasas de metal para pedidos del tenant"""
    tasas = db.query(TasaMetalPedido).filter(
        TasaMetalPedido.tenant_id == tenant.id
    ).all()
    return tasas


@router.post("/", response_model=TasaMetalPedidoOut)
def create_tasa_pedido(
    tasa_data: TasaMetalPedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user)
):
    """Crear una nueva tasa de metal para pedidos (solo admin/owner)"""
    if user.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    # Verificar si ya existe una tasa para este tipo de metal
    existing = db.query(TasaMetalPedido).filter(
        TasaMetalPedido.tenant_id == tenant.id,
        TasaMetalPedido.metal_type == tasa_data.metal_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe una tasa para {tasa_data.metal_type}"
        )
    
    tasa = TasaMetalPedido(
        tenant_id=tenant.id,
        metal_type=tasa_data.metal_type,
        rate_per_gram=tasa_data.rate_per_gram
    )
    db.add(tasa)
    db.commit()
    db.refresh(tasa)
    return tasa


@router.put("/{tasa_id}", response_model=TasaMetalPedidoOut)
def update_tasa_pedido(
    tasa_id: int,
    tasa_data: TasaMetalPedidoUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user)
):
    """Actualizar una tasa de metal para pedidos (solo admin/owner)"""
    if user.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    tasa = db.query(TasaMetalPedido).filter(
        TasaMetalPedido.id == tasa_id,
        TasaMetalPedido.tenant_id == tenant.id
    ).first()
    
    if not tasa:
        raise HTTPException(status_code=404, detail="Tasa no encontrada")
    
    tasa.metal_type = tasa_data.metal_type
    tasa.rate_per_gram = tasa_data.rate_per_gram
    
    db.commit()
    db.refresh(tasa)
    return tasa


@router.delete("/{tasa_id}")
def delete_tasa_pedido(
    tasa_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user)
):
    """Eliminar una tasa de metal para pedidos (solo admin/owner)"""
    if user.role not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    tasa = db.query(TasaMetalPedido).filter(
        TasaMetalPedido.id == tasa_id,
        TasaMetalPedido.tenant_id == tenant.id
    ).first()
    
    if not tasa:
        raise HTTPException(status_code=404, detail="Tasa no encontrada")
    
    db.delete(tasa)
    db.commit()
    return {"detail": "Tasa eliminada exitosamente"}








