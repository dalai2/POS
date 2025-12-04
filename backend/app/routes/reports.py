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
from app.models.venta_contado import VentasContado, ItemVentaContado
from app.models.apartado import Apartado, ItemApartado
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
    productos_liquidados_apartados: float  # NUEVO: Productos liquidados de apartados
    productos_liquidados_pedidos: float  # NUEVO: Productos liquidados de pedidos
    ultimo_abono_apartado: Optional[Dict[str, Any]] = None  # NUEVO: Info del último abono de apartado
    ultimo_abono_pedido: Optional[Dict[str, Any]] = None  # NUEVO: Info del último abono de pedido


class ResumenPiezas(BaseModel):
    nombre: str  # Nombre del producto
    modelo: Optional[str]  # Modelo del producto
    quilataje: Optional[str]  # Kilataje
    talla: Optional[str]  # Talla del producto
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
    """Generate corte de caja report using corte_caja_service metrics."""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
    
    from app.services.corte_caja_service import get_detailed_corte_caja as service_get_detailed_corte_caja

    report = service_get_detailed_corte_caja(start_date, end_date, db, tenant)
    resumen_pagos = report.get("resumen_pagos", [])
    resumen_piezas_raw = report.get("resumen_piezas", [])
    vendedores = report.get("vendedores", [])

    def _sum_pasivos(tipo_prefix: str, metodo: str) -> float:
        return sum(
            float(entry.get("total", 0.0))
            for entry in resumen_pagos
            if entry.get("metodo_pago") == metodo
            and entry.get("tipo_movimiento", "").lower().startswith(tipo_prefix.lower())
        )

    pasivos_efectivo = sum(
        float(entry.get("total", 0.0))
        for entry in resumen_pagos
        if entry.get("metodo_pago") == "Efectivo"
    )
    pasivos_tarjeta = sum(
        float(entry.get("total", 0.0))
        for entry in resumen_pagos
        if entry.get("metodo_pago") == "Tarjeta"
    )

    abonos_efectivo = (
        _sum_pasivos("abono de apartado", "Efectivo")
        + _sum_pasivos("abono de pedido apartado", "Efectivo")
    )
    abonos_tarjeta = (
        _sum_pasivos("abono de apartado", "Tarjeta")
        + _sum_pasivos("abono de pedido apartado", "Tarjeta")
    )
    abonos_total = abonos_efectivo + abonos_tarjeta
    
    ventas_contado_total = float(report.get("total_contado", 0.0))
    ventas_credito_total = float(report.get("total_credito", 0.0))
    ventas_contado_count = int(report.get("contado_count", 0))
    ventas_credito_count = int(report.get("credito_count", 0))

    efectivo_ventas = float(report.get("total_efectivo_contado", 0.0))
    tarjeta_ventas = float(report.get("total_tarjeta_contado", 0.0))
    credito_ventas = ventas_credito_total

    total_efectivo = efectivo_ventas + pasivos_efectivo
    total_tarjeta = tarjeta_ventas + pasivos_tarjeta
    returns_count = int(report.get("cancelaciones_ventas_contado_count", 0))
    returns_total = float(report.get("cancelaciones_ventas_contado_monto", 0.0))
    total_revenue = total_efectivo + total_tarjeta + credito_ventas - returns_total
    
    total_cost = float(report.get("costo_total", 0.0))
    total_profit = float(report.get("utilidad_total", 0.0))
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    resumen_piezas = [
        ResumenPiezas(
            nombre=item.get("nombre") or "Sin nombre",
            modelo=item.get("modelo"),
            quilataje=item.get("quilataje"),
            talla=item.get("talla"),
            piezas_vendidas=int(item.get("piezas_vendidas") or 0),
            piezas_pedidas=int(item.get("piezas_pedidas") or 0),
            piezas_apartadas=int(item.get("piezas_apartadas") or 0),
            piezas_liquidadas=int(item.get("piezas_liquidadas") or 0),
            total_piezas=int(item.get("total_piezas") or 0),
        )
        for item in resumen_piezas_raw
    ]

    return CorteDeCajaReport(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        ventas_contado_count=ventas_contado_count,
        ventas_contado_total=ventas_contado_total,
        ventas_credito_count=ventas_credito_count,
        ventas_credito_total=ventas_credito_total,
        efectivo_ventas=efectivo_ventas,
        tarjeta_ventas=tarjeta_ventas,
        credito_ventas=credito_ventas,
        abonos_efectivo=abonos_efectivo,
        abonos_tarjeta=abonos_tarjeta,
        abonos_total=abonos_total,
        total_efectivo=total_efectivo,
        total_tarjeta=total_tarjeta,
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_profit=total_profit,
        profit_margin=profit_margin,
        returns_count=returns_count,
        returns_total=returns_total,
        resumen_piezas=resumen_piezas,
        vendedores=vendedores,
    )

class DailySummaryReport(BaseModel):
    fecha: str
    costo: float
    venta: float
    utilidad: float


class SaleDetailReport(BaseModel):
    id: str  # Puede ser int o string (formato "venta_id-item_id" cuando hay múltiples productos)
    fecha: str
    cliente: str
    piezas: int
    total: float
    estado: str
    tipo: str
    vendedor: str
    efectivo: float = 0.0
    tarjeta: float = 0.0
    codigo_producto: Optional[str] = None
    costo: Optional[float] = None
    ganancia: Optional[float] = None
    is_parent: Optional[bool] = False


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
    id: str  # Puede ser int o string (formato "apartado_id-item_id" cuando hay múltiples productos)
    fecha: str
    cliente: str
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str
    codigo_producto: Optional[str] = None
    costo: Optional[float] = None
    ganancia: Optional[float] = None
    is_parent: Optional[bool] = False

class PedidoHistorialReport(BaseModel):
    id: str  # Cambiado a string para soportar IDs compuestos
    fecha: str
    cliente: str
    producto: str
    cantidad: int
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str
    codigo_producto: Optional[str] = None
    costo: Optional[float] = None
    ganancia: Optional[float] = None
    is_parent: Optional[bool] = False

class AbonoApartadoReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    monto: float
    metodo_pago: str
    vendedor: str
    codigo_producto: Optional[str] = None

class AbonoPedidoReport(BaseModel):
    id: int
    fecha: str
    cliente: str
    producto: str
    monto: float
    metodo_pago: str
    vendedor: str
    codigo_producto: Optional[str] = None

class ApartadoCanceladoVencidoReport(BaseModel):
    id: str  # Puede ser int o string (formato "apartado_id-item_id" cuando hay múltiples productos)
    fecha: str
    cliente: str
    total: float
    anticipo: float
    saldo: float
    estado: str
    vendedor: str
    motivo: str
    codigo_producto: Optional[str] = None
    costo: Optional[float] = None
    ganancia: Optional[float] = None
    is_parent: Optional[bool] = False

class PedidoCanceladoVencidoReport(BaseModel):
    id: str  # Cambiado a string para soportar IDs compuestos
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
    codigo_producto: Optional[str] = None
    costo: Optional[float] = None
    ganancia: Optional[float] = None
    is_parent: Optional[bool] = False

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
    
    # NUEVO: Get ventas de contado by vendedor
    ventas_contado = db.query(VentasContado).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.created_at >= start_datetime,
        VentasContado.created_at <= end_datetime,
        VentasContado.vendedor_id != None
    ).all()
    
    # NUEVO: Get apartados by vendedor
    apartados = db.query(Apartado).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.created_at >= start_datetime,
        Apartado.created_at <= end_datetime,
        Apartado.vendedor_id != None
    ).all()
    
    # NUEVO: Get pedidos by vendedor (user_id)
    pedidos = db.query(Pedido).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.created_at >= start_datetime,
        Pedido.created_at <= end_datetime,
        Pedido.user_id != None
    ).all()
    
    # Aggregate by vendor
    vendor_stats = {}
    
    # Process new ventas de contado
    for venta in ventas_contado:
        vendedor_id = venta.vendedor_id
        if vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == vendedor_id).first()
            vendor_stats[vendedor_id] = {
                "vendedor_id": vendedor_id,
                "vendedor_name": vendor.email if vendor else "Unknown",
                "sales_count": 0,
                "total_sales": 0.0,
                "total_profit": 0.0
            }
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        vendor_stats[vendedor_id]["total_sales"] += float(venta.total)
        vendor_stats[vendedor_id]["total_profit"] += float(venta.utilidad or 0)
    
    # Process new apartados
    for apartado in apartados:
        vendedor_id = apartado.vendedor_id
        if vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == vendedor_id).first()
            vendor_stats[vendedor_id] = {
                "vendedor_id": vendedor_id,
                "vendedor_name": vendor.email if vendor else "Unknown",
                "sales_count": 0,
                "total_sales": 0.0,
                "total_profit": 0.0
            }
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        vendor_stats[vendedor_id]["total_sales"] += float(apartado.total)
        vendor_stats[vendedor_id]["total_profit"] += float(apartado.utilidad or 0)
    
    # Process new pedidos
    for pedido in pedidos:
        vendedor_id = pedido.user_id
        if vendedor_id not in vendor_stats:
            vendor = db.query(User).filter(User.id == vendedor_id).first()
            vendor_stats[vendedor_id] = {
                "vendedor_id": vendedor_id,
                "vendedor_name": vendor.email if vendor else "Unknown",
                "sales_count": 0,
                "total_sales": 0.0,
                "total_profit": 0.0
            }
        
        vendor_stats[vendedor_id]["sales_count"] += 1
        vendor_stats[vendedor_id]["total_sales"] += float(pedido.total)
        # Pedidos no tienen utilidad directa, se calcula desde items si es necesario
    
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

