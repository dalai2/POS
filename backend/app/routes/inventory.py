from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user, require_admin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.inventory_closure import InventoryClosure
from app.services.inventory_service import (
    get_inventory_report,
    get_stock_grouped,
    get_stock_grouped_historical,
    get_stock_pedidos,
    get_stock_eliminado,
    get_stock_devuelto,
    get_stock_apartado,
    get_productos_pedido_apartado,
    get_pedidos_recibidos_apartados,
)

router = APIRouter()


class InventoryMovementCreate(BaseModel):
    product_id: int
    movement_type: str  # "entrada" or "salida"
    quantity: int
    cost: Optional[float] = None
    notes: Optional[str] = None


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    movement_type: str
    quantity: int
    cost: Optional[float]
    notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


@router.get("/product/{product_id}", response_model=List[InventoryMovementResponse])
def get_product_movements(
    product_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all inventory movements for a specific product"""
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.tenant_id == tenant.id,
        InventoryMovement.product_id == product_id
    ).order_by(InventoryMovement.created_at.desc()).all()
    return movements


@router.post("", response_model=InventoryMovementResponse)
def create_movement(
    data: InventoryMovementCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
):
    """Create an inventory movement (entrada or salida)"""
    # Verify product exists
    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.tenant_id == tenant.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate movement type
    if data.movement_type not in ["entrada", "salida"]:
        raise HTTPException(status_code=400, detail="Invalid movement type. Must be 'entrada' or 'salida'")
    
    # Create movement
    movement = InventoryMovement(
        tenant_id=tenant.id,
        product_id=data.product_id,
        user_id=current_user.id,
        movement_type=data.movement_type,
        quantity=data.quantity,
        cost=data.cost,
        notes=data.notes
    )
    db.add(movement)
    
    # Update product stock
    if data.movement_type == "entrada":
        product.stock += data.quantity
        # Update cost if provided
        if data.cost is not None:
            product.cost_price = data.cost
            product.costo = data.cost
    else:  # salida
        if product.stock < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.stock -= data.quantity
    
    db.commit()
    db.refresh(movement)
    return movement


@router.get("", response_model=List[InventoryMovementResponse])
def get_all_movements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all inventory movements for the tenant"""
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.tenant_id == tenant.id
    ).order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()
    return movements


def _ensure_inventory_closure_table(db: Session) -> None:
    """Ensure inventory_closures table exists"""
    try:
        InventoryClosure.__table__.create(bind=db.get_bind(), checkfirst=True)
    except Exception:
        # If creation fails, proceed; subsequent operations may still work if table exists
        pass


@router.get("/report")
def get_inventory_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Generate inventory report for the specified date range.
    If a closure exists for the date range, return it. Otherwise, generate new report.
    """
    from app.services.inventory_service import get_inventory_report as service_get_inventory_report
    
    # Check if using closure (single day)
    if start_date == end_date:
        _ensure_inventory_closure_table(db)
        closure = (
            db.query(InventoryClosure)
            .filter(
                InventoryClosure.tenant_id == tenant.id,
                InventoryClosure.closure_date == start_date,
            )
            .first()
        )
        if closure:
            return closure.data
    
    # Generate new report
    report = service_get_inventory_report(
        start_date=start_date,
        end_date=end_date,
        db=db,
        tenant=tenant
    )
    return report


@router.post("/close-day")
def close_inventory_day(
    for_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin),
):
    """
    Close inventory for a day: calculates inventory metrics for the day and saves them once.
    If a closure already exists for that day, returns a 400 error.
    """
    _ensure_inventory_closure_table(db)

    target_date = for_date or date.today()

    # Check if already closed
    existing = (
        db.query(InventoryClosure)
        .filter(
            InventoryClosure.tenant_id == tenant.id,
            InventoryClosure.closure_date == target_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="El cierre de inventario de este día ya fue realizado")

    # Generate report for that day
    from app.services.inventory_service import get_inventory_report as service_get_inventory_report
    from app.services.inventory_service import _build_inventory_snapshot
    
    report = service_get_inventory_report(
        start_date=target_date, end_date=target_date, db=db, tenant=tenant
    )
    
    snapshot = _build_inventory_snapshot(report)

    # Save complete JSON
    closure = InventoryClosure(
        tenant_id=tenant.id,
        closure_date=target_date,
        data=snapshot,
    )
    db.add(closure)
    db.commit()
    db.refresh(closure)

    return {"status": "ok", "message": "Cierre de inventario guardado", "date": target_date.isoformat(), "closure_id": closure.id}


@router.get("/closure")
def get_day_closure(
    for_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    View Inventory: read saved metrics from inventory closure for the day.
    If no closure exists, return 404.
    """
    _ensure_inventory_closure_table(db)

    target_date = for_date or date.today()
    closure = (
        db.query(InventoryClosure)
        .filter(
            InventoryClosure.tenant_id == tenant.id,
            InventoryClosure.closure_date == target_date,
        )
        .first()
    )
    if not closure:
        raise HTTPException(status_code=404, detail="Cierre de inventario pendiente para este día")

    return closure.data


@router.get("/closure-range")
def get_closure_range(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    View Period: aggregate saved closures in the range. Does not recalculate anything.
    Days without closures are omitted.
    """
    _ensure_inventory_closure_table(db)

    closures = (
        db.query(InventoryClosure)
        .filter(
            InventoryClosure.tenant_id == tenant.id,
            InventoryClosure.closure_date >= start_date,
            InventoryClosure.closure_date <= end_date,
        )
        .order_by(InventoryClosure.closure_date.asc())
        .all()
    )

    if not closures:
        raise HTTPException(status_code=404, detail="No hay cierres de inventario en este período")

    # Aggregate closures (for now, return list of closures)
    # In the future, could aggregate metrics
    return [closure.data for closure in closures]


class RemovePiecesRequest(BaseModel):
    product_id: int
    quantity: int
    notes: str


@router.post("/remove-pieces")
def remove_pieces(
    data: RemovePiecesRequest,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin),
):
    """
    Remove pieces from inventory (create salida movement with notes).
    """
    # Verify product exists
    product = db.query(Product).filter(
        Product.id == data.product_id,
        Product.tenant_id == tenant.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente")
    
    # Create salida movement
    movement = InventoryMovement(
        tenant_id=tenant.id,
        product_id=data.product_id,
        user_id=current_user.id,
        movement_type="salida",
        quantity=data.quantity,
        notes=data.notes
    )
    db.add(movement)
    
    # Update product stock
    product.stock -= data.quantity
    
    db.commit()
    db.refresh(movement)
    
    return {
        "id": movement.id,
        "product_id": movement.product_id,
        "user_id": movement.user_id,
        "movement_type": movement.movement_type,
        "quantity": movement.quantity,
        "notes": movement.notes,
        "created_at": movement.created_at.isoformat() if movement.created_at else "",
    }


@router.get("/stock-grouped")
def get_stock_grouped_endpoint(
    for_date: Optional[date] = Query(None, description="Calculate historical stock for this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get stock grouped by nombre, modelo, quilataje, marca, color, base, tipo_joya, talla.
    If for_date is provided, calculates historical stock for that date.
    Otherwise, returns current stock.
    """
    if for_date:
        stock = get_stock_grouped_historical(target_date=for_date, db=db, tenant=tenant)
    else:
        stock = get_stock_grouped(db=db, tenant=tenant)
    
    return stock


@router.get("/stock-pedidos")
def get_stock_pedidos(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get stock from pedidos recibidos (pedidos a proveedores).
    Returns products that came from received or paid pedidos.
    """
    from app.services.inventory_service import get_stock_pedidos as service_get_stock_pedidos
    
    stock = service_get_stock_pedidos(db=db, tenant=tenant)
    return stock


@router.get("/pedidos-recibidos")
def get_pedidos_recibidos(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of pedidos with estado='recibido'.
    Returns pedidos that have been received but not yet delivered.
    """
    from app.services.inventory_service import get_pedidos_recibidos as service_get_pedidos_recibidos
    
    pedidos = service_get_pedidos_recibidos(db=db, tenant=tenant)
    return pedidos


@router.get("/pedidos-entregados")
def get_pedidos_entregados(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of pedidos with estado='entregado'.
    Returns pedidos that have been delivered to customers.
    """
    from app.services.inventory_service import get_pedidos_entregados as service_get_pedidos_entregados
    
    pedidos = service_get_pedidos_entregados(db=db, tenant=tenant)
    return pedidos


@router.get("/productos-pedido")
def get_productos_pedido(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of products (piezas) from pedidos apartados with estado='pedido'.
    Returns all items from pedidos apartados that are in 'pedido' state (waiting to be ordered from suppliers).
    Shows only: modelo, nombre, quilataje.
    """
    productos = get_productos_pedido_apartado(db=db, tenant=tenant)
    return productos


@router.get("/stock-pedidos-estado-pedido")
def get_stock_pedidos_estado_pedido(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of products (piezas) from pedidos apartados with estado='pedido'.
    Shows only: modelo, nombre, quilataje.
    """
    productos = get_productos_pedido_apartado(db=db, tenant=tenant)
    return productos


@router.get("/pedidos-recibidos-apartados")
def get_pedidos_recibidos_apartados_endpoint(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of pedidos apartados with estado='recibido'.
    Returns only pedidos apartados that have been received.
    """
    pedidos = get_pedidos_recibidos_apartados(db=db, tenant=tenant)
    return pedidos


@router.get("/stock-eliminado")
def get_stock_eliminado(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get stock from eliminated products (active=False).
    """
    from app.services.inventory_service import get_stock_eliminado as service_get_stock_eliminado
    
    stock = service_get_stock_eliminado(db=db, tenant=tenant)
    return stock


@router.get("/stock-devuelto")
def get_stock_devuelto(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get stock from returned products.
    """
    from app.services.inventory_service import get_stock_devuelto as service_get_stock_devuelto
    
    stock = service_get_stock_devuelto(db=db, tenant=tenant)
    return stock


@router.get("/stock-apartado")
def get_stock_apartado_endpoint(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Get stock from ventas de apartado with credit_status 'pendiente' or 'pagado'.
    """
    stock = get_stock_apartado(db=db, tenant=tenant)
    return stock

