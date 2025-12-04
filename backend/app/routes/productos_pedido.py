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
    vip_discount_pct: float = 0  # Descuento VIP
    total: Optional[float] = None  # Total opcional para sobrescribir cálculo automático
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
    vip_discount_pct: float = 0  # Descuento VIP
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

        # Leer inicialmente con keep_default_na=False para evitar NaN en celdas vacías
        df = pd.read_excel(io.BytesIO(contents), keep_default_na=False, na_values=[''])

        # Procesar cada columna para convertir datetime objects y otros tipos problemáticos a strings
        for col in df.columns:
            # Verificar si la columna contiene datetime objects
            has_datetime = df[col].apply(lambda x: isinstance(x, pd.Timestamp) if pd.notna(x) else False).any()

            if has_datetime:
                print(f"DEBUG IMPORT: Convirtiendo columna '{col}' de datetime a string", file=sys.stderr)
                # Convertir datetime objects a strings
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, pd.Timestamp) else x)

            # También convertir cualquier otro objeto datetime.datetime
            def convert_datetime_to_talla(x):
                if hasattr(x, 'hour') and hasattr(x, 'minute'):
                    # Si es un datetime que parece representar un número de talla
                    # (ej: 2025-05-04 00:00:00 representa talla 4)
                    if x.year == 2025 and x.month == 5 and x.day <= 31:
                        return str(x.day)
                    else:
                        # Para otros datetime, convertir a string completo
                        return str(x)
                return x

            df[col] = df[col].apply(convert_datetime_to_talla)

        # Forzar tipos string para columnas que deben ser texto
        text_columns = ['nombre', 'modelo', 'marca', 'color', 'quilataje', 'base', 'talla', 'peso', 'codigo', 'categoria', 'category']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
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
            'peso': 'peso_gramos',
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
        
        # Debug: verificar columnas después del mapeo
        import sys
        print(f"DEBUG IMPORT: Columnas después del mapeo: {list(df.columns)}", file=sys.stderr)
        print(f"DEBUG IMPORT: Columnas después del mapeo: {list(df.columns)}")
        if 'quilataje' in df.columns:
            print(f"DEBUG IMPORT: Columna 'quilataje' encontrada. Primeros valores: {df['quilataje'].head(3).tolist()}", file=sys.stderr)
        if 'nombre' in df.columns:
            print(f"DEBUG IMPORT: Columna 'nombre' encontrada. Primeros valores: {df['nombre'].head(3).tolist()}", file=sys.stderr)
        if 'modelo' in df.columns:
            print(f"DEBUG IMPORT: Columna 'modelo' encontrada. Primeros valores: {df['modelo'].head(3).tolist()}", file=sys.stderr)
        if 'peso' in df.columns:
            print(f"DEBUG IMPORT: Columna 'peso' encontrada. Primeros valores: {df['peso'].head(3).tolist()}", file=sys.stderr)
        
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
        
        # Cargar tasas de metal de pedidos para cálculo automático de precios
        from ..models.tasa_metal_pedido import TasaMetalPedido
        
        # Obtener tasas de metal de pedidos para cálculo de precios
        tasas_pedido = db.query(TasaMetalPedido).filter(
            TasaMetalPedido.tenant_id == tenant.id,
            TasaMetalPedido.tipo == 'precio'  # Solo tasas de precio
        ).all()
        
        # Crear diccionario para búsqueda rápida (case-insensitive)
        tasas_precio = {}
        tasas_precio_lower = {}
        for tasa in tasas_pedido:
            tasas_precio[tasa.metal_type] = tasa.rate_per_gram
            tasas_precio_lower[tasa.metal_type.lower()] = tasa.rate_per_gram
        
        print(f"DEBUG IMPORT: Tasas de precio cargadas: {list(tasas_precio.keys())}", file=sys.stderr)
        
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
            
            # Procesar quilataje con validación mejorada
            quilataje_value = None
            if 'quilataje' in df.columns:
                try:
                    raw_quilataje = row['quilataje']  # Acceso directo a la Serie de pandas
                    if pd.notna(raw_quilataje):
                        quilataje_str = str(raw_quilataje).strip()
                        if quilataje_str and quilataje_str.lower() != 'nan':
                            quilataje_value = quilataje_str
                        else:
                            print(f"DEBUG IMPORT: Quilataje vacío o 'nan' para código {row['codigo']}: '{quilataje_str}'", file=sys.stderr)
                    else:
                        print(f"DEBUG IMPORT: Quilataje es NaN para código {row['codigo']}", file=sys.stderr)
                except (KeyError, IndexError) as e:
                    # Si no existe la columna, dejar como None
                    print(f"DEBUG IMPORT: Error accediendo quilataje para código {row['codigo']}: {e}", file=sys.stderr)
                    pass
            else:
                print(f"DEBUG IMPORT: Columna 'quilataje' no está en df.columns para código {row['codigo']}", file=sys.stderr)
            
            # Procesar nombre con validación mejorada
            nombre_value = None
            if 'nombre' in df.columns:
                try:
                    raw_nombre = row['nombre']  # Acceso directo a la Serie de pandas
                    if pd.notna(raw_nombre):
                        nombre_str = str(raw_nombre).strip()
                        if nombre_str and nombre_str.lower() != 'nan':
                            nombre_value = nombre_str
                except (KeyError, IndexError) as e:
                    print(f"DEBUG IMPORT: Error accediendo nombre para código {row['codigo']}: {e}", file=sys.stderr)
            
            # Procesar peso con validación mejorada
            peso_value = None
            if 'peso_gramos' in df.columns:
                try:
                    raw_peso = row['peso_gramos']  # Usar la columna mapeada peso_gramos
                    if pd.notna(raw_peso):
                        peso_str = str(raw_peso).strip()
                        if peso_str and peso_str.lower() != 'nan':
                            peso_value = peso_str
                            print(f"DEBUG IMPORT: peso_value asignado para código {row['codigo']}: '{peso_value}'", file=sys.stderr)
                except (KeyError, IndexError) as e:
                    print(f"DEBUG IMPORT: Error accediendo peso_gramos para código {row['codigo']}: {e}", file=sys.stderr)
            # Fallback: si no hay peso_gramos, intentar con la columna peso original (antes del mapeo)
            elif 'peso' in df.columns:
                try:
                    raw_peso = row['peso']
                    if pd.notna(raw_peso):
                        peso_str = str(raw_peso).strip()
                        if peso_str and peso_str.lower() != 'nan':
                            peso_value = peso_str
                            print(f"DEBUG IMPORT: peso_value (fallback) asignado para código {row['codigo']}: '{peso_value}'", file=sys.stderr)
                except (KeyError, IndexError) as e:
                    print(f"DEBUG IMPORT: Error accediendo peso para código {row['codigo']}: {e}", file=sys.stderr)
            
            # Procesar modelo con validación mejorada
            modelo_value = None
            if 'modelo' in df.columns:
                try:
                    raw_modelo = row['modelo']  # Acceso directo a la Serie de pandas
                    if pd.notna(raw_modelo):
                        modelo_str = str(raw_modelo).strip()
                        if modelo_str and modelo_str.lower() != 'nan':
                            modelo_value = modelo_str
                except (KeyError, IndexError) as e:
                    print(f"DEBUG IMPORT: Error accediendo modelo para código {row['codigo']}: {e}", file=sys.stderr)
            
            # Procesar peso_gramos para cálculo de precio
            peso_gramos_value = None
            if 'peso_gramos' in df.columns:
                try:
                    raw_peso_gramos = row['peso_gramos']
                    if pd.notna(raw_peso_gramos):
                        try:
                            peso_gramos_value = float(raw_peso_gramos)
                            print(f"DEBUG IMPORT: peso_gramos encontrado para código {row['codigo']}: {peso_gramos_value}g", file=sys.stderr)
                        except (ValueError, TypeError):
                            print(f"DEBUG IMPORT: peso_gramos no es numérico para código {row['codigo']}: {raw_peso_gramos}", file=sys.stderr)
                except (KeyError, IndexError) as e:
                    print(f"DEBUG IMPORT: Error accediendo peso_gramos para código {row['codigo']}: {e}", file=sys.stderr)
            # Si no hay peso_gramos, intentar usar 'peso' si es numérico
            elif 'peso' in df.columns and peso_gramos_value is None:
                try:
                    raw_peso = row['peso']
                    if pd.notna(raw_peso):
                        try:
                            # Intentar convertir a float si es numérico
                            peso_gramos_value = float(raw_peso)
                            print(f"DEBUG IMPORT: peso usado como peso_gramos para código {row['codigo']}: {peso_gramos_value}g", file=sys.stderr)
                        except (ValueError, TypeError):
                            print(f"DEBUG IMPORT: peso no es numérico para código {row['codigo']}: {raw_peso} (tipo: {type(raw_peso)})", file=sys.stderr)
                except (KeyError, IndexError) as e:
                    print(f"DEBUG IMPORT: Error accediendo peso para código {row['codigo']}: {e}", file=sys.stderr)
            
            # Debug: mostrar qué valores tenemos para el cálculo
            print(f"DEBUG IMPORT: Para código {row['codigo']}: quilataje_value={quilataje_value}, peso_gramos_value={peso_gramos_value}", file=sys.stderr)
            
            # Calcular precio automáticamente usando tasas de metal de pedidos
            # Si hay quilataje y peso_gramos, calcular precio automáticamente
            precio_calculado = None
            
            if quilataje_value and peso_gramos_value:
                # Buscar tasa de precio para el quilataje (case-insensitive)
                quilataje_lower = quilataje_value.lower().strip()
                tasa_encontrada = None
                
                # Buscar en múltiples formas para asegurar coincidencia case-insensitive bidireccional
                # 1. Coincidencia exacta en tasas_precio
                if quilataje_value in tasas_precio:
                    tasa_encontrada = tasas_precio[quilataje_value]
                    print(f"DEBUG IMPORT: Tasa encontrada (exacta) para quilataje '{quilataje_value}': ${tasa_encontrada}/g", file=sys.stderr)
                # 2. Buscar quilataje en minúsculas en tasas_precio_lower (funciona si tasa está en mayúsculas)
                elif quilataje_lower in tasas_precio_lower:
                    tasa_encontrada = tasas_precio_lower[quilataje_lower]
                    print(f"DEBUG IMPORT: Tasa encontrada (case-insensitive, quilataje lower) para quilataje '{quilataje_value}': ${tasa_encontrada}/g", file=sys.stderr)
                # 3. Buscar quilataje en minúsculas directamente en tasas_precio (por si la tasa está guardada en minúsculas)
                elif quilataje_lower in tasas_precio:
                    tasa_encontrada = tasas_precio[quilataje_lower]
                    print(f"DEBUG IMPORT: Tasa encontrada (quilataje lower en tasas_precio) para quilataje '{quilataje_value}': ${tasa_encontrada}/g", file=sys.stderr)
                # 4. Buscar quilataje original en tasas_precio_lower (por si la tasa está guardada en minúsculas pero el quilataje viene en mayúsculas)
                elif quilataje_value in tasas_precio_lower:
                    tasa_encontrada = tasas_precio_lower[quilataje_value]
                    print(f"DEBUG IMPORT: Tasa encontrada (quilataje original en tasas_precio_lower) para quilataje '{quilataje_value}': ${tasa_encontrada}/g", file=sys.stderr)
                
                if tasa_encontrada:
                    # Calcular: peso_gramos × tasa_precio (redondeado a entero)
                    precio_calculado = round(float(peso_gramos_value) * float(tasa_encontrada))
                    print(f"DEBUG IMPORT: ✅ Precio calculado para código {row['codigo']}: {peso_gramos_value}g × ${tasa_encontrada}/g = ${precio_calculado}", file=sys.stderr)
                else:
                    print(f"DEBUG IMPORT: ⚠️ No se encontró tasa de precio para quilataje '{quilataje_value}' (código {row['codigo']}). Quilataje lower: '{quilataje_lower}'. Tasas disponibles: {list(tasas_precio.keys())}, Tasas lower keys: {list(tasas_precio_lower.keys())}", file=sys.stderr)
            
            # Si no se calculó precio, usar el precio del Excel o 0.0
            if precio_calculado is None:
                if 'precio' in df.columns and not pd.isna(row.get('precio')):
                    try:
                        precio_excel = float(row['precio'])
                        # Solo usar precio del Excel si no es 0 (ya que todos vienen en 0 según el usuario)
                        if precio_excel > 0:
                            precio_calculado = round(precio_excel)
                            print(f"DEBUG IMPORT: Usando precio del Excel para código {row['codigo']}: {precio_calculado}", file=sys.stderr)
                        else:
                            precio_calculado = 0.0
                            print(f"DEBUG IMPORT: Precio del Excel es 0 para código {row['codigo']}, usando 0.0", file=sys.stderr)
                    except (ValueError, TypeError):
                        precio_calculado = 0.0
                        print(f"DEBUG IMPORT: ⚠️ Precio del Excel no es numérico para código {row['codigo']}, usando 0.0", file=sys.stderr)
                else:
                    precio_calculado = 0.0
                    print(f"DEBUG IMPORT: ⚠️ No hay precio para código {row['codigo']}, usando 0.0", file=sys.stderr)
            
            # Preparar datos del producto
            producto_data = {
                'tenant_id': tenant.id,
                'modelo': modelo_value,
                'precio': precio_calculado,
                'nombre': nombre_value,
                'codigo': str(row['codigo']).strip(),
                'marca': str(row['marca']).strip() if 'marca' in df.columns and not pd.isna(row.get('marca')) else None,
                'color': str(row['color']).strip() if 'color' in df.columns and not pd.isna(row.get('color')) else None,
                'quilataje': quilataje_value,
                'base': str(row['base']).strip() if 'base' in df.columns and not pd.isna(row.get('base')) else None,
                'talla': str(row['talla']).strip() if 'talla' in df.columns and not pd.isna(row.get('talla')) else None,
                'peso': peso_value,
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
