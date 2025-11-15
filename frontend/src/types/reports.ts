export interface CorteDeCajaReport {
  start_date: string;
  end_date: string;
  ventas_contado_count: number;
  ventas_contado_total: number;
  ventas_credito_count: number;
  ventas_credito_total: number;
  efectivo_ventas: number;
  tarjeta_ventas: number;
  credito_ventas: number;
  abonos_efectivo: number;
  abonos_tarjeta: number;
  abonos_total: number;
  pedidos_count: number;
  pedidos_total: number;
  pedidos_anticipos: number;
  pedidos_saldo: number;
  pedidos_efectivo: number;
  pedidos_tarjeta: number;
  pedidos_pagos_total: number;
  total_efectivo: number;
  total_tarjeta: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  profit_margin: number;
  returns_count: number;
  returns_total: number;
  vendedores: Array<{
    vendedor_id: number;
    vendedor_name: string;
    sales_count: number;
    contado_count: number;
    credito_count: number;
    total_contado: number;
    total_credito: number;
    total_profit: number;
  }>;
}

export interface ResumenPiezas {
  nombre: string;
  modelo: string | null;
  quilataje: string | null;
  piezas_vendidas: number;
  piezas_pedidas: number;
  piezas_apartadas: number;
  piezas_liquidadas: number;
  total_piezas: number;
}

export interface DashboardValue {
  monto: number;
  count: number;
}

export interface DashboardTarjetaValue {
  bruto: number;
  neto: number;
  count: number;
}

export interface DashboardBreakdown {
  total: DashboardValue;
  efectivo: DashboardValue;
  tarjeta: DashboardTarjetaValue;
}

export interface DashboardMetodoDetalle {
  efectivo?: DashboardValue;
  tarjeta?: DashboardTarjetaValue;
  total?: DashboardValue;
}

export interface DashboardMetrics {
  ventas: {
    contado: DashboardValue;
    pedidos_contado: DashboardValue;
    total: DashboardValue;
  };
  anticipos: {
    apartados: DashboardBreakdown;
    pedidos_apartados: DashboardBreakdown;
    total: DashboardValue;
  };
  abonos: {
    apartados: DashboardBreakdown;
    pedidos_apartados: DashboardBreakdown;
    total: DashboardValue;
  };
  liquidaciones: {
    apartados: DashboardValue;
    pedidos_apartados: DashboardValue;
    total: DashboardValue;
  };
  vencimientos: {
    apartados: DashboardValue;
    pedidos_apartados: DashboardValue;
    total: DashboardValue;
  };
  cancelaciones: {
    ventas_contado: DashboardValue;
    pedidos_contado: DashboardValue;
    pedidos_apartados: DashboardValue;
    apartados: DashboardValue;
    total: DashboardValue;
  };
  metodos_pago: {
    ventas_contado: DashboardMetodoDetalle;
    pedidos_contado: DashboardMetodoDetalle;
    anticipos_apartados: DashboardMetodoDetalle;
    anticipos_pedidos_apartados: DashboardMetodoDetalle;
    abonos_apartados: DashboardMetodoDetalle;
    abonos_pedidos_apartados: DashboardMetodoDetalle;
  };
  contadores: Record<string, number>;
}

export interface DetailedCorteCajaReport {
  start_date: string;
  end_date: string;
  generated_at: string;
  ventas_validas: number;
  contado_count: number;
  credito_count: number;
  total_contado: number;
  total_credito: number;
  liquidacion_count: number;
  liquidacion_total: number;
  ventas_pasivas_total: number;
  apartados_pendientes_anticipos: number;
  apartados_pendientes_abonos_adicionales: number;
  pedidos_pendientes_anticipos: number;
  pedidos_pendientes_abonos: number;
  cuentas_por_cobrar: number;
  total_vendido: number;
  costo_total: number;
  costo_ventas_contado: number;
  costo_apartados_pedidos_liquidados: number;
  utilidad_productos_liquidados: number;
  total_efectivo_contado: number;
  total_tarjeta_contado: number;
  utilidad_ventas_activas: number;
  utilidad_total: number;
  piezas_vendidas: number;
  pendiente_credito: number;
  pedidos_count: number;
  pedidos_total: number;
  pedidos_anticipos: number;
  pedidos_saldo: number;
  pedidos_liquidados_count: number;
  pedidos_liquidados_total: number;
  num_piezas_vendidas: number;
  num_piezas_entregadas: number;
  num_piezas_apartadas_pagadas: number;
  num_piezas_pedidos_pagados: number;
  num_piezas_pedidos_apartados_liquidados: number;
  num_solicitudes_apartado: number;
  num_pedidos_hechos: number;
  resumen_piezas: ResumenPiezas[];
  total_piezas_por_nombre_sin_liquidadas?: Record<string, number>;  // Total de piezas por nombre excluyendo liquidadas
  dashboard?: DashboardMetrics;
  resumen_ventas_activas: Array<{
    tipo_movimiento: string;
    metodo_pago: string;
    cantidad_operaciones: number;
    subtotal: number;
    total: number;
  }>;
  resumen_pagos: Array<{
    tipo_movimiento: string;
    metodo_pago: string;
    cantidad_operaciones: number;
    subtotal: number;
    total: number;
  }>;
  num_cancelaciones: number;
  num_apartados_vencidos: number;
  num_pedidos_vencidos: number;
  num_abonos_apartados: number;
  num_abonos_pedidos: number;
  subtotal_venta_tarjeta: number;
  total_tarjeta_neto: number;
  reembolso_apartados_cancelados: number;
  reembolso_pedidos_cancelados: number;
  saldo_vencido_apartados: number;
  saldo_vencido_pedidos: number;
  vendedores: Array<{
    vendedor_id: number;
    vendedor_name: string;
    sales_count: number;
    contado_count: number;
    credito_count: number;
    total_contado: number;
    total_credito: number;
    total_profit: number;
    total_efectivo_contado: number;
    total_tarjeta_contado: number;
    total_tarjeta_neto: number;
    anticipos_apartados: number;
    anticipos_pedidos: number;
    abonos_apartados: number;
    abonos_pedidos: number;
    ventas_total_activa: number;
    venta_total_pasiva: number;
    cuentas_por_cobrar: number;
    productos_liquidados: number;
  }>;
  daily_summaries: Array<{
    fecha: string;
    costo: number;
    venta: number;
    utilidad: number;
  }>;
  sales_details: Array<{
    id: number;
    fecha: string;
    cliente: string;
    piezas: number;
    total: number;
    estado: string;
    tipo: string;
    vendedor: string;
    efectivo: number;
    tarjeta: number;
    producto?: string;
    cantidad?: number;
  }>;
  historial_apartados: Array<{
    id: number;
    fecha: string;
    cliente: string;
    total: number;
    anticipo: number;
    saldo: number;
    estado: string;
    vendedor: string;
  }>;
  historial_pedidos: Array<{
    id: number;
    fecha: string;
    cliente: string;
    producto: string;
    cantidad: number;
    total: number;
    anticipo: number;
    saldo: number;
    estado: string;
    vendedor: string;
  }>;
  historial_abonos_apartados: Array<{
    id: number;
    fecha: string;
    cliente: string;
    monto: number;
    metodo_pago: string;
    vendedor: string;
  }>;
  historial_abonos_pedidos: Array<{
    id: number;
    fecha: string;
    cliente: string;
    producto: string;
    monto: number;
    metodo_pago: string;
    vendedor: string;
  }>;
  apartados_cancelados_vencidos: Array<{
    id: number;
    fecha: string;
    cliente: string;
    total: number;
    anticipo: number;
    saldo: number;
    estado: string;
    vendedor: string;
    motivo: string;
  }>;
  pedidos_cancelados_vencidos: Array<{
    id: number;
    fecha: string;
    cliente: string;
    producto: string;
    cantidad: number;
    total: number;
    anticipo: number;
    saldo: number;
    estado: string;
    vendedor: string;
    motivo: string;
  }>;
}

