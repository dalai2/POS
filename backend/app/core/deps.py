from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.tenant import Tenant
from app.models.user import User
from app.core.roles import Role, ADMIN_ROLES


def get_tenant_slug(request: Request, x_tenant_id: Optional[str] = Header(None)) -> str:
    if x_tenant_id:
        return x_tenant_id
    # Fallback: subdomain e.g., tenant.myapp.com
    host = request.headers.get("host", "")
    parts = host.split(":")[0].split(".")
    if len(parts) >= 3:
        return parts[0]
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tenant header")


def get_tenant(db: Session = Depends(get_db), tenant_slug: str = Depends(get_tenant_slug)) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    tenant: Tenant = Depends(get_tenant),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id), User.tenant_id == tenant.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in {r.value for r in ADMIN_ROLES}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
    return user

def require_owner(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.owner.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner role required")
    return user


