from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .tenant import Base

class ProductoPedido(Base):
    __tablename__ = "productos_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Campos base
    modelo = Column(String(255), nullable=False)  # Renombrado de "name"
    nombre = Column(String(50), nullable=True, index=True)  # Renombrado de "tipo_joya"
    precio = Column(Numeric(10, 2), nullable=False, default=0)  # Renombrado de "price"
    cost_price = Column(Numeric(10, 2), nullable=False, default=0)
    category = Column(String(100), nullable=True, index=True)
    default_discount_pct = Column(Numeric(5, 2), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Campos específicos de joyería
    codigo = Column(String(100), nullable=True, index=True)
    marca = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    quilataje = Column(String(20), nullable=True, index=True)
    base = Column(String(50), nullable=True)
    talla = Column(String(20), nullable=True)
    peso = Column(String(100), nullable=True)  # Peso descriptivo
    peso_gramos = Column(Numeric(10, 3), nullable=True)
    precio_manual = Column(Numeric(10, 2), nullable=True)
    
    # Campos específicos para pedidos
    anticipo_sugerido = Column(Numeric(10, 2))  # Anticipo sugerido, no obligatorio
    disponible = Column(Boolean, default=True)  # Si está disponible para pedidos

class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    producto_pedido_id = Column(Integer, ForeignKey("productos_pedido.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información del cliente
    cliente_nombre = Column(String(255), nullable=False)
    cliente_telefono = Column(String(20))
    cliente_email = Column(String(255))
    
    # Detalles del pedido
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    folio_pedido = Column(String(50), nullable=True, index=True)  # Folio único para pedidos
    
    # Pagos
    anticipo_pagado = Column(Numeric(10, 2), default=0)
    saldo_pendiente = Column(Numeric(10, 2), nullable=False)
    
    # Estado del pedido
    estado = Column(String(20), default="pendiente")  # pendiente, confirmado, en_proceso, entregado, cancelado, recibido, vencido
    tipo_pedido = Column(String(20), default="apartado")  # contado, apartado
    fecha_entrega_estimada = Column(DateTime(timezone=True))
    fecha_entrega_real = Column(DateTime(timezone=True))
    
    # Notas
    notas_cliente = Column(Text)
    notas_internas = Column(Text)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PagoPedido(Base):
    __tablename__ = "pagos_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    
    # Información del pago
    monto = Column(Numeric(10, 2), nullable=False)
    metodo_pago = Column(String(20), nullable=False)  # efectivo, tarjeta, transferencia
    tipo_pago = Column(String(20), nullable=False)  # anticipo, saldo, total
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
