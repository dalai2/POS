from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.products import router as products_router
from app.routes.health import router as health_router
from app.routes.admin import router as admin_router
from app.routes.billing import router as billing_router
from app.routes.sales import router as sales_router
from app.routes.metal_rates import router as metal_rates_router
from app.routes.inventory import router as inventory_router
from app.routes.credits import router as credits_router
from app.routes.reports import router as reports_router
from app.routes.import_export import router as import_export_router
from app.core.database import SessionLocal, init_db
from app.services.seed import seed_demo


def create_app() -> FastAPI:
    app = FastAPI(title="ERP POS API", version="0.1.0")

    origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health_router, tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"]) 
    app.include_router(products_router, prefix="/products", tags=["products"]) 
    app.include_router(admin_router, prefix="/admin", tags=["admin"]) 
    app.include_router(billing_router, prefix="/billing", tags=["billing"]) 
    app.include_router(sales_router, prefix="/sales", tags=["sales"])
    app.include_router(metal_rates_router, prefix="/metal-rates", tags=["metal-rates"])
    app.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
    app.include_router(credits_router, prefix="/credits", tags=["credits"])
    app.include_router(reports_router, prefix="/reports", tags=["reports"])
    app.include_router(import_export_router, prefix="/import", tags=["import-export"]) 

    return app


app = create_app()

# Optional dev seed
try:
    init_db()
    with SessionLocal() as db:
        seed_demo(db)
except Exception:
    pass


