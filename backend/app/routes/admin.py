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


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserOut], dependencies=[Depends(require_owner)])
def list_users(db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant), user: User = Depends(get_current_user)):
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


@router.post("/reseed", dependencies=[Depends(require_owner)])
def reseed_demo(db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant), user: User = Depends(get_current_user)):
    if tenant.slug != 'demo':
        raise HTTPException(status_code=400, detail="Reseed is only allowed for the demo tenant")
    seed_demo(db)
    return {"ok": True}



