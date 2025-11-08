from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class StatusHistory(Base):
    __tablename__ = "status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Tipo de entidad (sale o pedido)
    entity_type = Column(String(20), nullable=False)  # "sale" or "pedido"
    entity_id = Column(Integer, nullable=False)  # ID de la venta o pedido
    
    # Información del cambio
    old_status = Column(String(50), nullable=True)  # Estado anterior (null para creación)
    new_status = Column(String(50), nullable=False)  # Nuevo estado
    
    # Usuario que hizo el cambio
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_email = Column(String(255), nullable=False)  # Guardamos el email por si el usuario se elimina
    
    # Notas opcionales
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")

