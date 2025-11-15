from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import pandas as pd
import io

from ..core.deps import get_db, get_tenant, get_current_user
from ..models.producto_pedido import ProductoPedido, Pedido, PagoPedido, PedidoItem
from ..models.tenant import Tenant
from ..models.user import User
from ..routes.status_history import create_status_history

router = APIRouter()

# Pydantic Models
class ProductoPedidoBase(BaseModel):
    modelo: str  # Renombrado de "name"
    nombre: Optional[str] = None  # Renombrado de "tipo_joya"
    precio: float  # Renombrado de "price"
    cost_price: Optional[float] = None
    category: Optional[str] = None
    default_discount_pct: Optional[float] = None
    # Campos específicos de joyería
    codigo: Optional[str] = None
    marca: Optional[str] = None
    color: Optional[str] = None
    quilataje: Optional[str] = None
    base: Optional[str] = None
    talla: Optional[str] = None
    peso: Optional[str] = None
    peso_gramos: Optional[float] = None
    precio_manual: Optional[float] = None
    # Campos específicos para pedidos
    anticipo_sugerido: Optional[float] = None
    disponible: bool = True

class ProductoPedidoCreate(ProductoPedidoBase):
    pass

class ProductoPedidoUpdate(BaseModel):
    modelo: Optional[str] = None  # Renombrado de "name"
    nombre: Optional[str] = None  # Renombrado de "tipo_joya"
    precio: Optional[float] = None  # Renombrado de "price"
    cost_price: Optional[float] = None
    category: Optional[str] = None
    default_discount_pct: Optional[float] = None
    # Campos específicos de joyería
    codigo: Optional[str] = None
    marca: Optional[str] = None
    color: Optional[str] = None
    quilataje: Optional[str] = None
    base: Optional[str] = None
    talla: Optional[str] = None
    peso: Optional[str] = None
    peso_gramos: Optional[float] = None
    precio_manual: Optional[float] = None
    # Campos específicos para pedidos
    anticipo_sugerido: Optional[float] = None
    disponible: Optional[bool] = None
    active: Optional[bool] = None

class ProductoPedidoOut(ProductoPedidoBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PedidoItemCreate(BaseModel):
    producto_pedido_id: int
    cantidad: int = 1

class PedidoItemOut(BaseModel):
    id: int
    pedido_id: int
    producto_pedido_id: Optional[int] = None
    modelo: Optional[str] = None
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    color: Optional[str] = None
    quilataje: Optional[str] = None
    base: Optional[str] = None
    talla: Optional[str] = None
    peso: Optional[str] = None
    peso_gramos: Optional[float] = None
    cantidad: int
    precio_unitario: float
    total: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PedidoBase(BaseModel):
    producto_pedido_id: Optional[int] = None  # Opcional para compatibilidad hacia atrás
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[str] = None
    cantidad: int = 1  # Mantener para compatibilidad
    anticipo_pagado: float = 0
    tipo_pedido: str = "apartado"  # 'contado' o 'apartado'
    metodo_pago_efectivo: Optional[float] = 0  # Para pedidos de contado
    metodo_pago_tarjeta: Optional[float] = 0  # Para pedidos de contado
    notas_cliente: Optional[str] = None
    items: Optional[List[PedidoItemCreate]] = None  # Lista de items para múltiples productos

class PedidoCreate(PedidoBase):
    user_id: Optional[int] = None  # Vendedor que realiza el pedido

class PedidoUpdate(BaseModel):
    estado: Optional[str] = None
    fecha_entrega_estimada: Optional[datetime] = None
    fecha_entrega_real: Optional[datetime] = None
    notas_internas: Optional[str] = None

class PedidoOut(BaseModel):
    id: int
    producto_pedido_id: Optional[int] = None
    user_id: int
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[str] = None
    cantidad: int
    precio_unitario: float
    total: float
    anticipo_pagado: float
    saldo_pendiente: float
    estado: str
    tipo_pedido: str
    folio_pedido: Optional[str] = None  # Folio único para pedidos
    fecha_entrega_estimada: Optional[datetime] = None
    fecha_entrega_real: Optional[datetime] = None
    notas_cliente: Optional[str] = None
    notas_internas: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Información del producto (para compatibilidad hacia atrás)
    producto: Optional[ProductoPedidoOut] = None
    # Items del pedido (múltiples productos)
    items: Optional[List[PedidoItemOut]] = None
    # Información del vendedor
    vendedor_email: Optional[str] = None
    
    class Config:
        from_attributes = True

class PagoPedidoCreate(BaseModel):
    monto: float
    metodo_pago: str
    tipo_pago: str  # anticipo, saldo, total

class PagoPedidoOut(BaseModel):
    id: int
    monto: float
    metodo_pago: str
    tipo_pago: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Endpoints para Productos sobre Pedido
@router.get("/", response_model=List[ProductoPedidoOut])
def list_productos_pedido(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
    q: Optional[str] = Query(None, description="Search by name, modelo, color"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=2000),
    activo: Optional[bool] = Query(None),
):
    query = db.query(ProductoPedido).filter(ProductoPedido.tenant_id == tenant.id)
    
    if q:
        qn = q.strip().lower()
        if qn:
            query = query.filter(
                or_(
                    func.lower(func.coalesce(ProductoPedido.modelo, '')).like(f"%{qn}%"),
                    func.lower(func.coalesce(ProductoPedido.nombre, '')).like(f"%{qn}%"),
                    func.lower(func.coalesce(ProductoPedido.codigo, '')).like(f"%{qn}%"),
                    func.lower(func.coalesce(ProductoPedido.marca, '')).like(f"%{qn}%"),
                    func.lower(func.coalesce(ProductoPedido.color, '')).like(f"%{qn}%"),
                    func.lower(func.coalesce(ProductoPedido.quilataje, '')).like(f"%{qn}%"),
                    func.lower(func.coalesce(ProductoPedido.talla, '')).like(f"%{qn}%"),
                )
            )
    
    if activo is not None:
        query = query.filter(ProductoPedido.active == activo)
    
    items = query.offset(skip).limit(limit).all()
    return items

@router.post("/", response_model=ProductoPedidoOut)
def create_producto_pedido(
    producto: ProductoPedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    db_producto = ProductoPedido(
        tenant_id=tenant.id,
        **producto.dict()
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

@router.get("/{producto_id}", response_model=ProductoPedidoOut)
def get_producto_pedido(
    producto_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    producto = db.query(ProductoPedido).filter(
        ProductoPedido.id == producto_id,
        ProductoPedido.tenant_id == tenant.id
    ).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return producto

@router.put("/{producto_id}", response_model=ProductoPedidoOut)
def update_producto_pedido(
    producto_id: int,
    producto_update: ProductoPedidoUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    producto = db.query(ProductoPedido).filter(
        ProductoPedido.id == producto_id,
        ProductoPedido.tenant_id == tenant.id
    ).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = producto_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(producto, field, value)
    
    db.commit()
    db.refresh(producto)
    return producto

@router.delete("/{producto_id}")
def delete_producto_pedido(
    producto_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    producto = db.query(ProductoPedido).filter(
        ProductoPedido.id == producto_id,
        ProductoPedido.tenant_id == tenant.id
    ).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado correctamente"}

# Endpoints para Pedidos
@router.get("/pedidos/", response_model=List[PedidoOut])
def list_pedidos(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
    estado: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    from datetime import datetime, timedelta
    
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
    from app.models.user import User
    for pedido in pedidos:
        # Cargar items si existen
        if pedido.items:
            pedido.items = pedido.items  # Ya está cargado por la relación
        elif pedido.producto_pedido_id:
            # Compatibilidad hacia atrás: cargar producto
            producto = db.query(ProductoPedido).filter(
                ProductoPedido.id == pedido.producto_pedido_id,
                ProductoPedido.tenant_id == tenant.id
            ).first()
            pedido.producto = producto
        
        # Agregar información del vendedor
        vendedor = db.query(User).filter(User.id == pedido.user_id).first()
        if vendedor:
            pedido.vendedor_email = vendedor.email
    
    return pedidos

@router.post("/pedidos/", response_model=PedidoOut)
def create_pedido(
    pedido: PedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    from decimal import Decimal
    
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
    
    total = float(total_pedido)
    
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
            notas_cliente=pedido.notas_cliente
        )
        
        db.add(db_pedido)
        db.flush()  # Get the pedido.id
        
        # Generate folio_pedido
        db_pedido.folio_pedido = f"PED-{str(db_pedido.id).zfill(6)}"
        
        # Crear items del pedido
        for item_create in items_to_create:
            producto = productos_map[item_create.producto_pedido_id]
            precio_unitario_item = Decimal(str(producto.precio))
            item_total = float(precio_unitario_item * item_create.cantidad)
            
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
                total=item_total
            )
            db.add(pedido_item)
        
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
            notas_cliente=pedido.notas_cliente
        )

        db.add(db_pedido)
        db.flush()  # Get the pedido.id
        
        # Generate folio_pedido
        db_pedido.folio_pedido = f"PED-{str(db_pedido.id).zfill(6)}"
        
        # Crear items del pedido
        for item_create in items_to_create:
            producto = productos_map[item_create.producto_pedido_id]
            precio_unitario_item = Decimal(str(producto.precio))
            item_total = float(precio_unitario_item * item_create.cantidad)
            
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
                total=item_total
            )
            db.add(pedido_item)
        
        db.commit()
        db.refresh(db_pedido)

        # Crear registros de pago separados por método
        if pedido.metodo_pago_efectivo and pedido.metodo_pago_efectivo > 0:
            pago_efectivo = PagoPedido(
                pedido_id=db_pedido.id,
                monto=Decimal(str(pedido.metodo_pago_efectivo)),
                metodo_pago="efectivo",
                tipo_pago="anticipo"
            )
            db.add(pago_efectivo)

        if pedido.metodo_pago_tarjeta and pedido.metodo_pago_tarjeta > 0:
            pago_tarjeta = PagoPedido(
                pedido_id=db_pedido.id,
                monto=Decimal(str(pedido.metodo_pago_tarjeta)),
                metodo_pago="tarjeta",
                tipo_pago="anticipo"
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
            new_status="pendiente",
            user_id=user.id,
            user_email=user.email,
            notes=f"Pedido apartado creado - Anticipo: ${pedido.anticipo_pagado:.2f} (Efectivo: ${pedido.metodo_pago_efectivo or 0:.2f}, Tarjeta: ${pedido.metodo_pago_tarjeta or 0:.2f})"
        )
        
        # NOTE: Ticket generation moved to frontend to match sales logic
    
    # Cargar items y producto para la respuesta
    db.refresh(db_pedido)
    if db_pedido.items:
        db_pedido.items = db_pedido.items  # Ya está cargado por la relación
    elif db_pedido.producto_pedido_id:
        # Compatibilidad hacia atrás: cargar producto
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == db_pedido.producto_pedido_id
        ).first()
        db_pedido.producto = producto
    
    return db_pedido

@router.put("/pedidos/{pedido_id}", response_model=PedidoOut)
def update_pedido(
    pedido_id: int,
    pedido_update: PedidoUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(
        Pedido.id == pedido_id,
        Pedido.tenant_id == tenant.id
    ).first()
    
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Guardar estado anterior si se va a actualizar el estado
    old_estado = pedido.estado if 'estado' in pedido_update.dict(exclude_unset=True) else None
    
    update_data = pedido_update.dict(exclude_unset=True)
    
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
    
    db.commit()
    db.refresh(pedido)
    return pedido

@router.get("/pedidos/{pedido_id}/pagos")
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

@router.post("/pedidos/{pedido_id}/pagos", response_model=PagoPedidoOut)
def registrar_pago_pedido(
    pedido_id: int,
    pago: PagoPedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    from datetime import datetime, timedelta
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
    from decimal import Decimal
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
    
    # NOTE: Ticket generation for abonos moved to frontend to match sales logic
    
    # Return payment as dict with serialized created_at
    return {
        "id": db_pago.id,
        "monto": float(db_pago.monto),
        "metodo_pago": db_pago.metodo_pago,
        "tipo_pago": db_pago.tipo_pago,
        "created_at": db_pago.created_at.isoformat()
    }

# Import/Export endpoints
@router.post("/import/")
def import_productos_pedido(
    file: UploadFile = File(...),
    mode: str = "add",  # "add" or "replace"
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    try:
        # Leer el archivo Excel
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.lower().str.strip()
        
        # Mapear nombres de columnas
        column_mapping = {
            'modelo': 'modelo',
            'name': 'modelo',  # Compatibilidad con archivos viejos
            'nombre': 'nombre',
            'tipo de joya': 'nombre',
            'tipo_joya': 'nombre',
            'codigo': 'codigo',
            'marca': 'marca',
            'color': 'color',
            'quilataje': 'quilataje',
            'base': 'base',
            'talla': 'talla',
            'peso': 'peso',
            'peso en gramos': 'peso_gramos',
            'peso_gramos': 'peso_gramos',
            'precio': 'precio',
            'price': 'precio',  # Compatibilidad con archivos viejos
            'costo': 'cost_price',
            'cost_price': 'cost_price',
            'precio_manual': 'precio_manual',
            'categoria': 'category',
            'category': 'category',
            'descuento': 'default_discount_pct',
            'default_discount_pct': 'default_discount_pct',
            'anticipo_sugerido': 'anticipo_sugerido',
            'disponible': 'disponible'
        }
        
        # Renombrar columnas
        df = df.rename(columns=column_mapping)
        
        # Validar columnas requeridas
        required_cols = ['codigo']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"Faltan columnas requeridas: {', '.join(missing_cols)}"
            )
        
        # Si es modo replace, eliminar productos existentes
        if mode == "replace":
            db.query(ProductoPedido).filter(ProductoPedido.tenant_id == tenant.id).delete()
        
        # Procesar cada fila
        productos_creados = 0
        productos_actualizados = 0
        
        for _, row in df.iterrows():
            # Validar datos requeridos (solo codigo es obligatorio)
            if pd.isna(row['codigo']):
                continue
            
            # Buscar producto existente por código
            existing_product = db.query(ProductoPedido).filter(
                ProductoPedido.tenant_id == tenant.id,
                ProductoPedido.codigo == str(row['codigo']).strip()
            ).first()
            
            # Preparar datos del producto
            producto_data = {
                'tenant_id': tenant.id,
                'modelo': str(row['modelo']).strip() if 'modelo' in df.columns and not pd.isna(row.get('modelo')) else None,
                'precio': float(row['precio']) if 'precio' in df.columns and not pd.isna(row.get('precio')) else 0.0,
                'nombre': str(row['nombre']).strip() if 'nombre' in df.columns and not pd.isna(row.get('nombre')) else None,
                'codigo': str(row['codigo']).strip(),
                'marca': str(row['marca']).strip() if 'marca' in df.columns and not pd.isna(row.get('marca')) else None,
                'color': str(row['color']).strip() if 'color' in df.columns and not pd.isna(row.get('color')) else None,
                'quilataje': str(row['quilataje']).strip() if 'quilataje' in df.columns and not pd.isna(row.get('quilataje')) else None,
                'base': str(row['base']).strip() if 'base' in df.columns and not pd.isna(row.get('base')) else None,
                'talla': str(row['talla']).strip() if 'talla' in df.columns and not pd.isna(row.get('talla')) else None,
                'peso': str(row['peso']).strip() if 'peso' in df.columns and not pd.isna(row.get('peso')) else None,
                'peso_gramos': float(row['peso_gramos']) if 'peso_gramos' in df.columns and not pd.isna(row.get('peso_gramos')) else None,
                'cost_price': float(row['cost_price']) if 'cost_price' in df.columns and not pd.isna(row.get('cost_price')) else None,
                'precio_manual': float(row['precio_manual']) if 'precio_manual' in df.columns and not pd.isna(row.get('precio_manual')) else None,
                'category': str(row['category']).strip() if 'category' in df.columns and not pd.isna(row.get('category')) else None,
                'default_discount_pct': float(row['default_discount_pct']) if 'default_discount_pct' in df.columns and not pd.isna(row.get('default_discount_pct')) else None,
                'anticipo_sugerido': float(row['anticipo_sugerido']) if 'anticipo_sugerido' in df.columns and not pd.isna(row.get('anticipo_sugerido')) else None,
                'disponible': bool(row['disponible']) if 'disponible' in df.columns and not pd.isna(row.get('disponible')) else True,
                'active': True
            }
            
            if existing_product:
                # Actualizar producto existente
                for key, value in producto_data.items():
                    if key != 'tenant_id':
                        setattr(existing_product, key, value)
                productos_actualizados += 1
            else:
                # Crear nuevo producto
                new_product = ProductoPedido(**producto_data)
                db.add(new_product)
                productos_creados += 1
        
        db.commit()
        
        return {
            "message": f"Importación completada: {productos_creados} productos creados, {productos_actualizados} productos actualizados",
            "productos_creados": productos_creados,
            "productos_actualizados": productos_actualizados
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error procesando archivo: {str(e)}")

@router.get("/export/")
def export_productos_pedido(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user)
):
    try:
        # Obtener productos
        productos = db.query(ProductoPedido).filter(ProductoPedido.tenant_id == tenant.id).all()
        
        # Crear DataFrame
        data = []
        for p in productos:
            data.append({
                'modelo': p.modelo,
                'nombre': p.nombre,
                'codigo': p.codigo,
                'marca': p.marca,
                'color': p.color,
                'quilataje': p.quilataje,
                'base': p.base,
                'talla': p.talla,
                'peso': p.peso,
                'peso_gramos': p.peso_gramos,
                'precio': p.precio,
                'cost_price': p.cost_price,
                'precio_manual': p.precio_manual,
                'category': p.category,
                'default_discount_pct': p.default_discount_pct,
                'anticipo_sugerido': p.anticipo_sugerido,
                'disponible': p.disponible,
                'active': p.active
            })
        
        df = pd.DataFrame(data)
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Productos Pedido', index=False)
        
        output.seek(0)
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=productos_pedido.xlsx"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando productos: {str(e)}")
