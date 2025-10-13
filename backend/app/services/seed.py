from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.services.jewelry_seed import seed_jewelry_demo


def seed_demo(db: Session):
    if db.query(Tenant).filter(Tenant.slug == 'demo').first():
        # Ensure base user exists and jewelry products are seeded
        tenant = db.query(Tenant).filter(Tenant.slug == 'demo').first()
        if tenant:
            seed_jewelry_demo(db)
        return
    tenant = Tenant(name='Demo', slug='demo')
    db.add(tenant)
    db.flush()
    user = User(email='owner@demo.com', hashed_password=hash_password('secret123'), role='owner', tenant_id=tenant.id)
    db.add(user)
    db.commit()
    seed_jewelry_demo(db)


