from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from typing import Optional, List, Dict, Any, Tuple
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
from app.models.cash_closure import CashClosure

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
    productos_liquidados: float  # Total de productos liquidados por vendedor


class ResumenPiezas(BaseModel):
    nombre: str  # Nombre del producto
    modelo: Optional[str]  # Modelo del producto
    quilataje: Optional[str]  # Kilataje
    piezas_vendidas: int  # Piezas vendidas (contado + apartados pagados)
    piezas_pedidas: int  # Piezas en pedidos (apartado tipo pedido)
    piezas_apartadas: int  # Piezas en apartados (credito pendiente)
    piezas_liquidadas: int  # Piezas liquidadas (apartados/pedidos pagados)
    total_piezas: int  # Total de piezas (suma de todas las categorías)


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
    
    # Resumen de Piezas
    resumen_piezas: List[ResumenPiezas]
    
    # Vendors summary
    vendedores: List[SalesByVendorReport]


def _ensure_cash_closure_table(db: Session) -> None:
    # Lazily ensure the table exists without a migration
    try:
        CashClosure.__table__.create(bind=db.get_bind(), checkfirst=True)
    except Exception:
        # If creation fails, proceed; subsequent operations may still work if table exists
        pass


@router.post("/close-day")
def close_day(
    for_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin),
):
    """
    Cerrar Caja para un día: calcula las métricas existentes del día y las guarda una sola vez.
    Si ya existe un cierre para ese día, devuelve un error 400 informando que ya fue realizado.
    """
    _ensure_cash_closure_table(db)

    target_date = for_date or date.today()

    # Checar si ya está cerrado
    existing = (
        db.query(CashClosure)
        .filter(
            CashClosure.tenant_id == tenant.id,
            CashClosure.closure_date == target_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="El cierre de este día ya fue realizado")

    # Reutilizar cálculo existente de reporte detallado para ese día
    # Llamamos internamente la lógica de get_detailed_corte_caja para un solo día
    from app.services.corte_caja_service import get_detailed_corte_caja as service_get_detailed_corte_caja
    report = service_get_detailed_corte_caja(
        start_date=target_date, end_date=target_date, db=db, tenant=tenant
    )

    # Guardar JSON completo tal cual (sin renombrar métricas)
    closure = CashClosure(
        tenant_id=tenant.id,
        closure_date=target_date,
        data=report,  # Pydantic dict-like return
    )
    db.add(closure)
    db.commit()
    db.refresh(closure)

    return {"status": "ok", "message": "Cierre guardado", "date": target_date.isoformat(), "closure_id": closure.id}


@router.get("/closure")
def get_day_closure(
    for_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Ver Caja: leer métricas guardadas del cierre del día.
    Si no existe cierre, devolver 404 (pendiente).
    """
    _ensure_cash_closure_table(db)

    target_date = for_date or date.today()
    closure = (
        db.query(CashClosure)
        .filter(
            CashClosure.tenant_id == tenant.id,
            CashClosure.closure_date == target_date,
        )
        .first()
    )
    if not closure:
        raise HTTPException(status_code=404, detail="Cierre pendiente para este día")

    return closure.data


@router.get("/closure-range")
def get_closure_range(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
):
    """
    Ver Periodo: sumar cierres guardados en el rango. No recalcula nada.
    Si hay días sin cierre, se omiten o quedan pendientes.
    """
    _ensure_cash_closure_table(db)

    closures = (
        db.query(CashClosure)
        .filter(
            CashClosure.tenant_id == tenant.id,
            CashClosure.closure_date >= start_date,
            CashClosure.closure_date <= end_date,
        )
        .order_by(CashClosure.closure_date.asc())
        .all()
    )

    # Si no hay cierres, regresar vacío
    if not closures:
        return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "days": [], "totals": {}}

    # Sumar métricas numéricas principales del DetailedCorteCajaReport
    numeric_fields = [
        "ventas_validas",
        "contado_count",
        "credito_count",
        "total_contado",
        "total_credito",
        "liquidacion_count",
        "liquidacion_total",
        "ventas_pasivas_total",
        "apartados_pendientes_anticipos",
        "apartados_pendientes_abonos_adicionales",
        "pedidos_pendientes_anticipos",
        "pedidos_pendientes_abonos",
        "cuentas_por_cobrar",
        "total_vendido",
        "costo_total",
        "costo_ventas_contado",
        "costo_apartados_pedidos_liquidados",
        "utilidad_productos_liquidados",
        "total_efectivo_contado",
        "total_tarjeta_contado",
        "total_ventas_activas_neto",
        "utilidad_ventas_activas",
        "utilidad_total",
        "piezas_vendidas",
        "pendiente_credito",
        "pedidos_count",
        "pedidos_total",
        "pedidos_anticipos",
        "pedidos_saldo",
        "pedidos_liquidados_count",
        "pedidos_liquidados_total",
        "num_piezas_vendidas",
        "num_piezas_entregadas",
        "num_piezas_apartadas_pagadas",
        "num_piezas_pedidos_pagados",
        "num_piezas_pedidos_apartados_liquidados",
        "num_solicitudes_apartado",
        "num_pedidos_hechos",
        "num_cancelaciones",
        "num_apartados_vencidos",
        "num_pedidos_vencidos",
        "num_abonos_apartados",
        "num_abonos_pedidos",
        "subtotal_venta_tarjeta",
        "total_tarjeta_neto",
        "reembolso_apartados_cancelados",
        "reembolso_pedidos_cancelados",
        "saldo_vencido_apartados",
        "saldo_vencido_pedidos",
    ]

    totals = {k: 0 for k in numeric_fields}
    days = []
    for c in closures:
        data = c.data or {}
        # keep list of days for UI
        days.append({"date": c.closure_date.isoformat(), "has_closure": True})
        for k in numeric_fields:
            v = data.get(k)
            if isinstance(v, (int, float)):
                totals[k] += v

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": days,
        "totals": totals,
        "closed_days": len(days),
    }
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
    
    cancelaciones_ventas_contado_monto = returns_total
    cancelaciones_ventas_contado_count = returns_count
    piezas_canceladas_ventas = 0
    for retorno in returns:
        sale_items = db.query(SaleItem).filter(SaleItem.sale_id == retorno.id).all()
        piezas_canceladas_ventas += sum(item.quantity for item in sale_items)
    
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
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        if sale.tipo_venta == "contado":
            vendor_stats[vendedor_id]["contado_count"] += 1
            vendor_stats[vendedor_id]["total_contado"] += float(sale.total)
        else:
            vendor_stats[vendedor_id]["credito_count"] += 1
            vendor_stats[vendedor_id]["total_credito"] += float(sale.total)
        vendor_stats[vendedor_id]["total_profit"] += float(sale.utilidad or 0)
    


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

    dashboard: Dict[str, Any]

    # Resumen de Piezas
    resumen_piezas: List[ResumenPiezas]
    total_piezas_por_nombre_sin_liquidadas: Dict[str, int]  # Total de piezas por nombre excluyendo liquidadas

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
    from app.services.corte_caja_service import get_detailed_corte_caja as service_get_detailed_corte_caja
    
    # Default to today if no dates provided
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()

    # Call the service
    return service_get_detailed_corte_caja(start_date, end_date, db, tenant)


def _build_resumen_piezas(
    db: Session,
    all_sales: List[Sale],
    apartados_pendientes: List[Sale],
    pedidos_pendientes: List[Pedido],
    pedidos_liquidados: List[Pedido],
) -> List[dict]:
    resumen_piezas_dict: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

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

    from app.models.producto_pedido import ProductoPedido

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
    """Agrupa el resumen de piezas solo por nombre, sumando todas las categorías excepto liquidadas"""
    total_por_nombre_dict: Dict[str, int] = {}
    
    for pieza in resumen_piezas:
        nombre = pieza["nombre"]
        if nombre not in total_por_nombre_dict:
            total_por_nombre_dict[nombre] = 0
        
        # Sumar todas las categorías excepto liquidadas
        total_por_nombre_dict[nombre] += (
            pieza["piezas_vendidas"]
            + pieza["piezas_pedidas"]
            + pieza["piezas_apartadas"]
        )
    
    return total_por_nombre_dict
