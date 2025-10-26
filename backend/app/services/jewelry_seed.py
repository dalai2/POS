"""
Seed script for jewelry store demo data
"""
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.metal_rate import MetalRate
from app.models.sale import Sale, SaleItem
from app.models.credit_payment import CreditPayment


def seed_jewelry_demo(db: Session):
    """Seed basic data for jewelry store"""
    
    # Always create the Andani tenant
    print("Creating Andani tenant...")
    tenant = Tenant(name='Andani', slug='andani')
    db.add(tenant)
    db.flush()
    print(f"Tenant created with ID: {tenant.id}")
    
    # Create owner user
    print("Creating owner user...")
    owner = User(
        email='owner@demo.com',
        hashed_password=hash_password('secret123'),
        role='owner',
        tenant_id=tenant.id
    )
    db.add(owner)
    db.flush()
    print(f"Owner user created with ID: {owner.id}")
    
    # Create metal rates
    metal_rates_data = [
        # Oro
        ('10k', 25.50),
        ('14k', 35.75),
        ('18k', 45.90),
        ('oro_italiano', 52.00),
        # Plata
        ('plata_gold', 15.50),
        ('plata_silver', 12.25),
    ]
    
    print("Creating metal rates...")
    for metal_type, rate in metal_rates_data:
        metal_rate = MetalRate(
            tenant_id=tenant.id,
            metal_type=metal_type,
            rate_per_gram=rate
        )
        db.add(metal_rate)
        print(f"  - {metal_type}: ${rate}/g")
    
    db.commit()
    print(f"\nBasic data seeded successfully for tenant '{tenant.slug}'")

