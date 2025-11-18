"""
Helpers genéricos de serialización.
NO contiene lógica de negocio, solo utilidades de formato.
"""
def serialize_decimal(value):
    """Convierte Decimal a float para serialización JSON"""
    if value is None:
        return None
    return float(value)

def serialize_datetime(value):
    """Convierte datetime a string ISO para serialización JSON"""
    if value is None:
        return None
    return value.isoformat()

