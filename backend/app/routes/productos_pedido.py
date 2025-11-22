from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import pandas as pd
import io

from ..core.deps import get_db, get_tenant, get_current_user
from ..core.folio_service import generate_folio
from ..core.serialization_helpers import serialize_decimal, serialize_datetime
from ..models.producto_pedido import ProductoPedido, Pedido, PagoPedido, PedidoItem
from ..models.tenant import Tenant
from ..models.user import User
from ..routes.status_history import create_status_history

router = APIRouter()


def build_producto_snapshot(producto: ProductoPedido) -> dict:
    return {
        "id": producto.id,
        "tenant_id": producto.tenant_id,
        "modelo": producto.modelo,
        "nombre": producto.nombre,
        "precio": serialize_decimal(producto.precio),
        "cost_price": serialize_decimal(producto.cost_price),
        "category": producto.category,
        "default_discount_pct": serialize_decimal(producto.default_discount_pct),
        "codigo": producto.codigo,
        "marca": producto.marca,
        "color": producto.color,
        "quilataje": producto.quilataje,
        "base": producto.base,
        "talla": producto.talla,
        "peso": producto.peso,
        "peso_gramos": serialize_decimal(producto.peso_gramos),
        "precio_manual": serialize_decimal(producto.precio_manual),
        "anticipo_sugerido": serialize_decimal(producto.anticipo_sugerido),
        "disponible": producto.disponible,
        "active": producto.active,
        "created_at": serialize_datetime(producto.created_at),
        "updated_at": serialize_datetime(producto.updated_at),
    }


class SnapshotProducto:
    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)


def hydrate_pedido_item_product(db: Session, tenant_id: int, item: PedidoItem):
    if getattr(item, "producto", None):
        return
    if item.producto_snapshot:
        item.producto = SnapshotProducto(item.producto_snapshot)
        return
    if item.producto_pedido_id:
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == item.producto_pedido_id,
            ProductoPedido.tenant_id == tenant_id
        ).first()
        if producto:
            item.producto = producto
            item.producto_snapshot = build_producto_snapshot(producto)


def hydrate_pedido_products(db: Session, pedido: Pedido, tenant_id: int):
    if pedido.items:
        # Force load and hydrate each item
        for item in pedido.items:
            hydrate_pedido_item_product(db, tenant_id, item)
    elif pedido.producto_pedido_id:
        # No items (modo legacy), try to load product directly
        producto = db.query(ProductoPedido).filter(
            ProductoPedido.id == pedido.producto_pedido_id,
            ProductoPedido.tenant_id == tenant_id
        ).first()
        if producto:
            pedido.producto = producto
        else:
            # Fallback: usar snapshot del primer item si existe
            for item in pedido.items or []:
                if item.producto_snapshot:
                    pedido.producto = SnapshotProducto(item.producto_snapshot)
                    break
    else:
        # No producto_pedido_id, intentar usar snapshot de algún item
        for item in pedido.items or []:
            if item.producto_snapshot:
                pedido.producto = SnapshotProducto(item.producto_snapshot)
                break

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
    producto_snapshot: Optional[dict] = None
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
    notas_cliente: Optional[str] = None
    items: Optional[List[PedidoItemCreate]] = None

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

# Endpoints para Pedidos - MOVIDOS A routes/pedidos.py
# Los endpoints de pedidos ahora están en /pedidos/
# Ver routes/pedidos.py para la gestión de pedidos

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
            'descuento_porcentaje': 'default_discount_pct',
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
                'quilataje': str(row['quilataje']).strip() if 'quilataje' in df.columns and pd.notna(row.get('quilataje')) and str(row.get('quilataje')).strip() != '' else None,
                'base': str(row['base']).strip() if 'base' in df.columns and not pd.isna(row.get('base')) else None,
                'talla': str(row['talla']).strip() if 'talla' in df.columns and not pd.isna(row.get('talla')) else None,
                'peso': str(row['peso']).strip() if 'peso' in df.columns and not pd.isna(row.get('peso')) else None,
                'peso_gramos': float(row['peso_gramos']) if 'peso_gramos' in df.columns and not pd.isna(row.get('peso_gramos')) else None,
                'cost_price': float(row['cost_price']) if 'cost_price' in df.columns and not pd.isna(row.get('cost_price')) else 0.0,
                'precio_manual': float(row['precio_manual']) if 'precio_manual' in df.columns and not pd.isna(row.get('precio_manual')) else None,
                'category': str(row['category']).strip() if 'category' in df.columns and not pd.isna(row.get('category')) else None,
                'default_discount_pct': float(row['default_discount_pct']) if 'default_discount_pct' in df.columns and not pd.isna(row.get('default_discount_pct')) else 0.0,
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
