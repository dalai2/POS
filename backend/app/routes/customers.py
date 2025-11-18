from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, case

from app.core.database import get_db
from app.core.deps import get_current_user, get_tenant
from app.models.tenant import Tenant
from app.models.user import User
from app.models.customer import Customer
from app.models.venta_contado import VentasContado
from app.models.apartado import Apartado
from app.models.producto_pedido import Pedido


router = APIRouter()


class CustomerReport(BaseModel):
    id: int
    nombre: str
    telefono: str
    total_gastado: float
    fecha_registro: str
    num_ventas_contado: int
    num_apartados: int
    num_pedidos: int

    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


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
    Get all customers with their total spending and registration date.
    Uses Customer model (agrupado por teléfono: mismo teléfono = mismo cliente).
    """
    # Obtener todos los clientes de la tabla customers
    customers = db.query(Customer).filter(Customer.tenant_id == tenant.id).all()
    
    # Obtener estadísticas de ventas de contado por cliente (agrupado por teléfono)
    ventas_stats = db.query(
        VentasContado.customer_phone.label('telefono'),
        func.sum(VentasContado.total).label('total_ventas'),
        func.count(VentasContado.id).label('num_ventas')
    ).filter(
        VentasContado.tenant_id == tenant.id,
        VentasContado.customer_name != None,
        VentasContado.customer_name != ''
    ).group_by(VentasContado.customer_phone).all()
    
    # Obtener estadísticas de apartados por cliente (agrupado por teléfono)
    apartados_stats = db.query(
        Apartado.customer_phone.label('telefono'),
        func.sum(Apartado.amount_paid).label('total_pagado'),
        func.count(Apartado.id).label('num_apartados')
    ).filter(
        Apartado.tenant_id == tenant.id,
        Apartado.customer_name != None,
        Apartado.customer_name != ''
    ).group_by(Apartado.customer_phone).all()
    
    # Obtener estadísticas de pedidos por cliente (agrupado por teléfono)
    pedidos_stats = db.query(
        Pedido.cliente_telefono.label('telefono'),
        func.sum(Pedido.anticipo_pagado).label('total_pagado'),
        func.count(Pedido.id).label('num_pedidos')
    ).filter(
        Pedido.tenant_id == tenant.id,
        Pedido.cliente_nombre != None,
        Pedido.cliente_nombre != ''
    ).group_by(Pedido.cliente_telefono).all()
    
    # Crear diccionarios de estadísticas por teléfono
    ventas_dict = {v.telefono or '': {'total': float(v.total_ventas or 0), 'count': v.num_ventas} for v in ventas_stats}
    apartados_dict = {a.telefono or '': {'total': float(a.total_pagado or 0), 'count': a.num_apartados} for a in apartados_stats}
    pedidos_dict = {p.telefono or '': {'total': float(p.total_pagado or 0), 'count': p.num_pedidos} for p in pedidos_stats}
    
    # Construir lista de CustomerReport
    customers_list = []
    for customer in customers:
        phone_key = customer.phone or ''
        ventas_data = ventas_dict.get(phone_key, {'total': 0, 'count': 0})
        apartados_data = apartados_dict.get(phone_key, {'total': 0, 'count': 0})
        pedidos_data = pedidos_dict.get(phone_key, {'total': 0, 'count': 0})
        
        total_gastado = ventas_data['total'] + apartados_data['total'] + pedidos_data['total']
        
        customers_list.append(CustomerReport(
            id=customer.id,
            nombre=customer.name,
            telefono=customer.phone or "",
            total_gastado=total_gastado,
            fecha_registro=customer.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            num_ventas_contado=ventas_data['count'],
            num_apartados=apartados_data['count'],
            num_pedidos=pedidos_data['count']
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


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Update customer name and/or phone.
    Mismo teléfono = mismo cliente (agrupación automática).
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == tenant.id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Si se actualiza el teléfono, verificar si ya existe otro cliente con ese teléfono
    if customer_update.phone is not None and customer_update.phone != customer.phone:
        existing_customer = db.query(Customer).filter(
            Customer.tenant_id == tenant.id,
            Customer.phone == customer_update.phone,
            Customer.id != customer_id
        ).first()
        
        if existing_customer:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe un cliente con el teléfono {customer_update.phone}. Mismo teléfono = mismo cliente."
            )
    
    # Actualizar campos
    if customer_update.name is not None:
        customer.name = customer_update.name
    if customer_update.phone is not None:
        customer.phone = customer_update.phone
    
    customer.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(customer)
    
    return CustomerOut(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        created_at=customer.created_at.isoformat(),
        updated_at=customer.updated_at.isoformat() if customer.updated_at else None
    )

