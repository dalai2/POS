"""
Servicio de negocio para ventas de contado.
Contiene la lógica de negocio para crear y gestionar ventas de contado.
"""
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.venta_contado import VentasContado, ItemVentaContado
from app.models.payment import Payment
from app.core.folio_service import generate_folio


def calculate_sale_totals(
    items: List[Dict[str, Any]],
    discount_amount: Decimal = Decimal("0"),
    tax_rate: Decimal = Decimal("0")
) -> Dict[str, Decimal]:
    """
    Calcula los totales de una venta.
    
    Args:
        items: Lista de items con 'subtotal', 'discount_amount', 'total_price'
        discount_amount: Descuento general aplicado
        tax_rate: Tasa de impuesto
    
    Returns:
        Diccionario con subtotal, discount_amount, tax_amount, total
    """
    subtotal = sum(Decimal(str(item.get('total_price', 0))) for item in items)
    subtotal_val = subtotal.quantize(Decimal("0.01"))
    discount_val = Decimal(str(discount_amount)).quantize(Decimal("0.01"))
    tax_rate_val = Decimal(str(tax_rate)).quantize(Decimal("0.01"))
    taxable = max(Decimal("0"), subtotal_val - discount_val).quantize(Decimal("0.01"))
    tax_amount_val = (taxable * tax_rate_val / Decimal("100")).quantize(Decimal("0.01"))
    total_val = (taxable + tax_amount_val).quantize(Decimal("0.01"))
    
    return {
        'subtotal': subtotal_val,
        'discount_amount': discount_val,
        'tax_rate': tax_rate_val,
        'tax_amount': tax_amount_val,
        'total': total_val
    }


def validate_stock(db: Session, tenant_id: int, items: List[Dict[str, Any]]) -> Dict[int, Product]:
    """
    Valida stock y retorna mapa de productos.
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        items: Lista de items con 'product_id' y 'quantity'
    
    Returns:
        Mapa de product_id -> Product
    
    Raises:
        ValueError: Si algún producto no existe o no hay stock suficiente
    """
    product_map: Dict[int, Product] = {}
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        
        p = db.query(Product).filter(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
            Product.active == True
        ).first()
        
        if not p:
            raise ValueError(f"Producto inválido: {product_id}")
        
        if p.stock is not None and p.stock < quantity:
            raise ValueError(f"Stock insuficiente para {p.name}")
        
        product_map[product_id] = p
    
    return product_map


def create_venta_contado(
    db: Session,
    tenant: Tenant,
    user: User,
    items: List[Dict[str, Any]],
    payments: Optional[List[Dict[str, Any]]] = None,
    discount_amount: Decimal = Decimal("0"),
    tax_rate: Decimal = Decimal("0"),
    vendedor_id: Optional[int] = None,
    utilidad: Optional[Decimal] = None,
    total_cost: Optional[Decimal] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_address: Optional[str] = None,
    build_product_snapshot_func=None
) -> VentasContado:
    """
    Crea una venta de contado.
    
    Args:
        db: Sesión de base de datos
        tenant: Tenant
        user: Usuario que crea la venta
        items: Lista de items de la venta
        payments: Lista de pagos (opcional)
        discount_amount: Descuento general
        tax_rate: Tasa de impuesto
        vendedor_id: ID del vendedor (opcional)
        utilidad: Utilidad calculada (opcional)
        total_cost: Costo total (opcional)
        customer_name: Nombre del cliente (opcional)
        customer_phone: Teléfono del cliente (opcional)
        customer_address: Dirección del cliente (opcional)
        build_product_snapshot_func: Función para crear snapshot del producto
    
    Returns:
        VentasContado creada
    """
    # Validar stock y obtener productos
    product_map = validate_stock(db, tenant.id, items)
    
    # Calcular totales por item
    calculated_items = []
    for item in items:
        p = product_map[item['product_id']]
        q = max(1, int(item.get('quantity', 1)))
        unit = Decimal(str(p.price)).quantize(Decimal("0.01"))
        line_subtotal = (unit * q).quantize(Decimal("0.01"))
        line_disc_pct = Decimal(str(item.get('discount_pct', 0) or 0)).quantize(Decimal("0.01"))
        line_disc_amount = (line_subtotal * line_disc_pct / Decimal('100')).quantize(Decimal('0.01'))
        line_total = (line_subtotal - line_disc_amount).quantize(Decimal('0.01'))
        
        calculated_items.append({
            'product': p,
            'quantity': q,
            'unit_price': unit,
            'discount_pct': line_disc_pct,
            'discount_amount': line_disc_amount,
            'total_price': line_total
        })
        
        # Decrementar stock
        if p.stock is not None:
            p.stock = int(p.stock) - q
    
    # Calcular totales
    totals = calculate_sale_totals(
        [{'total_price': item['total_price']} for item in calculated_items],
        discount_amount,
        tax_rate
    )
    
    # Validar pagos
    paid = Decimal("0")
    if payments:
        for p in payments:
            amt = Decimal(str(p.get('amount', 0)))
            paid += amt
    
    if payments and paid < totals['total']:
        raise ValueError(f"Pago insuficiente: {paid} < {totals['total']}")
    
    # Crear venta
    venta = VentasContado(
        tenant_id=tenant.id,
        user_id=user.id,
        subtotal=totals['subtotal'],
        discount_amount=totals['discount_amount'],
        tax_rate=totals['tax_rate'],
        tax_amount=totals['tax_amount'],
        total=totals['total'],
        vendedor_id=vendedor_id or user.id,
        utilidad=utilidad,
        total_cost=total_cost,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
    )
    db.add(venta)
    db.flush()
    
    # Generar folio
    venta.folio_venta = generate_folio(db, tenant.id, "VENTA")
    
    # Crear items
    for item_data in calculated_items:
        p = item_data['product']
        snapshot = build_product_snapshot_func(p) if build_product_snapshot_func else None
        
        db.add(ItemVentaContado(
            venta_id=venta.id,
            product_id=p.id,
            name=p.name,
            codigo=p.codigo,
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            discount_pct=item_data['discount_pct'],
            discount_amount=item_data['discount_amount'],
            total_price=item_data['total_price'],
            product_snapshot=snapshot
        ))
    
    # Crear pagos
    if payments:
        for p_data in payments:
            amt = Decimal(str(p_data.get('amount', 0))).quantize(Decimal("0.01"))
            db.add(Payment(
                venta_contado_id=venta.id,
                method=p_data.get('method', 'cash'),
                amount=amt
            ))
    
    db.commit()
    db.refresh(venta)
    return venta

