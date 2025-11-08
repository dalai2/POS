from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.status_history import StatusHistory

router = APIRouter()


class StatusHistoryResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    old_status: Optional[str]
    new_status: str
    user_email: str
    notes: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


def create_status_history(
    db: Session,
    tenant_id: int,
    entity_type: str,
    entity_id: int,
    old_status: Optional[str],
    new_status: str,
    user_id: int,
    user_email: str,
    notes: Optional[str] = None
):
    """Helper function to create a status history entry"""
    history = StatusHistory(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        old_status=old_status,
        new_status=new_status,
        user_id=user_id,
        user_email=user_email,
        notes=notes
    )
    db.add(history)
    db.commit()
    return history


@router.get("/{entity_type}/{entity_id}", response_model=List[StatusHistoryResponse])
def get_status_history(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get status history for a sale or pedido"""
    if entity_type not in ["sale", "pedido"]:
        raise HTTPException(status_code=400, detail="Invalid entity type")
    
    history = db.query(StatusHistory).filter(
        StatusHistory.tenant_id == tenant.id,
        StatusHistory.entity_type == entity_type,
        StatusHistory.entity_id == entity_id
    ).order_by(StatusHistory.created_at.desc()).all()
    
    return [
        {
            "id": h.id,
            "entity_type": h.entity_type,
            "entity_id": h.entity_id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "user_email": h.user_email,
            "notes": h.notes,
            "created_at": h.created_at.isoformat()
        }
        for h in history
    ]

