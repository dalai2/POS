export interface InventoryMovement {
  id: number;
  product_id: number;
  product_name: string;
  product_codigo?: string;
  movement_type: 'entrada' | 'salida';
  quantity: number;
  cost?: number;
  notes?: string;
  created_at: string;
  user_id: number;
}

export interface PedidoRecibido {
  id: number;
  folio_pedido: string;
  cliente_nombre: string;
  producto_nombre: string;
  producto_modelo: string;
  cantidad: number;
  precio_unitario: number;
  total: number;
  created_at: string;
  fecha_recepcion: string;
}

export interface PiezaDevuelta {
  id: number;
  tipo: 'venta' | 'pedido';
  folio?: string;
  cliente_nombre?: string;
  producto_nombre: string;
  cantidad: number;
  motivo: string;
  fecha: string;
}

export interface PiezasIngresadasGroup {
  nombre?: string;
  modelo?: string;
  quilataje?: string;
  cantidad_total: number;
  productos: Array<{
    id: number;
    codigo?: string;
    cantidad: number;
    fecha: string;
    tipo: string;
    notas?: string;
  }>;
}

export interface StockGrouped {
  nombre?: string;
  modelo?: string;
  quilataje?: string;
  marca?: string;
  color?: string;
  base?: string;
  tipo_joya?: string;
  talla?: string;
  cantidad_total: number;
  productos: Array<{
    id: number;
    codigo?: string;
    stock: number;
    precio: number;
    costo: number;
  }>;
}

export interface InventoryReport {
  piezas_ingresadas: PiezasIngresadasGroup[];
  historial_entradas: InventoryMovement[];
  historial_salidas: InventoryMovement[];
  pedidos_recibidos: PedidoRecibido[];
  piezas_devueltas: PiezaDevuelta[];
  total_entradas: number;
  total_salidas: number;
  piezas_devueltas_total: number;
  piezas_vendidas_por_nombre?: Record<string, number>;
  piezas_entregadas_por_nombre?: Record<string, number>;
}

export interface StockApartado {
  nombre?: string;
  modelo?: string;
  quilataje?: string;
  marca?: string;
  color?: string;
  base?: string;
  tipo_joya?: string;
  talla?: string;
  cantidad_total: number;
  productos: Array<{
    id: number;
    codigo?: string;
    cantidad: number;
    precio: number;
    folio_apartado: string;
    cliente: string;
    status: string;
    sale_id: number;
  }>;
}

