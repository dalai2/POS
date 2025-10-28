from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import pandas as pd
import io

from ..core.deps import get_db, get_tenant, get_current_user
from ..models.producto_pedido import ProductoPedido, Pedido, PagoPedido
from ..models.tenant import Tenant
from ..models.user import User

router = APIRouter()

# Pydantic Models
class ProductoPedidoBase(BaseModel):
    name: str
    price: float
    cost_price: Optional[float] = None
    category: Optional[str] = None
    default_discount_pct: Optional[float] = None
    # Campos específicos de joyería
    codigo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    color: Optional[str] = None
    quilataje: Optional[str] = None
    base: Optional[str] = None
    tipo_joya: Optional[str] = None
    talla: Optional[str] = None
    peso_gramos: Optional[float] = None
    precio_manual: Optional[float] = None
    # Campos específicos para pedidos
    anticipo_sugerido: Optional[float] = None
    disponible: bool = True

class ProductoPedidoCreate(ProductoPedidoBase):
    pass

class ProductoPedidoUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    category: Optional[str] = None
    default_discount_pct: Optional[float] = None
    # Campos específicos de joyería
    codigo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    color: Optional[str] = None
    quilataje: Optional[str] = None
    base: Optional[str] = None
    tipo_joya: Optional[str] = None
    talla: Optional[str] = None
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

class PedidoBase(BaseModel):
    producto_pedido_id: int
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[str] = None
    cantidad: int = 1
    anticipo_pagado: float = 0
    notas_cliente: Optional[str] = None

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(BaseModel):
    estado: Optional[str] = None
    fecha_entrega_estimada: Optional[datetime] = None
    fecha_entrega_real: Optional[datetime] = None
    notas_internas: Optional[str] = None

class PedidoOut(BaseModel):
    id: int
    producto_pedido_id: int
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[str] = None
    cantidad: int
    precio_unitario: float
    total: float
    anticipo_pagado: float
    saldo_pendiente: float
    estado: str
    fecha_entrega_estimada: Optional[datetime] = None
    fecha_entrega_real: Optional[datetime] = None
    notas_cliente: Optional[str] = None
    notas_internas: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Información del producto
    producto: Optional[ProductoPedidoOut] = None
    
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
    limit: int = Query(50, ge=1, le=200),
    activo: Optional[bool] = Query(None),
):
    query = db.query(ProductoPedido).filter(ProductoPedido.tenant_id == tenant.id)
    
    if q:
        qn = q.strip().lower()
        if qn:
            query = query.filter(
                or_(
                    func.lower(ProductoPedido.name).like(f"%{qn}%"),
                    func.lower(ProductoPedido.codigo).like(f"%{qn}%"),
                    func.lower(ProductoPedido.marca).like(f"%{qn}%"),
                    func.lower(ProductoPedido.modelo).like(f"%{qn}%"),
                    func.lower(ProductoPedido.color).like(f"%{qn}%"),
                    func.lower(ProductoPedido.quilataje).like(f"%{qn}%"),
                    func.lower(ProductoPedido.tipo_joya).like(f"%{qn}%"),
                    func.lower(ProductoPedido.talla).like(f"%{qn}%"),
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
    query = db.query(Pedido).filter(Pedido.tenant_id == tenant.id)
    
    if estado:
        query = query.filter(Pedido.estado == estado)
    
    pedidos = query.offset(skip).limit(limit).all()
    
    # Agregar información del producto a cada pedido
    for pedido in pedidos:
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id,
            ProductoPedido.tenant_id == tenant.id
        ).first()
        pedido.producto = producto
    
    return pedidos

@router.post("/pedidos/", response_model=PedidoOut)
def create_pedido(
    pedido: PedidoCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    user: User = Depends(get_current_user),
):
    # Verificar que el producto existe
    producto = db.query(ProductoPedido).filter(
        ProductoPedido.id == pedido.producto_pedido_id,
        ProductoPedido.tenant_id == tenant.id,
        ProductoPedido.active == True,
        ProductoPedido.disponible == True
    ).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no disponible")
    
    # Calcular totales
    precio_unitario = float(producto.price)
    total = precio_unitario * pedido.cantidad
    
    # Anticipo flexible - no hay validación estricta
    saldo_pendiente = total - pedido.anticipo_pagado
    
    db_pedido = Pedido(
        tenant_id=tenant.id,
        user_id=user.id,
        precio_unitario=precio_unitario,
        total=total,
        saldo_pendiente=saldo_pendiente,
        **pedido.dict()
    )
    
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    
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
    
    update_data = pedido_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pedido, field, value)
    
    db.commit()
    db.refresh(pedido)
    return pedido

@router.post("/pedidos/{pedido_id}/pagos", response_model=PagoPedidoOut)
def registrar_pago_pedido(
    pedido_id: int,
    pago: PagoPedidoCreate,
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
    
    # Crear el pago
    db_pago = PagoPedido(
        pedido_id=pedido_id,
        **pago.dict()
    )
    db.add(db_pago)
    
    # Actualizar el pedido
    if pago.tipo_pago == "anticipo":
        pedido.anticipo_pagado += pago.monto
        pedido.saldo_pendiente -= pago.monto
    elif pago.tipo_pago == "saldo":
        pedido.saldo_pendiente -= pago.monto
    
    # Si el saldo pendiente es 0 o menos, marcar como entregado
    if pedido.saldo_pendiente <= 0:
        pedido.estado = "entregado"
        pedido.fecha_entrega_real = datetime.now()
    
    db.commit()
    db.refresh(db_pago)
    return db_pago

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
            'nombre': 'name',
            'name': 'name',
            'codigo': 'codigo',
            'marca': 'marca',
            'modelo': 'modelo',
            'color': 'color',
            'quilataje': 'quilataje',
            'base': 'base',
            'tipo de joya': 'tipo_joya',
            'tipo_joya': 'tipo_joya',
            'talla': 'talla',
            'peso': 'peso_gramos',
            'peso_gramos': 'peso_gramos',
            'precio': 'price',
            'price': 'price',
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
        required_cols = ['name', 'price']
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
            # Validar datos requeridos
            if pd.isna(row['name']) or pd.isna(row['price']):
                continue
            
            # Buscar producto existente por código o nombre
            existing_product = None
            if 'codigo' in df.columns and not pd.isna(row.get('codigo')):
                existing_product = db.query(ProductoPedido).filter(
                    ProductoPedido.tenant_id == tenant.id,
                    ProductoPedido.codigo == str(row['codigo']).strip()
                ).first()
            
            if not existing_product:
                existing_product = db.query(ProductoPedido).filter(
                    ProductoPedido.tenant_id == tenant.id,
                    ProductoPedido.name == str(row['name']).strip()
                ).first()
            
            # Preparar datos del producto
            producto_data = {
                'tenant_id': tenant.id,
                'name': str(row['name']).strip(),
                'price': float(row['price']),
                'codigo': str(row['codigo']).strip() if 'codigo' in df.columns and not pd.isna(row.get('codigo')) else None,
                'marca': str(row['marca']).strip() if 'marca' in df.columns and not pd.isna(row.get('marca')) else None,
                'modelo': str(row['modelo']).strip() if 'modelo' in df.columns and not pd.isna(row.get('modelo')) else None,
                'color': str(row['color']).strip() if 'color' in df.columns and not pd.isna(row.get('color')) else None,
                'quilataje': str(row['quilataje']).strip() if 'quilataje' in df.columns and not pd.isna(row.get('quilataje')) else None,
                'base': str(row['base']).strip() if 'base' in df.columns and not pd.isna(row.get('base')) else None,
                'tipo_joya': str(row['tipo_joya']).strip() if 'tipo_joya' in df.columns and not pd.isna(row.get('tipo_joya')) else None,
                'talla': str(row['talla']).strip() if 'talla' in df.columns and not pd.isna(row.get('talla')) else None,
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
                'name': p.name,
                'codigo': p.codigo,
                'marca': p.marca,
                'modelo': p.modelo,
                'color': p.color,
                'quilataje': p.quilataje,
                'base': p.base,
                'tipo_joya': p.tipo_joya,
                'talla': p.talla,
                'peso_gramos': p.peso_gramos,
                'price': p.price,
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
