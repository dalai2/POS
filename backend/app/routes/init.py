from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal, engine, _run_migration_notas_cliente
from app.models.tenant import Base
from app.services.jewelry_seed import seed_jewelry_demo
from app.models.tenant import Tenant
from sqlalchemy import text

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


@router.post("/run-migration-notas-cliente")
def run_migration_notas_cliente():
    """Ejecuta la migración para agregar columna notas_cliente a apartados"""
    try:
        with engine.connect() as connection:
            connection.execute(text("ALTER TABLE apartados ADD COLUMN IF NOT EXISTS notas_cliente TEXT"))
            connection.commit()
            
            # Verificar
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'apartados' 
                AND column_name = 'notas_cliente'
            """))
            row = result.fetchone()
            
            if row:
                return {
                    "success": True,
                    "message": "Migración ejecutada correctamente",
                    "column": {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2]
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "La columna no se pudo verificar"
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


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

