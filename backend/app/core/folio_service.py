"""
Servicio centralizado para generación de folios.
Maneja la generación de folios únicos por tenant y tipo usando FolioCounter.
"""
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.folio_counter import FolioCounter


def get_tenant_slug(db: Session, tenant_id: int) -> str:
    """
    Obtiene el slug del tenant para usar en el folio.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")
    return tenant.slug


def get_next_folio_seq(db: Session, tenant_id: int, tipo: str) -> int:
    """
    Obtiene el siguiente número de secuencia para un tipo de folio.
    Crea el contador si no existe.
    
    Usa with_for_update() para evitar condiciones de carrera en entornos concurrentes.
    NO hace commit - el caller debe hacer commit después de asignar el folio.
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        tipo: Tipo de folio ('VENTA', 'APARTADO', 'PEDIDO')
    
    Returns:
        Número de secuencia actual (antes de incrementar)
    """
    # Intentar con lock primero, si falla usar sin lock
    try:
        # Buscar o crear el contador con lock para evitar condiciones de carrera
        counter = db.query(FolioCounter).filter(
            FolioCounter.tenant_id == tenant_id,
            FolioCounter.tipo == tipo
        ).with_for_update().first()
    except Exception:
        # Si with_for_update falla (puede ser por nivel de aislamiento), intentar sin lock
        counter = db.query(FolioCounter).filter(
            FolioCounter.tenant_id == tenant_id,
            FolioCounter.tipo == tipo
        ).first()
    
    if not counter:
        # Crear nuevo contador
        counter = FolioCounter(
            tenant_id=tenant_id,
            tipo=tipo,
            next_seq=1
        )
        db.add(counter)
        db.flush()  # Flush para obtener el ID, pero no commit
    
    # Obtener secuencia actual y actualizar
    current_seq = counter.next_seq
    counter.next_seq += 1
    # NO hacer commit aquí - el caller debe hacer commit después de asignar el folio
    
    return current_seq


def generate_folio(db: Session, tenant_id: int, tipo: str) -> str:
    """
    Genera un folio único con formato: {PREFIX}-{SEQ:06d}
    (SIN slug del tenant)
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        tipo: Tipo de folio ('VENTA', 'APARTADO', 'PEDIDO')
    
    Returns:
        Folio generado (ej: 'V-000001', 'AP-000001', 'PED-000001')
    """
    # Mapeo de tipo a prefijo
    prefix_map = {
        'VENTA': 'V',
        'APARTADO': 'AP',
        'PEDIDO': 'PED'
    }
    
    if tipo not in prefix_map:
        raise ValueError(f"Tipo de folio inválido: {tipo}. Debe ser 'VENTA', 'APARTADO' o 'PEDIDO'")
    
    prefix = prefix_map[tipo]
    # REMOVIDO: slug del tenant - ahora solo PREFIX-SEQ
    seq = get_next_folio_seq(db, tenant_id, tipo)
    
    return f"{prefix}-{str(seq).zfill(6)}"

