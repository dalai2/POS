"""
Script to recreate database with new schema
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.models.tenant import Base
from app.core.database import SessionLocal
from app.services.jewelry_seed import seed_jewelry_demo

# Import all models to ensure they're registered
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.payment import Payment
from app.models.shift import Shift
from app.models.metal_rate import MetalRate
from app.models.inventory_movement import InventoryMovement
from app.models.inventory_closure import InventoryClosure
from app.models.credit_payment import CreditPayment
from app.models.producto_pedido import ProductoPedido, Pedido, PagoPedido

def recreate_db():
    print("Recreating database with new jewelry store schema...")
    
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    
    # Drop all tables
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables with new schema
    print("Creating tables with new schema...")
    Base.metadata.create_all(bind=engine)
    
    # Seed demo data
    print("Seeding demo data...")
    db = SessionLocal()
    try:
        seed_jewelry_demo(db)
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Database recreated successfully!")
    print("\nLogin credentials:")
    print("   Email: owner@demo.com")
    print("   Password: secret123")
    print("   Tenant: andani")

if __name__ == "__main__":
    recreate_db()

