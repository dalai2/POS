from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant
from app.models.tenant import Tenant
from app.models.user import User
from app.models.sale import Sale
from app.models.producto_pedido import Pedido


router = APIRouter()


class CustomerReport(BaseModel):
    nombre: str
    telefono: str
    total_gastado: float
    fecha_registro: str
    num_ventas_contado: int
    num_apartados: int
    num_pedidos: int


@router.get("/", response_model=List[CustomerReport])
def get_customers(
    search: Optional[str] = Query(None),
    order_by: Optional[str] = Query("nombre"),
    order_dir: Optional[str] = Query("asc"),
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Get all customers with their total spending and registration date
    """
    
    # Obtener todos los clientes únicos de ventas contado
    ventas_contado = db.query(
        Sale.customer_name.label('nombre'),
        Sale.customer_phone.label('telefono'),
        func.min(Sale.created_at).label('fecha_registro'),
        func.sum(Sale.total).label('total_ventas'),
        func.count(Sale.id).label('num_ventas')
    ).filter(
        Sale.tenant_id == tenant.id,
        Sale.customer_name != None,
        Sale.customer_name != '',
        Sale.tipo_venta == 'contado'
    ).group_by(Sale.customer_name, Sale.customer_phone).all()
    
    # Obtener todos los clientes únicos de apartados (crédito)
    apartados = db.query(
        Sale.customer_name.label('nombre'),
        Sale.customer_phone.label('telefono'),
        func.min(Sale.created_at).label('fecha_registro'),
        func.sum(Sale.amount_paid).label('total_pagado'),
        func.count(Sale.id).label('num_apartados')
    ).filter(
        Sale.tenant_id == tenant.id,
        Sale.customer_name != None,
        Sale.customer_name != '',
        Sale.tipo_venta == 'credito'
    ).group_by(Sale.customer_name, Sale.customer_phone).all()
    
    # Obtener todos los clientes únicos de pedidos
    pedidos_customers = db.query(
        Pedido.cliente_nombre.label('nombre'),
        Pedido.cliente_telefono.label('telefono'),
        func.min(Pedido.created_at).label('fecha_registro'),
        func.sum(Pedido.anticipo_pagado).label('total_pagado'),
        func.count(Pedido.id).label('num_pedidos')
    ).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.cliente_nombre != None,
        Pedido.cliente_nombre != ''
    ).group_by(Pedido.cliente_nombre, Pedido.cliente_telefono).all()
    
    # Combinar clientes usando el TELÉFONO como clave única (o nombre si no hay teléfono)
    customers_dict = {}
    
    # Función helper para obtener la clave única del cliente
    def get_customer_key(nombre: str, telefono: Optional[str]) -> str:
        """Obtiene la clave única del cliente: teléfono si existe, sino nombre"""
        if telefono and telefono.strip():
            return telefono.strip()
        return nombre.lower().strip() if nombre else ""
    
    # Procesar ventas de contado
    for customer in ventas_contado:
        key = get_customer_key(customer.nombre, customer.telefono)
        if not key:  # Saltar si no hay ni teléfono ni nombre
            continue
        if key not in customers_dict:
            customers_dict[key] = {
                'nombre': customer.nombre,
                'telefono': customer.telefono or "",
                'total_gastado': float(customer.total_ventas or 0),
                'fecha_registro': customer.fecha_registro,
                'num_ventas_contado': customer.num_ventas,
                'num_apartados': 0,
                'num_pedidos': 0
            }
        else:
            customers_dict[key]['total_gastado'] += float(customer.total_ventas or 0)
            customers_dict[key]['num_ventas_contado'] += customer.num_ventas
            # Actualizar teléfono si no existe
            if not customers_dict[key]['telefono'] and customer.telefono:
                customers_dict[key]['telefono'] = customer.telefono
            # Mantener la fecha más antigua
            # Normalizar ambas fechas para comparación (remover timezone info si existe)
            fecha_nueva = customer.fecha_registro.replace(tzinfo=None) if customer.fecha_registro and customer.fecha_registro.tzinfo else customer.fecha_registro
            fecha_existente = customers_dict[key]['fecha_registro'].replace(tzinfo=None) if customers_dict[key]['fecha_registro'].tzinfo else customers_dict[key]['fecha_registro']
            if fecha_nueva and fecha_existente and fecha_nueva < fecha_existente:
                customers_dict[key]['fecha_registro'] = customer.fecha_registro
    
    # Procesar apartados
    for customer in apartados:
        key = get_customer_key(customer.nombre, customer.telefono)
        if not key:  # Saltar si no hay ni teléfono ni nombre
            continue
        if key not in customers_dict:
            customers_dict[key] = {
                'nombre': customer.nombre,
                'telefono': customer.telefono or "",
                'total_gastado': float(customer.total_pagado or 0),
                'fecha_registro': customer.fecha_registro,
                'num_ventas_contado': 0,
                'num_apartados': customer.num_apartados,
                'num_pedidos': 0
            }
        else:
            customers_dict[key]['total_gastado'] += float(customer.total_pagado or 0)
            customers_dict[key]['num_apartados'] += customer.num_apartados
            if not customers_dict[key]['telefono'] and customer.telefono:
                customers_dict[key]['telefono'] = customer.telefono
            # Mantener la fecha más antigua
            # Normalizar ambas fechas para comparación (remover timezone info si existe)
            fecha_nueva = customer.fecha_registro.replace(tzinfo=None) if customer.fecha_registro and customer.fecha_registro.tzinfo else customer.fecha_registro
            fecha_existente = customers_dict[key]['fecha_registro'].replace(tzinfo=None) if customers_dict[key]['fecha_registro'].tzinfo else customers_dict[key]['fecha_registro']
            if fecha_nueva and fecha_existente and fecha_nueva < fecha_existente:
                customers_dict[key]['fecha_registro'] = customer.fecha_registro
    
    # Procesar pedidos
    for customer in pedidos_customers:
        key = get_customer_key(customer.nombre, customer.telefono)
        if not key:  # Saltar si no hay ni teléfono ni nombre
            continue
        if key not in customers_dict:
            customers_dict[key] = {
                'nombre': customer.nombre,
                'telefono': customer.telefono or "",
                'total_gastado': float(customer.total_pagado or 0),
                'fecha_registro': customer.fecha_registro,
                'num_ventas_contado': 0,
                'num_apartados': 0,
                'num_pedidos': customer.num_pedidos
            }
        else:
            customers_dict[key]['total_gastado'] += float(customer.total_pagado or 0)
            customers_dict[key]['num_pedidos'] += customer.num_pedidos
            if not customers_dict[key]['telefono'] and customer.telefono:
                customers_dict[key]['telefono'] = customer.telefono
            # Mantener la fecha más antigua
            # Normalizar ambas fechas para comparación (remover timezone info si existe)
            fecha_nueva = customer.fecha_registro.replace(tzinfo=None) if customer.fecha_registro and customer.fecha_registro.tzinfo else customer.fecha_registro
            fecha_existente = customers_dict[key]['fecha_registro'].replace(tzinfo=None) if customers_dict[key]['fecha_registro'].tzinfo else customers_dict[key]['fecha_registro']
            if fecha_nueva and fecha_existente and fecha_nueva < fecha_existente:
                customers_dict[key]['fecha_registro'] = customer.fecha_registro
    
    # Convertir a lista
    customers_list = []
    for customer_data in customers_dict.values():
        customers_list.append(CustomerReport(
            nombre=customer_data['nombre'],
            telefono=customer_data['telefono'],
            total_gastado=customer_data['total_gastado'],
            fecha_registro=customer_data['fecha_registro'].strftime("%Y-%m-%d %H:%M:%S"),
            num_ventas_contado=customer_data['num_ventas_contado'],
            num_apartados=customer_data['num_apartados'],
            num_pedidos=customer_data['num_pedidos']
        ))
    
    # Aplicar filtro de búsqueda
    if search:
        search_lower = search.lower()
        customers_list = [
            c for c in customers_list 
            if search_lower in c.nombre.lower() or search_lower in c.telefono
        ]
    
    # Aplicar ordenamiento
    reverse = order_dir == "desc"
    if order_by == "nombre":
        customers_list.sort(key=lambda x: x.nombre.lower(), reverse=reverse)
    elif order_by == "telefono":
        customers_list.sort(key=lambda x: x.telefono, reverse=reverse)
    elif order_by == "total_gastado":
        customers_list.sort(key=lambda x: x.total_gastado, reverse=reverse)
    elif order_by == "fecha_registro":
        customers_list.sort(key=lambda x: x.fecha_registro, reverse=reverse)
    
    return customers_list

