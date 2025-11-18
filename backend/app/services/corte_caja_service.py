"""
Service for generating detailed cash cut reports (corte de caja).
This service contains the business logic extracted from routes/reports.py
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Dict, List, Any, Tuple, Optional, TypedDict
from datetime import datetime, date, timedelta, timezone
from datetime import timezone as tz

from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.payment import Payment
from app.models.credit_payment import CreditPayment
from app.models.producto_pedido import Pedido, PagoPedido, ProductoPedido, PedidoItem
from app.models.venta_contado import VentasContado, ItemVentaContado
from app.models.apartado import Apartado, ItemApartado

# Constants
TARJETA_DISCOUNT_RATE = 0.97  # 3% discount for card payments
EFECTIVO_METHODS = ['efectivo', 'transferencia']
TARJETA_METHOD = 'tarjeta'


# TypedDict definitions for better type safety
class SalesData(TypedDict):
    """Structure for sales data returned by _get_sales_by_payment_date."""
    ventas_contado: List[VentasContado]
    apartados_pendientes: List[Apartado]


class PedidosData(TypedDict):
    """Structure for pedidos data returned by _get_pedidos_by_payment_date."""
    pedidos_liquidados: List[Pedido]
    pedidos_contado: List[Pedido]
    pedidos_pendientes: List[Pedido]


class VentasActivas(TypedDict):
    """Structure for active sales metrics."""
    neto: float
    utilidad: float


class VentasLiquidacion(TypedDict):
    """Structure for liquidation sales metrics."""
    total: float
    count: int


class VentasPasivas(TypedDict):
    """Structure for passive sales metrics."""
    total: float


class HistorialesData(TypedDict):
    """Structure for historiales data."""
    apartados: List[Dict[str, Any]]
    pedidos: List[Dict[str, Any]]
    abonos_apartados: List[Dict[str, Any]]
    abonos_pedidos: List[Dict[str, Any]]
    apartados_cancelados_vencidos: List[Dict[str, Any]]
    pedidos_cancelados_vencidos: List[Dict[str, Any]]


def get_detailed_corte_caja(
    start_date: date,
    end_date: date,
    db: Session,
    tenant: Tenant,
) -> Dict[str, Any]:
    """
    Generate a detailed corte de caja report with individual sales details,
    vendor breakdown, and daily summaries.
    
    This is the main orchestrator function that calls helper functions
    to build the complete report.
    
    Args:
        start_date: Start date for the report period
        end_date: End date for the report period
        db: Database session
        tenant: Tenant for filtering data
        
    Returns:
        Dictionary containing the complete report data
        
    Raises:
        ValueError: If start_date > end_date
    """
    # Validate input parameters
    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")
    
    # Convert to datetime for queries (timezone-aware)
    # The dates from frontend are in Mexico local time
    # Database timestamps are stored with timezone (after migration)
    # We need to interpret the dates as Mexico time (-6 hours from UTC)
    # Then convert to UTC for database queries
    mexico_offset = timedelta(hours=-6)  # CST (Central Standard Time)
    mexico_tz = timezone(mexico_offset)
    utc_tz = timezone.utc
    
    # Create datetime in Mexico timezone (local time)
    start_datetime_mexico = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=mexico_tz)
    end_datetime_mexico = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=mexico_tz)
    
    # Convert to UTC for database queries (DB stores in UTC)
    start_datetime = start_datetime_mexico.astimezone(utc_tz)
    end_datetime = end_datetime_mexico.astimezone(utc_tz)
    
    # Get base data
    sales_data = _get_sales_by_payment_date(db, tenant, start_datetime, end_datetime)
    pedidos_data = _get_pedidos_by_payment_date(db, tenant, start_datetime, end_datetime)
    
    # Initialize counters
    counters = _initialize_counters()
    
    # Also process ventas/apartados del nuevo esquema (VentasContado/Apartado)
    _process_new_schema_stats(
        db=db,
        tenant=tenant,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        counters=counters,
    )
    
    ventas_contado_period = sales_data['ventas_contado']
    
    # Process pedidos de contado
    _process_pedidos_contado(
        db, pedidos_data['pedidos_contado'], counters
    )
    
    # Process pedidos liquidados
    _process_pedidos_liquidados(
        db, pedidos_data['pedidos_liquidados'], counters
    )
    
    # Process apartados pendientes
    _process_apartados_pendientes(
        db, sales_data['apartados_pendientes'], counters
    )
    
    # Process pedidos pendientes
    _process_pedidos_pendientes(
        db, pedidos_data['pedidos_pendientes'], counters
    )
    
    # Calculate main metrics
    ventas_activas = _calculate_ventas_activas(counters)
    ventas_liquidacion = _calculate_ventas_liquidacion(counters)
    ventas_pasivas = _calculate_ventas_pasivas(
        db, tenant, start_datetime, end_datetime, counters
    )
    cuentas_por_cobrar = _calculate_cuentas_por_cobrar(
        sales_data['apartados_pendientes'],
        pedidos_data['pedidos_pendientes'],
        db,
        tenant,
        start_datetime,
        end_datetime,
    )
    
    # Build vendor stats
    vendor_stats = _build_vendor_stats(
        db, ventas_contado_period, pedidos_data['pedidos_contado'],
        pedidos_data['pedidos_liquidados'], sales_data['apartados_pendientes'],
        pedidos_data['pedidos_pendientes'], start_datetime, end_datetime, tenant
    )
    
    # Build dashboard (ahora incluye historiales internamente)
    dashboard = _build_dashboard_data(
        counters, 
        ventas_liquidacion,
        pedidos_data['pedidos_contado'],
        pedidos_data['pedidos_liquidados'],
        db,  # Parámetros adicionales
        tenant,
        start_datetime,
        end_datetime,
        pedidos_data['pedidos_pendientes']
    )
    
    # Extraer historiales del dashboard para compatibilidad con frontend
    historiales = dashboard.get('historiales', {})
    sales_details = _build_sales_details(
        db, ventas_contado_period, pedidos_data['pedidos_contado'],
        tenant, start_datetime, end_datetime
    )
    
    # Build piezas lists
    piezas_recibidas = _build_piezas_recibidas(db, tenant, start_datetime, end_datetime)
    piezas_solicitadas_cliente = _build_piezas_solicitadas_cliente(db, tenant, start_datetime, end_datetime)
    piezas_pedidas_proveedor = _build_piezas_pedidas_proveedor(db, tenant, start_datetime, end_datetime)
    
    additional_metrics = _calculate_additional_metrics(
        db, tenant, start_datetime, end_datetime
    )
    
    # Build resumen piezas
    resumen_piezas = _build_resumen_piezas(
        db,
        sales_data['apartados_pendientes'],
        pedidos_data['pedidos_pendientes'],
        pedidos_data['pedidos_liquidados'],
        tenant,
        start_datetime,
        end_datetime
    )
    piezas_por_nombre = _build_piezas_por_nombre(resumen_piezas)
    
    # Build daily summaries
    # Obtener ventas de contado para resumen diario
    daily_summaries = _build_daily_summaries(
        ventas_contado_period,
        pedidos_data['pedidos_contado'],
        db
    )
    
    # Build resumen ventas activas and pagos
    resumen_ventas_activas = _build_resumen_ventas_activas(
        db, tenant, start_datetime, end_datetime, pedidos_data['pedidos_contado']
    )
    resumen_pagos = _build_resumen_pagos(
        db, tenant, start_datetime, end_datetime,
        sales_data['apartados_pendientes'], pedidos_data['pedidos_pendientes']
    )
    
    # Assemble final report
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": datetime.now(mexico_tz).strftime("%Y-%m-%d %H:%M:%S"),
        "ventas_validas": counters['contado_count'],
        "contado_count": counters['contado_count'],
        "credito_count": counters['credito_count'],
        "total_contado": counters['total_contado'],
        "total_credito": counters['total_credito'],
        "liquidacion_count": ventas_liquidacion['count'],
        "liquidacion_total": ventas_liquidacion['total'],
        "ventas_pasivas_total": ventas_pasivas['total'],
        "apartados_pendientes_anticipos": counters['apartados_pendientes_anticipos'],
        "apartados_pendientes_abonos_adicionales": counters['apartados_pendientes_abonos_adicionales'],
        "pedidos_pendientes_anticipos": counters['pedidos_pendientes_anticipos'],
        "pedidos_pendientes_abonos": counters['pedidos_pendientes_abonos'],
        "cuentas_por_cobrar": cuentas_por_cobrar,
        "total_vendido": counters['total_vendido'],
        "costo_total": counters['costo_total'],
        "costo_ventas_contado": counters['costo_ventas_contado'],
        "costo_apartados_pedidos_liquidados": counters['costo_apartados_liquidados'] + counters['costo_pedidos_liquidados'],
        "utilidad_productos_liquidados": ventas_liquidacion['total'] - (counters['costo_apartados_liquidados'] + counters['costo_pedidos_liquidados']),
        "total_efectivo_contado": counters['total_efectivo_contado'],
        "total_tarjeta_contado": counters['total_tarjeta_contado'],
        "total_ventas_activas_neto": ventas_activas['neto'],
        "utilidad_ventas_activas": ventas_activas['utilidad'],
        "utilidad_total": counters['utilidad_total'],
        "piezas_vendidas": counters['piezas_vendidas'],
        "pendiente_credito": counters['pendiente_credito'],
        "pedidos_count": counters['pedidos_count'],
        "pedidos_total": counters['pedidos_total'],
        "pedidos_anticipos": counters['pedidos_anticipos'],
        "pedidos_saldo": counters['pedidos_saldo'],
        "pedidos_liquidados_count": counters['pedidos_liquidados_count'],
        "pedidos_liquidados_total": counters['pedidos_liquidados_total'],
        "num_piezas_vendidas": counters['num_piezas_vendidas'],
        "num_piezas_entregadas": counters['num_piezas_entregadas'],
        "num_piezas_apartadas_pagadas": counters['num_piezas_apartadas_pagadas'],
        "num_piezas_pedidos_pagados": counters['num_piezas_pedidos_pagados'],
        "num_piezas_pedidos_apartados_liquidados": counters['num_piezas_pedidos_apartados_liquidados'],
        "num_solicitudes_apartado": additional_metrics['num_solicitudes_apartado'],
        "num_pedidos_hechos": additional_metrics['num_pedidos_hechos'],
        "num_cancelaciones": additional_metrics['num_cancelaciones'],
        "num_apartados_vencidos": additional_metrics['num_apartados_vencidos'],
        "num_pedidos_vencidos": additional_metrics['num_pedidos_vencidos'],
        "num_abonos_apartados": additional_metrics['num_abonos_apartados'],
        "num_abonos_pedidos": additional_metrics['num_abonos_pedidos'],
        "subtotal_venta_tarjeta": counters['total_tarjeta_contado'],
        "total_tarjeta_neto": counters['total_tarjeta_contado'] * TARJETA_DISCOUNT_RATE,
        "reembolso_apartados_cancelados": counters['reembolso_apartados_cancelados'],
        "reembolso_pedidos_cancelados": counters['reembolso_pedidos_cancelados'],
        "saldo_vencido_apartados": counters['saldo_vencido_apartados'],
        "saldo_vencido_pedidos": counters['saldo_vencido_pedidos'],
        "resumen_piezas": resumen_piezas,
        "piezas_vendidas_por_nombre": piezas_por_nombre["vendidas"],
        "piezas_entregadas_por_nombre": piezas_por_nombre["entregadas"],
        "dashboard": dashboard,
        "vendedores": list(vendor_stats.values()),
        "daily_summaries": daily_summaries,
        "sales_details": sales_details,
        "piezas_recibidas": piezas_recibidas,
        "piezas_solicitadas_cliente": piezas_solicitadas_cliente,
        "piezas_pedidas_proveedor": piezas_pedidas_proveedor,
        "historial_apartados": historiales.get('apartados', []),
        "historial_pedidos": historiales.get('pedidos', []),
        "historial_abonos_apartados": historiales.get('abonos_apartados', []),
        "historial_abonos_pedidos": historiales.get('abonos_pedidos', []),
        "apartados_cancelados_vencidos": historiales.get('apartados_cancelados_vencidos', []),
        "pedidos_cancelados_vencidos": historiales.get('pedidos_cancelados_vencidos', []),
        "resumen_ventas_activas": resumen_ventas_activas,
        "resumen_pagos": resumen_pagos,
    }


def _get_sales_by_payment_date(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> SalesData:
    """Get sales filtered by payment date within the period."""
    ventas_contado = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime
    ).all()
    
    apartados_pendientes = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['pendiente', 'vencido']),
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime
    ).all()
    
    return {
        'ventas_contado': ventas_contado,
        'apartados_pendientes': apartados_pendientes,
    }


def _get_pedidos_by_payment_date(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> PedidosData:
    """Get pedidos filtered by payment date within the period."""
    # Get pedidos liquidados: usar fecha del último pago tipo saldo/total (momento en que se liquidan)
    pagos_saldo_subq = (
        db.query(
            PagoPedido.pedido_id.label("pedido_id"),
            func.max(PagoPedido.created_at).label("last_payment_at")
        )
        .filter(PagoPedido.tipo_pago.in_(['saldo', 'total']))
        .group_by(PagoPedido.pedido_id)
        .subquery()
    )
    
    pedidos_liquidados = (
        db.query(Pedido)
        .join(pagos_saldo_subq, pagos_saldo_subq.c.pedido_id == Pedido.id)
        .filter(
            Pedido.tenant_id == tenant.id,
            Pedido.tipo_pedido == 'apartado',
            Pedido.estado == 'pagado',
            pagos_saldo_subq.c.last_payment_at >= start_datetime,
            pagos_saldo_subq.c.last_payment_at <= end_datetime
        )
        .all()
    )
    
    # Get pedidos de contado: filtrar por fecha de CREACIÓN del pedido
    pedidos_contado = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'contado',
        Pedido.estado == 'pagado',
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).all()
    
    # Get pedidos pendientes filtrados por fecha de CREACIÓN en el periodo
    # Solo incluir pedidos creados en el periodo seleccionado
    pedidos_pendientes = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        ~Pedido.estado.in_(['pagado', 'entregado', 'cancelado']),
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).all()
    
    return {
        'pedidos_liquidados': pedidos_liquidados,
        'pedidos_contado': pedidos_contado,
        'pedidos_pendientes': pedidos_pendientes,
    }


def _initialize_counters() -> Dict[str, Any]:
    """Initialize all counter variables."""
    return {
        'contado_count': 0,
        'credito_count': 0,
        'ventas_credito_count': 0,
        'ventas_credito_total': 0.0,
        'credito_ventas': 0.0,
        'total_contado': 0.0,
        'total_credito': 0.0,
        'total_vendido': 0.0,
        'costo_total': 0.0,
        'costo_ventas_contado': 0.0,
        'costo_apartados_liquidados': 0.0,
        'costo_pedidos_liquidados': 0.0,
        'total_efectivo_contado': 0.0,
        'total_tarjeta_contado': 0.0,
        'utilidad_total': 0.0,
        'piezas_vendidas': 0,
        'pendiente_credito': 0.0,
        'pedidos_liquidados_count': 0,
        'pedidos_liquidados_total': 0.0,
        'apartados_pendientes_anticipos': 0.0,
        'apartados_pendientes_abonos_adicionales': 0.0,
        'pedidos_pendientes_anticipos': 0.0,
        'pedidos_pendientes_abonos': 0.0,
        'anticipos_apartados_total_monto': 0.0,
        'anticipos_apartados_count': 0,
        'anticipos_apartados_efectivo_monto': 0.0,
        'anticipos_apartados_efectivo_count': 0,
        'anticipos_apartados_tarjeta_bruto': 0.0,
        'anticipos_apartados_tarjeta_neto': 0.0,
        'anticipos_apartados_tarjeta_count': 0,
        'anticipos_pedidos_total_monto': 0.0,
        'anticipos_pedidos_count': 0,
        'anticipos_pedidos_efectivo_monto': 0.0,
        'anticipos_pedidos_efectivo_count': 0,
        'anticipos_pedidos_tarjeta_bruto': 0.0,
        'anticipos_pedidos_tarjeta_neto': 0.0,
        'anticipos_pedidos_tarjeta_count': 0,
        'abonos_apartados_total_neto': 0.0,
        'abonos_apartados_count': 0,
        'abonos_apartados_efectivo_monto': 0.0,
        'abonos_apartados_efectivo_count': 0,
        'abonos_apartados_tarjeta_bruto': 0.0,
        'abonos_apartados_tarjeta_neto': 0.0,
        'abonos_apartados_tarjeta_count': 0,
        'abonos_pedidos_total_neto': 0.0,
        'abonos_pedidos_count': 0,
        'abonos_pedidos_efectivo_monto': 0.0,
        'abonos_pedidos_efectivo_count': 0,
        'abonos_pedidos_tarjeta_bruto': 0.0,
        'abonos_pedidos_tarjeta_neto': 0.0,
        'abonos_pedidos_tarjeta_count': 0,
        'cancelaciones_pedidos_contado_monto': 0.0,
        'cancelaciones_pedidos_contado_count': 0,
        'cancelaciones_pedidos_apartados_monto': 0.0,
        'cancelaciones_pedidos_apartados_count': 0,
        'cancelaciones_apartados_monto': 0.0,
        'cancelaciones_apartados_count': 0,
        'cancelaciones_ventas_contado_monto': 0.0,
        'cancelaciones_ventas_contado_count': 0,
        'piezas_vencidas_apartados': 0,
        'piezas_vencidas_pedidos_apartados': 0,
        'piezas_canceladas_ventas': 0,
        'piezas_canceladas_pedidos_contado': 0,
        'piezas_canceladas_pedidos_apartados': 0,
        'piezas_canceladas_apartados': 0,
        'pedidos_count': 0,
        'pedidos_total': 0.0,
        'pedidos_anticipos': 0.0,
        'pedidos_saldo': 0.0,
        'num_piezas_vendidas': 0,
        'num_piezas_entregadas': 0,
        'num_piezas_apartadas_pagadas': 0,
        'num_piezas_pedidos_pagados': 0,
        'num_piezas_pedidos_apartados_liquidados': 0,
        'reembolso_apartados_cancelados': 0.0,
        'reembolso_pedidos_cancelados': 0.0,
        'saldo_vencido_apartados': 0.0,
        'saldo_vencido_pedidos': 0.0,
        'apartados_vencidos_count': 0,
        'pedidos_vencidos_count': 0,
    }


def _process_new_schema_stats(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
    counters: Dict[str, Any],
) -> None:
    """
    Complement counters with data from new schema tables:
    - VentasContado / ItemVentaContado
    - Apartado (estado pagado/entregado/pendiente/vencido/cancelado)
    """
    # --- Ventas de contado nuevas ---
    ventas_contado = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime,
    ).all()

    if ventas_contado:
        venta_ids = [v.id for v in ventas_contado]
        items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id.in_(venta_ids)).all()
        items_by_venta: Dict[int, list[ItemVentaContado]] = {}
        for it in items:
            items_by_venta.setdefault(it.venta_id, []).append(it)

        product_ids = list({it.product_id for it in items if it.product_id})
        products = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        } if product_ids else {}

        # Load all payments for ventas de contado
        venta_ids = [v.id for v in ventas_contado]
        payments = db.query(Payment).filter(
            Payment.venta_contado_id.in_(venta_ids)
        ).all()
        payments_by_venta: Dict[int, list[Payment]] = {}
        for p in payments:
            if p.venta_contado_id:
                payments_by_venta.setdefault(p.venta_contado_id, []).append(p)

        for venta in ventas_contado:
            total = float(venta.total or 0)
            
            # Si es una devolución (return_of_id no es None), contar como cancelación
            if venta.return_of_id is not None:
                # Las devoluciones tienen total negativo, usar valor absoluto
                counters['cancelaciones_ventas_contado_monto'] += abs(total)
                counters['cancelaciones_ventas_contado_count'] += 1
                # Las devoluciones NO se suman a contado_count ni total_contado
                # pero sí se restan del total_vendido (ya que total es negativo)
                counters['total_vendido'] += total  # total es negativo, así que se resta
                continue
            
            # Procesar como venta normal
            counters['contado_count'] += 1
            counters['total_contado'] += total
            counters['total_vendido'] += total

            # Costos y piezas
            venta_items = items_by_venta.get(venta.id, [])
            costo_venta = 0.0
            for it in venta_items:
                qty = int(it.quantity or 0)
                counters['num_piezas_vendidas'] += qty
                if it.product_id and it.product_id in products:
                    prod = products[it.product_id]
                    if getattr(prod, 'cost_price', None) is not None:
                        costo_venta += float(prod.cost_price) * qty
            counters['costo_ventas_contado'] += costo_venta
            counters['costo_total'] += costo_venta
            # Utilidad: total - costo
            counters['utilidad_total'] += total - costo_venta
            
            # Calcular pagos en efectivo y tarjeta
            venta_payments = payments_by_venta.get(venta.id, [])
            efectivo_venta = sum(float(p.amount) for p in venta_payments if p.method in ['efectivo', 'cash', 'transferencia'])
            tarjeta_venta = sum(float(p.amount) for p in venta_payments if p.method in ['tarjeta', 'card'])
            counters['total_efectivo_contado'] += efectivo_venta
            counters['total_tarjeta_contado'] += tarjeta_venta

    # --- Apartados nuevos ---
    apartados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
    ).all()

    for ap in apartados:
        total = float(ap.total or 0)
        amount_paid = float(ap.amount_paid or 0)
        saldo_pendiente = max(0.0, total - amount_paid)

        if ap.credit_status in ['pagado', 'entregado']:
            # Tratarlos como apartados liquidados (similar a ventas_credito)
            # Para resumen general: usar el TOTAL del apartado (el saldo total que se liquidó)
            # No usar el total pagado, sino el total del apartado
            
            counters['ventas_credito_count'] += 1
            counters['ventas_credito_total'] += total
            counters['credito_ventas'] += total
            # CAMBIO: Usar el total del apartado (ap.total), no el total pagado
            counters['total_credito'] += total  # total = ap.total (el saldo total que se liquidó)
            # CORRECCIÓN: Incrementar credito_count para que se cuente en liquidaciones
            counters['credito_count'] += 1
        elif ap.credit_status in ['pendiente', 'vencido']:
            # Pendiente de cobro
            counters['pendiente_credito'] += saldo_pendiente

        # Vencidos / cancelados para vencimientos/cancelaciones
        if ap.credit_status == 'vencido':
            # El saldo vencido es el monto total pagado (anticipo + abonos) porque el cliente puede pedirlo de regreso
            # Calcular todos los abonos (anticipo inicial + abonos adicionales)
            abonos_apartado = db.query(CreditPayment).filter(CreditPayment.apartado_id == ap.id).all()
            abonos_efectivo = sum(
                float(p.amount) for p in abonos_apartado
                if p.payment_method in ['efectivo', 'cash', 'transferencia']
            )
            abonos_tarjeta = sum(
                float(p.amount) for p in abonos_apartado
                if p.payment_method in ['tarjeta', 'card']
            )
            total_pagado_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            counters['saldo_vencido_apartados'] += total_pagado_neto
            counters['apartados_vencidos_count'] += 1
        elif ap.credit_status == 'cancelado':
            # Reembolsos y cancelaciones de apartados
            # Calcular todos los abonos (anticipo inicial + abonos adicionales)
            abonos_apartado = db.query(CreditPayment).filter(CreditPayment.apartado_id == ap.id).all()
            abonos_efectivo = sum(
                float(p.amount) for p in abonos_apartado
                if p.payment_method in ['efectivo', 'cash', 'transferencia']
            )
            abonos_tarjeta = sum(
                float(p.amount) for p in abonos_apartado
                if p.payment_method in ['tarjeta', 'card']
            )
            total_pagado_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            counters['reembolso_apartados_cancelados'] += total_pagado_neto
            counters['cancelaciones_apartados_monto'] += total_pagado_neto
            counters['cancelaciones_apartados_count'] += 1


def _process_pedidos_contado(
    db: Session,
    pedidos_contado: List[Pedido],
    counters: Dict[str, Any],
) -> None:
    """Process cash orders (pedidos de contado) for active sales."""
    # Initialize pedidos contado counters if not exist
    if 'pedidos_contado_efectivo' not in counters:
        counters['pedidos_contado_efectivo'] = 0.0
    if 'pedidos_contado_tarjeta_neto' not in counters:
        counters['pedidos_contado_tarjeta_neto'] = 0.0
    if 'costo_pedidos_contado' not in counters:
        counters['costo_pedidos_contado'] = 0.0
    
    for pedido in pedidos_contado:
        pagos_pedido_contado = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id
        ).all()
        
        efectivo_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago in ['efectivo', 'transferencia'])
        tarjeta_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago == 'tarjeta')
        tarjeta_pedido_neto = tarjeta_pedido * TARJETA_DISCOUNT_RATE
        
        # Acumular para ventas activas
        counters['pedidos_contado_efectivo'] += efectivo_pedido
        counters['pedidos_contado_tarjeta_neto'] += tarjeta_pedido_neto
        
        counters['total_efectivo_contado'] += efectivo_pedido
        counters['total_tarjeta_contado'] += tarjeta_pedido
        
        # Get product to calculate cost
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        
        if producto and producto.cost_price:
            costo_pedido = float(producto.cost_price) * pedido.cantidad
            counters['costo_ventas_contado'] += costo_pedido
            counters['costo_pedidos_contado'] += costo_pedido
        
        counters['num_piezas_vendidas'] += pedido.cantidad
        counters['total_contado'] += float(pedido.total)
        counters['contado_count'] += 1


def _process_pedidos_liquidados(
    db: Session,
    pedidos_liquidados: List[Pedido],
    counters: Dict[str, Any],
) -> None:
    """Process liquidated orders (pedidos liquidados) for liquidation sales."""
    counters['pedidos_liquidados_count'] = len(pedidos_liquidados)
    
    for pedido in pedidos_liquidados:
        # Para resumen general: usar el TOTAL del pedido (no el total pagado)
        # El total del pedido es el monto que se liquidó completamente
        
        # CAMBIO: Usar el total del pedido, no el total pagado neto
        counters['pedidos_liquidados_total'] += float(pedido.total)
        counters['pedidos_total'] += float(pedido.total)
        counters['pedidos_anticipos'] += float(pedido.anticipo_pagado)
        counters['pedidos_saldo'] += float(pedido.saldo_pendiente)
        
        # Get product and calculate cost
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        if producto and producto.cost_price:
            counters['costo_pedidos_liquidados'] += float(producto.cost_price) * pedido.cantidad
        
        counters['num_piezas_pedidos_pagados'] += pedido.cantidad
        counters['num_piezas_pedidos_apartados_liquidados'] += pedido.cantidad
        # Solo contar piezas entregadas si el estado es "entregado"
        if pedido.estado == 'entregado':
            counters['num_piezas_entregadas'] += pedido.cantidad


def _process_apartados_pendientes(
    db: Session,
    apartados_pendientes: List[Apartado],
    counters: Dict[str, Any],
) -> None:
    """Process pending apartados (apartados pendientes) for passive sales."""
    for apartado in apartados_pendientes:
        # Get initial down payment (anticipo inicial)
        # Buscar en CreditPayment con notes="Anticipo inicial"
        pagos_iniciales = db.query(CreditPayment).filter(
            CreditPayment.apartado_id == apartado.id,
            CreditPayment.notes == "Anticipo inicial"
        ).all()
        
        anticipo_efectivo = sum(float(p.amount) for p in pagos_iniciales if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        anticipo_tarjeta = sum(float(p.amount) for p in pagos_iniciales if p.payment_method in ['tarjeta', 'card'])
        anticipo_inicial = anticipo_efectivo + (anticipo_tarjeta * TARJETA_DISCOUNT_RATE)
        
        # Solo actualizar contadores específicos de apartados pendientes
        # Los contadores generales de anticipos/abonos se calculan en _calculate_ventas_pasivas
        counters['apartados_pendientes_anticipos'] += anticipo_inicial
        
        # Get additional payments (abonos posteriores)
        pagos_posteriores = db.query(CreditPayment).filter(
            CreditPayment.apartado_id == apartado.id,
            CreditPayment.notes != "Anticipo inicial"  # Excluir anticipo inicial
        ).all()
        
        abonos_efectivo = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        abonos_tarjeta = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['tarjeta', 'card'])
        abonos_posteriores = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
        
        counters['apartados_pendientes_abonos_adicionales'] += abonos_posteriores


def _process_pedidos_pendientes(
    db: Session,
    pedidos_pendientes: List[Pedido],
    counters: Dict[str, Any],
) -> None:
    """Process pending orders (pedidos pendientes) for passive sales."""
    for pedido in pedidos_pendientes:
        # Get down payments (anticipos)
        pagos_anticipo = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'anticipo'
        ).all()
        
        anticipo_totals = _calculate_payment_totals(pagos_anticipo)
        anticipo_efectivo = anticipo_totals['efectivo']
        anticipo_tarjeta = anticipo_totals['tarjeta']
        anticipo_neto = anticipo_efectivo + (anticipo_tarjeta * TARJETA_DISCOUNT_RATE)
        
        # Solo actualizar contadores específicos de pedidos pendientes
        # Los contadores generales de anticipos/abonos se calculan en _calculate_ventas_pasivas
        counters['pedidos_pendientes_anticipos'] += anticipo_neto
        counters['pedidos_total'] += float(pedido.total)
        counters['pedidos_anticipos'] += anticipo_neto
        counters['pedidos_saldo'] += float(pedido.saldo_pendiente)
        
        # Get additional payments (abonos)
        pagos_pedido_abonos = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'saldo'
        ).all()
        
        abonos_totals = _calculate_payment_totals(pagos_pedido_abonos)
        abonos_efectivo = abonos_totals['efectivo']
        abonos_tarjeta = abonos_totals['tarjeta']
        abonos_posteriores = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
        
        counters['pedidos_pendientes_abonos'] += abonos_posteriores


def _calculate_ventas_activas(counters: Dict[str, Any]) -> VentasActivas:
    """
    Calculate active sales metrics.
    
    Ventas activas incluyen:
    - Ventas de contado (efectivo y tarjeta)
    - Pedidos de contado (efectivo y tarjeta)
    """
    # Ventas de contado
    total_tarjeta_ventas_neto = counters['total_tarjeta_contado'] * TARJETA_DISCOUNT_RATE
    ventas_contado_neto = counters['total_efectivo_contado'] + total_tarjeta_ventas_neto
    
    # Pedidos de contado (ya vienen con descuento de tarjeta aplicado en counters)
    pedidos_contado_neto = counters.get('pedidos_contado_efectivo', 0) + counters.get('pedidos_contado_tarjeta_neto', 0)
    
    # Total de ventas activas
    total_ventas_activas_neto = ventas_contado_neto + pedidos_contado_neto
    
    # Utilidad = total neto - (costo ventas contado + costo pedidos contado)
    costo_total_activas = counters['costo_ventas_contado'] + counters.get('costo_pedidos_contado', 0)
    utilidad_ventas_activas = total_ventas_activas_neto - costo_total_activas
    
    return {
        'neto': total_ventas_activas_neto,
        'utilidad': utilidad_ventas_activas,
    }


def _calculate_ventas_liquidacion(counters: Dict[str, Any]) -> VentasLiquidacion:
    """Calculate liquidation sales metrics."""
    liquidacion_count = counters['credito_count'] + counters['pedidos_liquidados_count']
    liquidacion_total = counters['total_credito'] + counters['pedidos_liquidados_total']
    
    return {
        'count': liquidacion_count,
        'total': liquidacion_total,
    }


def _calculate_ventas_pasivas(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
    counters: Dict[str, Any]
) -> VentasPasivas:
    """Calculate passive sales metrics (anticipos and abonos).
    
    IMPORTANTE: 
    - Anticipos: se filtran por fecha de CREACIÓN del apartado/pedido (porque se crean al mismo tiempo)
    - Abonos: se filtran por fecha de CREACIÓN del abono (CreditPayment/PagoPedido.created_at)
    """
    # ========== ANTICIPOS DE APARTADOS ==========
    # Filtrar por fecha de creación del apartado (el anticipo se crea al mismo tiempo)
    apartados_ids_query = db.query(Apartado.id).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime
    )
    apartados_ids_list = [id for id, in apartados_ids_query.all()]
    
    # Obtener los anticipos iniciales de esos apartados
    # Los anticipos iniciales están en CreditPayment con notes="Anticipo inicial"
    anticipos_apartados_dia = []
    if apartados_ids_list:
        anticipos_apartados_dia = db.query(CreditPayment).filter(
            CreditPayment.apartado_id.in_(apartados_ids_list),
            CreditPayment.notes == "Anticipo inicial"
    ).all()
    
    anticipos_apartados_dia_total = 0.0
    anticipos_apartados_efectivo = 0.0
    anticipos_apartados_tarjeta_bruto = 0.0
    anticipos_apartados_tarjeta_neto = 0.0
    anticipos_apartados_count = 0
    anticipos_apartados_efectivo_count = 0
    anticipos_apartados_tarjeta_count = 0
    
    # Agrupar pagos por apartado (apartado_id) para contar correctamente los apartados únicos
    apartados_unicos = set()
    
    for pago in anticipos_apartados_dia:
        amount = float(pago.amount or 0)
        if pago.payment_method in ['tarjeta', 'card']:
            anticipos_apartados_tarjeta_bruto += amount
            anticipos_apartados_tarjeta_neto += amount * TARJETA_DISCOUNT_RATE
            anticipos_apartados_dia_total += amount * TARJETA_DISCOUNT_RATE
            anticipos_apartados_tarjeta_count += 1
        else:
            anticipos_apartados_efectivo += amount
            anticipos_apartados_dia_total += amount
            anticipos_apartados_efectivo_count += 1
        
        # Contar apartados únicos (no pagos)
        if pago.apartado_id:
            apartados_unicos.add(pago.apartado_id)
    
    # Asignar la cantidad de apartados únicos
    anticipos_apartados_count = len(apartados_unicos)
    
    # Actualizar contadores
    counters['anticipos_apartados_total_monto'] = anticipos_apartados_dia_total
    counters['anticipos_apartados_count'] = anticipos_apartados_count
    counters['anticipos_apartados_efectivo_monto'] = anticipos_apartados_efectivo
    counters['anticipos_apartados_efectivo_count'] = anticipos_apartados_efectivo_count
    counters['anticipos_apartados_tarjeta_bruto'] = anticipos_apartados_tarjeta_bruto
    counters['anticipos_apartados_tarjeta_neto'] = anticipos_apartados_tarjeta_neto
    counters['anticipos_apartados_tarjeta_count'] = anticipos_apartados_tarjeta_count
    
    # ========== ABONOS DE APARTADOS ==========
    # Filtrar por fecha de CREACIÓN del abono (CreditPayment.created_at)
    # Solo considerar abonos del nuevo esquema (apartado_id IS NOT NULL)
    abonos_apartados_dia = db.query(CreditPayment).filter(
        CreditPayment.tenant_id == tenant.id,
        CreditPayment.apartado_id.isnot(None),  # Solo abonos del nuevo esquema
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime,
        CreditPayment.notes != "Anticipo inicial"  # Excluir anticipos iniciales
    ).all()
    
    abonos_apartados_dia_total = 0.0
    abonos_apartados_efectivo = 0.0
    abonos_apartados_tarjeta_bruto = 0.0
    abonos_apartados_tarjeta_neto = 0.0
    abonos_apartados_count = 0
    abonos_apartados_efectivo_count = 0
    abonos_apartados_tarjeta_count = 0
    
    for abono in abonos_apartados_dia:
        # Verificar si este abono liquidó el apartado (es el último abono)
        if abono.apartado_id:
            apartado = db.query(Apartado).filter(
                Apartado.id == abono.apartado_id,
                Apartado.tenant_id == tenant.id
            ).first()
        
            if apartado and apartado.credit_status in ['pagado', 'entregado']:
                # Obtener todos los abonos del apartado para identificar el último
                todos_abonos = db.query(CreditPayment).filter(
                    CreditPayment.apartado_id == abono.apartado_id
                ).order_by(CreditPayment.created_at.desc()).all()
                
                # Si este es el último abono que liquidó, excluirlo (ya se cuenta en liquidación)
                if todos_abonos and abono.id == todos_abonos[0].id:
                    continue  # Este abono ya fue contado en ventas de liquidación
        
        # Contar el abono
        amount = float(abono.amount or 0)
        if abono.payment_method in ['tarjeta', 'card']:
            abonos_apartados_tarjeta_bruto += amount
            abonos_apartados_tarjeta_neto += amount * TARJETA_DISCOUNT_RATE
            abonos_apartados_dia_total += amount * TARJETA_DISCOUNT_RATE
            abonos_apartados_tarjeta_count += 1
        else:
            abonos_apartados_efectivo += amount
            abonos_apartados_dia_total += amount
            abonos_apartados_efectivo_count += 1
        abonos_apartados_count += 1
    
    # Actualizar contadores
    counters['abonos_apartados_total_neto'] = abonos_apartados_dia_total
    counters['abonos_apartados_count'] = abonos_apartados_count
    counters['abonos_apartados_efectivo_monto'] = abonos_apartados_efectivo
    counters['abonos_apartados_efectivo_count'] = abonos_apartados_efectivo_count
    counters['abonos_apartados_tarjeta_bruto'] = abonos_apartados_tarjeta_bruto
    counters['abonos_apartados_tarjeta_neto'] = abonos_apartados_tarjeta_neto
    counters['abonos_apartados_tarjeta_count'] = abonos_apartados_tarjeta_count
    
    # Anticipos de pedidos apartados: filtrar por fecha de creación del pago (anticipo)
    # Los anticipos se filtran por su fecha de creación (PagoPedido.created_at)
    anticipos_pedidos_dia = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        PagoPedido.tipo_pago == 'anticipo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).all()
    
    anticipos_pedidos_dia_total = 0.0
    anticipos_pedidos_efectivo = 0.0
    anticipos_pedidos_tarjeta_bruto = 0.0
    anticipos_pedidos_tarjeta_neto = 0.0
    anticipos_pedidos_count = 0
    anticipos_pedidos_efectivo_count = 0
    anticipos_pedidos_tarjeta_count = 0
    
    # Agrupar pagos por pedido (pedido_id) para contar correctamente los pedidos únicos
    pedidos_unicos = set()
    
    for pago in anticipos_pedidos_dia:
        amount = float(pago.monto or 0)
        if pago.metodo_pago == TARJETA_METHOD:
            anticipos_pedidos_tarjeta_bruto += amount
            anticipos_pedidos_tarjeta_neto += amount * TARJETA_DISCOUNT_RATE
            anticipos_pedidos_dia_total += amount * TARJETA_DISCOUNT_RATE
            anticipos_pedidos_tarjeta_count += 1
        else:
            anticipos_pedidos_efectivo += amount
            anticipos_pedidos_dia_total += amount
            anticipos_pedidos_efectivo_count += 1
        
        # Contar pedidos únicos (no pagos)
        pedidos_unicos.add(pago.pedido_id)
    
    # Asignar la cantidad de pedidos únicos
    anticipos_pedidos_count = len(pedidos_unicos)
    
    # Actualizar contadores
    counters['anticipos_pedidos_total_monto'] = anticipos_pedidos_dia_total
    counters['anticipos_pedidos_count'] = anticipos_pedidos_count
    counters['anticipos_pedidos_efectivo_monto'] = anticipos_pedidos_efectivo
    counters['anticipos_pedidos_efectivo_count'] = anticipos_pedidos_efectivo_count
    counters['anticipos_pedidos_tarjeta_bruto'] = anticipos_pedidos_tarjeta_bruto
    counters['anticipos_pedidos_tarjeta_neto'] = anticipos_pedidos_tarjeta_neto
    counters['anticipos_pedidos_tarjeta_count'] = anticipos_pedidos_tarjeta_count
    
    # Abonos de pedidos apartados: filtrar por fecha de creación del abono (PagoPedido.created_at)
    # Primero obtenemos los IDs de pedidos apartados para verificar
    pedidos_apartados_ids_query = db.query(Pedido.id).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado'
    )
    pedidos_apartados_ids_list = [id for id, in pedidos_apartados_ids_query.all()]
    
    # Luego obtenemos los abonos (tipo_pago == 'saldo') creados en el periodo
    if pedidos_apartados_ids_list:
        abonos_pedidos_dia = db.query(PagoPedido).filter(
            PagoPedido.pedido_id.in_(pedidos_apartados_ids_list),
        PagoPedido.tipo_pago == 'saldo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).all()
    else:
        abonos_pedidos_dia = []
    
    abonos_pedidos_dia_total = 0.0
    abonos_pedidos_efectivo = 0.0
    abonos_pedidos_tarjeta_bruto = 0.0
    abonos_pedidos_tarjeta_neto = 0.0
    abonos_pedidos_count = 0
    abonos_pedidos_efectivo_count = 0
    abonos_pedidos_tarjeta_count = 0
    
    for abono in abonos_pedidos_dia:
        # Verificar si este abono liquidó el pedido (es el último abono que cambió el estado a pagado)
        pedido = db.query(Pedido).filter(Pedido.id == abono.pedido_id).first()
        
        # Obtener todos los abonos del pedido para identificar el último que liquidó
        todos_abonos = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == abono.pedido_id,
            PagoPedido.tipo_pago == 'saldo'
        ).order_by(PagoPedido.created_at.desc()).all()
        
        # Identificar el último abono que cambió el estado a pagado
        ultimo_abono_liquidante = None
        if pedido and pedido.estado in ['pagado', 'entregado']:
            # Si el pedido está pagado, el último abono es el que lo liquidó
            if todos_abonos:
                ultimo_abono_liquidante = todos_abonos[0]
        
        # Excluir el último abono que liquidó el pedido
        if ultimo_abono_liquidante and abono.id == ultimo_abono_liquidante.id:
            continue  # Este abono ya fue contado en ventas de liquidación
        
        amount = float(abono.monto or 0)
        if abono.metodo_pago == TARJETA_METHOD:
            abonos_pedidos_tarjeta_bruto += amount
            abonos_pedidos_tarjeta_neto += amount * TARJETA_DISCOUNT_RATE
            abonos_pedidos_dia_total += amount * TARJETA_DISCOUNT_RATE
            abonos_pedidos_tarjeta_count += 1
        else:
            abonos_pedidos_efectivo += amount
            abonos_pedidos_dia_total += amount
            abonos_pedidos_efectivo_count += 1
        abonos_pedidos_count += 1
    
    # Actualizar contadores
    counters['abonos_pedidos_total_neto'] = abonos_pedidos_dia_total
    counters['abonos_pedidos_count'] = abonos_pedidos_count
    counters['abonos_pedidos_efectivo_monto'] = abonos_pedidos_efectivo
    counters['abonos_pedidos_efectivo_count'] = abonos_pedidos_efectivo_count
    counters['abonos_pedidos_tarjeta_bruto'] = abonos_pedidos_tarjeta_bruto
    counters['abonos_pedidos_tarjeta_neto'] = abonos_pedidos_tarjeta_neto
    counters['abonos_pedidos_tarjeta_count'] = abonos_pedidos_tarjeta_count
    
    ventas_pasivas_total = (
        anticipos_apartados_dia_total +
        abonos_apartados_dia_total +
        anticipos_pedidos_dia_total +
        abonos_pedidos_dia_total
    )
    
    return {'total': ventas_pasivas_total}


def _calculate_cuentas_por_cobrar(
    apartados_pendientes: List[Apartado],  # Cambiado de List[Sale] a List[Apartado]
    pedidos_pendientes: List[Pedido],
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
) -> float:
    """Calculate accounts receivable (cuentas por cobrar)."""
    cuentas_por_cobrar = 0.0
    # Apartados pendientes (nuevo esquema)
    for apartado in apartados_pendientes:
        saldo = float(apartado.total or 0) - float(apartado.amount_paid or 0)
        cuentas_por_cobrar += saldo

    # Apartados nuevos (Apartado) pendientes o vencidos creados en el periodo
    apartados_nuevos_pendientes = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
        Apartado.credit_status.in_(["pendiente", "vencido"]),
    ).all()
    for ap in apartados_nuevos_pendientes:
        saldo = float(ap.total or 0) - float(ap.amount_paid or 0)
        cuentas_por_cobrar += saldo
    for pedido in pedidos_pendientes:
        cuentas_por_cobrar += float(pedido.saldo_pendiente)
    return cuentas_por_cobrar


def _build_vendor_stats(
    db: Session,
    ventas_contado: List[VentasContado],
    pedidos_contado: List[Pedido],
    pedidos_liquidados: List[Pedido],
    apartados_pendientes: List[Apartado],
    pedidos_pendientes: List[Pedido],
    start_datetime: datetime,
    end_datetime: datetime,
    tenant: Tenant
) -> Dict[int, Dict[str, Any]]:
    """Build vendor statistics."""
    vendor_stats = {}
    
    # Process nuevas ventas de contado
    for venta in ventas_contado:
        vendedor_id = venta.vendedor_id or 0
        vendedor = "Mostrador"
        if venta.vendedor_id:
            vendor = db.query(User).filter(User.id == venta.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        if vendedor_id not in vendor_stats:
            vendor_stats[vendedor_id] = _init_vendor_stat(vendedor_id, vendedor)
        
        payments_vendor = db.query(Payment).filter(Payment.venta_contado_id == venta.id).all()
        efectivo_vendor = sum(float(p.amount) for p in payments_vendor if p.method in ['efectivo', 'cash', 'transferencia'])
        tarjeta_vendor = sum(float(p.amount) for p in payments_vendor if p.method in ['tarjeta', 'card'])
        tarjeta_neto = tarjeta_vendor * TARJETA_DISCOUNT_RATE
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        vendor_stats[vendedor_id]["contado_count"] += 1
        vendor_stats[vendedor_id]["total_contado"] += float(venta.total or 0)
        vendor_stats[vendedor_id]["total_efectivo_contado"] += efectivo_vendor
        vendor_stats[vendedor_id]["total_tarjeta_contado"] += tarjeta_vendor
        vendor_stats[vendedor_id]["total_tarjeta_neto"] += tarjeta_neto
        vendor_stats[vendedor_id]["ventas_total_activa"] += efectivo_vendor + tarjeta_neto
        vendor_stats[vendedor_id]["total_profit"] += float(venta.utilidad or 0)
    
    # Process pedidos de contado
    for pedido in pedidos_contado:
        if pedido.user_id:
            if pedido.user_id not in vendor_stats:
                vendor = db.query(User).filter(User.id == pedido.user_id).first()
                vendedor = vendor.email if vendor else "Unknown"
                vendor_stats[pedido.user_id] = _init_vendor_stat(pedido.user_id, vendedor)
            
            pagos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
            pagos_totals = _calculate_payment_totals(pagos)
            efectivo = pagos_totals['efectivo']
            tarjeta = pagos_totals['tarjeta']
            
            vendor_stats[pedido.user_id]["sales_count"] += 1
            vendor_stats[pedido.user_id]["contado_count"] += 1
            vendor_stats[pedido.user_id]["total_contado"] += float(pedido.total)
            vendor_stats[pedido.user_id]["total_efectivo_contado"] += efectivo
            vendor_stats[pedido.user_id]["total_tarjeta_contado"] += tarjeta
            vendor_stats[pedido.user_id]["total_tarjeta_neto"] += tarjeta * TARJETA_DISCOUNT_RATE
            vendor_stats[pedido.user_id]["ventas_total_activa"] += efectivo + (tarjeta * TARJETA_DISCOUNT_RATE)
    
    # Process apartados pendientes
    for apartado in apartados_pendientes:
        vendedor_id = apartado.vendedor_id or apartado.user_id
        if not vendedor_id:
            continue
        
        if vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == vendedor_id).first()
                vendedor = vendor.email if vendor else "Unknown"
            vendor_stats[vendedor_id] = _init_vendor_stat(vendedor_id, vendedor)
            
            # Buscar anticipos iniciales en CreditPayment con notes="Anticipo inicial"
            pagos_iniciales = db.query(CreditPayment).filter(
                CreditPayment.apartado_id == apartado.id,
                CreditPayment.notes == "Anticipo inicial"
            ).all()
            
            anticipo_efectivo = sum(float(p.amount) for p in pagos_iniciales if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            anticipo_tarjeta = sum(float(p.amount) for p in pagos_iniciales if p.payment_method in ['tarjeta', 'card'])
            anticipo_neto = anticipo_efectivo + (anticipo_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[vendedor_id]["anticipos_apartados"] += anticipo_neto
            vendor_stats[vendedor_id]["venta_total_pasiva"] += anticipo_neto
            
            # Abonos de apartados: obtener todos los abonos del apartado (excluyendo anticipo inicial)
            todos_abonos = db.query(CreditPayment).filter(
                CreditPayment.apartado_id == apartado.id,
                CreditPayment.notes != "Anticipo inicial"
            ).all()
            
            # Solo excluir el último abono si el apartado está pagado (fue el abono liquidante)
            if todos_abonos and apartado.credit_status == 'pagado':
                ultimo_abono = max(todos_abonos, key=lambda a: a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=tz.utc))
                # Excluir el último abono que liquidó
                pagos_posteriores = [p for p in todos_abonos if p.id != ultimo_abono.id]
            else:
                # Si no está pagado, incluir todos los abonos
                pagos_posteriores = todos_abonos
            
            # Filtrar abonos por fecha de creación dentro del periodo
            abonos_en_periodo = []
            for p in pagos_posteriores:
                # Asegurar que created_at tenga timezone
                abono_created = p.created_at
                if abono_created.tzinfo is None:
                    abono_created = abono_created.replace(tzinfo=tz.utc)
                if abono_created >= start_datetime and abono_created <= end_datetime:
                    abonos_en_periodo.append(p)
            
            abonos_efectivo = sum(float(p.amount) for p in abonos_en_periodo if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            abonos_tarjeta = sum(float(p.amount) for p in abonos_en_periodo if p.payment_method in ['tarjeta', 'card'])
            abonos_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[vendedor_id]["abonos_apartados"] += abonos_neto
            vendor_stats[vendedor_id]["venta_total_pasiva"] += abonos_neto
            vendor_stats[vendedor_id]["cuentas_por_cobrar"] += float(apartado.total) - float(apartado.amount_paid or 0)
    
    # También incluir apartados que tienen abonos en el periodo pero fueron creados fuera del periodo
    apartados_con_abonos = db.query(Apartado).join(CreditPayment).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['pendiente', 'vencido']),
        CreditPayment.apartado_id == Apartado.id,
        CreditPayment.notes != "Anticipo inicial",  # Excluir anticipos iniciales
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).distinct().all()
    
    apartados_ids_procesados = {a.id for a in apartados_pendientes}
    for apartado in apartados_con_abonos:
        if apartado.id in apartados_ids_procesados:
            continue  # Ya fue procesado arriba
        
        vendedor_id = apartado.vendedor_id or apartado.user_id
        if not vendedor_id:
            continue
        
        if vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == vendedor_id).first()
                vendedor = vendor.email if vendor else "Unknown"
            vendor_stats[vendedor_id] = _init_vendor_stat(vendedor_id, vendedor)
            
            # Solo contar abonos en el periodo (no anticipos)
            todos_abonos = db.query(CreditPayment).filter(
                CreditPayment.apartado_id == apartado.id,
                CreditPayment.notes != "Anticipo inicial"
            ).all()
            
            # Solo excluir el último abono si el apartado está pagado (fue el abono liquidante)
            if todos_abonos and apartado.credit_status == 'pagado':
                ultimo_abono = max(todos_abonos, key=lambda a: a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=tz.utc))
                pagos_posteriores = [p for p in todos_abonos if p.id != ultimo_abono.id]
            else:
                # Si no está pagado, incluir todos los abonos
                pagos_posteriores = todos_abonos
            
            # Filtrar abonos por fecha de creación dentro del periodo
            abonos_en_periodo = []
            for p in pagos_posteriores:
                # Asegurar que created_at tenga timezone
                abono_created = p.created_at
                if abono_created.tzinfo is None:
                    abono_created = abono_created.replace(tzinfo=tz.utc)
                if abono_created >= start_datetime and abono_created <= end_datetime:
                    abonos_en_periodo.append(p)
            
            abonos_efectivo = sum(float(p.amount) for p in abonos_en_periodo if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            abonos_tarjeta = sum(float(p.amount) for p in abonos_en_periodo if p.payment_method in ['tarjeta', 'card'])
            abonos_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            if abonos_neto > 0:  # Solo agregar si hay abonos en el periodo
                vendor_stats[vendedor_id]["abonos_apartados"] += abonos_neto
                vendor_stats[vendedor_id]["venta_total_pasiva"] += abonos_neto
    
    # Process pedidos pendientes
    for pedido in pedidos_pendientes:
        if pedido.user_id:
            if pedido.user_id not in vendor_stats:
                vendor = db.query(User).filter(User.id == pedido.user_id).first()
                vendedor = vendor.email if vendor else "Unknown"
                vendor_stats[pedido.user_id] = _init_vendor_stat(pedido.user_id, vendedor)
            
            pagos_todos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
            
            anticipos_pagos = [p for p in pagos_todos if p.tipo_pago == 'anticipo']
            anticipos_totals = _calculate_payment_totals(anticipos_pagos)
            anticipos_efectivo = anticipos_totals['efectivo']
            anticipos_tarjeta = anticipos_totals['tarjeta']
            anticipo_neto = anticipos_efectivo + (anticipos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[pedido.user_id]["anticipos_pedidos"] += anticipo_neto
            vendor_stats[pedido.user_id]["venta_total_pasiva"] += anticipo_neto
            
            # Abonos de pedidos: obtener todos los abonos del pedido
            todos_abonos = db.query(PagoPedido).filter(
                PagoPedido.pedido_id == pedido.id,
                PagoPedido.tipo_pago == 'saldo'
            ).all()
            
            # Solo excluir el último abono si el pedido está pagado (fue el abono liquidante)
            if todos_abonos and pedido.estado == 'pagado':
                ultimo_abono = max(todos_abonos, key=lambda a: a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=tz.utc))
                # Excluir el último abono que liquidó
                abonos_pagos = [p for p in todos_abonos if p.id != ultimo_abono.id]
            else:
                # Si no está pagado, incluir todos los abonos
                abonos_pagos = todos_abonos
            
            # Filtrar abonos por fecha de creación dentro del periodo
            abonos_en_periodo = []
            for p in abonos_pagos:
                # Asegurar que created_at tenga timezone
                abono_created = p.created_at
                if abono_created.tzinfo is None:
                    abono_created = abono_created.replace(tzinfo=tz.utc)
                if abono_created >= start_datetime and abono_created <= end_datetime:
                    abonos_en_periodo.append(p)
            
            abonos_totals = _calculate_payment_totals(abonos_en_periodo)
            abonos_efectivo = abonos_totals['efectivo']
            abonos_tarjeta = abonos_totals['tarjeta']
            abonos_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[pedido.user_id]["abonos_pedidos"] += abonos_neto
            vendor_stats[pedido.user_id]["venta_total_pasiva"] += abonos_neto
            vendor_stats[pedido.user_id]["cuentas_por_cobrar"] += float(pedido.saldo_pendiente)
    
    # También incluir pedidos que tienen abonos en el periodo pero fueron creados fuera del periodo
    pedidos_con_abonos = db.query(Pedido).join(PagoPedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        ~Pedido.estado.in_(['pagado', 'entregado', 'cancelado']),
        PagoPedido.tipo_pago == 'saldo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).distinct().all()
    
    pedidos_ids_procesados = {p.id for p in pedidos_pendientes}
    for pedido in pedidos_con_abonos:
        if pedido.id in pedidos_ids_procesados:
            continue  # Ya fue procesado arriba
        
        if pedido.user_id:
            if pedido.user_id not in vendor_stats:
                vendor = db.query(User).filter(User.id == pedido.user_id).first()
                vendedor = vendor.email if vendor else "Unknown"
                vendor_stats[pedido.user_id] = _init_vendor_stat(pedido.user_id, vendedor)
            
            # Solo contar abonos en el periodo (no anticipos)
            todos_abonos = db.query(PagoPedido).filter(
                PagoPedido.pedido_id == pedido.id,
                PagoPedido.tipo_pago == 'saldo'
            ).all()
            
            # Solo excluir el último abono si el pedido está pagado (fue el abono liquidante)
            if todos_abonos and pedido.estado == 'pagado':
                ultimo_abono = max(todos_abonos, key=lambda a: a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=tz.utc))
                abonos_pagos = [p for p in todos_abonos if p.id != ultimo_abono.id]
            else:
                # Si no está pagado, incluir todos los abonos
                abonos_pagos = todos_abonos
            
            # Filtrar abonos por fecha de creación dentro del periodo
            abonos_en_periodo = []
            for p in abonos_pagos:
                # Asegurar que created_at tenga timezone
                abono_created = p.created_at
                if abono_created.tzinfo is None:
                    abono_created = abono_created.replace(tzinfo=tz.utc)
                if abono_created >= start_datetime and abono_created <= end_datetime:
                    abonos_en_periodo.append(p)
            
            abonos_totals = _calculate_payment_totals(abonos_en_periodo)
            abonos_efectivo = abonos_totals['efectivo']
            abonos_tarjeta = abonos_totals['tarjeta']
            abonos_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            if abonos_neto > 0:  # Solo agregar si hay abonos en el periodo
                vendor_stats[pedido.user_id]["abonos_pedidos"] += abonos_neto
                vendor_stats[pedido.user_id]["venta_total_pasiva"] += abonos_neto
    
    # Calculate productos liquidados for new Apartado schema
    apartados_pagados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(["pagado", "entregado"])
    ).all()
    
    for apartado in apartados_pagados:
        # FIX: Incluir pagos con notes NULL o diferentes de "Anticipo inicial"
        # En SQL, NULL != "valor" devuelve NULL, por lo que se excluyen los pagos sin notes
        pagos = db.query(CreditPayment).filter(
            CreditPayment.apartado_id == apartado.id,
            or_(
                CreditPayment.notes.is_(None),
            CreditPayment.notes != "Anticipo inicial"
            )
        ).all()
        
        if not pagos:
            continue
        
        ultimo_abono = max(pagos, key=lambda a: _normalize_datetime(a.created_at))
        fecha_ultimo_abono = _normalize_datetime(ultimo_abono.created_at)
        
        if not (start_datetime <= fecha_ultimo_abono <= end_datetime):
            continue
        
        vendedor_id = apartado.vendedor_id or apartado.user_id or getattr(ultimo_abono, "user_id", None) or 0
        if vendedor_id not in vendor_stats:
            vendedor = "Mostrador"
            referencia_usuario = vendedor_id if vendedor_id else None
            if referencia_usuario:
                vendor = db.query(User).filter(User.id == referencia_usuario).first()
                vendedor = vendor.email if vendor else "Unknown"
            vendor_stats[vendedor_id] = _init_vendor_stat(vendedor_id, vendedor)
        
        monto_neto = _calculate_net_payment_amount(
            ultimo_abono.amount,
            getattr(ultimo_abono, "payment_method", None)
        )
        
        # Sumar a productos liquidados de apartados
        vendor_stats[vendedor_id]["productos_liquidados_apartados"] += monto_neto
        
        # Guardar el último abono más reciente (comparar con el que ya existe si hay)
        abono_info = {
            "id": ultimo_abono.id,
            "monto": float(ultimo_abono.amount),
            "monto_neto": monto_neto,
            "metodo_pago": getattr(ultimo_abono, "payment_method", "efectivo"),
            "fecha": ultimo_abono.created_at.isoformat() if ultimo_abono.created_at else None,
            "fecha_datetime": fecha_ultimo_abono,  # Para comparación
            "apartado_id": apartado.id,
            "folio_apartado": apartado.folio_apartado,
            "cliente": apartado.customer_name or "Sin nombre"
        }
        
        # Actualizar solo si es más reciente que el actual
        ultimo_actual = vendor_stats[vendedor_id]["ultimo_abono_apartado"]
        if (ultimo_actual is None or 
            (ultimo_actual.get("fecha_datetime") is not None and 
             fecha_ultimo_abono > ultimo_actual["fecha_datetime"])):
            # Remover fecha_datetime antes de guardar (solo para comparación interna)
            abono_info_clean = {k: v for k, v in abono_info.items() if k != "fecha_datetime"}
            vendor_stats[vendedor_id]["ultimo_abono_apartado"] = abono_info_clean
            # Mantener fecha_datetime para futuras comparaciones
            vendor_stats[vendedor_id]["ultimo_abono_apartado"]["fecha_datetime"] = fecha_ultimo_abono
    
    pedidos_pagados = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado.in_(['pagado', 'entregado'])
    ).all()
    
    for pedido in pedidos_pagados:
        abonos = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago.in_(['saldo', 'total'])
        ).all()
        
        if not abonos:
            continue
        
        ultimo_abono = max(abonos, key=lambda p: _normalize_datetime(p.created_at))
        fecha_ultimo_abono = _normalize_datetime(ultimo_abono.created_at)
        
        if not (start_datetime <= fecha_ultimo_abono <= end_datetime):
            continue
        
        vendedor_id = pedido.user_id or pedido.vendedor_id or 0
        if vendedor_id not in vendor_stats:
            vendedor = "Mostrador"
            referencia_usuario = pedido.user_id or pedido.vendedor_id
            if referencia_usuario:
                user = db.query(User).filter(User.id == referencia_usuario).first()
                vendedor = user.email if user else "Unknown"
            vendor_stats[vendedor_id] = _init_vendor_stat(vendedor_id, vendedor)
        
        monto_neto = _calculate_net_payment_amount(
            getattr(ultimo_abono, 'monto', 0),
            getattr(ultimo_abono, 'metodo_pago', None)
        )
        
        # Sumar a productos liquidados de pedidos
        vendor_stats[vendedor_id]["productos_liquidados_pedidos"] += monto_neto
        
        # Guardar el último abono más reciente (comparar con el que ya existe si hay)
        abono_info = {
            "id": ultimo_abono.id,
            "monto": float(getattr(ultimo_abono, 'monto', 0)),
            "monto_neto": monto_neto,
            "metodo_pago": getattr(ultimo_abono, 'metodo_pago', 'efectivo'),
            "fecha": ultimo_abono.created_at.isoformat() if ultimo_abono.created_at else None,
            "fecha_datetime": fecha_ultimo_abono,  # Para comparación
            "pedido_id": pedido.id,
            "folio_pedido": pedido.folio_pedido,
            "cliente": pedido.cliente_nombre or "Sin nombre"
        }
        
        # Actualizar solo si es más reciente que el actual
        ultimo_actual = vendor_stats[vendedor_id]["ultimo_abono_pedido"]
        if (ultimo_actual is None or 
            (ultimo_actual.get("fecha_datetime") is not None and 
             fecha_ultimo_abono > ultimo_actual["fecha_datetime"])):
            # Remover fecha_datetime antes de guardar (solo para comparación interna)
            abono_info_clean = {k: v for k, v in abono_info.items() if k != "fecha_datetime"}
            vendor_stats[vendedor_id]["ultimo_abono_pedido"] = abono_info_clean
            # Mantener fecha_datetime para futuras comparaciones
            vendor_stats[vendedor_id]["ultimo_abono_pedido"]["fecha_datetime"] = fecha_ultimo_abono
    
    # Calcular productos_liquidados como suma de apartados + pedidos
    # y limpiar campos temporales de fecha_datetime antes de retornar
    for vendedor_id in vendor_stats:
        # Calcular total
        vendor_stats[vendedor_id]["productos_liquidados"] = (
            vendor_stats[vendedor_id]["productos_liquidados_apartados"] + 
            vendor_stats[vendedor_id]["productos_liquidados_pedidos"]
        )
        
        # Limpiar fecha_datetime de los objetos de último abono
        if vendor_stats[vendedor_id].get("ultimo_abono_apartado") and "fecha_datetime" in vendor_stats[vendedor_id]["ultimo_abono_apartado"]:
            del vendor_stats[vendedor_id]["ultimo_abono_apartado"]["fecha_datetime"]
        if vendor_stats[vendedor_id].get("ultimo_abono_pedido") and "fecha_datetime" in vendor_stats[vendedor_id]["ultimo_abono_pedido"]:
            del vendor_stats[vendedor_id]["ultimo_abono_pedido"]["fecha_datetime"]
    
    return vendor_stats


def _init_vendor_stat(vendedor_id: int, vendedor_name: str) -> Dict[str, Any]:
    """Initialize vendor statistics structure."""
    return {
        "vendedor_id": vendedor_id,
        "vendedor_name": vendedor_name,
        "sales_count": 0,
        "contado_count": 0,
        "credito_count": 0,
        "total_contado": 0.0,
        "total_credito": 0.0,
        "total_profit": 0.0,
        "total_efectivo_contado": 0.0,
        "total_tarjeta_contado": 0.0,
        "total_tarjeta_neto": 0.0,
        "anticipos_apartados": 0.0,
        "anticipos_pedidos": 0.0,
        "abonos_apartados": 0.0,
        "abonos_pedidos": 0.0,
        "ventas_total_activa": 0.0,
        "venta_total_pasiva": 0.0,
        "cuentas_por_cobrar": 0.0,
        "productos_liquidados": 0.0,  # Se calculará como suma de apartados + pedidos
        "productos_liquidados_apartados": 0.0,  # Suma de todos los abonos que saldan apartados
        "productos_liquidados_pedidos": 0.0,  # Suma de todos los abonos que saldan pedidos
        "ultimo_abono_apartado": None,  # Info del último abono más reciente que saldó un apartado
        "ultimo_abono_pedido": None  # Info del último abono más reciente que saldó un pedido
    }


def _build_dashboard_data(
    counters: Dict[str, Any],
    ventas_liquidacion: Dict[str, Any],
    pedidos_contado: List[Pedido],
    pedidos_liquidados: List[Pedido],
    db: Session,  # Agregar parámetros
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
    pedidos_pendientes: List[Pedido]
) -> Dict[str, Any]:
    """Build dashboard data structure with all metrics and historiales."""
    # CORRECCIÓN: Procesar historiales PRIMERO para actualizar contadores
    historiales = _build_historiales(
        db, tenant, start_datetime, end_datetime, counters,
        pedidos_liquidados, pedidos_pendientes
    )
    
    # Calculate pedidos_contado totals
    pedidos_contado_total = sum(float(p.total) for p in pedidos_contado)
    pedidos_contado_count = len(pedidos_contado)
    
    # Calculate liquidaciones (usar contadores en lugar de recalcular)
    liquidaciones_apartados_monto = counters.get('total_credito', 0.0)
    liquidaciones_apartados_count = counters.get('credito_count', 0)
    liquidaciones_pedidos_monto = counters.get('pedidos_liquidados_total', 0.0)
    liquidaciones_pedidos_count = counters.get('pedidos_liquidados_count', 0)
    
    # Calculate ventas totals
    ventas_contado_monto = counters.get('total_contado', 0.0)
    ventas_contado_count = counters.get('contado_count', 0)
    ventas_total_monto = ventas_contado_monto + pedidos_contado_total
    ventas_total_count = ventas_contado_count + pedidos_contado_count
    
    # Calculate anticipos totals
    anticipos_total_monto = (
        counters.get('anticipos_apartados_total_monto', 0.0) +
        counters.get('anticipos_pedidos_total_monto', 0.0)
    )
    anticipos_total_count = (
        counters.get('anticipos_apartados_count', 0) +
        counters.get('anticipos_pedidos_count', 0)
    )
    
    # Calculate abonos totals
    abonos_total_monto = (
        counters.get('abonos_apartados_total_neto', 0.0) +
        counters.get('abonos_pedidos_total_neto', 0.0)
    )
    abonos_total_count = (
        counters.get('abonos_apartados_count', 0) +
        counters.get('abonos_pedidos_count', 0)
    )
    
    # Calculate liquidaciones totals
    liquidaciones_total_monto = liquidaciones_apartados_monto + liquidaciones_pedidos_monto
    liquidaciones_total_count = liquidaciones_apartados_count + liquidaciones_pedidos_count
    
    # Calculate vencimientos (from counters)
    vencimientos_apartados_monto = counters.get('saldo_vencido_apartados', 0.0)
    vencimientos_pedidos_monto = counters.get('saldo_vencido_pedidos', 0.0)
    vencimientos_total_monto = vencimientos_apartados_monto + vencimientos_pedidos_monto
    # Counts basados en contadores de vencidos
    vencimientos_apartados_count = counters.get('apartados_vencidos_count', 0)
    vencimientos_pedidos_count = counters.get('pedidos_vencidos_count', 0)
    vencimientos_total_count = vencimientos_apartados_count + vencimientos_pedidos_count
    
    # Calculate cancelaciones totals
    cancelaciones_ventas_contado_monto = counters.get('cancelaciones_ventas_contado_monto', 0.0)
    cancelaciones_ventas_contado_count = counters.get('cancelaciones_ventas_contado_count', 0)
    cancelaciones_pedidos_contado_monto = counters.get('cancelaciones_pedidos_contado_monto', 0.0)
    cancelaciones_pedidos_contado_count = counters.get('cancelaciones_pedidos_contado_count', 0)
    cancelaciones_pedidos_apartados_monto = counters.get('cancelaciones_pedidos_apartados_monto', 0.0)
    cancelaciones_pedidos_apartados_count = counters.get('cancelaciones_pedidos_apartados_count', 0)
    cancelaciones_apartados_monto = counters.get('cancelaciones_apartados_monto', 0.0)
    cancelaciones_apartados_count = counters.get('cancelaciones_apartados_count', 0)
    cancelaciones_total_monto = (
        cancelaciones_ventas_contado_monto +
        cancelaciones_pedidos_contado_monto +
        cancelaciones_pedidos_apartados_monto +
        cancelaciones_apartados_monto
    )
    cancelaciones_total_count = (
        cancelaciones_ventas_contado_count +
        cancelaciones_pedidos_contado_count +
        cancelaciones_pedidos_apartados_count +
        cancelaciones_apartados_count
    )
    
    # Calculate metodos_pago for ventas_contado
    ventas_contado_efectivo = counters.get('total_efectivo_contado', 0.0)
    ventas_contado_tarjeta_bruto = counters.get('total_tarjeta_contado', 0.0)
    ventas_contado_tarjeta_neto = ventas_contado_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    ventas_contado_total_metodo = ventas_contado_efectivo + ventas_contado_tarjeta_neto
    
    return {
        "ventas": {
            "contado": {
                "monto": ventas_contado_monto,
                "count": ventas_contado_count,
            },
            "pedidos_contado": {
                "monto": pedidos_contado_total,
                "count": pedidos_contado_count,
            },
            "total": {
                "monto": ventas_total_monto,
                "count": ventas_total_count,
            },
        },
        "anticipos": {
            "apartados": {
                "efectivo": {
                    "monto": counters.get('anticipos_apartados_efectivo_monto', 0.0),
                    "count": counters.get('anticipos_apartados_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('anticipos_apartados_tarjeta_bruto', 0.0),
                    "neto": counters.get('anticipos_apartados_tarjeta_neto', 0.0),
                    "count": counters.get('anticipos_apartados_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('anticipos_apartados_total_monto', 0.0),
                    "count": counters.get('anticipos_apartados_count', 0),
                },
            },
            "pedidos_apartados": {
                "efectivo": {
                    "monto": counters.get('anticipos_pedidos_efectivo_monto', 0.0),
                    "count": counters.get('anticipos_pedidos_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('anticipos_pedidos_tarjeta_bruto', 0.0),
                    "neto": counters.get('anticipos_pedidos_tarjeta_neto', 0.0),
                    "count": counters.get('anticipos_pedidos_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('anticipos_pedidos_total_monto', 0.0),
                    "count": counters.get('anticipos_pedidos_count', 0),
                },
            },
            "total": {
                "monto": anticipos_total_monto,
                "count": anticipos_total_count,
            },
        },
        "abonos": {
            "apartados": {
                "efectivo": {
                    "monto": counters.get('abonos_apartados_efectivo_monto', 0.0),
                    "count": counters.get('abonos_apartados_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('abonos_apartados_tarjeta_bruto', 0.0),
                    "neto": counters.get('abonos_apartados_tarjeta_neto', 0.0),
                    "count": counters.get('abonos_apartados_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('abonos_apartados_total_neto', 0.0),
                    "count": counters.get('abonos_apartados_count', 0),
                },
            },
            "pedidos_apartados": {
                "efectivo": {
                    "monto": counters.get('abonos_pedidos_efectivo_monto', 0.0),
                    "count": counters.get('abonos_pedidos_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('abonos_pedidos_tarjeta_bruto', 0.0),
                    "neto": counters.get('abonos_pedidos_tarjeta_neto', 0.0),
                    "count": counters.get('abonos_pedidos_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('abonos_pedidos_total_neto', 0.0),
                    "count": counters.get('abonos_pedidos_count', 0),
                },
            },
            "total": {
                "monto": abonos_total_monto,
                "count": abonos_total_count,
            },
        },
        "liquidaciones": {
            "apartados": {
                "monto": liquidaciones_apartados_monto,
                "count": liquidaciones_apartados_count,
            },
            "pedidos_apartados": {
                "monto": liquidaciones_pedidos_monto,
                "count": liquidaciones_pedidos_count,
            },
            "total": {
                "monto": liquidaciones_total_monto,
                "count": liquidaciones_total_count,
            },
        },
        "vencimientos": {
            "apartados": {
                "monto": vencimientos_apartados_monto,
                "count": vencimientos_apartados_count,
            },
            "pedidos_apartados": {
                "monto": vencimientos_pedidos_monto,
                "count": vencimientos_pedidos_count,
            },
            "total": {
                "monto": vencimientos_total_monto,
                "count": vencimientos_total_count,
            },
        },
        "cancelaciones": {
            "ventas_contado": {
                "monto": cancelaciones_ventas_contado_monto,
                "count": cancelaciones_ventas_contado_count,
            },
            "pedidos_contado": {
                "monto": cancelaciones_pedidos_contado_monto,
                "count": cancelaciones_pedidos_contado_count,
            },
            "pedidos_apartados": {
                "monto": cancelaciones_pedidos_apartados_monto,
                "count": cancelaciones_pedidos_apartados_count,
            },
            "apartados": {
                "monto": cancelaciones_apartados_monto,
                "count": cancelaciones_apartados_count,
            },
            "total": {
                "monto": cancelaciones_total_monto,
                "count": cancelaciones_total_count,
            },
        },
        "metodos_pago": {
            "ventas_contado": {
                "efectivo": {
                    "monto": ventas_contado_efectivo,
                    "count": ventas_contado_count if ventas_contado_efectivo > 0 else 0,
                },
                "tarjeta": {
                    "bruto": ventas_contado_tarjeta_bruto,
                    "neto": ventas_contado_tarjeta_neto,
                    "count": ventas_contado_count if ventas_contado_tarjeta_bruto > 0 else 0,
                },
                "total": {
                    "monto": ventas_contado_total_metodo,
                    "count": ventas_contado_count,
                },
            },
            "pedidos_contado": {
                "efectivo": {"monto": 0.0, "count": 0},
                "tarjeta": {"bruto": 0.0, "neto": 0.0, "count": 0},
                "total": {"monto": 0.0, "count": 0},
            },
            "anticipos_apartados": {
                "efectivo": {
                    "monto": counters.get('anticipos_apartados_efectivo_monto', 0.0),
                    "count": counters.get('anticipos_apartados_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('anticipos_apartados_tarjeta_bruto', 0.0),
                    "neto": counters.get('anticipos_apartados_tarjeta_neto', 0.0),
                    "count": counters.get('anticipos_apartados_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('anticipos_apartados_total_monto', 0.0),
                    "count": counters.get('anticipos_apartados_count', 0),
                },
            },
            "anticipos_pedidos_apartados": {
                "efectivo": {
                    "monto": counters.get('anticipos_pedidos_efectivo_monto', 0.0),
                    "count": counters.get('anticipos_pedidos_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('anticipos_pedidos_tarjeta_bruto', 0.0),
                    "neto": counters.get('anticipos_pedidos_tarjeta_neto', 0.0),
                    "count": counters.get('anticipos_pedidos_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('anticipos_pedidos_total_monto', 0.0),
                    "count": counters.get('anticipos_pedidos_count', 0),
                },
            },
            "abonos_apartados": {
                "efectivo": {
                    "monto": counters.get('abonos_apartados_efectivo_monto', 0.0),
                    "count": counters.get('abonos_apartados_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('abonos_apartados_tarjeta_bruto', 0.0),
                    "neto": counters.get('abonos_apartados_tarjeta_neto', 0.0),
                    "count": counters.get('abonos_apartados_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('abonos_apartados_total_neto', 0.0),
                    "count": counters.get('abonos_apartados_count', 0),
                },
            },
            "abonos_pedidos_apartados": {
                "efectivo": {
                    "monto": counters.get('abonos_pedidos_efectivo_monto', 0.0),
                    "count": counters.get('abonos_pedidos_efectivo_count', 0),
                },
                "tarjeta": {
                    "bruto": counters.get('abonos_pedidos_tarjeta_bruto', 0.0),
                    "neto": counters.get('abonos_pedidos_tarjeta_neto', 0.0),
                    "count": counters.get('abonos_pedidos_tarjeta_count', 0),
                },
                "total": {
                    "monto": counters.get('abonos_pedidos_total_neto', 0.0),
                    "count": counters.get('abonos_pedidos_count', 0),
                },
            },
        },
        "contadores": {
            "piezas_totales_vendidas": counters.get('num_piezas_vendidas', 0),
            "piezas_totales_vendidas_contado": counters.get('num_piezas_vendidas', 0),
            "piezas_totales_vendidas_pedidos_contado": 0,  # Will be calculated
            "piezas_entregadas": counters.get('num_piezas_entregadas', 0),
            "piezas_vencidas_totales": counters.get('piezas_vencidas_apartados', 0) + counters.get('piezas_vencidas_pedidos_apartados', 0),
            "piezas_vencidas_apartados": counters.get('piezas_vencidas_apartados', 0),
            "piezas_vencidas_pedidos_apartados": counters.get('piezas_vencidas_pedidos_apartados', 0),
            "piezas_canceladas_ventas": counters.get('piezas_canceladas_ventas', 0),
            "piezas_canceladas_pedidos_contado": counters.get('piezas_canceladas_pedidos_contado', 0),
            "piezas_canceladas_pedidos_apartados": counters.get('piezas_canceladas_pedidos_apartados', 0),
            "piezas_canceladas_apartados": counters.get('piezas_canceladas_apartados', 0),
            "piezas_canceladas_totales": (
                counters.get('piezas_canceladas_ventas', 0) +
                counters.get('piezas_canceladas_pedidos_contado', 0) +
                counters.get('piezas_canceladas_pedidos_apartados', 0) +
                counters.get('piezas_canceladas_apartados', 0)
            ),
        },
        # Agregar historiales al dashboard para consolidar toda la información
        "historiales": {
            "apartados": historiales['apartados'],
            "pedidos": historiales['pedidos'],
            "abonos_apartados": historiales['abonos_apartados'],
            "abonos_pedidos": historiales['abonos_pedidos'],
            "apartados_cancelados_vencidos": historiales['apartados_cancelados_vencidos'],
            "pedidos_cancelados_vencidos": historiales['pedidos_cancelados_vencidos'],
        },
    }


def _build_historiales(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
    counters: Dict[str, Any],
    pedidos_liquidados: List[Pedido],
    pedidos_pendientes: List[Pedido]
) -> HistorialesData:
    """Build historiales (apartados, pedidos, abonos)."""
    historial_apartados = []
    historial_pedidos = []
    historial_abonos_apartados = []
    historial_abonos_pedidos = []
    apartados_cancelados_vencidos = []
    pedidos_cancelados_vencidos = []
    
    # Historial de pedidos liquidados
    for pedido in pedidos_liquidados:
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        historial_pedidos.append({
            "id": pedido.id,
            "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": pedido.cliente_nombre,
            "producto": producto_name,
            "cantidad": pedido.cantidad,
            "total": float(pedido.total),
            "anticipo": float(pedido.anticipo_pagado),
            "saldo": float(pedido.saldo_pendiente),
            "estado": pedido.estado,
            "vendedor": vendedor
        })
    
    # Historial de pedidos pendientes
    for pedido in pedidos_pendientes:
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        historial_pedidos.append({
            "id": pedido.id,
            "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": pedido.cliente_nombre,
            "producto": producto_name,
            "cantidad": pedido.cantidad,
            "total": float(pedido.total),
            "anticipo": float(pedido.anticipo_pagado),
            "saldo": float(pedido.saldo_pendiente),
            "estado": pedido.estado,
            "vendedor": vendedor
        })
    
    # Historial de apartados activos (nuevo esquema)
    apartados_activos = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
        ~Apartado.credit_status.in_(['cancelado', 'vencido'])
    ).order_by(Apartado.created_at.desc()).all()
    
    for apartado in apartados_activos:
        vendedor = "Unknown"
        if apartado.vendedor_id:
            vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        saldo = float(apartado.total or 0) - float(apartado.amount_paid or 0)
        
        historial_apartados.append({
            "id": apartado.id,
            "fecha": apartado.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": apartado.customer_name or "Sin nombre",
            "total": float(apartado.total or 0),
            "anticipo": float(apartado.amount_paid or 0),
            "saldo": saldo,
            "estado": apartado.credit_status or "pendiente",
            "vendedor": vendedor
        })
    
    # Apartados cancelados y vencidos (nuevo esquema Apartado)
    apartados_nuevos_cancelados_vencidos = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
        Apartado.credit_status.in_(['cancelado', 'vencido'])
    ).order_by(Apartado.created_at.desc()).all()

    for ap in apartados_nuevos_cancelados_vencidos:
        vendedor = "Unknown"
        if ap.vendedor_id:
            vendor = db.query(User).filter(User.id == ap.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"

        saldo = float(ap.total or 0) - float(ap.amount_paid or 0)
        motivo = "Vencido" if ap.credit_status == "vencido" else "Cancelado"

        # Para el nuevo esquema, todos los pagos (anticipos+abonos) viven en credit_payments.apartado_id
        abonos_apartado = db.query(CreditPayment).filter(CreditPayment.apartado_id == ap.id).all()
        abonos_efectivo = sum(
            float(p.amount) for p in abonos_apartado
            if p.payment_method in ['efectivo', 'cash', 'transferencia']
        )
        abonos_tarjeta = sum(
            float(p.amount) for p in abonos_apartado
            if p.payment_method in ['tarjeta', 'card']
        )
        total_pagado_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)

        # No tenemos SaleItem para Apartado nuevo; las piezas se pueden aproximar a 0 aquí
        piezas_apartado = 0

        if ap.credit_status == "cancelado":
            counters['reembolso_apartados_cancelados'] += total_pagado_neto
            counters['cancelaciones_apartados_monto'] += total_pagado_neto
            counters['cancelaciones_apartados_count'] += 1
            counters['piezas_canceladas_apartados'] += piezas_apartado
        elif ap.credit_status == "vencido":
            # El saldo vencido es el monto total pagado (anticipo + abonos) porque el cliente puede pedirlo de regreso
            # total_pagado_neto ya incluye todos los abonos calculados arriba (anticipo + abonos adicionales)
            counters['saldo_vencido_apartados'] += total_pagado_neto
            counters['piezas_vencidas_apartados'] += piezas_apartado
            counters['apartados_vencidos_count'] += 1

        apartados_cancelados_vencidos.append({
            "id": ap.id,
            "fecha": ap.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": ap.customer_name or "Sin nombre",
            "total": float(ap.total or 0),
            "anticipo": float(ap.amount_paid or 0),
            "saldo": saldo,
            "estado": ap.credit_status,
            "vendedor": vendedor,
            "motivo": motivo,
        })
    
    # Historial de abonos de apartados: filtrar por fecha de creación del abono
    todos_abonos_apartados = db.query(CreditPayment).filter(
        CreditPayment.tenant_id == tenant.id,
        CreditPayment.apartado_id.isnot(None),  # Solo abonos del nuevo esquema
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).order_by(CreditPayment.created_at.desc()).all()
    
    for abono in todos_abonos_apartados:
        apartado = db.query(Apartado).filter(Apartado.id == abono.apartado_id).first() if abono.apartado_id else None
        vendedor = "Unknown"
        if abono.user_id:
            vendor = db.query(User).filter(User.id == abono.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        historial_abonos_apartados.append({
            "id": abono.id,
            "fecha": abono.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": apartado.customer_name if apartado else "Desconocido",
            "monto": float(abono.amount),
            "metodo_pago": abono.payment_method,
            "vendedor": vendedor
        })
    
    # Historial de abonos de pedidos: solo pedidos CREADOS en el periodo
    todos_abonos_pedidos = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        PagoPedido.tipo_pago == 'saldo'
    ).order_by(PagoPedido.created_at.desc()).all()
    
    for abono in todos_abonos_pedidos:
        pedido = db.query(Pedido).filter(Pedido.id == abono.pedido_id).first()
        vendedor = "Unknown"
        producto_name = "Desconocido"
        
        if pedido:
            if pedido.user_id:
                vendor = db.query(User).filter(User.id == pedido.user_id).first()
                vendedor = vendor.email if vendor else "Unknown"
            
            producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
            producto_name = producto.modelo if producto else "Producto desconocido"
        
        historial_abonos_pedidos.append({
            "id": abono.id,
            "fecha": abono.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": pedido.cliente_nombre if pedido else "Desconocido",
            "producto": producto_name,
            "monto": float(abono.monto),
            "metodo_pago": abono.metodo_pago,
            "vendedor": vendedor,
        })
    
    # Pedidos cancelados y vencidos
    pedidos_cancelados_vencidos_query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        or_(
            Pedido.estado == 'cancelado',
            and_(
                Pedido.tipo_pedido == 'apartado',
                Pedido.estado == 'vencido'
            )
        )
    ).order_by(Pedido.created_at.desc()).all()
    
    for pedido in pedidos_cancelados_vencidos_query:
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        motivo = "Vencido" if pedido.estado == "vencido" else "Cancelado"
        
        pagos_pedido_all = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        pagos_totals = _calculate_payment_totals(pagos_pedido_all)
        pagos_efectivo = pagos_totals['efectivo']
        pagos_tarjeta = pagos_totals['tarjeta']
        total_pagado_neto = pagos_efectivo + (pagos_tarjeta * TARJETA_DISCOUNT_RATE)
        
        if pedido.estado == "cancelado":
            counters['reembolso_pedidos_cancelados'] += total_pagado_neto
            if pedido.tipo_pedido == "contado":
                counters['cancelaciones_pedidos_contado_monto'] += total_pagado_neto
                counters['cancelaciones_pedidos_contado_count'] += 1
                counters['piezas_canceladas_pedidos_contado'] += pedido.cantidad or 0
            else:
                counters['cancelaciones_pedidos_apartados_monto'] += total_pagado_neto
                counters['cancelaciones_pedidos_apartados_count'] += 1
                counters['piezas_canceladas_pedidos_apartados'] += pedido.cantidad or 0
        elif pedido.estado == "vencido":
            # El saldo vencido es el monto total pagado (anticipo + abonos) porque el cliente puede pedirlo de regreso
            # total_pagado_neto ya incluye todos los pagos (anticipo + abonos adicionales) calculados arriba
            counters['saldo_vencido_pedidos'] += total_pagado_neto
            counters['pedidos_vencidos_count'] += 1
            if pedido.tipo_pedido == "apartado":
                counters['piezas_vencidas_pedidos_apartados'] += pedido.cantidad or 0
        
        pedidos_cancelados_vencidos.append({
            "id": pedido.id,
            "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": pedido.cliente_nombre,
            "producto": producto_name,
            "cantidad": pedido.cantidad,
            "total": float(pedido.total),
            "anticipo": float(pedido.anticipo_pagado),
            "saldo": float(pedido.saldo_pendiente),
            "estado": pedido.estado,
            "vendedor": vendedor,
            "motivo": motivo
        })
    
    return {
        'apartados': historial_apartados,
        'pedidos': historial_pedidos,
        'abonos_apartados': historial_abonos_apartados,
        'abonos_pedidos': historial_abonos_pedidos,
        'apartados_cancelados_vencidos': apartados_cancelados_vencidos,
        'pedidos_cancelados_vencidos': pedidos_cancelados_vencidos,
    }


def _build_sales_details(
    db: Session,
    ventas_contado: List[VentasContado],
    pedidos_contado: List[Pedido],
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[Dict[str, Any]]:
    """Build sales details list."""
    sales_details = []
    
    # Procesar VentasContado (nuevo esquema)
    for venta in ventas_contado:
        vendedor = "Mostrador"
        if venta.vendedor_id:
            vendor = db.query(User).filter(User.id == venta.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        payments = db.query(Payment).filter(Payment.venta_contado_id == venta.id).all()
        efectivo_amount = sum(float(p.amount) for p in payments if p.method in ['efectivo', 'cash', 'transferencia'])
        tarjeta_amount = sum(float(p.amount) for p in payments if p.method in ['tarjeta', 'card'])
        
        # Calcular piezas desde items
        items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id == venta.id).all()
        piezas = sum(int(item.quantity or 0) for item in items)
        
        sales_details.append({
            "id": venta.id,
            "fecha": venta.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": venta.customer_name or "Mostrador",
            "piezas": piezas,
            "total": float(venta.total or 0),
            "estado": "Pagada",
            "tipo": "contado",
            "vendedor": vendedor,
            "efectivo": efectivo_amount,
            "tarjeta": tarjeta_amount
        })
    
    for pedido in pedidos_contado:
        pagos_pedido_contado = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id
        ).all()
        
        efectivo_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago in ['efectivo', 'transferencia'])
        tarjeta_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago == 'tarjeta')
        
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        sales_details.append({
            "id": pedido.id,
            "tipo": "Pedido Contado",
            "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": pedido.cliente_nombre,
            "producto": producto_name,
            "cantidad": pedido.cantidad,
            "piezas": pedido.cantidad,
            "total": float(pedido.total),
            "estado": "Pagada",
            "vendedor": vendedor,
            "efectivo": efectivo_pedido,
            "tarjeta": tarjeta_pedido
        })
    
    return sales_details


def _build_piezas_recibidas(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[Dict[str, Any]]:
    """Build list of received pieces (piezas recibidas)."""
    piezas_recibidas = []
    
    # Obtener pedidos con estado "recibido" creados en el periodo
    pedidos_recibidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado == 'recibido',
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).all()
    
    for pedido in pedidos_recibidos:
        # Obtener items del pedido
        pedido_items = db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).all()
        
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        if pedido_items:
            # Si tiene items múltiples
            for item in pedido_items:
                piezas_recibidas.append({
                    "id": pedido.id,
                    "folio": pedido.folio_pedido or f"PED-{pedido.id:06d}",
                    "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                    "fecha_recibido": pedido.fecha_entrega_real.strftime("%Y-%m-%d %H:%M") if pedido.fecha_entrega_real else pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                    "cliente": pedido.cliente_nombre,
                    "producto": item.nombre or item.modelo or "Sin nombre",
                    "modelo": item.modelo or "N/A",
                    "codigo": item.codigo or "N/A",
                    "color": item.color or "N/A",
                    "quilataje": item.quilataje or "N/A",
                    "talla": item.talla or None,
                    "cantidad": item.cantidad,
                    "precio_unitario": float(item.precio_unitario),
                    "total": float(item.total),
                    "vendedor": vendedor,
                })
        else:
            # Fallback: usar producto_pedido_id si no hay items
            producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
            producto_name = producto.nombre or producto.modelo if producto else "Producto desconocido"
            
            piezas_recibidas.append({
                "id": pedido.id,
                "folio": pedido.folio_pedido or f"PED-{pedido.id:06d}",
                "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                "fecha_recibido": pedido.fecha_entrega_real.strftime("%Y-%m-%d %H:%M") if pedido.fecha_entrega_real else pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                "cliente": pedido.cliente_nombre,
                "producto": producto_name,
                "modelo": producto.modelo if producto else "N/A",
                "codigo": producto.codigo if producto else "N/A",
                "color": producto.color if producto else "N/A",
                "quilataje": producto.quilataje if producto else "N/A",
                "talla": producto.talla if producto else None,
                "cantidad": pedido.cantidad,
                "precio_unitario": float(pedido.precio_unitario),
                "total": float(pedido.total),
                "vendedor": vendedor,
            })
    
    return piezas_recibidas


def _build_piezas_solicitadas_cliente(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[Dict[str, Any]]:
    """Build list of pieces requested by clients (anticipos pedidos apartados)."""
    piezas_solicitadas = []
    
    # Obtener pedidos apartados con estado "pendiente" y con anticipo pagado
    # Filtrar por fecha de creación del anticipo (PagoPedido.created_at)
    pedidos_apartados_ids = db.query(PagoPedido.pedido_id).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado == 'pendiente',
        PagoPedido.tipo_pago == 'anticipo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).distinct().all()
    
    pedidos_apartados_ids_list = [id for id, in pedidos_apartados_ids]
    pedidos_apartados = db.query(Pedido).filter(
        Pedido.id.in_(pedidos_apartados_ids_list)
    ).all() if pedidos_apartados_ids_list else []
    
    for pedido in pedidos_apartados:
        # Obtener items del pedido
        pedido_items = db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).all()
        
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        # Obtener anticipos pagados
        anticipos = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'anticipo'
        ).all()
        
        anticipo_efectivo = sum(float(p.monto) for p in anticipos if p.metodo_pago in ['efectivo', 'transferencia'])
        anticipo_tarjeta = sum(float(p.monto) for p in anticipos if p.metodo_pago == 'tarjeta')
        
        if pedido_items:
            # Si tiene items múltiples
            for item in pedido_items:
                piezas_solicitadas.append({
                    "id": pedido.id,
                    "folio": pedido.folio_pedido or f"PED-{pedido.id:06d}",
                    "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                    "cliente": pedido.cliente_nombre,
                    "producto": item.nombre or item.modelo or "Sin nombre",
                    "modelo": item.modelo or "N/A",
                    "codigo": item.codigo or "N/A",
                    "color": item.color or "N/A",
                    "quilataje": item.quilataje or "N/A",
                    "talla": item.talla or None,
                    "cantidad": item.cantidad,
                    "precio_unitario": float(item.precio_unitario),
                    "total": float(item.total),
                    "anticipo_pagado": float(pedido.anticipo_pagado),
                    "anticipo_efectivo": anticipo_efectivo,
                    "anticipo_tarjeta": anticipo_tarjeta,
                    "saldo_pendiente": float(pedido.saldo_pendiente),
                    "estado": pedido.estado,
                    "vendedor": vendedor,
                })
        else:
            # Fallback: usar producto_pedido_id si no hay items
            producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
            producto_name = producto.nombre or producto.modelo if producto else "Producto desconocido"
            
            piezas_solicitadas.append({
                "id": pedido.id,
                "folio": pedido.folio_pedido or f"PED-{pedido.id:06d}",
                "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                "cliente": pedido.cliente_nombre,
                "producto": producto_name,
                "modelo": producto.modelo if producto else "N/A",
                "codigo": producto.codigo if producto else "N/A",
                "color": producto.color if producto else "N/A",
                "quilataje": producto.quilataje if producto else "N/A",
                "talla": producto.talla if producto else None,
                "cantidad": pedido.cantidad,
                "precio_unitario": float(pedido.precio_unitario),
                "total": float(pedido.total),
                "anticipo_pagado": float(pedido.anticipo_pagado),
                "anticipo_efectivo": anticipo_efectivo,
                "anticipo_tarjeta": anticipo_tarjeta,
                "saldo_pendiente": float(pedido.saldo_pendiente),
                "estado": pedido.estado,
                "vendedor": vendedor,
            })
    
    return piezas_solicitadas


def _build_piezas_pedidas_proveedor(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[Dict[str, Any]]:
    """Build list of pieces ordered to suppliers (pedidas a proveedores)."""
    piezas_pedidas = []
    
    # Obtener pedidos con estado "pedidas" que fueron pedidos al proveedor
    pedidos_proveedor = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.estado == 'pedidas',
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).all()
    
    for pedido in pedidos_proveedor:
        # Obtener items del pedido
        pedido_items = db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).all()
        
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        if pedido_items:
            # Si tiene items múltiples
            for item in pedido_items:
                piezas_pedidas.append({
                    "id": pedido.id,
                    "folio": pedido.folio_pedido or f"PED-{pedido.id:06d}",
                    "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                    "fecha_entrega_estimada": pedido.fecha_entrega_estimada.strftime("%Y-%m-%d") if pedido.fecha_entrega_estimada else None,
                    "cliente": pedido.cliente_nombre,
                    "producto": item.nombre or item.modelo or "Sin nombre",
                    "modelo": item.modelo or "N/A",
                    "codigo": item.codigo or "N/A",
                    "color": item.color or "N/A",
                    "quilataje": item.quilataje or "N/A",
                    "talla": item.talla or None,
                    "cantidad": item.cantidad,
                    "precio_unitario": float(item.precio_unitario),
                    "total": float(item.total),
                    "estado": pedido.estado,
                    "tipo_pedido": pedido.tipo_pedido,
                    "vendedor": vendedor,
                })
        else:
            # Fallback: usar producto_pedido_id si no hay items
            producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
            producto_name = producto.nombre or producto.modelo if producto else "Producto desconocido"
            
            piezas_pedidas.append({
                "id": pedido.id,
                "folio": pedido.folio_pedido or f"PED-{pedido.id:06d}",
                "fecha": pedido.created_at.strftime("%Y-%m-%d %H:%M"),
                "fecha_entrega_estimada": pedido.fecha_entrega_estimada.strftime("%Y-%m-%d") if pedido.fecha_entrega_estimada else None,
                "cliente": pedido.cliente_nombre,
                "producto": producto_name,
                "modelo": producto.modelo if producto else "N/A",
                "codigo": producto.codigo if producto else "N/A",
                "color": producto.color if producto else "N/A",
                "quilataje": producto.quilataje if producto else "N/A",
                "talla": producto.talla if producto else None,
                "cantidad": pedido.cantidad,
                "precio_unitario": float(pedido.precio_unitario),
                "total": float(pedido.total),
                "estado": pedido.estado,
                "tipo_pedido": pedido.tipo_pedido,
                "vendedor": vendedor,
            })
    
    return piezas_pedidas


def _calculate_additional_metrics(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> Dict[str, int]:
    """Calculate additional metrics."""
    num_solicitudes_apartado = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime
    ).count()
    
    num_pedidos_hechos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).count()
    
    num_apartados_vencidos = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
        Apartado.credit_status == "vencido"
    ).count()
    
    num_pedidos_vencidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at <= end_datetime,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado == "vencido"
    ).count()
    
    num_cancelaciones = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.estado == "cancelado"
    ).count()
    
    num_cancelaciones += db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
        Apartado.credit_status == "cancelado"
    ).count()
    
    num_abonos_apartados = db.query(CreditPayment).filter(
        CreditPayment.tenant_id == tenant.id,
        CreditPayment.apartado_id.isnot(None),  # Solo abonos del nuevo esquema
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).count()
    
    num_abonos_pedidos = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        PagoPedido.tipo_pago == 'saldo'
    ).count()
    
    return {
        'num_solicitudes_apartado': num_solicitudes_apartado,
        'num_pedidos_hechos': num_pedidos_hechos,
        'num_apartados_vencidos': num_apartados_vencidos,
        'num_pedidos_vencidos': num_pedidos_vencidos,
        'num_cancelaciones': num_cancelaciones,
        'num_abonos_apartados': num_abonos_apartados,
        'num_abonos_pedidos': num_abonos_pedidos,
    }


def _build_daily_summaries(
    ventas_contado: List[VentasContado],
    pedidos_contado: List[Pedido],
    db: Session
) -> List[Dict[str, Any]]:
    """Build daily summaries."""
    daily_stats = {}
    
    # Procesar VentasContado (nuevo esquema)
    for venta in ventas_contado:
        sale_date = venta.created_at.date().isoformat()
        if sale_date not in daily_stats:
            daily_stats[sale_date] = {
                "fecha": sale_date,
                "costo": 0.0,
                "venta": 0.0,
                "utilidad": 0.0
            }
        
        if venta.total_cost:
            daily_stats[sale_date]["costo"] += float(venta.total_cost)
        daily_stats[sale_date]["venta"] += float(venta.total or 0)
        daily_stats[sale_date]["utilidad"] += float(venta.utilidad or 0)
    
    # Procesar pedidos de contado
    for pedido in pedidos_contado:
        sale_date = pedido.created_at.date().isoformat()
        if sale_date not in daily_stats:
            daily_stats[sale_date] = {
                "fecha": sale_date,
                "costo": 0.0,
                "venta": 0.0,
                "utilidad": 0.0
            }
        
        # Calcular costo del pedido
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        if producto and producto.cost_price:
            costo_pedido = float(producto.cost_price) * pedido.cantidad
            daily_stats[sale_date]["costo"] += costo_pedido
        
        daily_stats[sale_date]["venta"] += float(pedido.total)
        # Utilidad = total - costo
        if producto and producto.cost_price:
            utilidad_pedido = float(pedido.total) - (float(producto.cost_price) * pedido.cantidad)
            daily_stats[sale_date]["utilidad"] += utilidad_pedido
    
    return list(daily_stats.values())


def _build_resumen_ventas_activas(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
    pedidos_contado: List[Pedido]
) -> List[Dict[str, Any]]:
    """Build resumen de ventas activas."""
    resumen_ventas_activas = []
    
    # Contar ventas de contado (usar VentasContado)
    ventas_contado_efectivo_count = 0
    ventas_contado_efectivo_bruto = 0.0
    ventas_contado_tarjeta_count = 0
    ventas_contado_tarjeta_bruto = 0.0
    
    ventas_contado_query = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime
    ).all()
    
    for venta in ventas_contado_query:
        pagos = db.query(Payment).filter(Payment.venta_contado_id == venta.id).all()
        for pago in pagos:
            if pago.method in ['efectivo', 'cash', 'transferencia']:
                ventas_contado_efectivo_count += 1
                ventas_contado_efectivo_bruto += float(pago.amount)
            elif pago.method in ['tarjeta', 'card']:
                ventas_contado_tarjeta_count += 1
                ventas_contado_tarjeta_bruto += float(pago.amount)
    
    # Contar pedidos de contado
    pedidos_contado_efectivo_count = 0
    pedidos_contado_efectivo_bruto = 0.0
    pedidos_contado_tarjeta_count = 0
    pedidos_contado_tarjeta_bruto = 0.0
    
    for pedido in pedidos_contado:
        pagos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        for pago in pagos:
            if pago.metodo_pago in EFECTIVO_METHODS:
                pedidos_contado_efectivo_count += 1
                pedidos_contado_efectivo_bruto += float(pago.monto)
            elif pago.metodo_pago == TARJETA_METHOD:
                pedidos_contado_tarjeta_count += 1
                pedidos_contado_tarjeta_bruto += float(pago.monto)
    
    # Construir tabla
    resumen_ventas_activas.append({
        "tipo_movimiento": "Venta de contado",
        "metodo_pago": "Efectivo",
        "cantidad_operaciones": ventas_contado_efectivo_count,
        "subtotal": ventas_contado_efectivo_bruto,
        "total": ventas_contado_efectivo_bruto
    })
    resumen_ventas_activas.append({
        "tipo_movimiento": "Venta de contado",
        "metodo_pago": "Tarjeta",
        "cantidad_operaciones": ventas_contado_tarjeta_count,
        "subtotal": ventas_contado_tarjeta_bruto,
        "total": ventas_contado_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    })
    resumen_ventas_activas.append({
        "tipo_movimiento": "Venta de contado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": ventas_contado_efectivo_count + ventas_contado_tarjeta_count,
        "subtotal": ventas_contado_efectivo_bruto + ventas_contado_tarjeta_bruto,
        "total": ventas_contado_efectivo_bruto + (ventas_contado_tarjeta_bruto * TARJETA_DISCOUNT_RATE)
    })
    
    resumen_ventas_activas.append({
        "tipo_movimiento": "Pedido de contado",
        "metodo_pago": "Efectivo",
        "cantidad_operaciones": pedidos_contado_efectivo_count,
        "subtotal": pedidos_contado_efectivo_bruto,
        "total": pedidos_contado_efectivo_bruto
    })
    resumen_ventas_activas.append({
        "tipo_movimiento": "Pedido de contado",
        "metodo_pago": "Tarjeta",
        "cantidad_operaciones": pedidos_contado_tarjeta_count,
        "subtotal": pedidos_contado_tarjeta_bruto,
        "total": pedidos_contado_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    })
    resumen_ventas_activas.append({
        "tipo_movimiento": "Pedido de contado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": pedidos_contado_efectivo_count + pedidos_contado_tarjeta_count,
        "subtotal": pedidos_contado_efectivo_bruto + pedidos_contado_tarjeta_bruto,
        "total": pedidos_contado_efectivo_bruto + (pedidos_contado_tarjeta_bruto * TARJETA_DISCOUNT_RATE)
    })
    
    return resumen_ventas_activas


def _build_resumen_pagos(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime,
    apartados_pendientes: List[Apartado],  # Cambiado de List[Sale] a List[Apartado]
    pedidos_pendientes: List[Pedido]
) -> List[Dict[str, Any]]:
    """Build resumen de pagos (ventas pasivas)."""
    resumen_pagos = []
    
    # Anticipos de apartados
    anticipos_apart_efectivo_count = 0
    anticipos_apart_efectivo_bruto = 0.0
    anticipos_apart_tarjeta_count = 0
    anticipos_apart_tarjeta_bruto = 0.0
    
    # Abonos de apartados
    abonos_apart_efectivo_count = 0
    abonos_apart_efectivo_bruto = 0.0
    abonos_apart_tarjeta_count = 0
    abonos_apart_tarjeta_bruto = 0.0
    
    # Anticipos de pedidos apartados
    anticipos_ped_efectivo_count = 0
    anticipos_ped_efectivo_bruto = 0.0
    anticipos_ped_tarjeta_count = 0
    anticipos_ped_tarjeta_bruto = 0.0
    
    # Abonos de pedidos apartados
    abonos_ped_efectivo_count = 0
    abonos_ped_efectivo_bruto = 0.0
    abonos_ped_tarjeta_count = 0
    abonos_ped_tarjeta_bruto = 0.0
    
    # Contar anticipos de apartados pendientes
    for apartado in apartados_pendientes:
        # Buscar anticipos iniciales en CreditPayment con notes="Anticipo inicial"
        pagos_iniciales = db.query(CreditPayment).filter(
            CreditPayment.apartado_id == apartado.id,
            CreditPayment.notes == "Anticipo inicial"
        ).all()
        for pago in pagos_iniciales:
            if pago.payment_method in ['efectivo', 'cash', 'transferencia']:
                anticipos_apart_efectivo_count += 1
                anticipos_apart_efectivo_bruto += float(pago.amount)
            elif pago.payment_method in ['tarjeta', 'card']:
                anticipos_apart_tarjeta_count += 1
                anticipos_apart_tarjeta_bruto += float(pago.amount)
    
    # Contar abonos de apartados pendientes
    for apartado in apartados_pendientes:
        # Buscar abonos (excluyendo anticipo inicial)
        abonos = db.query(CreditPayment).filter(
            CreditPayment.apartado_id == apartado.id,
            CreditPayment.notes != "Anticipo inicial"
        ).all()
        for abono in abonos:
            if abono.payment_method in ['efectivo', 'cash', 'transferencia']:
                abonos_apart_efectivo_count += 1
                abonos_apart_efectivo_bruto += float(abono.amount)
            elif abono.payment_method in ['tarjeta', 'card']:
                abonos_apart_tarjeta_count += 1
                abonos_apart_tarjeta_bruto += float(abono.amount)
    
    # Contar anticipos de pedidos apartados pendientes
    for pedido in pedidos_pendientes:
        pagos_anticipo = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'anticipo'
        ).all()
        for pago in pagos_anticipo:
            if pago.metodo_pago in EFECTIVO_METHODS:
                anticipos_ped_efectivo_count += 1
                anticipos_ped_efectivo_bruto += float(pago.monto)
            elif pago.metodo_pago == TARJETA_METHOD:
                anticipos_ped_tarjeta_count += 1
                anticipos_ped_tarjeta_bruto += float(pago.monto)
    
    # Contar abonos de pedidos apartados pendientes
    for pedido in pedidos_pendientes:
        pagos_abono = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'saldo'
        ).all()
        for pago in pagos_abono:
            if pago.metodo_pago in EFECTIVO_METHODS:
                abonos_ped_efectivo_count += 1
                abonos_ped_efectivo_bruto += float(pago.monto)
            elif pago.metodo_pago == TARJETA_METHOD:
                abonos_ped_tarjeta_count += 1
                abonos_ped_tarjeta_bruto += float(pago.monto)
    
    # Construir la tabla de resumen con subtotales
    # Anticipos de apartado
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de apartado",
        "metodo_pago": "Efectivo",
        "cantidad_operaciones": anticipos_apart_efectivo_count,
        "subtotal": anticipos_apart_efectivo_bruto,
        "total": anticipos_apart_efectivo_bruto
    })
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de apartado",
        "metodo_pago": "Tarjeta",
        "cantidad_operaciones": anticipos_apart_tarjeta_count,
        "subtotal": anticipos_apart_tarjeta_bruto,
        "total": anticipos_apart_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    })
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": anticipos_apart_efectivo_count + anticipos_apart_tarjeta_count,
        "subtotal": anticipos_apart_efectivo_bruto + anticipos_apart_tarjeta_bruto,
        "total": anticipos_apart_efectivo_bruto + (anticipos_apart_tarjeta_bruto * TARJETA_DISCOUNT_RATE)
    })
    
    # Abonos de apartado
    resumen_pagos.append({
        "tipo_movimiento": "Abono de apartado",
        "metodo_pago": "Efectivo",
        "cantidad_operaciones": abonos_apart_efectivo_count,
        "subtotal": abonos_apart_efectivo_bruto,
        "total": abonos_apart_efectivo_bruto
    })
    resumen_pagos.append({
        "tipo_movimiento": "Abono de apartado",
        "metodo_pago": "Tarjeta",
        "cantidad_operaciones": abonos_apart_tarjeta_count,
        "subtotal": abonos_apart_tarjeta_bruto,
        "total": abonos_apart_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    })
    resumen_pagos.append({
        "tipo_movimiento": "Abono de apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": abonos_apart_efectivo_count + abonos_apart_tarjeta_count,
        "subtotal": abonos_apart_efectivo_bruto + abonos_apart_tarjeta_bruto,
        "total": abonos_apart_efectivo_bruto + (abonos_apart_tarjeta_bruto * TARJETA_DISCOUNT_RATE)
    })
    
    # Anticipos de pedido apartado
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de pedido apartado",
        "metodo_pago": "Efectivo",
        "cantidad_operaciones": anticipos_ped_efectivo_count,
        "subtotal": anticipos_ped_efectivo_bruto,
        "total": anticipos_ped_efectivo_bruto
    })
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de pedido apartado",
        "metodo_pago": "Tarjeta",
        "cantidad_operaciones": anticipos_ped_tarjeta_count,
        "subtotal": anticipos_ped_tarjeta_bruto,
        "total": anticipos_ped_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    })
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de pedido apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": anticipos_ped_efectivo_count + anticipos_ped_tarjeta_count,
        "subtotal": anticipos_ped_efectivo_bruto + anticipos_ped_tarjeta_bruto,
        "total": anticipos_ped_efectivo_bruto + (anticipos_ped_tarjeta_bruto * TARJETA_DISCOUNT_RATE)
    })
    
    # Abonos de pedido apartado
    resumen_pagos.append({
        "tipo_movimiento": "Abono de pedido apartado",
        "metodo_pago": "Efectivo",
        "cantidad_operaciones": abonos_ped_efectivo_count,
        "subtotal": abonos_ped_efectivo_bruto,
        "total": abonos_ped_efectivo_bruto
    })
    resumen_pagos.append({
        "tipo_movimiento": "Abono de pedido apartado",
        "metodo_pago": "Tarjeta",
        "cantidad_operaciones": abonos_ped_tarjeta_count,
        "subtotal": abonos_ped_tarjeta_bruto,
        "total": abonos_ped_tarjeta_bruto * TARJETA_DISCOUNT_RATE
    })
    resumen_pagos.append({
        "tipo_movimiento": "Abono de pedido apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": abonos_ped_efectivo_count + abonos_ped_tarjeta_count,
        "subtotal": abonos_ped_efectivo_bruto + abonos_ped_tarjeta_bruto,
        "total": abonos_ped_efectivo_bruto + (abonos_ped_tarjeta_bruto * TARJETA_DISCOUNT_RATE)
    })
    
    return resumen_pagos


def _calculate_payment_totals(pagos: List[Any]) -> Dict[str, float]:
    """
    Calculate efectivo and tarjeta totals from payments.
    
    Wrapper function that calls _calculate_payment_totals_by_method for consistency.
    Mantiene compatibilidad con código existente y elimina duplicación de código.
    
    Args:
        pagos: List of payment objects with metodo_pago attribute (PagoPedido)
        
    Returns:
        Dictionary with 'efectivo' and 'tarjeta' totals (brutos, sin descuento)
    """
    return _calculate_payment_totals_by_method(pagos, 'metodo_pago')


def _calculate_payment_totals_by_method(pagos: List[Any], method_attr: str = 'metodo_pago') -> Dict[str, float]:
    """
    Calculate efectivo and tarjeta totals from payments with flexible attribute name.
    
    Args:
        pagos: List of payment objects
        method_attr: Attribute name for payment method (default: 'metodo_pago')
        
    Returns:
        Dictionary with 'efectivo' and 'tarjeta' totals
    """
    efectivo = sum(
        float(getattr(p, 'monto', 0)) 
        for p in pagos 
        if getattr(p, method_attr, None) in EFECTIVO_METHODS
    )
    tarjeta = sum(
        float(getattr(p, 'monto', 0)) 
        for p in pagos 
        if getattr(p, method_attr, None) == TARJETA_METHOD
    )
    return {'efectivo': efectivo, 'tarjeta': tarjeta}


_MEXICO_TZ = timezone(timedelta(hours=-6))


def _normalize_datetime(value: Optional[datetime]) -> datetime:
    """Return datetime value normalized to UTC, interpreting naive datetimes as Mexico local time."""
    if value is None:
        return datetime.min.replace(tzinfo=tz.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=_MEXICO_TZ)
    return value.astimezone(tz.utc)


def _calculate_net_payment_amount(amount: Any, method: Optional[str]) -> float:
    """Apply tarjeta discount when needed and return float amount."""
    base_amount = float(amount or 0)
    method_normalized = (method or "").lower()
    if method_normalized in EFECTIVO_METHODS or method_normalized == "cash":
        return base_amount
    if method_normalized in (TARJETA_METHOD, "card"):
        return base_amount * TARJETA_DISCOUNT_RATE
    return base_amount


def _build_piezas_por_nombre(resumen_piezas: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Agrupa el resumen de piezas por nombre para métricas agregadas.
    - vendidas: piezas_vendidas
    - entregadas: piezas_liquidadas (apartados/pedidos liquidados)
    """
    vendidas: Dict[str, int] = {}
    entregadas: Dict[str, int] = {}
    
    for pieza in resumen_piezas:
        nombre = (pieza.get("nombre") or "").strip() or "Sin nombre"
        vendidas[nombre] = vendidas.get(nombre, 0) + int(pieza.get("piezas_vendidas") or 0)
        entregadas[nombre] = entregadas.get(nombre, 0) + int(pieza.get("piezas_liquidadas") or 0)
    
    # Ordenar diccionarios para consistencia (alfabético)
    vendidas_ordenadas = dict(sorted(vendidas.items(), key=lambda item: item[0]))
    entregadas_ordenadas = dict(sorted(entregadas.items(), key=lambda item: item[0]))
    
    return {
        "vendidas": vendidas_ordenadas,
        "entregadas": entregadas_ordenadas,
    }


def _build_resumen_piezas(
    db: Session,
    apartados_pendientes: List[Apartado],
    pedidos_pendientes: List[Pedido],
    pedidos_liquidados: List[Pedido],
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> List[dict]:
    """
    Build summary of pieces by product (name, model, quilataje).
    
    Returns:
        List of dictionaries with piece summaries
    """
    resumen_piezas_dict: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    # Procesar VentasContado (nuevo esquema)
    ventas_contado = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime
    ).all()
    
    for venta in ventas_contado:
        items = db.query(ItemVentaContado).filter(ItemVentaContado.venta_id == venta.id).all()
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue
            key = (product.name or "Sin nombre", product.modelo or "N/A", product.quilataje or "N/A")
            if key not in resumen_piezas_dict:
                resumen_piezas_dict[key] = {
                    "nombre": product.name or "Sin nombre",
                    "modelo": product.modelo or "N/A",
                    "quilataje": product.quilataje or "N/A",
                    "talla": product.talla or None,
                    "piezas_vendidas": 0,
                    "piezas_pedidas": 0,
                    "piezas_apartadas": 0,
                    "piezas_liquidadas": 0,
                    "total_piezas": 0,
                }
            resumen_piezas_dict[key]["piezas_vendidas"] += int(item.quantity or 0)

    # Process pending apartados (nuevo esquema)
    for apartado in apartados_pendientes:
        items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue
            key = (product.name or "Sin nombre", product.modelo or "N/A", product.quilataje or "N/A")
            if key not in resumen_piezas_dict:
                resumen_piezas_dict[key] = {
                    "nombre": product.name or "Sin nombre",
                    "modelo": product.modelo or "N/A",
                    "quilataje": product.quilataje or "N/A",
                    "talla": product.talla or None,
                    "piezas_vendidas": 0,
                    "piezas_pedidas": 0,
                    "piezas_apartadas": 0,
                    "piezas_liquidadas": 0,
                    "total_piezas": 0,
                }
            resumen_piezas_dict[key]["piezas_apartadas"] += int(item.quantity or 0)

    # Process liquidated apartados (nuevo esquema)
    apartados_liquidados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.credit_status.in_(['pagado', 'entregado']),
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime
    ).all()
    
    for apartado in apartados_liquidados:
        items = db.query(ItemApartado).filter(ItemApartado.apartado_id == apartado.id).all()
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue
            key = (product.name or "Sin nombre", product.modelo or "N/A", product.quilataje or "N/A")
            if key not in resumen_piezas_dict:
                resumen_piezas_dict[key] = {
                    "nombre": product.name or "Sin nombre",
                    "modelo": product.modelo or "N/A",
                    "quilataje": product.quilataje or "N/A",
                    "talla": product.talla or None,
                    "piezas_vendidas": 0,
                    "piezas_pedidas": 0,
                    "piezas_apartadas": 0,
                    "piezas_liquidadas": 0,
                    "total_piezas": 0,
                }
            resumen_piezas_dict[key]["piezas_liquidadas"] += int(item.quantity or 0)
    
    # Process pending pedidos (solo los creados en el periodo)
    # Nota: pedidos_pendientes contiene pedidos con tipo_pedido='apartado' que están pendientes
    # Estos son pedidos con anticipo, por lo que se suman a piezas_pedidas
    for pedido in pedidos_pendientes:
        # Obtener items del pedido (puede tener múltiples items)
        pedido_items = db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).all()
        
        if pedido_items:
            # Si tiene items, usar los items
            for item in pedido_items:
                # Construir key basado en los datos del item
                nombre = item.nombre or item.modelo or "Sin nombre"
                modelo = item.modelo or "N/A"
                quilataje = item.quilataje or "N/A"
                talla = item.talla or None
                key = (nombre, modelo, quilataje)
                
                if key not in resumen_piezas_dict:
                    resumen_piezas_dict[key] = {
                        "nombre": nombre,
                        "modelo": modelo,
                        "quilataje": quilataje,
                        "talla": talla,
                        "piezas_vendidas": 0,
                        "piezas_pedidas": 0,
                        "piezas_apartadas": 0,
                        "piezas_liquidadas": 0,
                        "total_piezas": 0,
                    }
                resumen_piezas_dict[key]["piezas_pedidas"] += item.cantidad
        else:
            # Fallback: usar producto_pedido_id si no hay items (compatibilidad hacia atrás)
            producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
            if not producto:
                continue
            key = (producto.nombre or producto.modelo or "Sin nombre", producto.modelo or "N/A", producto.quilataje or "N/A")
            if key not in resumen_piezas_dict:
                resumen_piezas_dict[key] = {
                    "nombre": producto.nombre or producto.modelo or "Sin nombre",
                    "modelo": producto.modelo or "N/A",
                    "quilataje": producto.quilataje or "N/A",
                    "talla": producto.talla or None,
                    "piezas_vendidas": 0,
                    "piezas_pedidas": 0,
                    "piezas_apartadas": 0,
                    "piezas_liquidadas": 0,
                    "total_piezas": 0,
                }
            resumen_piezas_dict[key]["piezas_pedidas"] += pedido.cantidad

    # Process liquidated pedidos (pedidos apartados que fueron completamente pagados)
    # Estos pedidos se suman solo a piezas_liquidadas
    for pedido in pedidos_liquidados:
        # Obtener items del pedido (puede tener múltiples items)
        pedido_items = db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).all()
        
        if pedido_items:
            # Si tiene items, usar los items
            for item in pedido_items:
                # Construir key basado en los datos del item
                nombre = item.nombre or item.modelo or "Sin nombre"
                modelo = item.modelo or "N/A"
                quilataje = item.quilataje or "N/A"
                talla = item.talla or None
                key = (nombre, modelo, quilataje)
                
                if key not in resumen_piezas_dict:
                    resumen_piezas_dict[key] = {
                        "nombre": nombre,
                        "modelo": modelo,
                        "quilataje": quilataje,
                        "talla": talla,
                        "piezas_vendidas": 0,
                        "piezas_pedidas": 0,
                        "piezas_apartadas": 0,
                        "piezas_liquidadas": 0,
                        "total_piezas": 0,
                    }
                # Los pedidos liquidados solo se suman a piezas_liquidadas
                resumen_piezas_dict[key]["piezas_liquidadas"] += item.cantidad
        else:
            # Fallback: usar producto_pedido_id si no hay items (compatibilidad hacia atrás)
            producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
            if not producto:
                continue
            key = (producto.nombre or producto.modelo or "Sin nombre", producto.modelo or "N/A", producto.quilataje or "N/A")
            if key not in resumen_piezas_dict:
                resumen_piezas_dict[key] = {
                    "nombre": producto.nombre or producto.modelo or "Sin nombre",
                    "modelo": producto.modelo or "N/A",
                    "quilataje": producto.quilataje or "N/A",
                    "talla": producto.talla or None,
                    "piezas_vendidas": 0,
                    "piezas_pedidas": 0,
                    "piezas_apartadas": 0,
                    "piezas_liquidadas": 0,
                    "total_piezas": 0,
                }
            # Los pedidos liquidados solo se suman a piezas_liquidadas
            resumen_piezas_dict[key]["piezas_liquidadas"] += pedido.cantidad

    # Calculate totals
    for data in resumen_piezas_dict.values():
        data["total_piezas"] = (
            data["piezas_vendidas"]
            + data["piezas_pedidas"]
            + data["piezas_apartadas"]
            + data["piezas_liquidadas"]
        )

    return sorted(
        resumen_piezas_dict.values(),
        key=lambda x: (x["nombre"], x["modelo"], x["quilataje"]),
    )


