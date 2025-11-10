from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user, require_admin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.payment import Payment
from app.models.credit_payment import CreditPayment
from app.models.producto_pedido import Pedido, PagoPedido

router = APIRouter()


class SalesByVendorReport(BaseModel):
    vendedor_id: int
    vendedor_name: str
    sales_count: int
    contado_count: int
    credito_count: int
    total_contado: float
    total_credito: float
    total_profit: float
    # Nuevas métricas para Resumen por Vendedores
    total_efectivo_contado: float  # Ventas de contado en efectivo
    total_tarjeta_contado: float  # Ventas de contado con tarjeta (sin descuento)
    total_tarjeta_neto: float  # Ventas con tarjeta (-3%)
    anticipos_apartados: float  # Anticipos de apartados
    anticipos_pedidos: float  # Anticipos de pedidos
    abonos_apartados: float  # Abonos de apartados
    abonos_pedidos: float  # Abonos de pedidos
    ventas_total_activa: float  # Contado + Tarjeta finalizadas
    venta_total_pasiva: float  # Anticipos + Abonos
    cuentas_por_cobrar: float  # Saldo pendiente


class CorteDeCajaReport(BaseModel):
    start_date: str
    end_date: str
    
    # Sales by type
    ventas_contado_count: int
    ventas_contado_total: float
    ventas_credito_count: int
    ventas_credito_total: float
    
    # Payments by method
    efectivo_ventas: float
    tarjeta_ventas: float
    credito_ventas: float
    
    # Credit payments (abonos)
    abonos_efectivo: float
    abonos_tarjeta: float
    abonos_total: float
    
    # Totals
    total_efectivo: float  # Cash sales + cash abonos
    total_tarjeta: float   # Card sales + card abonos
    total_revenue: float   # All income
    
    # Profit
    total_cost: float
    total_profit: float
    profit_margin: float
    
    # Returns
    returns_count: int
    returns_total: float
    
    # Vendors summary
    vendedores: List[SalesByVendorReport]


@router.get("/corte-de-caja", response_model=CorteDeCajaReport)
def get_corte_de_caja(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
):
    """
    Generate a corte de caja (cash cut) report showing:
    - Sales by payment method
    - Credit payments (abonos)
    - Profit calculations
    - Returns
    """
    # Default to today if no dates provided
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
    
    # Convert to datetime for queries (timezone-aware)
    from datetime import timezone as tz
    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=tz.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=tz.utc)
    
    # Get all sales in date range (excluding returns)
    # Include: all "contado" sales + credit sales that are paid or delivered
    sales_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.return_of_id == None,
        or_(
            Sale.tipo_venta == "contado",
            and_(
                Sale.tipo_venta == "credito",
                Sale.credit_status.in_(['pagado', 'entregado'])
            )
        )
    )
    
    all_sales = sales_query.all()
    
    # Initialize counters
    ventas_contado_count = 0
    ventas_contado_total = 0.0
    ventas_credito_count = 0
    ventas_credito_total = 0.0
    efectivo_ventas = 0.0
    tarjeta_ventas = 0.0
    credito_ventas = 0.0
    total_cost = 0.0
    total_profit = 0.0
    
    # Process each sale
    for sale in all_sales:
        if sale.tipo_venta == "contado":
            ventas_contado_count += 1
            ventas_contado_total += float(sale.total)
            
            # Get all payment methods for this sale
            payments = db.query(Payment).filter(Payment.sale_id == sale.id).all()
            for payment in payments:
                if payment.method == "efectivo" or payment.method == "cash":
                    efectivo_ventas += float(payment.amount)
                elif payment.method == "tarjeta" or payment.method == "card":
                    tarjeta_ventas += float(payment.amount)
        else:  # credito
            ventas_credito_count += 1
            ventas_credito_total += float(sale.total)
            credito_ventas += float(sale.total)
        
        # Accumulate costs and profits
        if sale.total_cost:
            total_cost += float(sale.total_cost)
        if sale.utilidad:
            total_profit += float(sale.utilidad)
    
    # Get credit payments (abonos) in date range
    abonos = db.query(CreditPayment).filter(
        CreditPayment.tenant_id == tenant.id,
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).all()
    
    abonos_efectivo = 0.0
    abonos_tarjeta = 0.0
    
    for abono in abonos:
        if abono.payment_method == "efectivo":
            abonos_efectivo += float(abono.amount)
        elif abono.payment_method == "tarjeta":
            abonos_tarjeta += float(abono.amount)
    
    abonos_total = abonos_efectivo + abonos_tarjeta
    
    # Get pedidos (orders) in date range
    pedidos_query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    )
    
    all_pedidos = pedidos_query.all()
    
    # Initialize pedidos counters
    pedidos_count = len(all_pedidos)
    pedidos_total = sum(float(p.total) for p in all_pedidos)
    pedidos_anticipos = sum(float(p.anticipo_pagado) for p in all_pedidos)
    pedidos_saldo = sum(float(p.saldo_pendiente) for p in all_pedidos)
    
    # Get pagos de pedidos (order payments) in date range
    pagos_pedidos_query = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime
    )
    
    pagos_pedidos = pagos_pedidos_query.all()
    
    # Count pedidos payments by method
    pedidos_efectivo = 0.0
    pedidos_tarjeta = 0.0
    
    for pago in pagos_pedidos:
        if pago.metodo_pago == "efectivo":
            pedidos_efectivo += float(pago.monto)
        elif pago.metodo_pago == "tarjeta":
            pedidos_tarjeta += float(pago.monto)
    
    pedidos_pagos_total = pedidos_efectivo + pedidos_tarjeta
    
    # Get returns
    returns = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.return_of_id != None
    ).all()
    
    returns_count = len(returns)
    returns_total = sum(float(r.total) for r in returns)
    
    # Calculate totals
    total_efectivo = efectivo_ventas + abonos_efectivo + pedidos_efectivo
    total_tarjeta = tarjeta_ventas + abonos_tarjeta + pedidos_tarjeta
    total_revenue = total_efectivo + total_tarjeta + credito_ventas - returns_total
    
    # Calculate profit margin
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calculate vendor stats
    vendor_stats = {}
    for sale in all_sales:
        vendedor_id = sale.vendedor_id or 0
        if vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == vendedor_id).first() if vendedor_id > 0 else None
            vendor_stats[vendedor_id] = {
                "vendedor_id": vendedor_id,
                "vendedor_name": vendor.email if vendor else "Mostrador",
                "sales_count": 0,
                "contado_count": 0,
                "credito_count": 0,
                "total_contado": 0.0,
                "total_credito": 0.0,
                "total_profit": 0.0
            }
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        if sale.tipo_venta == "contado":
            vendor_stats[vendedor_id]["contado_count"] += 1
            vendor_stats[vendedor_id]["total_contado"] += float(sale.total)
        else:
            vendor_stats[vendedor_id]["credito_count"] += 1
            vendor_stats[vendedor_id]["total_credito"] += float(sale.total)
        vendor_stats[vendedor_id]["total_profit"] += float(sale.utilidad or 0)
    
    vendedores = list(vendor_stats.values())
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "ventas_contado_count": ventas_contado_count,
        "ventas_contado_total": ventas_contado_total,
        "ventas_credito_count": ventas_credito_count,
        "ventas_credito_total": ventas_credito_total,
        "efectivo_ventas": efectivo_ventas,
        "tarjeta_ventas": tarjeta_ventas,
        "credito_ventas": credito_ventas,
        "abonos_efectivo": abonos_efectivo,
        "abonos_tarjeta": abonos_tarjeta,
        "abonos_total": abonos_total,
        "pedidos_count": pedidos_count,
        "pedidos_total": pedidos_total,
        "pedidos_anticipos": pedidos_anticipos,
        "pedidos_saldo": pedidos_saldo,
        "pedidos_efectivo": pedidos_efectivo,
        "pedidos_tarjeta": pedidos_tarjeta,
        "pedidos_pagos_total": pedidos_pagos_total,
        "total_efectivo": total_efectivo,
        "total_tarjeta": total_tarjeta,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "profit_margin": profit_margin,
        "returns_count": returns_count,
        "returns_total": returns_total,
        "vendedores": vendedores
    }


class DailySummaryReport(BaseModel):
    fecha: str
    costo: float
    venta: float
    utilidad: float


class SaleDetailReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    piezas: int
    total: float
    estado: str
    tipo: str
    vendedor: str
    efectivo: float = 0.0
    tarjeta: float = 0.0


class PedidoDetailReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    producto: str
    cantidad: int
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str

class ApartadoHistorialReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str

class PedidoHistorialReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    producto: str
    cantidad: int
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str

class AbonoApartadoReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    monto: float
    metodo_pago: str
    vendedor: str

class AbonoPedidoReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    producto: str
    monto: float
    metodo_pago: str
    vendedor: str

class ApartadoCanceladoVencidoReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str
    motivo: str

class PedidoCanceladoVencidoReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    producto: str
    cantidad: int
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str
    motivo: str

class ResumenPagosReport(BaseModel):
    tipo_movimiento: str
    metodo_pago: str
    cantidad_operaciones: int
    subtotal: float
    total: float

class ResumenVentasActivasReport(BaseModel):
    tipo_movimiento: str
    metodo_pago: str
    cantidad_operaciones: int
    subtotal: float
    total: float

class DetailedCorteCajaReport(BaseModel):
    start_date: str
    end_date: str
    generated_at: str

    # Resumen general
    ventas_validas: int  # Cantidad de ventas de contado
    contado_count: int
    credito_count: int
    total_contado: float  # Suma de ventas de contado
    total_credito: float  # Suma de ventas a crédito pagadas/entregadas
    liquidacion_count: int  # Apartados + Pedidos liquidados
    liquidacion_total: float  # Suma de apartados + pedidos liquidados
    ventas_pasivas_total: float  # Anticipos/abonos de ventas NO liquidadas
    apartados_pendientes_anticipos: float  # Anticipos iniciales de apartados pendientes
    apartados_pendientes_abonos_adicionales: float  # Abonos posteriores de apartados pendientes
    pedidos_pendientes_anticipos: float  # Anticipos de pedidos pendientes
    pedidos_pendientes_abonos: float  # Abonos de pedidos pendientes
    cuentas_por_cobrar: float  # Saldo pendiente de apartados + pedidos
    total_vendido: float
    costo_total: float
    costo_ventas_contado: float  # Costo total de ventas de contado (Ventas Activas)
    costo_apartados_pedidos_liquidados: float  # Costo de apartados y pedidos liquidados
    utilidad_productos_liquidados: float  # Utilidad de apartados y pedidos liquidados
    total_efectivo_contado: float  # Total pagado en efectivo en ventas de contado (Ventas Activas)
    total_tarjeta_contado: float  # Total pagado con tarjeta en ventas de contado sin descuento (Ventas Activas)
    total_ventas_activas_neto: float  # Total de Ventas Activas con descuento 3% aplicado a tarjetas
    utilidad_ventas_activas: float  # Utilidad de ventas activas (con descuento 3% tarjeta)
    utilidad_total: float
    piezas_vendidas: int
    pendiente_credito: float
    
    # Pedidos
    pedidos_count: int
    pedidos_total: float
    pedidos_anticipos: float
    pedidos_saldo: float
    pedidos_liquidados_count: int  # Cantidad de pedidos liquidados
    pedidos_liquidados_total: float  # Total de pedidos liquidados
    
    # Resumen Detallado - Métricas adicionales
    num_piezas_vendidas: int
    num_piezas_entregadas: int
    num_piezas_apartadas_pagadas: int
    num_piezas_pedidos_pagados: int
    num_piezas_pedidos_apartados_liquidados: int  # Piezas de pedidos apartados completados (excluye pedidos de contado)
    num_solicitudes_apartado: int
    num_pedidos_hechos: int
    num_cancelaciones: int
    num_apartados_vencidos: int
    num_pedidos_vencidos: int
    num_abonos_apartados: int
    num_abonos_pedidos: int
    subtotal_venta_tarjeta: float  # Suma de ventas con tarjeta (sin descuento)
    total_tarjeta_neto: float  # Total tarjeta con descuento del 3%
    
    # Reembolsos y Saldos Vencidos
    reembolso_apartados_cancelados: float  # Total pagado en apartados cancelados
    reembolso_pedidos_cancelados: float  # Total pagado en pedidos cancelados
    saldo_vencido_apartados: float  # Total pagado en apartados vencidos
    saldo_vencido_pedidos: float  # Total pagado en pedidos vencidos

    # Vendedores
    vendedores: List[SalesByVendorReport]

    # Resumen diario
    daily_summaries: List[DailySummaryReport]

    # Detalle de ventas
    sales_details: List[SaleDetailReport]
    
    # Historiales
    historial_apartados: List[ApartadoHistorialReport]
    historial_pedidos: List[PedidoHistorialReport]
    historial_abonos_apartados: List[AbonoApartadoReport]
    historial_abonos_pedidos: List[AbonoPedidoReport]
    apartados_cancelados_vencidos: List[ApartadoCanceladoVencidoReport]
    pedidos_cancelados_vencidos: List[PedidoCanceladoVencidoReport]
    
    # Resumen de ventas activas
    resumen_ventas_activas: List[ResumenVentasActivasReport]
    
    # Resumen de pagos (Ventas Pasivas)
    resumen_pagos: List[ResumenPagosReport]


@router.get("/sales-by-vendor", response_model=list[SalesByVendorReport])
def get_sales_by_vendor(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get sales report grouped by salesperson"""
    # Default to today if no dates provided
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Group sales by vendedor
    sales = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.return_of_id == None,
        Sale.vendedor_id != None
    ).all()
    
    # Aggregate by vendor
    vendor_stats = {}
    for sale in sales:
        if sale.vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == sale.vendedor_id).first()
            vendor_stats[sale.vendedor_id] = {
                "vendedor_id": sale.vendedor_id,
                "vendedor_name": vendor.email if vendor else "Unknown",
                "sales_count": 0,
                "total_sales": 0.0,
                "total_profit": 0.0
            }
        
        vendor_stats[sale.vendedor_id]["sales_count"] += 1
        vendor_stats[sale.vendedor_id]["total_sales"] += float(sale.total)
        vendor_stats[sale.vendedor_id]["total_profit"] += float(sale.utilidad or 0)
    
    return list(vendor_stats.values())


@router.get("/detailed-corte-caja", response_model=DetailedCorteCajaReport)
def get_detailed_corte_caja(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
):
    """
    Generate a detailed corte de caja report with individual sales details,
    vendor breakdown, and daily summaries
    """
    # Default to today if no dates provided
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()

    # Convert to datetime for queries (timezone-aware)
    from datetime import timezone as tz
    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=tz.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=tz.utc)

    # Get all sales in date range (excluding returns)
    # Include: all "contado" sales + credit sales that are paid or delivered
    sales_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.return_of_id == None,
        or_(
            Sale.tipo_venta == "contado",
            and_(
                Sale.tipo_venta == "credito",
                Sale.credit_status.in_(['pagado', 'entregado'])
            )
        )
    )

    all_sales = sales_query.all()
    
    # Get pedidos liquidados (pagados/entregados) para "Ventas de liquidación"
    # SOLO pedidos apartados completados, NO pedidos de contado (esos van en Ventas Activas)
    pedidos_liquidados_query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.tipo_pedido == 'apartado',  # Solo pedidos apartados, NO contado
        Pedido.estado.in_(['pagado', 'entregado'])
    )
    pedidos_liquidados = pedidos_liquidados_query.all()
    
    # Get pedidos de contado (tipo_pedido='contado' y estado='pagado') para Ventas Activas
    pedidos_contado_query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.tipo_pedido == 'contado',
        Pedido.estado == 'pagado'
    )
    pedidos_contado = pedidos_contado_query.all()
    
    # Get pedidos pendientes (NO pagados/entregados) para "Ventas pasivas"
    # SOLO pedidos apartados pendientes, NO pedidos de contado
    pedidos_pendientes_query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.tipo_pedido == 'apartado',  # Solo pedidos apartados
        ~Pedido.estado.in_(['pagado', 'entregado', 'cancelado'])
    )
    pedidos_pendientes = pedidos_pendientes_query.all()
    
    # Get apartados pendientes para "Ventas pasivas"
    apartados_pendientes_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito",
        Sale.credit_status.in_(['pendiente', 'vencido'])
    )
    apartados_pendientes = apartados_pendientes_query.all()

    # Initialize counters for summary
    contado_count = 0
    credito_count = 0
    total_contado = 0.0  # Suma de ventas de contado
    total_credito = 0.0  # Suma de ventas a crédito pagadas/entregadas
    total_vendido = 0.0
    costo_total = 0.0
    costo_ventas_contado = 0.0  # Costo total de ventas de contado (Ventas Activas)
    costo_apartados_liquidados = 0.0  # Costo de apartados con status pagado/entregado
    costo_pedidos_liquidados = 0.0  # Costo de pedidos con status pagado/entregado
    total_efectivo_contado = 0.0  # Total pagado en efectivo en ventas de contado
    total_tarjeta_contado = 0.0  # Total pagado con tarjeta en ventas de contado
    utilidad_total = 0.0
    piezas_vendidas = 0
    pendiente_credito = 0.0
    
    # Pedidos liquidados counters
    pedidos_liquidados_count = len(pedidos_liquidados)
    pedidos_liquidados_total = 0.0
    
    # Ventas pasivas counters (anticipos/abonos NO liquidados)
    apartados_pendientes_anticipos = 0.0  # Anticipos iniciales de apartados
    apartados_pendientes_abonos_adicionales = 0.0  # Abonos posteriores de apartados
    pedidos_pendientes_anticipos = 0.0  # Anticipos iniciales de pedidos
    pedidos_pendientes_abonos = 0.0  # Abonos posteriores de pedidos
    
    # Pedidos details (todos, liquidados y pendientes)
    pedidos_count = len(pedidos_liquidados) + len(pedidos_pendientes)
    pedidos_total = 0.0
    pedidos_anticipos = 0.0
    pedidos_saldo = 0.0
    
    # Resumen Detallado - Nuevas métricas
    num_piezas_vendidas = 0  # Piezas de ventas de contado
    num_piezas_entregadas = 0  # Piezas de apartados/pedidos liquidados
    num_piezas_apartadas_pagadas = 0  # Piezas de apartados pagados
    num_piezas_pedidos_pagados = 0  # Piezas de pedidos pagados (incluye todos los tipos)
    num_piezas_pedidos_apartados_liquidados = 0  # Piezas de pedidos APARTADOS liquidados (excluye pedidos de contado)
    num_solicitudes_apartado = 0  # Total de apartados creados (pendientes + pagados)
    num_pedidos_hechos = 0  # Total de pedidos creados (pendientes + pagados)
    num_cancelaciones = 0  # Ventas/apartados/pedidos cancelados
    num_apartados_vencidos = 0  # Apartados con status vencido
    num_pedidos_vencidos = 0  # Pedidos con status vencido
    num_abonos_apartados = 0  # Cantidad de abonos a apartados
    num_abonos_pedidos = 0  # Cantidad de abonos a pedidos
    
    # Reembolsos y Saldos Vencidos
    reembolso_apartados_cancelados = 0.0  # Suma de anticipos de apartados cancelados
    reembolso_pedidos_cancelados = 0.0  # Suma de anticipos de pedidos cancelados
    saldo_vencido_apartados = 0.0  # Suma de saldos pendientes de apartados vencidos
    saldo_vencido_pedidos = 0.0  # Suma de saldos pendientes de pedidos vencidos

    # Group sales by vendedor for vendor stats
    vendor_stats = {}
    daily_stats = {}
    sales_details = []
    historial_apartados = []
    historial_pedidos = []
    historial_abonos_apartados = []
    historial_abonos_pedidos = []
    apartados_cancelados_vencidos = []
    pedidos_cancelados_vencidos = []

    for sale in all_sales:
        # Update summary counters
        if sale.tipo_venta == "contado":
            contado_count += 1
            total_contado += float(sale.total)
            
            # Calcular costo desde los productos vendidos (SaleItem)
            sale_items = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
            for item in sale_items:
                num_piezas_vendidas += item.quantity  # Contar piezas vendidas
                if item.product_id:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    if product and product.cost_price:
                        costo_ventas_contado += float(product.cost_price) * item.quantity
            
            # Calcular efectivo y tarjeta de ventas de contado
            payments_contado = db.query(Payment).filter(Payment.sale_id == sale.id).all()
            total_efectivo_contado += sum(float(p.amount) for p in payments_contado if p.method in ['efectivo', 'cash', 'transferencia'])
            total_tarjeta_contado += sum(float(p.amount) for p in payments_contado if p.method in ['tarjeta', 'card'])
        else:  # credito (pagado o entregado) - Apartados liquidados
            credito_count += 1
            
            # Calcular pagos de apartados liquidados aplicando descuento 3% a tarjetas
            pagos_apartado = db.query(Payment).filter(Payment.sale_id == sale.id).all()
            efectivo_apartado = sum(float(p.amount) for p in pagos_apartado if p.method in ['efectivo', 'cash', 'transferencia'])
            tarjeta_apartado = sum(float(p.amount) for p in pagos_apartado if p.method in ['tarjeta', 'card'])
            
            abonos_apartado = db.query(CreditPayment).filter(CreditPayment.sale_id == sale.id).all()
            efectivo_abonos = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            tarjeta_abonos = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['tarjeta', 'card'])
            
            total_credito_neto = efectivo_apartado + (tarjeta_apartado * 0.97) + efectivo_abonos + (tarjeta_abonos * 0.97)
            total_credito += total_credito_neto
            
            # Calcular costo de apartados liquidados desde los productos vendidos
            sale_items_apartado = db.query(SaleItem).filter(SaleItem.sale_id == sale.id).all()
            for item in sale_items_apartado:
                num_piezas_apartadas_pagadas += item.quantity  # Contar piezas de apartados pagados
                num_piezas_entregadas += item.quantity  # Contar piezas entregadas
                if item.product_id:
                    product = db.query(Product).filter(Product.id == item.product_id).first()
                    if product and product.cost_price:
                        costo_apartados_liquidados += float(product.cost_price) * item.quantity

        total_vendido += float(sale.total)
        if sale.total_cost:
            costo_total += float(sale.total_cost)
        if sale.utilidad:
            utilidad_total += float(sale.utilidad)

        # Count items in sale (simplified - should be calculated from sale items)
        piezas_vendidas += 1  # This should be calculated properly from sale items

        # Get vendor info
        vendedor = "Mostrador"
        if sale.vendedor_id:
            vendor = db.query(User).filter(User.id == sale.vendedor_id).first()
            vendedor = vendor.email if vendor else "Unknown"

        # Add to vendor stats
        if sale.vendedor_id not in vendor_stats:
            vendor_stats[sale.vendedor_id] = {
                "vendedor_id": sale.vendedor_id or 0,
                "vendedor_name": vendedor,
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

        vendor_stats[sale.vendedor_id]["sales_count"] += 1
        
        # Calculate payment methods for this sale
        payments_vendor = db.query(Payment).filter(Payment.sale_id == sale.id).all()
        efectivo_vendor = sum(float(p.amount) for p in payments_vendor if p.method in ['efectivo', 'cash', 'transferencia'])
        tarjeta_vendor = sum(float(p.amount) for p in payments_vendor if p.method in ['tarjeta', 'card'])
        
        if sale.tipo_venta == "contado":
            vendor_stats[sale.vendedor_id]["contado_count"] += 1
            vendor_stats[sale.vendedor_id]["total_contado"] += float(sale.total)
            vendor_stats[sale.vendedor_id]["total_efectivo_contado"] += efectivo_vendor
            vendor_stats[sale.vendedor_id]["total_tarjeta_contado"] += tarjeta_vendor
            vendor_stats[sale.vendedor_id]["total_tarjeta_neto"] += tarjeta_vendor * 0.97
            vendor_stats[sale.vendedor_id]["ventas_total_activa"] += efectivo_vendor + (tarjeta_vendor * 0.97)
        else:
            vendor_stats[sale.vendedor_id]["credito_count"] += 1
            vendor_stats[sale.vendedor_id]["total_credito"] += float(sale.total)
        vendor_stats[sale.vendedor_id]["total_profit"] += float(sale.utilidad or 0)

        # Daily summary
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

        # Calculate payment methods for this sale
        payments = db.query(Payment).filter(Payment.sale_id == sale.id).all()
        efectivo_amount = sum(float(p.amount) for p in payments if p.method in ['efectivo', 'cash', 'transferencia'])
        tarjeta_amount = sum(float(p.amount) for p in payments if p.method in ['tarjeta', 'card'])
        
        # Sale details
        sales_details.append({
            "id": sale.id,
            "fecha": sale.created_at.strftime("%Y-%m-%d %H:%M"),
            "cliente": sale.customer_name or "Mostrador",
            "piezas": 1,  # This should be calculated from sale items
            "total": float(sale.total),
            "estado": "Pagada" if sale.tipo_venta == "contado" else "Crédito",
            "tipo": sale.tipo_venta,
            "vendedor": vendedor,
            "efectivo": efectivo_amount,
            "tarjeta": tarjeta_amount
        })

    # Process pedidos de contado para Ventas Activas
    from app.models.producto_pedido import ProductoPedido
    for pedido in pedidos_contado:
        # Obtener los pagos del pedido
        pagos_pedido_contado = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id
        ).all()
        
        efectivo_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago in ['efectivo', 'transferencia'])
        tarjeta_pedido = sum(float(p.monto) for p in pagos_pedido_contado if p.metodo_pago == 'tarjeta')
        
        total_efectivo_contado += efectivo_pedido
        total_tarjeta_contado += tarjeta_pedido
        
        # Obtener producto para calcular costo
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id
        ).first()
        
        if producto and producto.cost_price:
            costo_ventas_contado += float(producto.cost_price) * pedido.cantidad
        
        # Contar piezas vendidas
        num_piezas_vendidas += pedido.cantidad
        
        # Obtener vendedor
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        # Agregar a sales_details para aparecer en listas detalladas
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
        
        # Actualizar stats por vendedor si existe
        if pedido.user_id:
            if pedido.user_id not in vendor_stats:
                vendor_stats[pedido.user_id] = {
                    "vendedor_id": pedido.user_id,
                    "vendedor_name": vendedor,
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
            
            vendor_stats[pedido.user_id]["sales_count"] += 1
            vendor_stats[pedido.user_id]["contado_count"] += 1
            vendor_stats[pedido.user_id]["total_contado"] += float(pedido.total)
            vendor_stats[pedido.user_id]["total_efectivo_contado"] += efectivo_pedido
            vendor_stats[pedido.user_id]["total_tarjeta_contado"] += tarjeta_pedido
            vendor_stats[pedido.user_id]["total_tarjeta_neto"] += tarjeta_pedido * 0.97
            vendor_stats[pedido.user_id]["ventas_total_activa"] += efectivo_pedido + (tarjeta_pedido * 0.97)

    # Process pedidos liquidados para "Ventas de liquidación"
    for pedido in pedidos_liquidados:
        # Calcular pagos de pedidos liquidados aplicando descuento 3% a tarjetas
        pagos_pedido_liq = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        efectivo_pedido_liq = sum(float(p.monto) for p in pagos_pedido_liq if p.metodo_pago in ['efectivo', 'transferencia'])
        tarjeta_pedido_liq = sum(float(p.monto) for p in pagos_pedido_liq if p.metodo_pago == 'tarjeta')
        total_pedido_neto = efectivo_pedido_liq + (tarjeta_pedido_liq * 0.97)
        
        pedidos_liquidados_total += total_pedido_neto
        pedidos_total += float(pedido.total)
        pedidos_anticipos += float(pedido.anticipo_pagado)
        pedidos_saldo += float(pedido.saldo_pendiente)
        
        # Get vendedor
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
            
            # Agregar vendedor a stats si no existe
            if pedido.user_id not in vendor_stats:
                vendor_stats[pedido.user_id] = {
                    "vendedor_id": pedido.user_id,
                    "vendedor_name": vendedor,
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
        
        # Get producto name and cost
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        # Calcular costo de pedidos liquidados
        if producto and producto.cost_price:
            costo_pedidos_liquidados += float(producto.cost_price) * pedido.cantidad
        
        # Contar piezas de pedidos pagados
        num_piezas_pedidos_pagados += pedido.cantidad
        num_piezas_pedidos_apartados_liquidados += pedido.cantidad  # Este loop solo procesa pedidos apartados
        num_piezas_entregadas += pedido.cantidad
        
        # Agregar a historial de pedidos
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
    
    # Process pedidos pendientes (anticipos de pedidos NO liquidados)
    for pedido in pedidos_pendientes:
        # Obtener pagos de anticipo separados por método para aplicar descuento 3% a tarjeta
        pagos_anticipo = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'anticipo'
        ).all()
        anticipo_efectivo = sum(float(p.monto) for p in pagos_anticipo if p.metodo_pago in ['efectivo', 'transferencia'])
        anticipo_tarjeta = sum(float(p.monto) for p in pagos_anticipo if p.metodo_pago == 'tarjeta')
        anticipo_neto = anticipo_efectivo + (anticipo_tarjeta * 0.97)
        
        pedidos_pendientes_anticipos += anticipo_neto
        pedidos_total += float(pedido.total)
        pedidos_anticipos += anticipo_neto
        pedidos_saldo += float(pedido.saldo_pendiente)
        
        # Get vendedor
        vendedor = "Unknown"
        if pedido.user_id:
            vendor = db.query(User).filter(User.id == pedido.user_id).first()
            vendedor = vendor.email if vendor else "Unknown"
        
        # Get producto name
        producto = db.query(ProductoPedido).filter(ProductoPedido.id == pedido.producto_pedido_id).first()
        producto_name = producto.modelo if producto else "Producto desconocido"
        
        # Agregar a historial de pedidos
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
    
    # Process apartados pendientes (apartados NO liquidados)
    for apartado in apartados_pendientes:
        # Obtener el anticipo inicial de la tabla Payment (pago al crear la venta)
        pagos_iniciales = db.query(Payment).filter(
            Payment.sale_id == apartado.id
        ).all()
        anticipo_efectivo = sum(float(p.amount) for p in pagos_iniciales if p.method in ['efectivo', 'cash', 'transferencia'])
        anticipo_tarjeta = sum(float(p.amount) for p in pagos_iniciales if p.method in ['tarjeta', 'card'])
        anticipo_inicial = anticipo_efectivo + (anticipo_tarjeta * 0.97)  # Aplicar 3% descuento a tarjeta
        apartados_pendientes_anticipos += anticipo_inicial
        
        # Obtener abonos posteriores de CreditPayment (pagos después de crear la venta)
        pagos_posteriores = db.query(CreditPayment).filter(
            CreditPayment.sale_id == apartado.id
        ).all()
        abonos_efectivo = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        abonos_tarjeta = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['tarjeta', 'card'])
        abonos_posteriores = abonos_efectivo + (abonos_tarjeta * 0.97)  # Aplicar 3% descuento a tarjeta
        apartados_pendientes_abonos_adicionales += abonos_posteriores
    
    # Process pedidos pendientes (pedidos NO liquidados) - calcular abonos SOLAMENTE
    for pedido in pedidos_pendientes:
        # Obtener SOLO los abonos (tipo_pago='saldo'), NO los anticipos que ya se contaron antes
        pagos_pedido_abonos = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'saldo'  # Solo abonos, NO anticipos
        ).all()
        
        # Sumar solo los abonos aplicando descuento 3% a tarjeta
        abonos_efectivo = sum(float(p.monto) for p in pagos_pedido_abonos if p.metodo_pago in ['efectivo', 'transferencia'])
        abonos_tarjeta = sum(float(p.monto) for p in pagos_pedido_abonos if p.metodo_pago == 'tarjeta')
        abonos_posteriores = abonos_efectivo + (abonos_tarjeta * 0.97)  # Aplicar 3% descuento a tarjeta
        pedidos_pendientes_abonos += abonos_posteriores
        
        # NOTA: Los anticipos (tipo_pago='anticipo') ya fueron sumados en el bucle anterior
        # NO debemos incluirlos aquí para evitar duplicación

    # Calcular anticipos y abonos por vendedor (apartados pendientes)
    for apartado in apartados_pendientes:
        if apartado.vendedor_id:
            # Crear vendedor en stats si no existe
            if apartado.vendedor_id not in vendor_stats:
                vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
                vendedor_name = vendor.email if vendor else "Unknown"
                vendor_stats[apartado.vendedor_id] = {
                    "vendedor_id": apartado.vendedor_id,
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
            # Anticipo inicial (Payment) - aplicar 3% descuento a tarjeta
            pagos_iniciales = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
            anticipo_efectivo = sum(float(p.amount) for p in pagos_iniciales if p.method in ['efectivo', 'cash', 'transferencia'])
            anticipo_tarjeta = sum(float(p.amount) for p in pagos_iniciales if p.method in ['tarjeta', 'card'])
            anticipo_neto = anticipo_efectivo + (anticipo_tarjeta * 0.97)
            vendor_stats[apartado.vendedor_id]["anticipos_apartados"] += anticipo_neto
            vendor_stats[apartado.vendedor_id]["venta_total_pasiva"] += anticipo_neto
            
            # Abonos posteriores (CreditPayment) - aplicar 3% descuento a tarjeta
            pagos_posteriores = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
            abonos_efectivo = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['efectivo', 'cash', 'transferencia'])
            abonos_tarjeta = sum(float(p.amount) for p in pagos_posteriores if p.payment_method in ['tarjeta', 'card'])
            abonos_neto = abonos_efectivo + (abonos_tarjeta * 0.97)
            vendor_stats[apartado.vendedor_id]["abonos_apartados"] += abonos_neto
            vendor_stats[apartado.vendedor_id]["venta_total_pasiva"] += abonos_neto
            
            # Cuentas por cobrar (saldo pendiente)
            saldo = float(apartado.total) - float(apartado.amount_paid or 0)
            vendor_stats[apartado.vendedor_id]["cuentas_por_cobrar"] += saldo
    
    # Calcular anticipos y abonos por vendedor (pedidos pendientes)
    for pedido in pedidos_pendientes:
        if pedido.user_id:
            # Crear vendedor en stats si no existe
            if pedido.user_id not in vendor_stats:
                vendor = db.query(User).filter(User.id == pedido.user_id).first()
                vendedor_name = vendor.email if vendor else "Unknown"
                vendor_stats[pedido.user_id] = {
                    "vendedor_id": pedido.user_id,
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
            # Obtener TODOS los pagos del pedido (incluyendo anticipo)
            pagos_pedido_todos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
            
            # Separar anticipos (tipo_pago='anticipo') - aplicar 3% descuento a tarjeta
            anticipos_efectivo = sum(float(p.monto) for p in pagos_pedido_todos if p.tipo_pago == 'anticipo' and p.metodo_pago in ['efectivo', 'transferencia'])
            anticipos_tarjeta = sum(float(p.monto) for p in pagos_pedido_todos if p.tipo_pago == 'anticipo' and p.metodo_pago == 'tarjeta')
            anticipo_neto = anticipos_efectivo + (anticipos_tarjeta * 0.97)
            vendor_stats[pedido.user_id]["anticipos_pedidos"] += anticipo_neto
            vendor_stats[pedido.user_id]["venta_total_pasiva"] += anticipo_neto
            
            # Separar abonos posteriores (tipo_pago='saldo') - aplicar 3% descuento a tarjeta
            abonos_efectivo = sum(float(p.monto) for p in pagos_pedido_todos if p.tipo_pago == 'saldo' and p.metodo_pago in ['efectivo', 'transferencia'])
            abonos_tarjeta = sum(float(p.monto) for p in pagos_pedido_todos if p.tipo_pago == 'saldo' and p.metodo_pago == 'tarjeta')
            abonos_neto = abonos_efectivo + (abonos_tarjeta * 0.97)
            vendor_stats[pedido.user_id]["abonos_pedidos"] += abonos_neto
            vendor_stats[pedido.user_id]["venta_total_pasiva"] += abonos_neto
            
            # Cuentas por cobrar (saldo pendiente)
            vendor_stats[pedido.user_id]["cuentas_por_cobrar"] += float(pedido.saldo_pendiente)

    # Calcular productos liquidados por vendedor
    # Apartados que se completaron en el período
    apartados_pagados = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito",
        Sale.credit_status == "pagado"
    ).all()
    
    print(f"DEBUG: Encontrados {len(apartados_pagados)} apartados pagados")
    print(f"DEBUG: Período de consulta: {start_datetime} a {end_datetime}")
    
    for apartado in apartados_pagados:
        # Verificar si el último abono fue en el período de consulta
        pagos = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
        abonos = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
        
        # Encontrar la fecha del último pago/abono
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
        
        print(f"DEBUG: Apartado {apartado.id}, vendedor: {apartado.vendedor_id}, fecha_ultimo_pago: {fecha_ultimo_pago}")
        print(f"DEBUG: ¿En período? {fecha_ultimo_pago >= start_datetime and fecha_ultimo_pago <= end_datetime}")
        
        # Solo contar si se liquidó en el período de consulta
        if fecha_ultimo_pago >= start_datetime and fecha_ultimo_pago <= end_datetime:
            if apartado.vendedor_id:
                # Inicializar vendedor si no existe
                if apartado.vendedor_id not in vendor_stats:
                    vendor = db.query(User).filter(User.id == apartado.vendedor_id).first()
                    vendedor_name = vendor.email if vendor else "Unknown"
                    vendor_stats[apartado.vendedor_id] = {
                        "vendedor_id": apartado.vendedor_id,
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
                
                # Solo contar el último abono que completó el pago
                if abonos:
                    # Encontrar el abono más reciente
                    ultimo_abono = max(abonos, key=lambda a: a.created_at if a.created_at.tzinfo else a.created_at.replace(tzinfo=tz.utc))
                    monto = float(ultimo_abono.amount)
                    print(f"DEBUG: Sumando ${monto} de último abono al vendedor {apartado.vendedor_id}")
                    vendor_stats[apartado.vendedor_id]["productos_liquidados"] += monto
                elif pagos:
                    # Si no hay abonos, el anticipo inicial completó el pago
                    ultimo_pago = max(pagos, key=lambda p: p.created_at if p.created_at.tzinfo else p.created_at.replace(tzinfo=tz.utc))
                    monto = float(ultimo_pago.amount)
                    print(f"DEBUG: Sumando ${monto} de último pago al vendedor {apartado.vendedor_id}")
                    vendor_stats[apartado.vendedor_id]["productos_liquidados"] += monto
    
    # Pedidos apartados que se completaron en el período
    pedidos_pagados = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.tipo_pedido == 'apartado',
        Pedido.estado == 'pagado'
    ).all()
    
    print(f"DEBUG: Encontrados {len(pedidos_pagados)} pedidos apartados pagados")
    
    for pedido in pedidos_pagados:
        # Obtener todos los pagos del pedido
        pagos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        
        if not pagos:
            continue
        
        # Encontrar la fecha del último pago
        fechas_pagos = []
        for p in pagos:
            if p.created_at.tzinfo is None:
                fechas_pagos.append(p.created_at.replace(tzinfo=tz.utc))
            else:
                fechas_pagos.append(p.created_at)
        fecha_ultimo_pago = max(fechas_pagos)
        
        # Solo contar si se liquidó en el período de consulta
        if fecha_ultimo_pago >= start_datetime and fecha_ultimo_pago <= end_datetime:
            if pedido.user_id:
                # Inicializar vendedor si no existe
                if pedido.user_id not in vendor_stats:
                    user = db.query(User).filter(User.id == pedido.user_id).first()
                    vendedor_name = user.email if user else "Unknown"
                    vendor_stats[pedido.user_id] = {
                        "vendedor_id": pedido.user_id,
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
                
                # Solo contar el último pago que completó el pedido
                ultimo_pago_pedido = max(pagos, key=lambda p: p.created_at if p.created_at.tzinfo else p.created_at.replace(tzinfo=tz.utc))
                monto = float(ultimo_pago_pedido.monto)
                print(f"DEBUG: Sumando ${monto} de último pago de pedido al vendedor {pedido.user_id}")
                vendor_stats[pedido.user_id]["productos_liquidados"] += monto

    # Convert vendor_stats to list
    print("DEBUG: Productos liquidados por vendedor:")
    for vid, vdata in vendor_stats.items():
        if vdata["productos_liquidados"] > 0:
            print(f"  Vendedor {vdata['vendedor_name']}: ${vdata['productos_liquidados']}")
    
    vendedores = list(vendor_stats.values())
    daily_summaries = list(daily_stats.values())
    
    # Calcular "Ventas de liquidación" = Apartados liquidados + Pedidos liquidados
    liquidacion_count = credito_count + pedidos_liquidados_count
    liquidacion_total = total_credito + pedidos_liquidados_total
    
    # Calcular "Ventas pasivas totales" = Todos los anticipos y abonos de ventas NO liquidadas
    ventas_pasivas_total = (apartados_pendientes_anticipos + 
                           apartados_pendientes_abonos_adicionales + 
                           pedidos_pendientes_anticipos + 
                           pedidos_pendientes_abonos)
    
    # Calcular "Cuentas por Cobrar" = Saldo pendiente de apartados + pedidos
    cuentas_por_cobrar = 0.0
    for apartado in apartados_pendientes:
        saldo = float(apartado.total) - float(apartado.amount_paid or 0)
        cuentas_por_cobrar += saldo
    for pedido in pedidos_pendientes:
        cuentas_por_cobrar += float(pedido.saldo_pendiente)
    
    # Sumar costo de apartados y pedidos liquidados
    costo_apartados_pedidos_liquidados = costo_apartados_liquidados + costo_pedidos_liquidados
    
    # Calcular "Utilidades de Productos Liquidados"
    # = (Total de Apartados Liquidados + Total de Pedidos Liquidados) - Costos
    utilidad_productos_liquidados = liquidacion_total - costo_apartados_pedidos_liquidados
    
    # Calcular "Utilidades de Ventas Activas"
    # = (Efectivo + Tarjeta con -3%) - Costo de productos vendidos
    total_tarjeta_neto = total_tarjeta_contado * 0.97  # Tarjeta menos 3%
    total_ventas_activas_neto = total_efectivo_contado + total_tarjeta_neto  # Total con descuento aplicado
    utilidad_ventas_activas = total_ventas_activas_neto - costo_ventas_contado
    
    # Queries adicionales para Resumen Detallado
    
    # Número de solicitudes de apartado (todos los apartados del período, independiente del status)
    num_solicitudes_apartado = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito"
    ).count()
    
    # Número de pedidos hechos (todos los pedidos del período)
    num_pedidos_hechos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime
    ).count()
    
    # Número de apartados vencidos
    num_apartados_vencidos = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.tipo_venta == "credito",
        Sale.credit_status == "vencido"
    ).count()
    
    # Número de pedidos vencidos (SOLO pedidos apartados, NO pedidos de contado)
    num_pedidos_vencidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.tipo_pedido == 'apartado',  # Solo pedidos apartados pueden vencer
        Pedido.estado == "vencido"
    ).count()
    
    # Número de cancelaciones (ventas, apartados, pedidos cancelados)
    num_cancelaciones = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.estado == "cancelado"
    ).count()
    # Agregar apartados cancelados si existe ese status
    num_cancelaciones += db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.credit_status == "cancelado"
    ).count()
    
    # Número de abonos realizados para apartados
    num_abonos_apartados = db.query(CreditPayment).join(Sale).filter(
        Sale.tenant_id == tenant.id,
        CreditPayment.created_at >= start_datetime,
        CreditPayment.created_at <= end_datetime
    ).count()
    
    # Número de abonos realizados para pedidos (SOLO abonos, NO anticipos)
    num_abonos_pedidos = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime,
        PagoPedido.tipo_pago == 'saldo'  # Solo abonos, NO anticipos
    ).count()
    
    # Generar historial de apartados (excluir cancelados y vencidos)
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
    
    # Generar historial de apartados cancelados y vencidos
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
        
        # Calcular total pagado aplicando descuento 3% a tarjetas
        pagos_apartado = db.query(Payment).filter(Payment.sale_id == apartado.id).all()
        pagos_efectivo = sum(float(p.amount) for p in pagos_apartado if p.method in ['efectivo', 'cash', 'transferencia'])
        pagos_tarjeta = sum(float(p.amount) for p in pagos_apartado if p.method in ['tarjeta', 'card'])
        
        abonos_apartado = db.query(CreditPayment).filter(CreditPayment.sale_id == apartado.id).all()
        abonos_efectivo = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['efectivo', 'cash', 'transferencia'])
        abonos_tarjeta = sum(float(p.amount) for p in abonos_apartado if p.payment_method in ['tarjeta', 'card'])
        
        total_pagado_neto = pagos_efectivo + (pagos_tarjeta * 0.97) + abonos_efectivo + (abonos_tarjeta * 0.97)
        
        # Calcular reembolsos y saldos vencidos con descuento 3% aplicado
        if apartado.credit_status == "cancelado":
            reembolso_apartados_cancelados += total_pagado_neto
        elif apartado.credit_status == "vencido":
            saldo_vencido_apartados += total_pagado_neto
        
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
    
    # Generar historial de abonos de apartados
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
    
    # Generar historial de abonos de pedidos (SOLO abonos, NO anticipos)
    todos_abonos_pedidos = db.query(PagoPedido).join(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        PagoPedido.created_at >= start_datetime,
        PagoPedido.created_at <= end_datetime,
        PagoPedido.tipo_pago == 'saldo'  # Solo abonos, NO anticipos
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
            "vendedor": vendedor
        })
    
    # Generar historial de pedidos cancelados y vencidos
    # Los pedidos de contado pueden ser cancelados, pero NO vencidos
    # Los pedidos apartados pueden ser cancelados o vencidos
    pedidos_cancelados_vencidos_query = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        or_(
            Pedido.estado == 'cancelado',  # Cualquier tipo puede ser cancelado
            and_(
                Pedido.tipo_pedido == 'apartado',  # Solo apartados pueden vencer
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
        
        # Calcular total pagado (anticipo + abonos) aplicando descuento 3% a tarjetas
        pagos_pedido_all = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        pagos_efectivo = sum(float(p.monto) for p in pagos_pedido_all if p.metodo_pago in ['efectivo', 'transferencia'])
        pagos_tarjeta = sum(float(p.monto) for p in pagos_pedido_all if p.metodo_pago == 'tarjeta')
        total_pagado_neto = pagos_efectivo + (pagos_tarjeta * 0.97)
        
        # Calcular reembolsos y saldos vencidos con descuento 3% aplicado
        if pedido.estado == "cancelado":
            reembolso_pedidos_cancelados += total_pagado_neto
        elif pedido.estado == "vencido":
            saldo_vencido_pedidos += total_pagado_neto
        
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
    
    # Generar resumen de ventas activas (Ventas y Pedidos de Contado)
    resumen_ventas_activas = []
    
    # Contadores para ventas de contado
    ventas_contado_efectivo_count = 0
    ventas_contado_efectivo_bruto = 0.0
    ventas_contado_tarjeta_count = 0
    ventas_contado_tarjeta_bruto = 0.0
    
    # Contadores para pedidos de contado
    pedidos_contado_efectivo_count = 0
    pedidos_contado_efectivo_bruto = 0.0
    pedidos_contado_tarjeta_count = 0
    pedidos_contado_tarjeta_bruto = 0.0
    
    # Contar ventas de contado
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
    
    # Contar pedidos de contado (ya tenemos pedidos_contado del query anterior)
    for pedido in pedidos_contado:
        pagos = db.query(PagoPedido).filter(PagoPedido.pedido_id == pedido.id).all()
        for pago in pagos:
            if pago.metodo_pago in ['efectivo', 'transferencia']:
                pedidos_contado_efectivo_count += 1
                pedidos_contado_efectivo_bruto += float(pago.monto)
            elif pago.metodo_pago == 'tarjeta':
                pedidos_contado_tarjeta_count += 1
                pedidos_contado_tarjeta_bruto += float(pago.monto)
    
    # Construir tabla de ventas activas con subtotales
    # Ventas de contado
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
        "total": ventas_contado_tarjeta_bruto * 0.97
    })
    resumen_ventas_activas.append({
        "tipo_movimiento": "Venta de contado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": ventas_contado_efectivo_count + ventas_contado_tarjeta_count,
        "subtotal": ventas_contado_efectivo_bruto + ventas_contado_tarjeta_bruto,
        "total": ventas_contado_efectivo_bruto + (ventas_contado_tarjeta_bruto * 0.97)
    })
    
    # Pedidos de contado
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
        "total": pedidos_contado_tarjeta_bruto * 0.97
    })
    resumen_ventas_activas.append({
        "tipo_movimiento": "Pedido de contado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": pedidos_contado_efectivo_count + pedidos_contado_tarjeta_count,
        "subtotal": pedidos_contado_efectivo_bruto + pedidos_contado_tarjeta_bruto,
        "total": pedidos_contado_efectivo_bruto + (pedidos_contado_tarjeta_bruto * 0.97)
    })
    
    # Generar resumen de pagos (Ventas Pasivas)
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
            if pago.metodo_pago in ['efectivo', 'transferencia']:
                anticipos_ped_efectivo_count += 1
                anticipos_ped_efectivo_bruto += float(pago.monto)
            elif pago.metodo_pago == 'tarjeta':
                anticipos_ped_tarjeta_count += 1
                anticipos_ped_tarjeta_bruto += float(pago.monto)
    
    # Contar abonos de pedidos apartados pendientes
    for pedido in pedidos_pendientes:
        pagos_abono = db.query(PagoPedido).filter(
            PagoPedido.pedido_id == pedido.id,
            PagoPedido.tipo_pago == 'saldo'
        ).all()
        for pago in pagos_abono:
            if pago.metodo_pago in ['efectivo', 'transferencia']:
                abonos_ped_efectivo_count += 1
                abonos_ped_efectivo_bruto += float(pago.monto)
            elif pago.metodo_pago == 'tarjeta':
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
        "total": anticipos_apart_tarjeta_bruto * 0.97
    })
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": anticipos_apart_efectivo_count + anticipos_apart_tarjeta_count,
        "subtotal": anticipos_apart_efectivo_bruto + anticipos_apart_tarjeta_bruto,
        "total": anticipos_apart_efectivo_bruto + (anticipos_apart_tarjeta_bruto * 0.97)
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
        "total": abonos_apart_tarjeta_bruto * 0.97
    })
    resumen_pagos.append({
        "tipo_movimiento": "Abono de apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": abonos_apart_efectivo_count + abonos_apart_tarjeta_count,
        "subtotal": abonos_apart_efectivo_bruto + abonos_apart_tarjeta_bruto,
        "total": abonos_apart_efectivo_bruto + (abonos_apart_tarjeta_bruto * 0.97)
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
        "total": anticipos_ped_tarjeta_bruto * 0.97
    })
    resumen_pagos.append({
        "tipo_movimiento": "Anticipo de pedido apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": anticipos_ped_efectivo_count + anticipos_ped_tarjeta_count,
        "subtotal": anticipos_ped_efectivo_bruto + anticipos_ped_tarjeta_bruto,
        "total": anticipos_ped_efectivo_bruto + (anticipos_ped_tarjeta_bruto * 0.97)
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
        "total": abonos_ped_tarjeta_bruto * 0.97
    })
    resumen_pagos.append({
        "tipo_movimiento": "Abono de pedido apartado",
        "metodo_pago": "SUBTOTAL",
        "cantidad_operaciones": abonos_ped_efectivo_count + abonos_ped_tarjeta_count,
        "subtotal": abonos_ped_efectivo_bruto + abonos_ped_tarjeta_bruto,
        "total": abonos_ped_efectivo_bruto + (abonos_ped_tarjeta_bruto * 0.97)
    })

    print("DEBUG: Vendedores en el return:")
    for v in vendedores:
        print(f"  {v['vendedor_name']}: productos_liquidados = {v['productos_liquidados']}")

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ventas_validas": contado_count,  # Cantidad de ventas de contado
        "contado_count": contado_count,
        "credito_count": credito_count,
        "total_contado": total_contado,  # Suma total de ventas de contado
        "total_credito": total_credito,  # Suma total de créditos pagados/entregados
        "liquidacion_count": liquidacion_count,  # Apartados + Pedidos liquidados
        "liquidacion_total": liquidacion_total,  # Suma de apartados + pedidos liquidados
        "ventas_pasivas_total": ventas_pasivas_total,  # Anticipos/abonos de ventas NO liquidadas
        "apartados_pendientes_anticipos": apartados_pendientes_anticipos,
        "apartados_pendientes_abonos_adicionales": apartados_pendientes_abonos_adicionales,
        "pedidos_pendientes_anticipos": pedidos_pendientes_anticipos,
        "pedidos_pendientes_abonos": pedidos_pendientes_abonos,
        "cuentas_por_cobrar": cuentas_por_cobrar,  # Saldo pendiente de apartados + pedidos
        "total_vendido": total_vendido,
        "costo_total": costo_total,
        "costo_ventas_contado": costo_ventas_contado,  # Costo de ventas activas (contado)
        "costo_apartados_pedidos_liquidados": costo_apartados_pedidos_liquidados,  # Costo apartados+pedidos liquidados
        "utilidad_productos_liquidados": utilidad_productos_liquidados,  # Utilidad apartados+pedidos liquidados
        "total_efectivo_contado": total_efectivo_contado,  # Efectivo de ventas activas
        "total_tarjeta_contado": total_tarjeta_contado,  # Tarjeta de ventas activas (sin descuento)
        "total_ventas_activas_neto": total_ventas_activas_neto,  # Total ventas activas con descuento 3%
        "utilidad_ventas_activas": utilidad_ventas_activas,  # Utilidad ventas activas
        "utilidad_total": utilidad_total,
        "piezas_vendidas": piezas_vendidas,
        "pendiente_credito": pendiente_credito,
        "pedidos_count": pedidos_count,
        "pedidos_total": pedidos_total,
        "pedidos_anticipos": pedidos_anticipos,
        "pedidos_saldo": pedidos_saldo,
        "pedidos_liquidados_count": pedidos_liquidados_count,
        "pedidos_liquidados_total": pedidos_liquidados_total,
        "num_piezas_vendidas": num_piezas_vendidas,
        "num_piezas_entregadas": num_piezas_entregadas,
        "num_piezas_apartadas_pagadas": num_piezas_apartadas_pagadas,
        "num_piezas_pedidos_pagados": num_piezas_pedidos_pagados,
        "num_piezas_pedidos_apartados_liquidados": num_piezas_pedidos_apartados_liquidados,
        "num_solicitudes_apartado": num_solicitudes_apartado,
        "num_pedidos_hechos": num_pedidos_hechos,
        "num_cancelaciones": num_cancelaciones,
        "num_apartados_vencidos": num_apartados_vencidos,
        "num_pedidos_vencidos": num_pedidos_vencidos,
        "num_abonos_apartados": num_abonos_apartados,
        "num_abonos_pedidos": num_abonos_pedidos,
        "subtotal_venta_tarjeta": total_tarjeta_contado,  # Subtotal sin descuento
        "total_tarjeta_neto": total_tarjeta_neto,  # Con descuento del 3%
        "reembolso_apartados_cancelados": reembolso_apartados_cancelados,
        "reembolso_pedidos_cancelados": reembolso_pedidos_cancelados,
        "saldo_vencido_apartados": saldo_vencido_apartados,
        "saldo_vencido_pedidos": saldo_vencido_pedidos,
        "vendedores": vendedores,
        "daily_summaries": daily_summaries,
        "sales_details": sales_details,
        "historial_apartados": historial_apartados,
        "historial_pedidos": historial_pedidos,
        "historial_abonos_apartados": historial_abonos_apartados,
        "historial_abonos_pedidos": historial_abonos_pedidos,
        "apartados_cancelados_vencidos": apartados_cancelados_vencidos,
        "pedidos_cancelados_vencidos": pedidos_cancelados_vencidos,
        "resumen_ventas_activas": resumen_ventas_activas,
        "resumen_pagos": resumen_pagos
    }

