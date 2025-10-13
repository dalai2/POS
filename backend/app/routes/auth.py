from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_token, hash_password, verify_password
from app.core.deps import get_tenant
from app.models.tenant import Tenant
from app.models.user import User


router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "owner"
    tenant_name: str
    tenant_slug: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_tenant = db.query(Tenant).filter(Tenant.slug == data.tenant_slug).first()
    if existing_tenant:
        raise HTTPException(status_code=400, detail="Tenant already exists")

    tenant = Tenant(name=data.tenant_name, slug=data.tenant_slug)
    db.add(tenant)
    db.flush()

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        tenant_id=tenant.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_token(str(user.id), settings.access_token_expire_minutes, token_type="access")
    refresh = create_token(str(user.id), settings.refresh_token_expire_minutes, token_type="refresh")
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    user = db.query(User).filter(User.email == data.email, User.tenant_id == tenant.id).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access = create_token(str(user.id), settings.access_token_expire_minutes, token_type="access")
    refresh = create_token(str(user.id), settings.refresh_token_expire_minutes, token_type="refresh")
    return TokenResponse(access_token=access, refresh_token=refresh)


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(data: RefreshRequest, db: Session = Depends(get_db), tenant: Tenant = Depends(get_tenant)):
    from app.core.security import decode_token

    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == int(payload["sub"]), User.tenant_id == tenant.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access = create_token(str(user.id), settings.access_token_expire_minutes, token_type="access")
    refresh = create_token(str(user.id), settings.refresh_token_expire_minutes, token_type="refresh")
    return TokenResponse(access_token=access, refresh_token=refresh)



