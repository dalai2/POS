from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_tenant, require_owner
from app.core.database import get_db
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.services.seed import seed_demo

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    role: str | None = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant), user: User = Depends(get_current_user)):
    """List all users for the tenant (all authenticated users can view for vendor selection)"""
    return db.query(User).filter(User.tenant_id == tenant.id).all()


@router.post("/users", response_model=UserOut, dependencies=[Depends(require_owner)])
def create_user(data: UserCreate, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant), user: User = Depends(get_current_user)):
    if db.query(User).filter(User.tenant_id == tenant.id, User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists for this tenant")
    new_user = User(email=data.email, hashed_password=hash_password(data.password), role=data.role, tenant_id=tenant.id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_owner)])
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    user_to_update = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant.id
    ).first()
    
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent owner from removing their own owner role
    if user_to_update.id == current_user.id and data.role and data.role != 'owner':
        raise HTTPException(status_code=400, detail="Cannot change your own owner role")
    
    # Update fields
    if data.email:
        # Check if email already exists for another user
        existing = db.query(User).filter(
            User.tenant_id == tenant.id,
            User.email == data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        user_to_update.email = data.email
    
    if data.password:
        user_to_update.hashed_password = hash_password(data.password)
    
    if data.role:
        user_to_update.role = data.role
    
    db.commit()
    db.refresh(user_to_update)
    return user_to_update


@router.delete("/users/{user_id}", dependencies=[Depends(require_owner)])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    user_to_delete = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant.id
    ).first()
    
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent owner from deleting themselves
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user_to_delete)
    db.commit()
    return {"message": "User deleted successfully"}


@router.post("/reseed", dependencies=[Depends(require_owner)])
def reseed_demo(db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant), user: User = Depends(get_current_user)):
    if tenant.slug != 'demo':
        raise HTTPException(status_code=400, detail="Reseed is only allowed for the demo tenant")
    seed_demo(db)
    return {"ok": True}



