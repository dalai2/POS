"""
Service for generating detailed cash cut reports (corte de caja).
This service contains the business logic extracted from routes/reports.py
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Dict, List, Any, Tuple, Optional, TypedDict
from datetime import datetime, date, timezone as tz, timedelta

from app.models.tenant import Tenant
from app.models.user import User
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.payment import Payment
from app.models.credit_payment import CreditPayment
from app.models.producto_pedido import Pedido, PagoPedido, ProductoPedido

# Constants
TARJETA_DISCOUNT_RATE = 0.97  # 3% discount for card payments
EFECTIVO_METHODS = ['efectivo', 'transferencia']
TARJETA_METHOD = 'tarjeta'


# TypedDict definitions for better type safety
class SalesData(TypedDict):
    """Structure for sales data returned by _get_sales_by_payment_date."""
    all_sales: List[Sale]
    ventas_contado_ids: List[int]
    apartados_pendientes: List[Sale]
    apartados_pendientes_ids_payment: List[int]
    apartados_pendientes_ids_credit: List[int]


class PedidosData(TypedDict):
    """Structure for pedidos data returned by _get_pedidos_by_payment_date."""
    pedidos_liquidados: List[Pedido]
    pedidos_liquidados_ids: List[int]
    pedidos_contado: List[Pedido]
    pedidos_contado_ids: List[int]
    pedidos_pendientes: List[Pedido]
    pedidos_pendientes_ids_payment: List[int]
    pedidos_pendientes_ids_credit: List[int]


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
    # Note: After running fix_all_timestamps_timezone.sql, dates are already in Mexico time
    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=tz.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=tz.utc)
    
    # Get base data
    sales_data = _get_sales_by_payment_date(db, tenant, start_datetime, end_datetime)
    pedidos_data = _get_pedidos_by_payment_date(db, tenant, start_datetime, end_datetime)
    
    # Initialize counters
    counters = _initialize_counters()
    
    # Process sales for statistics
    _process_sales_for_stats(
        db, sales_data['all_sales'], counters, sales_data['ventas_contado_ids']
    )
    
    # Process pedidos de contado
    _process_pedidos_contado(
        db, pedidos_data['pedidos_contado'], counters, pedidos_data['pedidos_contado_ids']
    )
    
    # Process pedidos liquidados
    _process_pedidos_liquidados(
        db, pedidos_data['pedidos_liquidados'], counters, pedidos_data['pedidos_liquidados_ids']
    )
    
    # Process apartados pendientes
    _process_apartados_pendientes(
        db, sales_data['apartados_pendientes'], counters,
        sales_data['apartados_pendientes_ids_payment'],
        sales_data['apartados_pendientes_ids_credit']
    )
    
    # Process pedidos pendientes
    _process_pedidos_pendientes(
        db, pedidos_data['pedidos_pendientes'], counters,
        pedidos_data['pedidos_pendientes_ids_payment'],
        pedidos_data['pedidos_pendientes_ids_credit']
    )
    
    # Calculate main metrics
    ventas_activas = _calculate_ventas_activas(counters)
    ventas_liquidacion = _calculate_ventas_liquidacion(counters)
    ventas_pasivas = _calculate_ventas_pasivas(
        db, tenant, start_datetime, end_datetime, counters
    )
    cuentas_por_cobrar = _calculate_cuentas_por_cobrar(
        sales_data['apartados_pendientes'], pedidos_data['pedidos_pendientes']
    )
    
    # Build vendor stats
    vendor_stats = _build_vendor_stats(
        db, sales_data['all_sales'], pedidos_data['pedidos_contado'],
        pedidos_data['pedidos_liquidados'], sales_data['apartados_pendientes'],
        pedidos_data['pedidos_pendientes'], start_datetime, end_datetime, tenant
    )
    
    # Build additional data
    dashboard = _build_dashboard_data(
        counters, 
        ventas_liquidacion,
        pedidos_data['pedidos_contado'],
        pedidos_data['pedidos_liquidados']
    )
    historiales = _build_historiales(
        db, tenant, start_datetime, end_datetime, counters,
        pedidos_data['pedidos_liquidados'], pedidos_data['pedidos_pendientes']
    )
    sales_details = _build_sales_details(
        db, sales_data['all_sales'], pedidos_data['pedidos_contado']
    )
    additional_metrics = _calculate_additional_metrics(
        db, tenant, start_datetime, end_datetime
    )
    
    # Build resumen piezas
    resumen_piezas = _build_resumen_piezas(
        db,
        sales_data['all_sales'],
        sales_data['apartados_pendientes'],
        pedidos_data['pedidos_pendientes'],
        pedidos_data['pedidos_liquidados']
    )
    total_piezas_por_nombre = _build_total_piezas_por_nombre_sin_liquidadas(resumen_piezas)
    
    # Build daily summaries
    daily_summaries = _build_daily_summaries(sales_data['all_sales'])
    
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
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
        "total_piezas_por_nombre_sin_liquidadas": total_piezas_por_nombre,
        "dashboard": dashboard,
        "vendedores": list(vendor_stats.values()),
        "daily_summaries": daily_summaries,
        "sales_details": sales_details,
        "historial_apartados": historiales['apartados'],
        "historial_pedidos": historiales['pedidos'],
        "historial_abonos_apartados": historiales['abonos_apartados'],
        "historial_abonos_pedidos": historiales['abonos_pedidos'],
        "apartados_cancelados_vencidos": historiales['apartados_cancelados_vencidos'],
        "pedidos_cancelados_vencidos": historiales['pedidos_cancelados_vencidos'],
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
    # Get ventas de contado with payments in the period
    # Note: Payment doesn't have created_at, so we use Sale.created_at since payments are created with the sale
    ventas_contado_ids = db.query(Sale.id).join(Payment).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "contado",
        Sale.return_of_id == None,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).distinct()
    
    # Get apartados that are pagado/entregado with payments in the period
    # For Payment (initial payment), use Sale.created_at
    apartados_payment_ids = db.query(Sale.id).join(Payment).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.credit_status.in_(['pagado', 'entregado']),
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).distinct()
    
    # For CreditPayment (subsequent payments), use CreditPayment.created_at
    apartados_credit_ids = db.query(Sale.id).join(CreditPayment).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.credit_status.in_(['pagado', 'entregado']),
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).distinct()
    
    # Combine all sales IDs
    # Convert queries to lists of IDs
    ventas_contado_ids_list = [id for id, in ventas_contado_ids.all()]
    apartados_payment_ids_list = [id for id, in apartados_payment_ids.all()]
    apartados_credit_ids_list = [id for id, in apartados_credit_ids.all()]
    all_sale_ids = set(ventas_contado_ids_list) | set(apartados_payment_ids_list) | set(apartados_credit_ids_list)
    
    # Get all sales
    all_sales = db.query(Sale).filter(Sale.id.in_(all_sale_ids)).all() if all_sale_ids else []
    
    # Get apartados pendientes (filtered by payment date for anticipos)
    # For Payment (initial payment), use Sale.created_at
    apartados_pendientes_ids_payment = db.query(Sale.id).join(Payment).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.credit_status.in_(['pendiente', 'vencido']),
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).distinct()
    
    # For CreditPayment (subsequent payments), use CreditPayment.created_at
    apartados_pendientes_ids_credit = db.query(Sale.id).join(CreditPayment).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.credit_status.in_(['pendiente', 'vencido']),
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).distinct()
    
    apartados_pendientes_ids_payment_list = [id for id, in apartados_pendientes_ids_payment.all()]
    apartados_pendientes_ids_credit_list = [id for id, in apartados_pendientes_ids_credit.all()]
    apartados_pendientes_ids = set(apartados_pendientes_ids_payment_list) | set(apartados_pendientes_ids_credit_list)
    apartados_pendientes = db.query(Sale).filter(Sale.id.in_(apartados_pendientes_ids)).all() if apartados_pendientes_ids else []
    
    return {
        'all_sales': all_sales,
        'ventas_contado_ids': ventas_contado_ids_list,
        'apartados_pendientes': apartados_pendientes,
        'apartados_pendientes_ids_payment': apartados_pendientes_ids_payment_list,
        'apartados_pendientes_ids_credit': apartados_pendientes_ids_credit_list,
    }


def _get_pedidos_by_payment_date(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> PedidosData:
    """Get pedidos filtered by payment date within the period."""
    # Get pedidos liquidados (apartados) with payments in the period
    pedidos_liquidados_ids = db.query(Pedido.id).join(PagoPedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado.in_(['pagado', 'entregado']),
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).distinct()
    
    pedidos_liquidados_ids_list = [id for id, in pedidos_liquidados_ids.all()]
    pedidos_liquidados = db.query(Pedido).filter(
        Pedido.id.in_(pedidos_liquidados_ids_list)
    ).all() if pedidos_liquidados_ids_list else []
    
    # Get pedidos de contado with payments in the period
    pedidos_contado_ids = db.query(Pedido.id).join(PagoPedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'contado',
        Pedido.estado == 'pagado',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).distinct()
    
    pedidos_contado_ids_list = [id for id, in pedidos_contado_ids.all()]
    pedidos_contado = db.query(Pedido).filter(
        Pedido.id.in_(pedidos_contado_ids_list)
    ).all() if pedidos_contado_ids_list else []
    
    # Get pedidos pendientes (filtered by payment date)
    pedidos_pendientes_ids_payment = db.query(Pedido.id).join(PagoPedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        ~Pedido.estado.in_(['pagado', 'entregado', 'cancelado']),
        PagoPedido.tipo_pago == 'anticipo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).distinct()
    
    pedidos_pendientes_ids_credit = db.query(Pedido.id).join(PagoPedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        ~Pedido.estado.in_(['pagado', 'entregado', 'cancelado']),
        PagoPedido.tipo_pago == 'saldo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).distinct()
    
    pedidos_pendientes_ids_payment_list = [id for id, in pedidos_pendientes_ids_payment.all()]
    pedidos_pendientes_ids_credit_list = [id for id, in pedidos_pendientes_ids_credit.all()]
    pedidos_pendientes_ids = set(pedidos_pendientes_ids_payment_list) | set(pedidos_pendientes_ids_credit_list)
    pedidos_pendientes = db.query(Pedido).filter(
        Pedido.id.in_(pedidos_pendientes_ids)
    ).all() if pedidos_pendientes_ids else []
    
    return {
        'pedidos_liquidados': pedidos_liquidados,
        'pedidos_liquidados_ids': pedidos_liquidados_ids_list,
        'pedidos_contado': pedidos_contado,
        'pedidos_contado_ids': pedidos_contado_ids_list,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_pendientes_ids_payment': pedidos_pendientes_ids_payment_list,
        'pedidos_pendientes_ids_credit': pedidos_pendientes_ids_credit_list,
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
    }


def _process_sales_for_stats(
    db: Session,
    all_sales: List[Sale],
    counters: Dict[str, Any],
    ventas_contado_ids: Any
) -> None:
    """Process sales to update counters and statistics."""
    if not all_sales:
        return
    
    # Optimize: Load all related data in batch queries
    all_sale_ids = [s.id for s in all_sales]
    
    # Load all sale items
    all_sale_items = db.query(SaleItem).filter(SaleItem.sale_id.in_(all_sale_ids)).all()
    items_by_sale = {}
    for item in all_sale_items:
        if item.sale_id not in items_by_sale:
            items_by_sale[item.sale_id] = []
        items_by_sale[item.sale_id].append(item)
    
    # Load all products
    product_ids = list(set(item.product_id for item in all_sale_items if item.product_id))
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()} if product_ids else {}
    
    # Load all payments
    all_payments = db.query(Payment).filter(Payment.sale_id.in_(all_sale_ids)).all()
    payments_by_sale = {}
    for payment in all_payments:
        if payment.sale_id not in payments_by_sale:
            payments_by_sale[payment.sale_id] = []
        payments_by_sale[payment.sale_id].append(payment)
    
    # Load all credit payments
    all_credit_payments = db.query(CreditPayment).filter(CreditPayment.sale_id.in_(all_sale_ids)).all()
    credit_payments_by_sale = {}
    for credit_payment in all_credit_payments:
        if credit_payment.sale_id not in credit_payments_by_sale:
            credit_payments_by_sale[credit_payment.sale_id] = []
        credit_payments_by_sale[credit_payment.sale_id].append(credit_payment)
    
    # Process each sale
    for sale in all_sales:
        sale_items = items_by_sale.get(sale.id, [])
        payments_contado = payments_by_sale.get(sale.id, [])
        pagos_apartado = payments_by_sale.get(sale.id, [])
        abonos_apartado = credit_payments_by_sale.get(sale.id, [])
        
        if sale.tipo_venta == "contado":
            counters['contado_count'] += 1
            counters['total_contado'] += float(sale.total)
            
            # Calculate cost from sold products
            for item in sale_items:
                counters['num_piezas_vendidas'] += item.quantity
                if item.product_id and item.product_id in products:
                    product = products[item.product_id]
                    if product.cost_price:
                        counters['costo_ventas_contado'] += float(product.cost_price) * item.quantity
            
            # Calculate cash and card payments
            counters['total_efectivo_contado'] += sum(float(p.amount) for p in payments_contado if p.method in ['efectivo', 'cash', 'transferencia'])
            counters['total_tarjeta_contado'] += sum(float(p.amount) for p in payments_contado if p.method in ['tarjeta', 'card'])
        else:  # credito (pagado o entregado)
            counters['ventas_credito_count'] += 1
            counters['ventas_credito_total'] += float(sale.total)
            counters['credito_ventas'] += float(sale.total)
            
            # Calculate payments with 3% discount for cards
            efectivo_apartado = sum(float(p.amount) for p in pagos_apartado if p.method in ['efectivo', 'cash', 'transferencia'])
            tarjeta_apartado = sum(float(p.amount) for p in pagos_apartado if p.method in ['tarjeta', 'card'])
            
            efectivo_abonos = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            tarjeta_abonos = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['tarjeta', 'card'])
            
            total_credito_neto = efectivo_apartado + (tarjeta_apartado * TARJETA_DISCOUNT_RATE) + efectivo_abonos + (tarjeta_abonos * TARJETA_DISCOUNT_RATE)
            counters['total_credito'] += total_credito_neto
            
            # Calculate cost of liquidated apartados
            for item in sale_items:
                counters['num_piezas_apartadas_pagadas'] += item.quantity
                counters['num_piezas_entregadas'] += item.quantity
                if item.product_id and item.product_id in products:
                    product = products[item.product_id]
                    if product.cost_price:
                        counters['costo_apartados_liquidados'] += float(product.cost_price) * item.quantity
        
        counters['total_vendido'] += float(sale.total)
        if sale.total_cost:
            counters['costo_total'] += float(sale.total_cost)
        if sale.utilidad:
            counters['utilidad_total'] += float(sale.utilidad)
        
        counters['piezas_vendidas'] += 1


def _process_pedidos_contado(
    db: Session,
    pedidos_contado: List[Pedido],
    counters: Dict[str, Any],
    pedidos_contado_ids: Any
) -> None:
    """Process cash orders (pedidos de contado) for active sales."""
    for pedido in pedidos_contado:
        pagos_pedido_contado = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id
        ).all()
        
        efectivo_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago in ['efectivo', 'transferencia'])
        tarjeta_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago == 'tarjeta')
        
        counters['total_efectivo_contado'] += efectivo_pedido
        counters['total_tarjeta_contado'] += tarjeta_pedido
        
        # Get product to calculate cost
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        
        if producto and producto.cost_price:
            counters['costo_ventas_contado'] += float(producto.cost_price) * pedido.cantidad
        
        counters['num_piezas_vendidas'] += pedido.cantidad
        counters['total_contado'] += float(pedido.total)
        counters['contado_count'] += 1


def _process_pedidos_liquidados(
    db: Session,
    pedidos_liquidados: List[Pedido],
    counters: Dict[str, Any],
    pedidos_liquidados_ids: Any
) -> None:
    """Process liquidated orders (pedidos liquidados) for liquidation sales."""
    counters['pedidos_liquidados_count'] = len(pedidos_liquidados)
    
    for pedido in pedidos_liquidados:
        pagos_pedido_liq = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        pagos_liq_totals = _calculate_payment_totals(pagos_pedido_liq)
        efectivo_pedido_liq = pagos_liq_totals['efectivo']
        tarjeta_pedido_liq = pagos_liq_totals['tarjeta']
        total_pedido_neto = efectivo_pedido_liq + (tarjeta_pedido_liq * TARJETA_DISCOUNT_RATE)
        
        counters['pedidos_liquidados_total'] += total_pedido_neto
        counters['pedidos_total'] += float(pedido.total)
        counters['pedidos_anticipos'] += float(pedido.anticipo_pagado)
        counters['pedidos_saldo'] += float(pedido.saldo_pendiente)
        
        # Get product and calculate cost
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        if producto and producto.cost_price:
            counters['costo_pedidos_liquidados'] += float(producto.cost_price) * pedido.cantidad
        
        counters['num_piezas_pedidos_pagados'] += pedido.cantidad
        counters['num_piezas_pedidos_apartados_liquidados'] += pedido.cantidad
        counters['num_piezas_entregadas'] += pedido.cantidad


def _process_apartados_pendientes(
    db: Session,
    apartados_pendientes: List[Sale],
    counters: Dict[str, Any],
    apartados_pendientes_ids_payment: Any,
    apartados_pendientes_ids_credit: Any
) -> None:
    """Process pending apartados (apartados pendientes) for passive sales."""
    for apartado in apartados_pendientes:
        # Get initial down payment (Payment)
        pagos_iniciales = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
        anticipo_efectivo = sum(float(p.amount) for p in pagos_iniciales if p.method in ['efectivo', 'cash', 'transferencia'])
        anticipo_tarjeta = sum(float(p.amount) for p in pagos_iniciales if p.method in ['tarjeta', 'card'])
        anticipo_inicial = anticipo_efectivo + (anticipo_tarjeta * TARJETA_DISCOUNT_RATE)
        
        counters['apartados_pendientes_anticipos'] += anticipo_inicial
        counters['anticipos_apartados_total_monto'] += anticipo_inicial
        counters['anticipos_apartados_count'] += len(pagos_iniciales)
        counters['anticipos_apartados_efectivo_monto'] += anticipo_efectivo
        counters['anticipos_apartados_efectivo_count'] += sum(1 for p in pagos_iniciales if p.method in ['efectivo', 'cash', 'transferencia'])
        counters['anticipos_apartados_tarjeta_bruto'] += anticipo_tarjeta
        counters['anticipos_apartados_tarjeta_neto'] += anticipo_tarjeta * TARJETA_DISCOUNT_RATE
        counters['anticipos_apartados_tarjeta_count'] += sum(1 for p in pagos_iniciales if p.method in ['tarjeta', 'card'])
        
        # Get additional payments (CreditPayment)
        pagos_posteriores = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
        abonos_efectivo = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        abonos_tarjeta = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['tarjeta', 'card'])
        abonos_posteriores = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
        
        counters['apartados_pendientes_abonos_adicionales'] += abonos_posteriores
        counters['abonos_apartados_total_neto'] += abonos_posteriores
        counters['abonos_apartados_count'] += len(pagos_posteriores)
        counters['abonos_apartados_efectivo_monto'] += abonos_efectivo
        counters['abonos_apartados_efectivo_count'] += sum(1 for p in pagos_posteriores if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        counters['abonos_apartados_tarjeta_bruto'] += abonos_tarjeta
        counters['abonos_apartados_tarjeta_neto'] += abonos_tarjeta * TARJETA_DISCOUNT_RATE
        counters['abonos_apartados_tarjeta_count'] += sum(1 for p in pagos_posteriores if p.payment_method in ['tarjeta', 'card'])


def _process_pedidos_pendientes(
    db: Session,
    pedidos_pendientes: List[Pedido],
    counters: Dict[str, Any],
    pedidos_pendientes_ids_payment: Any,
    pedidos_pendientes_ids_credit: Any
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
        counters['abonos_pedidos_total_neto'] += abonos_posteriores
        counters['abonos_pedidos_count'] += len(pagos_pedido_abonos)
        counters['abonos_pedidos_efectivo_monto'] += abonos_efectivo
        counters['abonos_pedidos_efectivo_count'] += sum(1 for p in pagos_pedido_abonos if getattr(p, 'metodo_pago', None) in EFECTIVO_METHODS)
        counters['abonos_pedidos_tarjeta_bruto'] += abonos_tarjeta
        counters['abonos_pedidos_tarjeta_neto'] += abonos_tarjeta * TARJETA_DISCOUNT_RATE
        counters['abonos_pedidos_tarjeta_count'] += sum(1 for p in pagos_pedido_abonos if getattr(p, 'metodo_pago', None) == TARJETA_METHOD)


def _calculate_ventas_activas(counters: Dict[str, Any]) -> VentasActivas:
    """Calculate active sales metrics."""
    total_tarjeta_neto = counters['total_tarjeta_contado'] * TARJETA_DISCOUNT_RATE
    total_ventas_activas_neto = counters['total_efectivo_contado'] + total_tarjeta_neto
    utilidad_ventas_activas = total_ventas_activas_neto - counters['costo_ventas_contado']
    
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
    """Calculate passive sales metrics (anticipos and abonos)."""
    # Anticipos de apartados del día (filtered by Sale.created_at since Payment doesn't have created_at)
    anticipos_apartados_dia = db.query(Payment).join(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime
    ).all()
    
    anticipos_apartados_dia_total = 0.0
    for pago in anticipos_apartados_dia:
        amount = float(pago.amount or 0)
        if pago.method in ['tarjeta', 'card']:
            anticipos_apartados_dia_total += amount * TARJETA_DISCOUNT_RATE
        else:
            anticipos_apartados_dia_total += amount
    
    # Abonos de apartados del día
    abonos_apartados_dia = db.query(CreditPayment).join(Sale).filter(
        Sale.tenant_id == tenant.id,
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).all()
    
    abonos_apartados_dia_total = 0.0
    for abono in abonos_apartados_dia:
        amount = float(abono.amount or 0)
        if abono.payment_method in ['tarjeta', 'card']:
            abonos_apartados_dia_total += amount * TARJETA_DISCOUNT_RATE
        else:
            abonos_apartados_dia_total += amount
    
    # Anticipos de pedidos apartados del día
    anticipos_pedidos_dia = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        PagoPedido.tipo_pago == 'anticipo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).all()
    
    anticipos_pedidos_dia_total = 0.0
    for pago in anticipos_pedidos_dia:
        amount = float(pago.monto or 0)
        if pago.metodo_pago == TARJETA_METHOD:
            anticipos_pedidos_dia_total += amount * TARJETA_DISCOUNT_RATE
        else:
            anticipos_pedidos_dia_total += amount
    
    # Abonos de pedidos apartados del día
    abonos_pedidos_dia = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        PagoPedido.tipo_pago == 'saldo',
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    ).all()
    
    abonos_pedidos_dia_total = 0.0
    for abono in abonos_pedidos_dia:
        amount = float(abono.monto or 0)
        if abono.metodo_pago == TARJETA_METHOD:
            abonos_pedidos_dia_total += amount * TARJETA_DISCOUNT_RATE
        else:
            abonos_pedidos_dia_total += amount
    
    ventas_pasivas_total = (
        anticipos_apartados_dia_total +
        abonos_apartados_dia_total +
        anticipos_pedidos_dia_total +
        abonos_pedidos_dia_total
    )
    
    return {'total': ventas_pasivas_total}


def _calculate_cuentas_por_cobrar(
    apartados_pendientes: List[Sale],
    pedidos_pendientes: List[Pedido]
) -> float:
    """Calculate accounts receivable (cuentas por cobrar)."""
    cuentas_por_cobrar = 0.0
    for apartado in apartados_pendientes:
        saldo = float(apartado.total) - float(apartado.amount_paid or 0)
        cuentas_por_cobrar += saldo
    for pedido in pedidos_pendientes:
        cuentas_por_cobrar += float(pedido.saldo_pendiente)
    return cuentas_por_cobrar


def _build_vendor_stats(
    db: Session,
    all_sales: List[Sale],
    pedidos_contado: List[Pedido],
    pedidos_liquidados: List[Pedido],
    apartados_pendientes: List[Sale],
    pedidos_pendientes: List[Pedido],
    start_datetime: datetime,
    end_datetime: datetime,
    tenant: Tenant
) -> Dict[int, Dict[str, Any]]:
    """Build vendor statistics."""
    vendor_stats = {}
    
    # Process sales
    for sale in all_sales:
        vendedor_id = sale.vendedor_id or 0
        vendedor = "Mostrador"
        if sale.vendedor_id:
            vendor = db.query(User).filter(User.id == sale.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        if vendedor_id not in vendor_stats:
            vendor_stats[vendedor_id] = _init_vendor_stat(vendedor_id, vendedor)
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        
        payments_vendor = db.query(Payment).filter(Payment.sale_id == sale.id).all()
        efectivo_vendor = sum(float(p.amount) for p in payments_vendor if p.method in ['efectivo', 'cash', 'transferencia'])
        tarjeta_vendor = sum(float(p.amount) for p in payments_vendor if p.method in ['tarjeta', 'card'])
        
        if sale.tipo_venta == "contado":
            vendor_stats[vendedor_id]["contado_count"] += 1
            vendor_stats[vendedor_id]["total_contado"] += float(sale.total)
            vendor_stats[vendedor_id]["total_efectivo_contado"] += efectivo_vendor
            vendor_stats[vendedor_id]["total_tarjeta_contado"] += tarjeta_vendor
            vendor_stats[vendedor_id]["total_tarjeta_neto"] += tarjeta_vendor * TARJETA_DISCOUNT_RATE
            vendor_stats[vendedor_id]["ventas_total_activa"] += efectivo_vendor + (tarjeta_vendor * TARJETA_DISCOUNT_RATE)
        else:
            vendor_stats[vendedor_id]["credito_count"] += 1
            vendor_stats[vendedor_id]["total_credito"] += float(sale.total)
        
        vendor_stats[vendedor_id]["total_profit"] += float(sale.utilidad or 0)
    
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
        if apartado.vendedor_id:
            if apartado.vendedor_id not in vendor_stats:
                vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
                vendedor = vendor.email if vendor else "Unknown"
                vendor_stats[apartado.vendedor_id] = _init_vendor_stat(apartado.vendedor_id, vendedor)
            
            pagos_iniciales = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
            anticipo_efectivo = sum(float(p.amount) for p in pagos_iniciales if p.method in ['efectivo', 'cash', 'transferencia'])
            anticipo_tarjeta = sum(float(p.amount) for p in pagos_iniciales if p.method in ['tarjeta', 'card'])
            anticipo_neto = anticipo_efectivo + (anticipo_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[apartado.vendedor_id]["anticipos_apartados"] += anticipo_neto
            vendor_stats[apartado.vendedor_id]["venta_total_pasiva"] += anticipo_neto
            
            pagos_posteriores = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
            abonos_efectivo = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            abonos_tarjeta = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['tarjeta', 'card'])
            abonos_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[apartado.vendedor_id]["abonos_apartados"] += abonos_neto
            vendor_stats[apartado.vendedor_id]["venta_total_pasiva"] += abonos_neto
            vendor_stats[apartado.vendedor_id]["cuentas_por_cobrar"] += float(apartado.total) - float(apartado.amount_paid or 0)
    
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
            
            abonos_pagos = [p for p in pagos_todos if p.tipo_pago == 'saldo']
            abonos_totals = _calculate_payment_totals(abonos_pagos)
            abonos_efectivo = abonos_totals['efectivo']
            abonos_tarjeta = abonos_totals['tarjeta']
            abonos_neto = abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
            
            vendor_stats[pedido.user_id]["abonos_pedidos"] += abonos_neto
            vendor_stats[pedido.user_id]["venta_total_pasiva"] += abonos_neto
            vendor_stats[pedido.user_id]["cuentas_por_cobrar"] += float(pedido.saldo_pendiente)
    
    # Calculate productos liquidados (simplified - full implementation would check payment dates)
    apartados_pagados = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.credit_status == "pagado"
    ).all()
    
    for apartado in apartados_pagados:
        pagos = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
        abonos = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
        
        fechas = []
        if pagos:
            fecha_apartado = apartado.created_at
            if fecha_apartado.tzinfo is None:
                fecha_apartado = fecha_apartado.replace(tzinfo=tz.utc)
            fechas.append(fecha_apartado)
        if abonos:
            for a in abonos:
                if a.created_at.tzinfo is None:
                    fechas.append(a.created_at.replace(tzinfo=tz.utc))
                else:
                    fechas.append(a.created_at)
        
        if not fechas:
            continue
        
        fecha_ultimo_pago = max(fechas)
        
        if fecha_ultimo_pago >= start_datetime and fecha_ultimo_pago <= end_datetime:
            if apartado.vendedor_id:
                if apartado.vendedor_id not in vendor_stats:
                    vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
                    vendedor = vendor.email if vendor else "Unknown"
                    vendor_stats[apartado.vendedor_id] = _init_vendor_stat(apartado.vendedor_id, vendedor)
                
                if abonos:
                    ultimo_abono = max(abonos, key=lambda a: a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=tz.utc))
                    vendor_stats[apartado.vendedor_id]["productos_liquidados"] += float(ultimo_abono.amount)
                elif pagos:
                    ultimo_pago = max(pagos, key=lambda p: p.created_at if p.created_at.tzinfo else p.created_at.replace(tzinfo=tz.utc))
                    vendor_stats[apartado.vendedor_id]["productos_liquidados"] += float(ultimo_pago.amount)
    
    pedidos_pagados = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado == 'pagado'
    ).all()
    
    for pedido in pedidos_pagados:
        pagos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        
        if not pagos:
            continue
        
        fechas_pagos = []
        for p in pagos:
            if p.created_at.tzinfo is None:
                fechas_pagos.append(p.created_at.replace(tzinfo=tz.utc))
            else:
                fechas_pagos.append(p.created_at)
        
        fecha_ultimo_pago = max(fechas_pagos)
        
        if fecha_ultimo_pago >= start_datetime and fecha_ultimo_pago <= end_datetime:
            if pedido.user_id:
                if pedido.user_id not in vendor_stats:
                    user = db.query(User).filter(User.id == pedido.user_id).first()
                    vendedor = user.email if user else "Unknown"
                    vendor_stats[pedido.user_id] = _init_vendor_stat(pedido.user_id, vendedor)
                
                ultimo_pago_pedido = max(pagos, key=lambda p: p.created_at if p.created_at.tzinfo else p.created_at.replace(tzinfo=tz.utc))
                vendor_stats[pedido.user_id]["productos_liquidados"] += float(ultimo_pago_pedido.monto)
    
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
        "productos_liquidados": 0.0
    }


def _build_dashboard_data(
    counters: Dict[str, Any],
    ventas_liquidacion: Dict[str, Any],
    pedidos_contado: List[Pedido],
    pedidos_liquidados: List[Pedido]
) -> Dict[str, Any]:
    """Build dashboard data structure."""
    # Calculate pedidos_contado totals
    pedidos_contado_total = sum(float(p.total) for p in pedidos_contado)
    pedidos_contado_count = len(pedidos_contado)
    
    # Calculate liquidaciones
    liquidaciones_apartados_monto = ventas_liquidacion.get('total', 0.0) - sum(float(p.total) for p in pedidos_liquidados)
    liquidaciones_apartados_count = ventas_liquidacion.get('count', 0) - len(pedidos_liquidados)
    liquidaciones_pedidos_monto = sum(float(p.total) for p in pedidos_liquidados)
    liquidaciones_pedidos_count = len(pedidos_liquidados)
    
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
    # Counts would need to be calculated from actual vencidos, but using 0 for now
    vencimientos_apartados_count = 0
    vencimientos_pedidos_count = 0
    vencimientos_total_count = 0
    
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
    
    # Historial de apartados activos
    apartados_activos = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito",
        Sale.return_of_id == None,
        ~Sale.credit_status.in_(['cancelado', 'vencido'])
    ).order_by(Sale.created_at.desc()).all()
    
    for apartado in apartados_activos:
        vendedor = "Unknown"
        if apartado.vendedor_id:
            vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        saldo = float(apartado.total) - float(apartado.amount_paid or 0)
        
        historial_apartados.append({
            "id": apartado.id,
            "fecha": apartado.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": apartado.customer_name or "Sin nombre",
            "total": float(apartado.total),
            "anticipo": float(apartado.amount_paid or 0),
            "saldo": saldo,
            "estado": apartado.credit_status or "pendiente",
            "vendedor": vendedor
        })
    
    # Apartados cancelados y vencidos
    apartados_cancelados_vencidos_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito",
        Sale.return_of_id == None,
        Sale.credit_status.in_(['cancelado', 'vencido'])
    ).order_by(Sale.created_at.desc()).all()
    
    for apartado in apartados_cancelados_vencidos_query:
        vendedor = "Unknown"
        if apartado.vendedor_id:
            vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        saldo = float(apartado.total) - float(apartado.amount_paid or 0)
        motivo = "Vencido" if apartado.credit_status == "vencido" else "Cancelado"
        
        pagos_apartado = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
        pagos_efectivo = sum(float(p.amount) for p in pagos_apartado if p.method in ['efectivo', 'cash', 'transferencia'])
        pagos_tarjeta = sum(float(p.amount) for p in pagos_apartado if p.method in ['tarjeta', 'card'])
        
        abonos_apartado = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
        abonos_efectivo = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        abonos_tarjeta = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['tarjeta', 'card'])
        
        total_pagado_neto = pagos_efectivo + (pagos_tarjeta * TARJETA_DISCOUNT_RATE) + abonos_efectivo + (abonos_tarjeta * TARJETA_DISCOUNT_RATE)
        
        sale_items = db.query(SaleItem).filter(SaleItem.sale_id == apartado.id).all()
        piezas_apartado = sum(item.quantity for item in sale_items)
        
        if apartado.credit_status == "cancelado":
            counters['reembolso_apartados_cancelados'] += total_pagado_neto
            counters['cancelaciones_apartados_monto'] += total_pagado_neto
            counters['cancelaciones_apartados_count'] += 1
            counters['piezas_canceladas_apartados'] += piezas_apartado
        elif apartado.credit_status == "vencido":
            counters['saldo_vencido_apartados'] += total_pagado_neto
            counters['piezas_vencidas_apartados'] += piezas_apartado
        
        apartados_cancelados_vencidos.append({
            "id": apartado.id,
            "fecha": apartado.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": apartado.customer_name or "Sin nombre",
            "total": float(apartado.total),
            "anticipo": float(apartado.amount_paid or 0),
            "saldo": saldo,
            "estado": apartado.credit_status,
            "vendedor": vendedor,
            "motivo": motivo
        })
    
    # Historial de abonos de apartados
    todos_abonos_apartados = db.query(CreditPayment).join(Sale).filter(
        Sale.tenant_id == tenant.id,
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).order_by(CreditPayment.created_at.desc()).all()
    
    for abono in todos_abonos_apartados:
        sale = db.query(Sale).filter(Sale.id == abono.sale_id).first()
        vendedor = "Unknown"
        if abono.user_id:
            vendor = db.query(User).filter(User.id == abono.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        historial_abonos_apartados.append({
            "id": abono.id,
            "fecha": abono.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": sale.customer_name if sale else "Desconocido",
            "monto": float(abono.amount),
            "metodo_pago": abono.payment_method,
            "vendedor": vendedor
        })
    
    # Historial de abonos de pedidos
    todos_abonos_pedidos = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime,
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
            counters['saldo_vencido_pedidos'] += total_pagado_neto
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
    all_sales: List[Sale],
    pedidos_contado: List[Pedido]
) -> List[Dict[str, Any]]:
    """Build sales details list."""
    sales_details = []
    
    for sale in all_sales:
        vendedor = "Mostrador"
        if sale.vendedor_id:
            vendor = db.query(User).filter(User.id == sale.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        payments = db.query(Payment).filter(Payment.sale_id == sale.id).all()
        efectivo_amount = sum(float(p.amount) for p in payments if p.method in ['efectivo', 'cash', 'transferencia'])
        tarjeta_amount = sum(float(p.amount) for p in payments if p.method in ['tarjeta', 'card'])
        
        sales_details.append({
            "id": sale.id,
            "fecha": sale.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": sale.customer_name or "Mostrador",
            "piezas": 1,  # Should be calculated from sale items
            "total": float(sale.total),
            "estado": "Pagada" if sale.tipo_venta == "contado" else "Crédito",
            "tipo": sale.tipo_venta,
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


def _calculate_additional_metrics(
    db: Session,
    tenant: Tenant,
    start_datetime: datetime,
    end_datetime: datetime
) -> Dict[str, int]:
    """Calculate additional metrics."""
    num_solicitudes_apartado = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito"
    ).count()
    
    num_pedidos_hechos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).count()
    
    num_apartados_vencidos = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito",
        Sale.credit_status == "vencido"
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
    
    num_cancelaciones += db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.credit_status == "cancelado"
    ).count()
    
    num_abonos_apartados = db.query(CreditPayment).join(Sale).filter(
        Sale.tenant_id == tenant.id,
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).count()
    
    num_abonos_pedidos = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime,
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


def _build_daily_summaries(all_sales: List[Sale]) -> List[Dict[str, Any]]:
    """Build daily summaries."""
    daily_stats = {}
    
    for sale in all_sales:
        sale_date = sale.created_at.date().isoformat()
        if sale_date not in daily_stats:
            daily_stats[sale_date] = {
                "fecha": sale_date,
                "costo": 0.0,
                "venta": 0.0,
                "utilidad": 0.0
            }
        
        if sale.total_cost:
            daily_stats[sale_date]["costo"] += float(sale.total_cost)
        daily_stats[sale_date]["venta"] += float(sale.total)
        daily_stats[sale_date]["utilidad"] += float(sale.utilidad or 0)
    
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
    
    # Contar ventas de contado
    ventas_contado_efectivo_count = 0
    ventas_contado_efectivo_bruto = 0.0
    ventas_contado_tarjeta_count = 0
    ventas_contado_tarjeta_bruto = 0.0
    
    ventas_contado_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "contado"
    ).all()
    
    for venta in ventas_contado_query:
        pagos = db.query(Payment).filter(Payment.sale_id == venta.id).all()
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
    apartados_pendientes: List[Sale],
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
        pagos_iniciales = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
        for pago in pagos_iniciales:
            if pago.method in ['efectivo', 'cash', 'transferencia']:
                anticipos_apart_efectivo_count += 1
                anticipos_apart_efectivo_bruto += float(pago.amount)
            elif pago.method in ['tarjeta', 'card']:
                anticipos_apart_tarjeta_count += 1
                anticipos_apart_tarjeta_bruto += float(pago.amount)
    
    # Contar abonos de apartados pendientes
    for apartado in apartados_pendientes:
        abonos = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
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
    
    Args:
        pagos: List of payment objects with metodo_pago attribute
        
    Returns:
        Dictionary with 'efectivo' and 'tarjeta' totals
    """
    efectivo = sum(float(p.monto) for p in pagos if getattr(p, 'metodo_pago', None) in EFECTIVO_METHODS)
    tarjeta = sum(float(p.monto) for p in pagos if getattr(p, 'metodo_pago', None) == TARJETA_METHOD)
    return {'efectivo': efectivo, 'tarjeta': tarjeta}


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


def _build_resumen_piezas(
    db: Session,
    all_sales: List[Sale],
    apartados_pendientes: List[Sale],
    pedidos_pendientes: List[Pedido],
    pedidos_liquidados: List[Pedido],
) -> List[dict]:
    """
    Build summary of pieces by product (name, model, quilataje).
    
    Args:
        db: Database session
        all_sales: List of all sales in the period
        apartados_pendientes: List of pending apartados
        pedidos_pendientes: List of pending pedidos
        pedidos_liquidados: List of liquidated pedidos
        
    Returns:
        List of dictionaries with piece summaries
    """
    resumen_piezas_dict: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    # Process contado sales
    for sale in all_sales:
        if sale.tipo_venta == "contado":
            items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
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
                        "piezas_vendidas": 0,
                        "piezas_pedidas": 0,
                        "piezas_apartadas": 0,
                        "piezas_liquidadas": 0,
                        "total_piezas": 0,
                    }
                resumen_piezas_dict[key]["piezas_vendidas"] += item.quantity

    # Process pending apartados
    for apartado in apartados_pendientes:
        items = db.query(SaleItem).filter(SaleItem.sale_id == apartado.id).all()
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
                    "piezas_vendidas": 0,
                    "piezas_pedidas": 0,
                    "piezas_apartadas": 0,
                    "piezas_liquidadas": 0,
                    "total_piezas": 0,
                }
            resumen_piezas_dict[key]["piezas_apartadas"] += item.quantity

    # Process liquidated apartados (credito pagado/entregado)
    for sale in all_sales:
        if sale.tipo_venta == "credito" and sale.credit_status in ['pagado', 'entregado']:
            items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
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
                        "piezas_vendidas": 0,
                        "piezas_pedidas": 0,
                        "piezas_apartadas": 0,
                        "piezas_liquidadas": 0,
                        "total_piezas": 0,
                    }
                resumen_piezas_dict[key]["piezas_liquidadas"] += item.quantity

    # Process pending pedidos
    for pedido in pedidos_pendientes:
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        if not producto:
            continue
        key = (producto.nombre or producto.modelo or "Sin nombre", producto.modelo or "N/A", producto.quilataje or "N/A")
        if key not in resumen_piezas_dict:
            resumen_piezas_dict[key] = {
                "nombre": producto.nombre or producto.modelo or "Sin nombre",
                "modelo": producto.modelo or "N/A",
                "quilataje": producto.quilataje or "N/A",
                "piezas_vendidas": 0,
                "piezas_pedidas": 0,
                "piezas_apartadas": 0,
                "piezas_liquidadas": 0,
                "total_piezas": 0,
            }
        resumen_piezas_dict[key]["piezas_pedidas"] += pedido.cantidad

    # Process liquidated pedidos
    for pedido in pedidos_liquidados:
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        if not producto:
            continue
        key = (producto.nombre or producto.modelo or "Sin nombre", producto.modelo or "N/A", producto.quilataje or "N/A")
        if key not in resumen_piezas_dict:
            resumen_piezas_dict[key] = {
                "nombre": producto.nombre or producto.modelo or "Sin nombre",
                "modelo": producto.modelo or "N/A",
                "quilataje": producto.quilataje or "N/A",
                "piezas_vendidas": 0,
                "piezas_pedidas": 0,
                "piezas_apartadas": 0,
                "piezas_liquidadas": 0,
                "total_piezas": 0,
            }
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


def _build_total_piezas_por_nombre_sin_liquidadas(
    resumen_piezas: List[dict]
) -> Dict[str, int]:
    """
    Group piece summary by name only, summing all categories except liquidated.
    
    Args:
        resumen_piezas: List of piece summary dictionaries
        
    Returns:
        Dictionary mapping product name to total pieces (excluding liquidated)
    """
    total_por_nombre_dict: Dict[str, int] = {}
    
    for pieza in resumen_piezas:
        nombre = pieza["nombre"]
        if nombre not in total_por_nombre_dict:
            total_por_nombre_dict[nombre] = 0
        
        # Sum all categories except liquidated
        total_por_nombre_dict[nombre] += (
            pieza["piezas_vendidas"]
            + pieza["piezas_pedidas"]
            + pieza["piezas_apartadas"]
        )
    
    return total_por_nombre_dict

