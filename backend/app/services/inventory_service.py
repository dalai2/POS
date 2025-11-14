"""
Service for generating inventory control reports.
This service contains the business logic for inventory tracking and reporting.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime, date, timezone as tz

from app.models.tenant import Tenant
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.producto_pedido import Pedido, ProductoPedido


# TypedDict definitions for better type safety
class InventoryMovementData(TypedDict):
    """Structure for inventory movement data."""
    id: int
    product_id: int
    product_name: str
    product_codigo: Optional[str]
    movement_type: str
    quantity: int
    cost: Optional[float]
    notes: Optional[str]
    created_at: str
    user_id: int


class PedidoRecibidoData(TypedDict):
    """Structure for received pedido data."""
    id: int
    folio_pedido: str
    cliente_nombre: str
    producto_nombre: str
    producto_modelo: str
    cantidad: int
    precio_unitario: float
    total: float
    created_at: str
    fecha_recepcion: str


class PiezaDevueltaData(TypedDict):
    """Structure for returned piece data."""
    id: int
    tipo: str  # "venta" or "pedido"
    folio: Optional[str]
    cliente_nombre: Optional[str]
    producto_nombre: str
    cantidad: int
    motivo: str
    fecha: str


class PiezasIngresadasGroup(TypedDict):
    """Structure for grouped pieces by attributes."""
    nombre: Optional[str]
    modelo: Optional[str]
    quilataje: Optional[str]
    cantidad_total: int
    productos: List[Dict[str, Any]]


class InventoryReportData(TypedDict):
    """Structure for complete inventory report."""
    piezas_ingresadas: List[PiezasIngresadasGroup]
    historial_entradas: List[InventoryMovementData]
    historial_salidas: List[InventoryMovementData]
    pedidos_recibidos: List[PedidoRecibidoData]
    piezas_devueltas: List[PiezaDevueltaData]
    total_entradas: int
    total_salidas: int
    piezas_devueltas_total: int


def get_inventory_report(
    start_date: date,
    end_date: date,
    db: Session,
    tenant: Tenant,
) -> Dict[str, Any]:
    """
    Generate a complete inventory report for the specified date range.
    
    Args:
        start_date: Start date for the report period
        end_date: End date for the report period
        db: Database session
        tenant: Tenant for filtering data
        
    Returns:
        Dictionary containing the complete inventory report
        
    Raises:
        ValueError: If start_date > end_date
    """
    # Validate input parameters
    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")
    
    # Convert to datetime for queries (timezone-aware)
    # Adjust for Mexico timezone (UTC-6): 
    # - A movement created at 00:00 Mexico time = 06:00 UTC same day
    # - A movement created at 23:59 Mexico time = 05:59 UTC next day
    # So we need to:
    # - Start from 06:00 UTC of start_date (covers 00:00-23:59 Mexico time of start_date)
    # - End at 05:59:59 UTC of end_date+1 (covers 00:00-23:59 Mexico time of end_date)
    from datetime import timedelta
    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=tz.utc) + timedelta(hours=6)
    end_datetime = datetime.combine(end_date + timedelta(days=1), datetime.min.time()).replace(tzinfo=tz.utc) + timedelta(hours=6) - timedelta(seconds=1)
    
    # Get inventory movements
    movements_data = _get_inventory_movements_by_date_range(
        db, tenant, start_datetime, end_datetime
    )
    
    # Get pedidos recibidos
    pedidos_recibidos = _get_pedidos_recibidos_by_date_range(
        db, tenant, start_datetime, end_datetime
    )
    
    # Get piezas devueltas
    piezas_devueltas = _get_piezas_devueltas_by_date_range(
        db, tenant, start_datetime, end_datetime
    )
    
    # Group pieces by attributes (nombre, modelo, quilataje)
    piezas_ingresadas = _group_pieces_by_attributes(
        db, movements_data['entradas'], pedidos_recibidos, piezas_devueltas
    )
    
    # Calculate totals
    total_entradas = sum(m['quantity'] for m in movements_data['entradas'])
    total_salidas = sum(m['quantity'] for m in movements_data['salidas'])
    
    # Calculate total piezas devueltas:
    # - Pedidos vencidos/cancelados con tipo_pedido='apartado' en el rango de fechas
    # - Ventas de apartado devueltas (tipo_venta='credito' con return_of_id) en el rango de fechas
    # - Ventas de apartado vencidas/canceladas (tipo_venta='credito' con credit_status='vencido' o 'cancelado') en el rango de fechas
    pedidos_devueltos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado.in_(['vencido', 'cancelado']),
        Pedido.tipo_pedido == 'apartado',
        Pedido.updated_at >= start_datetime,
        Pedido.updated_at <= end_datetime
    ).all()
    
    ventas_apartado_devueltas = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == 'credito',
        Sale.return_of_id.isnot(None),
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).all()
    
    # Get ventas de apartado vencidas/canceladas (sin return_of_id, solo por status)
    ventas_apartado_vencidas_canceladas = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == 'credito',
        Sale.credit_status.in_(['vencido', 'cancelado']),
        Sale.return_of_id.is_(None),  # No devueltas, solo vencidas/canceladas
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).all()
    
    # Count pieces from pedidos devueltos
    total_piezas_devueltas = sum(p.cantidad for p in pedidos_devueltos)
    
    # Count pieces from ventas apartado devueltas
    for sale in ventas_apartado_devueltas:
        items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        total_piezas_devueltas += sum(item.quantity for item in items)
    
    # Count pieces from ventas apartado vencidas/canceladas
    for sale in ventas_apartado_vencidas_canceladas:
        items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        total_piezas_devueltas += sum(item.quantity for item in items)
    
    return {
        'piezas_ingresadas': piezas_ingresadas,
        'historial_entradas': movements_data['entradas'],
        'historial_salidas': movements_data['salidas'],
        'pedidos_recibidos': pedidos_recibidos,
        'piezas_devueltas': piezas_devueltas,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'piezas_devueltas_total': total_piezas_devueltas,
    }


def _get_inventory_movements_by_date_range(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> Dict[str, List[InventoryMovementData]]:
    """
    Get all inventory movements (entradas and salidas) in the date range.
    Uses datetime range comparison to handle timezone differences.
    
    Returns:
        Dictionary with 'entradas' and 'salidas' lists
    """
    movements = db.query(InventoryMovement).join(Product).filter(
        InventoryMovement.tenant_id == tenant.id,
        InventoryMovement.created_at >= start_datetime,
        InventoryMovement.created_at <= end_datetime
    ).order_by(InventoryMovement.created_at.desc()).all()
    
    entradas = []
    salidas = []
    
    for mov in movements:
        product = db.query(Product).filter(Product.id == mov.product_id).first()
        movement_data: InventoryMovementData = {
            'id': mov.id,
            'product_id': mov.product_id,
            'product_name': product.name if product else 'Producto eliminado',
            'product_codigo': product.codigo if product else None,
            'movement_type': mov.movement_type,
            'quantity': mov.quantity,
            'cost': float(mov.cost) if mov.cost else None,
            'notes': mov.notes,
            'created_at': mov.created_at.isoformat() if mov.created_at else '',
            'user_id': mov.user_id,
        }
        
        if mov.movement_type == 'entrada':
            entradas.append(movement_data)
        else:
            salidas.append(movement_data)
    
    return {'entradas': entradas, 'salidas': salidas}


def _get_pedidos_recibidos_by_date_range(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[PedidoRecibidoData]:
    """
    Get all pedidos with estado 'recibido' in the date range.
    Filter by updated_at to get when they were marked as received.
    Uses datetime range comparison to handle timezone differences.
    """
    pedidos = db.query(Pedido).join(ProductoPedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado == 'recibido',
        Pedido.updated_at >= start_datetime,
        Pedido.updated_at <= end_datetime
    ).order_by(Pedido.updated_at.desc()).all()
    
    result = []
    for pedido in pedidos:
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        
        pedido_data: PedidoRecibidoData = {
            'id': pedido.id,
            'folio_pedido': pedido.folio_pedido or f'PED-{pedido.id}',
            'cliente_nombre': pedido.cliente_nombre,
            'producto_nombre': producto.nombre if producto else 'N/A',
            'producto_modelo': producto.modelo if producto else 'N/A',
            'cantidad': pedido.cantidad,
            'precio_unitario': float(pedido.precio_unitario),
            'total': float(pedido.total),
            'created_at': pedido.created_at.isoformat() if pedido.created_at else '',
            'fecha_recepcion': pedido.updated_at.isoformat() if pedido.updated_at else '',
        }
        result.append(pedido_data)
    
    return result


def _get_piezas_devueltas_by_date_range(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[PiezaDevueltaData]:
    """
    Get all returned pieces (ventas with return_of_id, ventas de apartado devueltas, ventas de apartado vencidas/canceladas, and pedidos cancelados/vencidos).
    Uses datetime range comparison to handle timezone differences.
    """
    result = []
    
    # Get returned sales (ventas with return_of_id) - includes all returned sales
    returned_sales = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.return_of_id.isnot(None),
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).order_by(Sale.created_at.desc()).all()
    
    # Get returned credit sales (ventas de apartado devueltas) - tipo_venta='credito' with return_of_id
    returned_credit_sales = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == 'credito',
        Sale.return_of_id.isnot(None),
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).order_by(Sale.created_at.desc()).all()
    
    # Get ventas de apartado vencidas/canceladas (sin return_of_id, solo por status)
    ventas_apartado_vencidas_canceladas = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == 'credito',
        Sale.credit_status.in_(['vencido', 'cancelado']),
        Sale.return_of_id.is_(None),  # No devueltas, solo vencidas/canceladas
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).order_by(Sale.created_at.desc()).all()
    
    # Combine all sales lists, avoiding duplicates
    all_returned_sales = {s.id: s for s in returned_sales}
    for s in returned_credit_sales:
        if s.id not in all_returned_sales:
            all_returned_sales[s.id] = s
    for s in ventas_apartado_vencidas_canceladas:
        if s.id not in all_returned_sales:
            all_returned_sales[s.id] = s
    returned_sales = list(all_returned_sales.values())
    
    for sale in returned_sales:
        # Get sale items to get product info
        items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
        
        # Determine motivo based on sale type and status
        motivo = 'Devolución de venta'
        if sale.tipo_venta == 'credito':
            if sale.return_of_id is not None:
                motivo = 'Devolución de apartado'
            elif sale.credit_status == 'vencido':
                motivo = 'Apartado vencido'
            elif sale.credit_status == 'cancelado':
                motivo = 'Apartado cancelado'
        
        folio = sale.folio_apartado if sale.folio_apartado else f'VENTA-{sale.id}'
        
        for item in items:
            pieza_data: PiezaDevueltaData = {
                'id': sale.id,
                'tipo': 'venta',
                'folio': folio,
                'cliente_nombre': sale.customer_name,
                'producto_nombre': item.name,
                'cantidad': item.quantity,
                'motivo': motivo,
                'fecha': sale.created_at.isoformat() if sale.created_at else '',
            }
            result.append(pieza_data)
    
    # Get cancelled/expired pedidos
    cancelled_pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado.in_(['cancelado', 'vencido']),
        Pedido.updated_at >= start_datetime,
        Pedido.updated_at <= end_datetime
    ).order_by(Pedido.updated_at.desc()).all()
    
    for pedido in cancelled_pedidos:
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        
        motivo = 'Cancelado' if pedido.estado == 'cancelado' else 'Vencido'
        pieza_data: PiezaDevueltaData = {
            'id': pedido.id,
            'tipo': 'pedido',
            'folio': pedido.folio_pedido or f'PED-{pedido.id}',
            'cliente_nombre': pedido.cliente_nombre,
            'producto_nombre': producto.nombre if producto else 'N/A',
            'cantidad': pedido.cantidad,
            'motivo': motivo,
            'fecha': pedido.updated_at.isoformat() if pedido.updated_at else '',
        }
        result.append(pieza_data)
    
    return result


def _group_pieces_by_attributes(
    db: Session,
    entradas: List[InventoryMovementData],
    pedidos_recibidos: List[PedidoRecibidoData],
    piezas_devueltas: List[PiezaDevueltaData]
) -> List[PiezasIngresadasGroup]:
    """
    Group pieces by nombre, modelo, and quilataje.
    Includes pieces from entradas, pedidos recibidos, and devueltas.
    """
    groups: Dict[str, Dict[str, Any]] = {}
    
    # Process entradas
    for entrada in entradas:
        product = db.query(Product).filter(Product.id == entrada['product_id']).first()
        if not product:
            continue
        
        key = f"{product.name or ''}|{product.modelo or ''}|{product.quilataje or ''}"
        if key not in groups:
            groups[key] = {
                'nombre': product.name,
                'modelo': product.modelo,
                'quilataje': product.quilataje,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += entrada['quantity']
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'cantidad': entrada['quantity'],
            'fecha': entrada['created_at'],
            'tipo': 'entrada',
            'notas': entrada['notes']
        })
    
    # Process pedidos recibidos
    for pedido in pedidos_recibidos:
        key = f"{pedido['producto_nombre'] or ''}|{pedido['producto_modelo'] or ''}|"
        if key not in groups:
            groups[key] = {
                'nombre': pedido['producto_nombre'],
                'modelo': pedido['producto_modelo'],
                'quilataje': None,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += pedido['cantidad']
        groups[key]['productos'].append({
            'id': pedido['id'],
            'codigo': None,
            'cantidad': pedido['cantidad'],
            'fecha': pedido['fecha_recepcion'],
            'tipo': 'pedido_recibido',
            'notas': f"Pedido {pedido['folio_pedido']}"
        })
    
    # Process devueltas (they add to inventory)
    for devuelta in piezas_devueltas:
        key = f"{devuelta['producto_nombre'] or ''}||"
        if key not in groups:
            groups[key] = {
                'nombre': devuelta['producto_nombre'],
                'modelo': None,
                'quilataje': None,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += devuelta['cantidad']
        groups[key]['productos'].append({
            'id': devuelta['id'],
            'codigo': None,
            'cantidad': devuelta['cantidad'],
            'fecha': devuelta['fecha'],
            'tipo': 'devolucion',
            'notas': devuelta['motivo']
        })
    
    return list(groups.values())


def _build_inventory_snapshot(
    report_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a snapshot of inventory state for closure.
    This preserves the complete state at a point in time.
    """
    return {
        'report_data': report_data,
        'snapshot_date': datetime.now(tz.utc).isoformat(),
    }


def get_stock_grouped(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get current stock grouped by nombre, modelo, quilataje, marca, color, base, tipo_joya, talla.
    
    Returns:
        List of grouped stock entries with total quantities
    """
    products = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.active == True,
        Product.stock > 0
    ).all()
    
    groups: Dict[str, Dict[str, Any]] = {}
    
    for product in products:
        # Create grouping key from all relevant attributes
        key = "|".join([
            str(product.name or ''),
            str(product.modelo or ''),
            str(product.quilataje or ''),
            str(product.marca or ''),
            str(product.color or ''),
            str(product.base or ''),
            str(product.tipo_joya or ''),
            str(product.talla or ''),
        ])
        
        if key not in groups:
            groups[key] = {
                'nombre': product.name,
                'modelo': product.modelo,
                'quilataje': product.quilataje,
                'marca': product.marca,
                'color': product.color,
                'base': product.base,
                'tipo_joya': product.tipo_joya,
                'talla': product.talla,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += product.stock
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'stock': product.stock,
            'precio': float(product.price),
            'costo': float(product.cost_price),
        })
    
    return list(groups.values())


def get_stock_grouped_historical(
    target_date: date,
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Calculate historical stock grouped by nombre, modelo, quilataje, marca, color, base, tipo_joya, talla
    for a specific date by working backwards from current stock.
    
    Args:
        target_date: The date to calculate stock for
        db: Database session
        tenant: Tenant for filtering
        
    Returns:
        List of grouped stock entries with total quantities as they were on target_date
    """
    from datetime import timedelta
    
    # If target_date is today or future, use current stock
    if target_date >= date.today():
        return get_stock_grouped(db=db, tenant=tenant)
    
    # Convert target_date to datetime with Mexico timezone adjustment (UTC-6)
    # We want to include all movements UP TO the end of target_date in Mexico time
    # End of day in Mexico = 23:59:59 Mexico = 05:59:59 UTC next day
    target_datetime_end = datetime.combine(
        target_date + timedelta(days=1), 
        datetime.min.time()
    ).replace(tzinfo=tz.utc) + timedelta(hours=6) - timedelta(seconds=1)
    
    # Get all products that existed on or before target_date
    products = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.active == True
    ).all()
    
    # Calculate historical stock for each product
    historical_stocks: Dict[int, int] = {}
    
    for product in products:
        current_stock = int(product.stock) if product.stock else 0
        
        # Get movements that happened AFTER target_date
        movements_after = db.query(InventoryMovement).filter(
            InventoryMovement.tenant_id == tenant.id,
            InventoryMovement.product_id == product.id,
            InventoryMovement.created_at > target_datetime_end
        ).all()
        
        # Get sale items that happened AFTER target_date
        sales_after = db.query(SaleItem).join(Sale).filter(
            Sale.tenant_id == tenant.id,
            SaleItem.product_id == product.id,
            Sale.created_at > target_datetime_end,
            Sale.return_of_id == None  # Don't count returned sales
        ).all()
        
        # Calculate historical stock by reversing future changes
        historical_stock = current_stock
        
        # Reverse movements after target date
        for movement in movements_after:
            if movement.movement_type == 'entrada':
                # If it was an entrada (addition), subtract it to get historical stock
                historical_stock -= movement.quantity
            else:  # salida
                # If it was a salida (removal), add it back to get historical stock
                historical_stock += movement.quantity
        
        # Reverse sales after target date
        for sale_item in sales_after:
            # Sales reduce stock, so add them back
            historical_stock += sale_item.quantity
        
        # Stock can't be negative (data inconsistency protection)
        historical_stocks[product.id] = max(0, historical_stock)
    
    # Now group products with their historical stocks
    groups: Dict[str, Dict[str, Any]] = {}
    
    for product in products:
        historical_stock = historical_stocks.get(product.id, 0)
        
        # Skip products with no historical stock
        if historical_stock <= 0:
            continue
        
        # Create grouping key from all relevant attributes
        key = "|".join([
            str(product.name or ''),
            str(product.modelo or ''),
            str(product.quilataje or ''),
            str(product.marca or ''),
            str(product.color or ''),
            str(product.base or ''),
            str(product.tipo_joya or ''),
            str(product.talla or ''),
        ])
        
        if key not in groups:
            groups[key] = {
                'nombre': product.name,
                'modelo': product.modelo,
                'quilataje': product.quilataje,
                'marca': product.marca,
                'color': product.color,
                'base': product.base,
                'tipo_joya': product.tipo_joya,
                'talla': product.talla,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += historical_stock
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'stock': historical_stock,
            'precio': float(product.price),
            'costo': float(product.cost_price),
        })
    
    return list(groups.values())


def get_stock_pedidos(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get stock from pedidos recibidos and pagados (products that came from received or paid pedidos).
    """
    # Get all inventory movements from pedidos recibidos or pagados
    movements = db.query(InventoryMovement).join(Product).filter(
        InventoryMovement.tenant_id == tenant.id,
        InventoryMovement.movement_type == 'entrada',
        or_(
            InventoryMovement.notes.like('%Pedido recibido%'),
            InventoryMovement.notes.like('%Pedido pagado%')
        )
    ).all()
    
    # Also get pedidos with estado 'recibido' or 'pagado' to find related products
    pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado.in_(['recibido', 'pagado'])
    ).all()
    
    # Get product IDs from movements
    product_ids = [m.product_id for m in movements]
    
    # Get product IDs from pedidos (find products by codigo or create mapping)
    for pedido in pedidos:
        producto_pedido = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        if producto_pedido and producto_pedido.codigo:
            product = db.query(Product).filter(
                Product.tenant_id == tenant.id,
                Product.codigo == producto_pedido.codigo
            ).first()
            if product and product.id not in product_ids:
                product_ids.append(product.id)
    
    if not product_ids:
        return []
    
    products = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.id.in_(product_ids),
        Product.stock > 0
    ).all()
    
    groups: Dict[str, Dict[str, Any]] = {}
    
    for product in products:
        key = "|".join([
            str(product.name or ''),
            str(product.modelo or ''),
            str(product.quilataje or ''),
        ])
        
        if key not in groups:
            groups[key] = {
                'nombre': product.name,
                'modelo': product.modelo,
                'quilataje': product.quilataje,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += product.stock
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'stock': product.stock,
            'precio': float(product.price),
            'costo': float(product.cost_price),
        })
    
    return list(groups.values())


def get_stock_eliminado(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get stock from eliminated products (active=False) and pedidos entregados (tipo_pedido='apartado').
    """
    # Get products with active=False
    products = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.active == False,
        Product.stock > 0
    ).all()
    
    # Get pedidos entregados (tipo_pedido='apartado')
    pedidos_entregados = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado == 'entregado',
        Pedido.tipo_pedido == 'apartado'
    ).all()
    
    # Get products from pedidos entregados
    product_ids_from_pedidos = set()
    for pedido in pedidos_entregados:
        producto_pedido = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        if producto_pedido and producto_pedido.codigo:
            product = db.query(Product).filter(
                Product.tenant_id == tenant.id,
                Product.codigo == producto_pedido.codigo,
                Product.stock > 0
            ).first()
            if product:
                product_ids_from_pedidos.add(product.id)
    
    # Get products from pedidos entregados
    if product_ids_from_pedidos:
        products_from_pedidos = db.query(Product).filter(
            Product.tenant_id == tenant.id,
            Product.id.in_(list(product_ids_from_pedidos)),
            Product.stock > 0
        ).all()
        # Combine with eliminated products, avoiding duplicates
        product_dict = {p.id: p for p in products}
        for p in products_from_pedidos:
            if p.id not in product_dict:
                product_dict[p.id] = p
        products = list(product_dict.values())
    
    groups: Dict[str, Dict[str, Any]] = {}
    
    for product in products:
        key = "|".join([
            str(product.name or ''),
            str(product.modelo or ''),
            str(product.quilataje or ''),
            str(product.marca or ''),
            str(product.color or ''),
            str(product.base or ''),
            str(product.tipo_joya or ''),
            str(product.talla or ''),
        ])
        
        if key not in groups:
            groups[key] = {
                'nombre': product.name,
                'modelo': product.modelo,
                'quilataje': product.quilataje,
                'marca': product.marca,
                'color': product.color,
                'base': product.base,
                'tipo_joya': product.tipo_joya,
                'talla': product.talla,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += product.stock
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'stock': product.stock,
            'precio': float(product.price),
            'costo': float(product.cost_price),
        })
    
    return list(groups.values())


def get_stock_devuelto(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get stock from returned products (products that came from returns).
    """
    # Get all inventory movements from devoluciones
    movements = db.query(InventoryMovement).join(Product).filter(
        InventoryMovement.tenant_id == tenant.id,
        InventoryMovement.movement_type == 'entrada',
        or_(
            InventoryMovement.notes.like('%Devolución%'),
            InventoryMovement.notes.like('%devolución%'),
            InventoryMovement.notes.like('%Cancelado%'),
            InventoryMovement.notes.like('%Vencido%')
        )
    ).all()
    
    # Get current stock for these products
    product_ids = [m.product_id for m in movements]
    if not product_ids:
        return []
    
    products = db.query(Product).filter(
        Product.tenant_id == tenant.id,
        Product.id.in_(product_ids),
        Product.stock > 0
    ).all()
    
    groups: Dict[str, Dict[str, Any]] = {}
    
    for product in products:
        key = "|".join([
            str(product.name or ''),
            str(product.modelo or ''),
            str(product.quilataje or ''),
            str(product.marca or ''),
            str(product.color or ''),
            str(product.base or ''),
            str(product.tipo_joya or ''),
            str(product.talla or ''),
        ])
        
        if key not in groups:
            groups[key] = {
                'nombre': product.name,
                'modelo': product.modelo,
                'quilataje': product.quilataje,
                'marca': product.marca,
                'color': product.color,
                'base': product.base,
                'tipo_joya': product.tipo_joya,
                'talla': product.talla,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += product.stock
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'stock': product.stock,
            'precio': float(product.price),
            'costo': float(product.cost_price),
        })
    
    return list(groups.values())


def get_stock_apartado(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get stock from ventas de apartado with credit_status 'pendiente' or 'pagado'.
    Groups pieces by nombre, modelo, quilataje, marca, color, base, tipo_joya, talla.
    """
    # Get sales with tipo_venta='credito' and credit_status in ['pendiente', 'pagado']
    sales = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == 'credito',
        Sale.credit_status.in_(['pendiente', 'pagado'])
    ).all()
    
    # Get all sale items from these sales
    sale_ids = [s.id for s in sales]
    if not sale_ids:
        return []
    
    sale_items = db.query(SaleItem).filter(
        SaleItem.sale_id.in_(sale_ids)
    ).all()
    
    # Group by product attributes
    groups: Dict[str, Dict[str, Any]] = {}
    
    for item in sale_items:
        # Get product if exists
        product = None
        if item.product_id:
            product = db.query(Product).filter(
                Product.id == item.product_id,
                Product.tenant_id == tenant.id
            ).first()
        
        # Get sale info
        sale = next((s for s in sales if s.id == item.sale_id), None)
        
        # Create grouping key from product attributes or item name
        if product:
            key = "|".join([
                str(product.name or ''),
                str(product.modelo or ''),
                str(product.quilataje or ''),
                str(product.marca or ''),
                str(product.color or ''),
                str(product.base or ''),
                str(product.tipo_joya or ''),
                str(product.talla or ''),
            ])
            nombre = product.name
            modelo = product.modelo
            quilataje = product.quilataje
            marca = product.marca
            color = product.color
            base = product.base
            tipo_joya = product.tipo_joya
            talla = product.talla
        else:
            # Use item name if product doesn't exist
            key = f"{item.name}|{item.codigo or ''}|"
            nombre = item.name
            modelo = None
            quilataje = None
            marca = None
            color = None
            base = None
            tipo_joya = None
            talla = None
        
        if key not in groups:
            groups[key] = {
                'nombre': nombre,
                'modelo': modelo,
                'quilataje': quilataje,
                'marca': marca,
                'color': color,
                'base': base,
                'tipo_joya': tipo_joya,
                'talla': talla,
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += item.quantity
        
        # Add sale info to productos list
        folio = sale.folio_apartado if sale and sale.folio_apartado else f'APT-{item.sale_id}'
        cliente = sale.customer_name if sale else 'N/A'
        status = sale.credit_status if sale else 'N/A'
        
        groups[key]['productos'].append({
            'id': item.product_id or 0,
            'codigo': item.codigo,
            'cantidad': item.quantity,
            'precio': float(item.unit_price),
            'folio_apartado': folio,
            'cliente': cliente,
            'status': status,
            'sale_id': item.sale_id,
        })
    
    return list(groups.values())

