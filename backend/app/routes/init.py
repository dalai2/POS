from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal, engine
from app.models.tenant import Base
from app.services.jewelry_seed import seed_jewelry_demo
from app.models.tenant import Tenant

router = APIRouter()


@router.post("/initialize-database")
def initialize_database():
    """
    Initialize database with schema and demo data.
    WARNING: This will drop all existing tables and recreate them!
    """
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Create session for seeding
        db = SessionLocal()
        
        try:
            # Seed demo data
            from app.services.seed import seed_demo
            seed_demo(db)
            
            db.commit()
            
            return {
                "success": True,
                "message": "Database initialized successfully with demo data",
                "credentials": {
                    "email": "owner@demo.com",
                    "password": "secret123",
                    "tenant": "demo"
                }
            }
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing database: {str(e)}")


@router.get("/database-status")
def database_status(db: Session = Depends(get_db)):
    """Check if database is initialized"""
    try:
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.product import Product
        
        tenant_count = db.query(Tenant).count()
        user_count = db.query(User).count()
        product_count = db.query(Product).count()
        
        return {
            "initialized": tenant_count > 0,
            "tenants": tenant_count,
            "users": user_count,
            "products": product_count
        }
    except Exception as e:
        return {
            "initialized": False,
            "error": str(e)
        }

