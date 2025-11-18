"""
Reglas de inventario: determina cuándo se deben crear movimientos de inventario.

Regla general: Los movimientos de inventario solo se crean para cambios directos
en el inventario (creación de productos, importación, ajustes manuales).
NO se crean movimientos automáticos para operaciones de venta, apartados o pedidos.
"""
from typing import Dict, Any, Optional


def should_create_inventory_movement(operation_type: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Determina si se debe crear un movimiento de inventario para una operación.
    
    Args:
        operation_type: Tipo de operación:
            - 'product_create': Creación de producto nuevo
            - 'product_update': Actualización de producto (cambio de stock)
            - 'product_import': Importación masiva de productos
            - 'product_bulk_update': Actualización masiva de productos
            - 'venta_created': Venta de contado creada
            - 'apartado_created': Apartado creado
            - 'pedido_received': Pedido recibido
            - 'pedido_delivered': Pedido entregado
        context: Contexto adicional de la operación (opcional)
    
    Returns:
        True si se debe crear movimiento, False en caso contrario
    """
    # Operaciones que SÍ generan movimientos
    operations_with_movements = {
        'product_create',
        'product_update',
        'product_import',
        'product_bulk_update',
        'manual_adjustment',
        'inventory_adjustment'
    }
    
    # Operaciones que NO generan movimientos (son operaciones de negocio)
    operations_without_movements = {
        'venta_created',
        'apartado_created',
        'pedido_received',
        'pedido_delivered',
        'pedido_created',
        'sale_created'
    }
    
    if operation_type in operations_with_movements:
        return True
    
    if operation_type in operations_without_movements:
        return False
    
    # Por defecto, no crear movimiento (principio de precaución)
    return False


def get_movement_notes(operation_type: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Genera las notas para un movimiento de inventario basado en el tipo de operación.
    
    Args:
        operation_type: Tipo de operación
        context: Contexto adicional
    
    Returns:
        Notas para el movimiento
    """
    notes_map = {
        'product_create': 'Producto creado con stock inicial',
        'product_update': 'Ajuste manual de inventario desde página de productos',
        'product_import': 'Producto importado',
        'product_bulk_update': 'Actualización masiva de productos',
        'manual_adjustment': context.get('notes', 'Ajuste manual de inventario') if context else 'Ajuste manual',
        'inventory_adjustment': context.get('notes', 'Ajuste de inventario') if context else 'Ajuste de inventario'
    }
    
    return notes_map.get(operation_type, 'Movimiento de inventario')


def should_update_stock(operation_type: str) -> bool:
    """
    Determina si se debe actualizar el stock del producto.
    
    Args:
        operation_type: Tipo de operación
    
    Returns:
        True si se debe actualizar stock, False en caso contrario
    """
    # Las mismas operaciones que crean movimientos también actualizan stock
    return should_create_inventory_movement(operation_type)

