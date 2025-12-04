"""
Rutas para gestión de pedidos (contado y apartado).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.deps import get_db, get_tenant, get_current_user
from app.core.folio_service import generate_folio
from app.models.producto_pedido import ProductoPedido, Pedido, PagoPedido, PedidoItem
from app.models.tenant import Tenant
from app.models.user import User
from app.routes.status_history import create_status_history
from app.routes.productos_pedido import (
    build_producto_snapshot,
    hydrate_pedido_products,
    PedidoItemCreate,
    PedidoItemOut,
    PedidoBase,
    PedidoCreate,
    PedidoUpdate,
    PedidoOut,
    PagoPedidoCreate,
    PagoPedidoOut
)
from app.services.customer_service import upsert_customer

router = APIRouter()


@router.get("/", response_model=List[PedidoOut])
def list_pedidos(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
    estado: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """Listar todos los pedidos"""
    query = db.query(Pedido).filter(Pedido.tenant_id == tenant.id)
    
    if estado:
        query = query.filter(Pedido.estado == estado)
    
    pedidos = query.offset(skip).limit(limit).all()
    
    # Verificar y actualizar estado vencido (75 días = 2 meses + 15 días)
    fecha_limite = datetime.utcnow() - timedelta(days=75)
    for pedido in pedidos:
        # Si tiene saldo pendiente, no está pagado/entregado/cancelado, y han pasado 75 días
        if (float(pedido.saldo_pendiente) > 0 and 
            pedido.estado not in ['pagado', 'entregado', 'cancelado', 'vencido'] and
            pedido.created_at.replace(tzinfo=None) < fecha_limite):
            pedido.estado = 'vencido'
            db.add(pedido)
    
    # Commit cambios de estados
    db.commit()
    
    # Agregar información del producto, items y vendedor a cada pedido
    for pedido in pedidos:
        hydrate_pedido_products(db, pedido, tenant.id)
        
        # Agregar información del vendedor
        vendedor = db.query(User).filter(User.id == pedido.user_id).first()
        if vendedor:
            pedido.vendedor_email = vendedor.email
    
    return pedidos


@router.post("/", response_model=PedidoOut)
def create_pedido(
    pedido: PedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """Crear un nuevo pedido (contado o apartado)"""
    # Determinar si usar items o producto_pedido_id (compatibilidad hacia atrás)
    items_to_create = []
    
    if pedido.items and len(pedido.items) > 0:
        # Nuevo modo: múltiples items
        items_to_create = pedido.items
    elif pedido.producto_pedido_id:
        # Modo legacy: un solo producto
        items_to_create = [PedidoItemCreate(
            producto_pedido_id=pedido.producto_pedido_id,
            cantidad=pedido.cantidad
        )]
    else:
        raise HTTPException(status_code=400, detail="Debe proporcionar items o producto_pedido_id")
    
    # Validar y cargar productos
    productos_map = {}
    total_pedido = Decimal("0")
    cantidad_total = 0

    for item in items_to_create:
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == item.producto_pedido_id,
            ProductoPedido.tenant_id == tenant.id,
            ProductoPedido.active == True,
            ProductoPedido.disponible == True
        ).first()

        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto no disponible: {item.producto_pedido_id}")

        productos_map[item.producto_pedido_id] = producto
        precio_unitario = Decimal(str(producto.precio))
        item_total = precio_unitario * item.cantidad
        total_pedido += item_total
        cantidad_total += item.cantidad

    # Aplicar descuento VIP al total calculado
    subtotal = float(pedido.total) if pedido.total is not None else float(total_pedido)
    vip_discount_val = subtotal * pedido.vip_discount_pct / 100
    total = subtotal - vip_discount_val

    # Usar el user_id proporcionado o el usuario autenticado
    vendedor_id = pedido.user_id if pedido.user_id else user.id
    
    # Si se proporciona user_id, verificar que el usuario existe
    if pedido.user_id:
        vendedor = db.query(User).filter(
            User.id == pedido.user_id,
            User.tenant_id == tenant.id
        ).first()
        if not vendedor:
            raise HTTPException(status_code=404, detail="Vendedor no encontrado")
    
    # Calcular precio unitario promedio (para compatibilidad)
    precio_unitario_promedio = total / cantidad_total if cantidad_total > 0 else 0
    
    # Lógica según el tipo de pedido
    if pedido.tipo_pedido == "contado":
        # Pedido de contado: debe estar completamente pagado
        total_pagado = (pedido.metodo_pago_efectivo or 0) + (pedido.metodo_pago_tarjeta or 0)
        
        if abs(total_pagado - total) > 0.01:  # Tolerancia de 1 centavo
            raise HTTPException(
                status_code=400, 
                detail=f"El total pagado (${total_pagado:.2f}) debe ser igual al total del pedido (${total:.2f})"
            )
        
        # Generar folio ANTES de crear el pedido (no depende del ID)
        folio_pedido = generate_folio(db, tenant.id, "PEDIDO")
        # Crear pedido con estado 'pagado'
        db_pedido = Pedido(
            tenant_id=tenant.id,
            user_id=vendedor_id,
            precio_unitario=precio_unitario_promedio,
            total=total,
            anticipo_pagado=total,  # Total pagado
            saldo_pendiente=0,  # Sin saldo pendiente
            estado="pagado",
            tipo_pedido="contado",
            producto_pedido_id=pedido.producto_pedido_id,  # Mantener para compatibilidad
            cliente_nombre=pedido.cliente_nombre,
            cliente_telefono=pedido.cliente_telefono,
            cliente_email=pedido.cliente_email,
            cantidad=cantidad_total,
            notas_cliente=pedido.notas_cliente,
            vip_discount_pct=pedido.vip_discount_pct,
            folio_pedido=folio_pedido,  # Asignar folio al crear
        )
        
        db.add(db_pedido)
        db.flush()  # Get the pedido.id
        
        # Crear items del pedido
        for item_create in items_to_create:
            producto = productos_map[item_create.producto_pedido_id]
            precio_unitario_item = Decimal(str(producto.precio))
            item_total = float(precio_unitario_item * item_create.cantidad)
            producto_snapshot = build_producto_snapshot(producto)
            
            pedido_item = PedidoItem(
                pedido_id=db_pedido.id,
                producto_pedido_id=producto.id,
                modelo=producto.modelo,
                nombre=producto.nombre,
                codigo=producto.codigo,
                color=producto.color,
                quilataje=producto.quilataje,
                base=producto.base,
                talla=producto.talla,
                peso=producto.peso,
                peso_gramos=producto.peso_gramos,
                cantidad=item_create.cantidad,
                precio_unitario=float(precio_unitario_item),
                total=item_total,
                producto_snapshot=producto_snapshot
            )
            db.add(pedido_item)
        
        upsert_customer(db, tenant.id, pedido.cliente_nombre, pedido.cliente_telefono)
        db.commit()
        db.refresh(db_pedido)
        
        # Crear registros de pago
        if pedido.metodo_pago_efectivo and pedido.metodo_pago_efectivo > 0:
            pago_efectivo = PagoPedido(
                pedido_id=db_pedido.id,
                monto=Decimal(str(pedido.metodo_pago_efectivo)),
                metodo_pago="efectivo",
                tipo_pago="total"
            )
            db.add(pago_efectivo)
        
        if pedido.metodo_pago_tarjeta and pedido.metodo_pago_tarjeta > 0:
            pago_tarjeta = PagoPedido(
                pedido_id=db_pedido.id,
                monto=Decimal(str(pedido.metodo_pago_tarjeta)),
                metodo_pago="tarjeta",
                tipo_pago="total"
            )
            db.add(pago_tarjeta)
        
        db.commit()
        
        # Registrar estado inicial en el historial
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="pedido",
            entity_id=db_pedido.id,
            old_status=None,
            new_status="pagado",
            user_id=user.id,
            user_email=user.email,
            notes=f"Pedido de contado creado - Pagado completo (Efectivo: ${pedido.metodo_pago_efectivo or 0:.2f}, Tarjeta: ${pedido.metodo_pago_tarjeta or 0:.2f})"
        )
        
    else:  # tipo_pedido == "apartado"
        # Pedido apartado: con anticipo
        # Validar que el anticipo sea mayor a 0
        if pedido.anticipo_pagado <= 0:
            raise HTTPException(
                status_code=400, 
                detail="El anticipo inicial debe ser mayor a 0 para pedidos apartados"
            )
        
        saldo_pendiente = total - pedido.anticipo_pagado

        # Generar folio ANTES de crear el pedido (no depende del ID)
        folio_pedido = generate_folio(db, tenant.id, "PEDIDO")
        db_pedido = Pedido(
            tenant_id=tenant.id,
            user_id=vendedor_id,
            precio_unitario=precio_unitario_promedio,
            total=total,
            anticipo_pagado=pedido.anticipo_pagado,
            saldo_pendiente=saldo_pendiente,
            estado="pendiente",
            tipo_pedido="apartado",
            producto_pedido_id=pedido.producto_pedido_id,  # Mantener para compatibilidad
            cliente_nombre=pedido.cliente_nombre,
            cliente_telefono=pedido.cliente_telefono,
            cliente_email=pedido.cliente_email,
            cantidad=cantidad_total,
            notas_cliente=pedido.notas_cliente,
            vip_discount_pct=pedido.vip_discount_pct,
            folio_pedido=folio_pedido,  # Asignar folio al crear
        )

        db.add(db_pedido)
        db.flush()  # Get the pedido.id
        
        # Crear items del pedido
        for item_create in items_to_create:
            producto = productos_map[item_create.producto_pedido_id]
            precio_unitario_item = Decimal(str(producto.precio))
            item_total = float(precio_unitario_item * item_create.cantidad)
            producto_snapshot = build_producto_snapshot(producto)
            
            pedido_item = PedidoItem(
                pedido_id=db_pedido.id,
                producto_pedido_id=producto.id,
                modelo=producto.modelo,
                nombre=producto.nombre,
                codigo=producto.codigo,
                color=producto.color,
                quilataje=producto.quilataje,
                base=producto.base,
                talla=producto.talla,
                peso=producto.peso,
                peso_gramos=producto.peso_gramos,
                cantidad=item_create.cantidad,
                precio_unitario=float(precio_unitario_item),
                total=item_total,
                producto_snapshot=producto_snapshot
            )
            db.add(pedido_item)
        
        # Crear pago inicial
        db.add(PagoPedido(
            pedido_id=db_pedido.id,
            monto=pedido.anticipo_pagado,
            metodo_pago="efectivo",  # Por defecto, se puede ajustar después
            tipo_pago="anticipo"
        ))
        
        upsert_customer(db, tenant.id, pedido.cliente_nombre, pedido.cliente_telefono)
        db.commit()
        
        # Registrar estado inicial en el historial
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="pedido",
            entity_id=db_pedido.id,
            old_status=None,
            new_status="pendiente",
            user_id=user.id,
            user_email=user.email,
            notes=f"Pedido apartado creado - Anticipo: ${pedido.anticipo_pagado:.2f}, Saldo pendiente: ${saldo_pendiente:.2f}"
        )
    
    db.refresh(db_pedido)
    hydrate_pedido_products(db, db_pedido, tenant.id)
    return db_pedido


@router.get("/{pedido_id}", response_model=PedidoOut)
def get_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """Obtener un pedido por ID"""
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    hydrate_pedido_products(db, pedido, tenant.id)
    return pedido


@router.put("/{pedido_id}", response_model=PedidoOut)
def update_pedido(
    pedido_id: int,
    pedido_update: PedidoUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """Actualizar un pedido"""
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Guardar estado anterior si se va a actualizar el estado
    old_estado = pedido.estado if 'estado' in pedido_update.dict(exclude_unset=True) else None
    
    update_data = pedido_update.dict(exclude_unset=True)
    items_update = update_data.pop('items', None)
    
    # Validar que un pedido pagado no pueda moverse a pendiente o vencido
    if 'estado' in update_data:
        new_estado = update_data['estado']
        if pedido.estado == 'pagado' and new_estado in ['pendiente', 'vencido']:
            raise HTTPException(
                status_code=400, 
                detail="Un pedido pagado no puede cambiar a estado pendiente o vencido"
            )
    
    for field, value in update_data.items():
        setattr(pedido, field, value)
    
    # Si se enviaron nuevos items, reemplazar los existentes
    if items_update is not None:
        items_payload = items_update or []
        if not items_payload:
            # Eliminar todos los items
            db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).delete(synchronize_session=False)
            pedido.cantidad = 0
            pedido.producto_pedido_id = None
        else:
            productos_map = {}
            cantidad_total = 0
            new_items = []
            for raw_item in items_payload:
                item_data = raw_item if isinstance(raw_item, dict) else raw_item.dict()
                item_obj = PedidoItemCreate(**item_data)
                producto = db.query(ProductoPedido).filter(
                    ProductoPedido.id == item_obj.producto_pedido_id,
                    ProductoPedido.tenant_id == tenant.id,
                    ProductoPedido.active == True
                ).first()
                if not producto:
                    raise HTTPException(status_code=404, detail=f"Producto no disponible: {item_obj.producto_pedido_id}")
                productos_map[item_obj.producto_pedido_id] = producto
                precio_unitario_item = Decimal(str(producto.precio))
                item_total = float(precio_unitario_item * item_obj.cantidad)
                cantidad_total += item_obj.cantidad
                new_items.append(PedidoItem(
                    pedido_id=pedido.id,
                    producto_pedido_id=producto.id,
                    modelo=producto.modelo,
                    nombre=producto.nombre,
                    codigo=producto.codigo,
                    color=producto.color,
                    quilataje=producto.quilataje,
                    base=producto.base,
                    talla=producto.talla,
                    peso=producto.peso,
                    peso_gramos=producto.peso_gramos,
                    cantidad=item_obj.cantidad,
                    precio_unitario=float(precio_unitario_item),
                    total=item_total,
                    producto_snapshot=build_producto_snapshot(producto)
                ))
            # Reemplazar items existentes
            db.query(PedidoItem).filter(PedidoItem.pedido_id == pedido.id).delete(synchronize_session=False)
            for new_item in new_items:
                db.add(new_item)
            pedido.cantidad = cantidad_total
            # Compatibilidad: establecer producto_pedido_id si solo hay un item
            if len(new_items) == 1:
                pedido.producto_pedido_id = new_items[0].producto_pedido_id
            else:
                pedido.producto_pedido_id = None
    
    # Registrar cambio de estado si cambió
    if old_estado is not None and old_estado != pedido.estado:
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="pedido",
            entity_id=pedido.id,
            old_status=old_estado,
            new_status=pedido.estado,
            user_id=user.id,
            user_email=user.email,
            notes=f"Estado cambiado manualmente de {old_estado} a {pedido.estado}"
        )
        
        # Si el pedido cambió a "recibido", crear movimiento de inventario
        if pedido.estado == 'recibido':
            from app.models.inventory_movement import InventoryMovement
            from app.models.product import Product
            
            # Buscar producto relacionado (por código o crear uno nuevo si no existe)
            producto_pedido = db.query(ProductoPedido).filter(
                ProductoPedido.id == pedido.producto_pedido_id
            ).first()
            
            if producto_pedido:
                # Buscar producto en inventario por código o crear uno nuevo
                product = None
                if producto_pedido.codigo:
                    product = db.query(Product).filter(
                        Product.tenant_id == tenant.id,
                        Product.codigo == producto_pedido.codigo
                    ).first()
                
                # Si no existe, crear producto nuevo
                if not product:
                    product = Product(
                        tenant_id=tenant.id,
                        name=producto_pedido.nombre or producto_pedido.modelo,
                        codigo=producto_pedido.codigo,
                        modelo=producto_pedido.modelo,
                        marca=producto_pedido.marca,
                        color=producto_pedido.color,
                        quilataje=producto_pedido.quilataje,
                        base=producto_pedido.base,
                        tipo_joya=producto_pedido.nombre,
                        talla=producto_pedido.talla,
                        peso_gramos=producto_pedido.peso_gramos,
                        price=producto_pedido.precio,
                        cost_price=producto_pedido.cost_price,
                        stock=0,
                        active=True
                    )
                    db.add(product)
                    db.flush()
                
                # Crear movimiento de inventario tipo "entrada"
                movement = InventoryMovement(
                    tenant_id=tenant.id,
                    product_id=product.id,
                    user_id=user.id,
                    movement_type="entrada",
                    quantity=pedido.cantidad,
                    cost=float(producto_pedido.cost_price) if producto_pedido.cost_price else None,
                    notes=f"Pedido recibido: {pedido.folio_pedido or f'PED-{pedido.id}'}"
                )
                db.add(movement)
                
                # Actualizar stock del producto
                product.stock += pedido.cantidad
                
                db.flush()
    
    upsert_customer(db, tenant.id, pedido.cliente_nombre, pedido.cliente_telefono)
    db.commit()
    db.refresh(pedido)
    if pedido.items:
        pedido.items = pedido.items
    hydrate_pedido_products(db, pedido, tenant.id)
    return pedido


@router.get("/{pedido_id}/pagos")
def get_pagos_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """Obtener todos los pagos de un pedido (anticipo inicial + abonos posteriores)"""
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Crear lista de pagos combinados
    pagos = []
    
    # Obtener abonos de PagoPedido
    pagos_db = db.query(PagoPedido).filter(
        PagoPedido.pedido_id == pedido_id
    ).order_by(PagoPedido.created_at.asc()).all()
    
    # Separar pagos iniciales (anticipo/total) de abonos
    pagos_iniciales = [p for p in pagos_db if p.tipo_pago in ['anticipo', 'total']]
    abonos = [p for p in pagos_db if p.tipo_pago not in ['anticipo', 'total']]
    
    # Consolidar pagos iniciales en una sola entrada
    if pagos_iniciales:
        # Sumar todos los pagos iniciales
        total_inicial = sum(float(p.monto) for p in pagos_iniciales)
        metodo_efectivo = sum(float(p.monto) for p in pagos_iniciales if p.metodo_pago == 'efectivo')
        metodo_tarjeta = sum(float(p.monto) for p in pagos_iniciales if p.metodo_pago == 'tarjeta')
        
        # Determinar el método de pago a mostrar
        if metodo_efectivo > 0 and metodo_tarjeta > 0:
            metodo_display = f"mixto (E:${metodo_efectivo:.2f} T:${metodo_tarjeta:.2f})"
        elif metodo_tarjeta > 0:
            metodo_display = "tarjeta"
        else:
            metodo_display = "efectivo"
        
        # Agregar un solo registro consolidado para el anticipo inicial
        pagos.append({
            "id": pagos_iniciales[0].id,  # Usar el ID del primer pago para referencia
            "pedido_id": pedido.id,
            "monto": total_inicial,
            "metodo_pago": metodo_display,
            "tipo_pago": pagos_iniciales[0].tipo_pago,
            "notas": "Anticipo inicial",
            "created_at": pagos_iniciales[0].created_at.isoformat()
        })
    elif float(pedido.anticipo_pagado) > 0:
        # Fallback: Si no hay pagos registrados pero hay anticipo en el pedido
        pagos.append({
            "id": -pedido.id,
            "pedido_id": pedido.id,
            "monto": float(pedido.anticipo_pagado),
            "metodo_pago": "efectivo",
            "tipo_pago": "anticipo",
            "notas": "Anticipo inicial",
            "created_at": pedido.created_at.isoformat()
        })
    
    # Agregar abonos individuales
    for p in abonos:
        pagos.append({
            "id": p.id,
            "pedido_id": p.pedido_id,
            "monto": float(p.monto),
            "metodo_pago": p.metodo_pago,
            "tipo_pago": p.tipo_pago if p.tipo_pago else "abono",
            "notas": "Abono",
            "created_at": p.created_at.isoformat()
        })
    
    # Ordenar por fecha (más antiguos primero)
    pagos.sort(key=lambda x: x["created_at"])
    
    return pagos


@router.post("/{pedido_id}/pagos", response_model=PagoPedidoOut)
def registrar_pago_pedido(
    pedido_id: int,
    pago: PagoPedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    """Registrar un pago (abono) para un pedido"""
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Verificar si está vencido (no permitir pagos en pedidos vencidos sin cambiar estado)
    if pedido.estado == 'vencido':
        raise HTTPException(status_code=400, detail="No se pueden registrar pagos en pedidos vencidos. Cambie el estado primero.")
    
    # Crear el pago
    db_pago = PagoPedido(
        pedido_id=pedido_id,
        **pago.dict()
    )
    db.add(db_pago)
    
    # Actualizar el pedido (convertir a Decimal para evitar errores de tipo)
    monto_decimal = Decimal(str(pago.monto))
    if pago.tipo_pago == "anticipo":
        pedido.anticipo_pagado += monto_decimal
        pedido.saldo_pendiente -= monto_decimal
    elif pago.tipo_pago == "saldo":
        pedido.saldo_pendiente -= monto_decimal
    
    # Si el saldo pendiente es 0 o menos, marcar como pagado
    old_estado = pedido.estado
    if pedido.saldo_pendiente <= 0:
        pedido.estado = "pagado"
    
    db.commit()
    db.refresh(db_pago)
    
    # Registrar cambio de estado si cambió
    if old_estado != pedido.estado:
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="pedido",
            entity_id=pedido.id,
            old_status=old_estado,
            new_status=pedido.estado,
            user_id=user.id,
            user_email=user.email,
            notes=f"Pago de ${pago.monto:.2f} - Pedido completamente pagado"
        )
    
    # Return payment as dict with serialized created_at
    return {
        "id": db_pago.id,
        "monto": float(db_pago.monto),
        "metodo_pago": db_pago.metodo_pago,
        "tipo_pago": db_pago.tipo_pago,
        "created_at": db_pago.created_at.isoformat()
    }

