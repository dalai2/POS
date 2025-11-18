"""
Service for generating inventory control reports.
This service contains the business logic for inventory tracking and reporting.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime, date, timezone as tz, timedelta, timezone

from app.models.tenant import Tenant
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.venta_contado import VentasContado, ItemVentaContado
from app.models.apartado import Apartado, ItemApartado
from app.models.producto_pedido import Pedido, ProductoPedido, PedidoItem


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
    piezas_vendidas_por_nombre: Dict[str, int]
    piezas_entregadas_por_nombre: Dict[str, int]


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
    # Interpret dates as Mexico local time (UTC-6) for filtering
    mexico_offset = timedelta(hours=-6)  # CST (Central Standard Time)
    mexico_tz = timezone(mexico_offset)
    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=mexico_tz)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=mexico_tz)
    
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
    
    ventas_contado_devueltas = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.return_of_id.isnot(None),
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime
    ).all()
    
    apartados_cancelados_vencidos = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['vencido', 'cancelado']),
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime
    ).all()
    
    # Count pieces from pedidos devueltos
    total_piezas_devueltas = sum(p.cantidad for p in pedidos_devueltos)
    
    # Count pieces from ventas de contado devueltas (nuevo esquema)
    ventas_contado_ids = [venta.id for venta in ventas_contado_devueltas]
    if ventas_contado_ids:
        items_dev = db.query(ItemVentaContado).filter(
            ItemVentaContado.venta_id.in_(ventas_contado_ids)
        ).all()
        total_piezas_devueltas += sum(abs(int(item.quantity or 0)) for item in items_dev)
    
    # Count pieces from apartados cancelados/vencidos
    apartados_ids = [ap.id for ap in apartados_cancelados_vencidos]
    if apartados_ids:
        items_ap = db.query(ItemApartado).filter(
            ItemApartado.apartado_id.in_(apartados_ids)
        ).all()
        total_piezas_devueltas += sum(int(item.quantity or 0) for item in items_ap)
    
    piezas_por_nombre = _build_piezas_por_nombre_resumen(
        db=db,
        tenant=tenant,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
    
    return {
        'piezas_ingresadas': piezas_ingresadas,
        'historial_entradas': movements_data['entradas'],
        'historial_salidas': movements_data['salidas'],
        'pedidos_recibidos': pedidos_recibidos,
        'piezas_devueltas': piezas_devueltas,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'piezas_devueltas_total': total_piezas_devueltas,
        'piezas_vendidas_por_nombre': piezas_por_nombre['vendidas'],
        'piezas_entregadas_por_nombre': piezas_por_nombre['entregadas'],
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
    Get all returned pieces (ventas con devolución, apartados cancelados/vencidos y pedidos cancelados/vencidos).
    Usa el nuevo esquema (VentasContado/Apartado/Pedido).
    """
    result = []
    
    ventas_contado_devueltas = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.return_of_id.isnot(None),
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime
    ).order_by(VentasContado.created_at.desc()).all()
    
    apartados_vencidos_cancelados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['vencido', 'cancelado']),
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime
    ).order_by(Apartado.created_at.desc()).all()
    
    for venta in ventas_contado_devueltas:
        items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id == venta.id).all()
        for item in items:
            pieza_data: PiezaDevueltaData = {
                'id': venta.id,
                'tipo': 'venta',
                'folio': venta.folio_venta or f'VENTA-{venta.id}',
                'cliente_nombre': venta.customer_name,
                'producto_nombre': item.name,
                'cantidad': abs(int(item.quantity or 0)),
                'motivo': 'Devolución de venta',
                'fecha': venta.created_at.isoformat() if venta.created_at else '',
            }
            result.append(pieza_data)
    
    for apartado in apartados_vencidos_cancelados:
        items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
        motivo = 'Apartado vencido' if apartado.credit_status == 'vencido' else 'Apartado cancelado'
        for item in items:
            pieza_data: PiezaDevueltaData = {
                'id': apartado.id,
                'tipo': 'apartado',
                'folio': apartado.folio_apartado or f'AP-{apartado.id}',
                'cliente_nombre': apartado.customer_name,
                'producto_nombre': item.name,
                'cantidad': item.quantity,
                'motivo': motivo,
                'fecha': apartado.created_at.isoformat() if apartado.created_at else '',
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


def _build_piezas_por_nombre_resumen(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
) -> Dict[str, Dict[str, int]]:
    """
    Agrupa piezas vendidas y entregadas por nombre dentro del rango seleccionado.
    Vendidas = ventas de contado (nuevo esquema + legacy).
    Entregadas = apartados/pedidos liquidados (nuevo esquema + legacy).
    """
    vendidas: Dict[str, int] = {}
    entregadas: Dict[str, int] = {}
    
    def _add(target: Dict[str, int], nombre: Optional[str], cantidad: int) -> None:
        if not cantidad:
            return
        key = (nombre or "").strip() or "Sin nombre"
        target[key] = target.get(key, 0) + int(cantidad)
    
    # Ventas de contado (nuevo esquema)
    ventas_contado = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime,
        VentasContado.return_of_id.is_(None),
    ).all()
    venta_ids = [v.id for v in ventas_contado]
    if venta_ids:
        items = db.query(ItemVentaContado).filter(
            ItemVentaContado.venta_id.in_(venta_ids)
        ).all()
        product_ids = [item.product_id for item in items if item.product_id]
        products = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        } if product_ids else {}
        for item in items:
            product = products.get(item.product_id) if item.product_id else None
            nombre = product.name if product else item.name
            _add(vendidas, nombre, int(item.quantity or 0))
    
    # Apartados liquidados (nuevo esquema)
    apartados_liquidados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(["pagado", "entregado"]),
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
    ).all()
    apartado_ids = [a.id for a in apartados_liquidados]
    if apartado_ids:
        items = db.query(ItemApartado).filter(
            ItemApartado.apartado_id.in_(apartado_ids)
        ).all()
        product_ids = [item.product_id for item in items if item.product_id]
        products = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        } if product_ids else {}
        for item in items:
            product = products.get(item.product_id) if item.product_id else None
            nombre = product.name if product else item.name
            _add(entregadas, nombre, int(item.quantity or 0))
    
    # Pedidos liquidados (nuevo esquema)
    pedidos_liquidados = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado.in_(["pagado", "entregado"]),
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
    ).all()
    pedido_ids = [p.id for p in pedidos_liquidados]
    pedido_items_map: Dict[int, List[PedidoItem]] = {}
    if pedido_ids:
        pedido_items = db.query(PedidoItem).filter(
            PedidoItem.pedido_id.in_(pedido_ids)
        ).all()
        for item in pedido_items:
            pedido_items_map.setdefault(item.pedido_id, []).append(item)
    producto_ids = [
        pedido.producto_pedido_id for pedido in pedidos_liquidados
        if pedido.producto_pedido_id is not None
    ]
    productos_map = {
        prod.id: prod
        for prod in db.query(ProductoPedido).filter(ProductoPedido.id.in_(producto_ids)).all()
    } if producto_ids else {}
    for pedido in pedidos_liquidados:
        items = pedido_items_map.get(pedido.id, [])
        if items:
            for item in items:
                nombre = item.nombre or item.modelo or "Sin nombre"
                _add(entregadas, nombre, int(item.cantidad or 0))
        else:
            producto = productos_map.get(pedido.producto_pedido_id) if pedido.producto_pedido_id else None
            nombre = (producto.nombre if producto and producto.nombre else producto.modelo) if producto else "Sin nombre"
            _add(entregadas, nombre, int(pedido.cantidad or 0))
    
    vendidas_ordenadas = dict(sorted(vendidas.items(), key=lambda kv: kv[0]))
    entregadas_ordenadas = dict(sorted(entregadas.items(), key=lambda kv: kv[0]))
    
    return {
        "vendidas": vendidas_ordenadas,
        "entregadas": entregadas_ordenadas,
    }


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
    
    # Note: After running fix_all_timestamps_timezone.sql, dates are already in Mexico time
    # We want to include all movements UP TO the end of target_date
    target_datetime_end = datetime.combine(
        target_date, 
        datetime.max.time()
    ).replace(tzinfo=tz.utc)
    
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
        
        # Get sale items that happened AFTER target_date (usar VentasContado)
        ventas_contado_after = db.query(ItemVentaContado).join(VentasContado).filter(
            VentasContado.tenant_id == tenant.id,
            ItemVentaContado.product_id == product.id,
            VentasContado.created_at > target_datetime_end
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
        
        # Reverse ventas de contado after target date
        for item in ventas_contado_after:
            # Sales reduce stock, so add them back
            historical_stock += item.quantity
        
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
    Get stock from eliminated pieces (movements tipo 'salida' with notes/motivo).
    Only shows pieces that were removed from inventory with a reason (defectuoso, etc.).
    EXCLUDES pedidos entregados and any pedido status.
    """
    # Get all salida movements with notes (eliminaciones con motivo)
    movements = db.query(InventoryMovement).join(Product).filter(
        InventoryMovement.tenant_id == tenant.id,
        InventoryMovement.movement_type == 'salida',
        InventoryMovement.notes.isnot(None),
        InventoryMovement.notes != ''
    ).order_by(InventoryMovement.created_at.desc()).all()
    
    # Group by product attributes
    groups: Dict[str, Dict[str, Any]] = {}
    
    for mov in movements:
        product = db.query(Product).filter(Product.id == mov.product_id).first()
        if not product:
            continue
        
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
        
        groups[key]['cantidad_total'] += mov.quantity
        groups[key]['productos'].append({
            'id': product.id,
            'codigo': product.codigo,
            'stock': mov.quantity,  # Cantidad eliminada
            'precio': float(product.price),
            'costo': float(product.cost_price),
            'motivo': mov.notes,  # Motivo de eliminación
            'fecha_eliminacion': mov.created_at.isoformat() if mov.created_at else None
        })
    
    return list(groups.values())


def get_stock_devuelto(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get stock from returned products (ventas devueltas, apartados vencidos/cancelados, pedidos cancelados/vencidos).
    Includes:
    - VentasContado with return_of_id (ventas devueltas)
    - Apartados vencidos/cancelados
    - Pedidos cancelados/vencidos
    """
    from app.models.venta_contado import VentasContado, ItemVentaContado
    from app.models.apartado import Apartado, ItemApartado
    
    result_items = []
    
    # Get ventas de contado devueltas (return_of_id is not None)
    ventas_devueltas = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.return_of_id.isnot(None)
    ).all()
    
    for venta in ventas_devueltas:
        items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id == venta.id).all()
        for item in items:
            product = None
            if item.product_id:
                product = db.query(Product).filter(Product.id == item.product_id).first()
            
            result_items.append({
                'product_id': item.product_id,
                'product_name': item.name,
                'product_modelo': product.modelo if product else None,
                'product_quilataje': product.quilataje if product else None,
                'quantity': abs(item.quantity),  # Use absolute value
                'folio': venta.folio_venta or f'V-{venta.id}',
                'cliente': venta.customer_name,
                'motivo': 'Devolución de venta',
                'fecha': venta.created_at.isoformat() if venta.created_at else None
            })
    
    # Get apartados vencidos/cancelados
    apartados_vencidos_cancelados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['vencido', 'cancelado'])
    ).all()
    
    for apartado in apartados_vencidos_cancelados:
        items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
        motivo = 'Apartado vencido' if apartado.credit_status == 'vencido' else 'Apartado cancelado'
        for item in items:
            product = None
            if item.product_id:
                product = db.query(Product).filter(Product.id == item.product_id).first()
            
            result_items.append({
                'product_id': item.product_id,
                'product_name': item.name,
                'product_modelo': product.modelo if product else None,
                'product_quilataje': product.quilataje if product else None,
                'quantity': item.quantity,
                'folio': apartado.folio_apartado or f'AP-{apartado.id}',
                'cliente': apartado.customer_name,
                'motivo': motivo,
                'fecha': apartado.created_at.isoformat() if apartado.created_at else None
            })
    
    # Get pedidos cancelados/vencidos
    pedidos_cancelados_vencidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado.in_(['cancelado', 'vencido'])
    ).all()
    
    for pedido in pedidos_cancelados_vencidos:
        for item in pedido.items:
            result_items.append({
                'product_id': None,
                'product_name': item.nombre,
                'product_modelo': item.modelo,
                'product_quilataje': item.quilataje,
                'quantity': item.cantidad,
                'folio': pedido.folio_pedido or f'PED-{pedido.id}',
                'cliente': pedido.cliente_nombre,
                'motivo': 'Cancelado' if pedido.estado == 'cancelado' else 'Vencido',
                'fecha': pedido.updated_at.isoformat() if pedido.updated_at else None
            })
    
    # Group by product attributes
    groups: Dict[str, Dict[str, Any]] = {}
    
    for item in result_items:
        key = "|".join([
            str(item['product_name'] or ''),
            str(item['product_modelo'] or ''),
            str(item['product_quilataje'] or ''),
        ])
        
        if key not in groups:
            groups[key] = {
                'nombre': item['product_name'],
                'modelo': item['product_modelo'],
                'quilataje': item['product_quilataje'],
                'cantidad_total': 0,
                'productos': []
            }
        
        groups[key]['cantidad_total'] += item['quantity']
        groups[key]['productos'].append({
            'id': item['product_id'],
            'codigo': None,
            'stock': item['quantity'],
            'precio': 0,
            'costo': 0,
            'folio': item['folio'],
            'cliente': item['cliente'],
            'motivo': item['motivo'],
            'fecha': item['fecha']
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
    # NUEVO: Get apartados with credit_status in ['pendiente', 'pagado']
    apartados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['pendiente', 'pagado'])
    ).all()
    
    # Get all apartado items
    apartado_ids = [a.id for a in apartados]
    if not apartado_ids:
        return []
    
    apartado_items = db.query(ItemApartado).filter(
        ItemApartado.apartado_id.in_(apartado_ids)
    ).all()
    
    # Group by product attributes
    groups: Dict[str, Dict[str, Any]] = {}
    for item in apartado_items:
        # Get product if exists
        product = None
        if item.product_id:
            product = db.query(Product).filter(
                Product.id == item.product_id,
                Product.tenant_id == tenant.id
            ).first()
        
        # Get apartado info
        apartado = next((a for a in apartados if a.id == item.apartado_id), None)
        
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
        
        # Add apartado info to productos list (NUEVO)
        folio = apartado.folio_apartado if apartado and apartado.folio_apartado else f'AP-{item.apartado_id}'
        cliente = apartado.customer_name if apartado else 'N/A'
        status = apartado.credit_status if apartado else 'N/A'
        
        groups[key]['productos'].append({
            'id': item.product_id or 0,
            'codigo': item.codigo,
            'cantidad': item.quantity,
            'precio': float(item.unit_price),
            'folio_apartado': folio,
            'cliente': cliente,
            'status': status,
            'apartado_id': item.apartado_id,
        })
    
    return list(groups.values())


def get_pedidos_recibidos(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get list of pedidos with estado='recibido'.
    Returns list of pedidos with their details.
    """
    pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado == 'recibido'
    ).order_by(Pedido.created_at.desc()).all()
    
    result = []
    for pedido in pedidos:
        # Get items for this pedido
        items = []
        for item in pedido.items:
            items.append({
                'id': item.id,
                'modelo': item.modelo or '',
                'nombre': item.nombre or '',
                'codigo': item.codigo or '',
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario),
                'total': float(item.total)
            })
        
        result.append({
            'id': pedido.id,
            'folio_pedido': pedido.folio_pedido or f'PED-{pedido.id:06d}',
            'cliente_nombre': pedido.cliente_nombre,
            'cliente_telefono': pedido.cliente_telefono,
            'tipo_pedido': pedido.tipo_pedido,
            'cantidad': pedido.cantidad,
            'precio_unitario': float(pedido.precio_unitario),
            'total': float(pedido.total),
            'anticipo_pagado': float(pedido.anticipo_pagado),
            'saldo_pendiente': float(pedido.saldo_pendiente),
            'estado': pedido.estado,
            'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
            'items': items
        })
    
    return result


def get_pedidos_entregados(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get list of pedidos with estado='entregado'.
    Returns list of pedidos with their details.
    """
    pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado == 'entregado'
    ).order_by(Pedido.created_at.desc()).all()
    
    result = []
    for pedido in pedidos:
        # Get items for this pedido
        items = []
        for item in pedido.items:
            items.append({
                'id': item.id,
                'modelo': item.modelo or '',
                'nombre': item.nombre or '',
                'codigo': item.codigo or '',
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario),
                'total': float(item.total)
            })
        
        result.append({
            'id': pedido.id,
            'folio_pedido': pedido.folio_pedido or f'PED-{pedido.id:06d}',
            'cliente_nombre': pedido.cliente_nombre,
            'cliente_telefono': pedido.cliente_telefono,
            'tipo_pedido': pedido.tipo_pedido,
            'cantidad': pedido.cantidad,
            'precio_unitario': float(pedido.precio_unitario),
            'total': float(pedido.total),
            'anticipo_pagado': float(pedido.anticipo_pagado),
            'saldo_pendiente': float(pedido.saldo_pendiente),
            'estado': pedido.estado,
            'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
            'fecha_entrega_real': pedido.fecha_entrega_real.isoformat() if pedido.fecha_entrega_real else None,
            'items': items
        })
    
    return result


def get_productos_pedido_apartado(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get list of products (piezas) from pedidos apartados with estado='pedido'.
    Returns all items from pedidos apartados that are in 'pedido' state (waiting to be ordered from suppliers).
    Shows only: modelo, nombre, quilataje.
    """
    # Get pedidos apartados with estado='pedido'
    pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado == 'pedido'
    ).order_by(Pedido.created_at.desc()).all()
    
    result = []
    for pedido in pedidos:
        # Get items for this pedido
        for item in pedido.items:
            result.append({
                'id': item.id,
                'pedido_id': pedido.id,
                'folio_pedido': pedido.folio_pedido or f'PED-{pedido.id:06d}',
                'cliente_nombre': pedido.cliente_nombre,
                'cliente_telefono': pedido.cliente_telefono,
                'modelo': item.modelo or '',
                'nombre': item.nombre or '',
                'codigo': item.codigo or '',
                'color': item.color or '',
                'quilataje': item.quilataje or '',
                'base': item.base or '',
                'talla': item.talla or '',
                'peso': item.peso or '',
                'peso_gramos': float(item.peso_gramos) if item.peso_gramos else None,
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario),
                'total': float(item.total),
                'estado_pedido': pedido.estado,
                'created_at': pedido.created_at.isoformat() if pedido.created_at else None
            })
    
    return result


def get_pedidos_recibidos_apartados(
    db: Session,
    tenant: Tenant
) -> List[Dict[str, Any]]:
    """
    Get list of pedidos apartados with estado='recibido'.
    Returns only pedidos apartados that have been received.
    """
    pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado == 'recibido'
    ).order_by(Pedido.created_at.desc()).all()
    
    result = []
    for pedido in pedidos:
        # Get items for this pedido
        items = []
        for item in pedido.items:
            items.append({
                'id': item.id,
                'modelo': item.modelo or '',
                'nombre': item.nombre or '',
                'codigo': item.codigo or '',
                'cantidad': item.cantidad,
                'precio_unitario': float(item.precio_unitario),
                'total': float(item.total)
            })
        
        result.append({
            'id': pedido.id,
            'folio_pedido': pedido.folio_pedido or f'PED-{pedido.id:06d}',
            'cliente_nombre': pedido.cliente_nombre,
            'cliente_telefono': pedido.cliente_telefono,
            'tipo_pedido': pedido.tipo_pedido,
            'cantidad': pedido.cantidad,
            'precio_unitario': float(pedido.precio_unitario),
            'total': float(pedido.total),
            'anticipo_pagado': float(pedido.anticipo_pagado),
            'saldo_pendiente': float(pedido.saldo_pendiente),
            'estado': pedido.estado,
            'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
            'items': items
        })
    
    return result

