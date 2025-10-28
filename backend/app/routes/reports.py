from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.sale import Sale
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
    current_user: User = Depends(get_current_user)
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
    
    # Convert to datetime for queries
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get all sales in date range (excluding returns)
    sales_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.return_of_id == None
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


class DetailedCorteCajaReport(BaseModel):
    start_date: str
    end_date: str
    generated_at: str

    # Resumen general
    ventas_validas: int
    contado_count: int
    credito_count: int
    total_vendido: float
    costo_total: float
    utilidad_total: float
    piezas_vendidas: int
    pendiente_credito: float

    # Vendedores
    vendedores: List[SalesByVendorReport]

    # Resumen diario
    daily_summaries: List[DailySummaryReport]

    # Detalle de ventas
    sales_details: List[SaleDetailReport]


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
    current_user: User = Depends(get_current_user)
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

    # Convert to datetime for queries
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    # Get all sales in date range (excluding returns)
    sales_query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.created_at >= start_datetime,
        Sale.created_at <= end_datetime,
        Sale.return_of_id == None
    )

    all_sales = sales_query.all()

    # Initialize counters for summary
    ventas_validas = len(all_sales)
    contado_count = 0
    credito_count = 0
    total_vendido = 0.0
    costo_total = 0.0
    utilidad_total = 0.0
    piezas_vendidas = 0
    pendiente_credito = 0.0

    # Group sales by vendedor for vendor stats
    vendor_stats = {}
    daily_stats = {}
    sales_details = []

    for sale in all_sales:
        # Update summary counters
        if sale.tipo_venta == "contado":
            contado_count += 1
        else:  # credito
            credito_count += 1
            pendiente_credito += float(sale.total)

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
                "total_profit": 0.0
            }

        vendor_stats[sale.vendedor_id]["sales_count"] += 1
        if sale.tipo_venta == "contado":
            vendor_stats[sale.vendedor_id]["contado_count"] += 1
            vendor_stats[sale.vendedor_id]["total_contado"] += float(sale.total)
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
        efectivo_amount = sum(float(p.amount) for p in payments if p.method in ['efectivo', 'cash'])
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

    # Convert vendor_stats to list
    vendedores = list(vendor_stats.values())
    daily_summaries = list(daily_stats.values())

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ventas_validas": ventas_validas,
        "contado_count": contado_count,
        "credito_count": credito_count,
        "total_vendido": total_vendido,
        "costo_total": costo_total,
        "utilidad_total": utilidad_total,
        "piezas_vendidas": piezas_vendidas,
        "pendiente_credito": pendiente_credito,
        "vendedores": vendedores,
        "daily_summaries": daily_summaries,
        "sales_details": sales_details
    }

