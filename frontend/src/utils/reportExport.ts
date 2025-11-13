import { DetailedCorteCajaReport } from '../types/reports';

const csvEscape = (value: string | number): string =>
  `"${String(value ?? '')
    .replace(/"/g, '""')
    .replace(/\r?\n/g, ' ')}"`;

export const buildDetailedReportCsv = (
  report: DetailedCorteCajaReport,
  startDate: string,
  endDate: string,
): string => {
  const rows: Array<Array<string | number>> = [];

  rows.push(['REPORTE DETALLADO DE CORTE DE CAJA']);
  rows.push([`Fecha: ${startDate} a ${endDate}`]);
  rows.push([]);

  rows.push(['RESUMEN GENERAL']);
  rows.push(['Concepto', 'Valor']);
  rows.push(['Ventas Activas totales (Contado)', `$${report.total_contado.toFixed(2)}`]);
  rows.push(['Ventas de liquidación (Apartados + Pedidos)', `$${report.liquidacion_total.toFixed(2)}`]);
  rows.push(['Ventas Pasivas totales', `$${report.ventas_pasivas_total.toFixed(2)}`]);
  rows.push(['Cuentas por Cobrar (Saldo Pendiente)', `$${report.cuentas_por_cobrar.toFixed(2)}`]);
  rows.push([]);

  rows.push(['COSTOS Y UTILIDADES']);
  rows.push(['Concepto', 'Valor']);
  rows.push(['Costos Total de Ventas Activas', `$${report.costo_ventas_contado.toFixed(2)}`]);
  rows.push(['Costo de Apartados y Pedidos Liquidados/Entregados', `$${report.costo_apartados_pedidos_liquidados.toFixed(2)}`]);
  rows.push(['Utilidades de Productos Liquidados (Apartados + Pedidos)', `$${report.utilidad_productos_liquidados.toFixed(2)}`]);
  rows.push(['Utilidades de Ventas Activas', `$${report.utilidad_ventas_activas.toFixed(2)}`]);
  rows.push([]);

  rows.push(['RESUMEN DETALLADO']);
  rows.push([]);
  rows.push(['Abonos y Anticipos']);
  rows.push(['Abonos de apartados', `$${report.apartados_pendientes_abonos_adicionales.toFixed(2)}`]);
  rows.push(['Anticipos de apartados', `$${report.apartados_pendientes_anticipos.toFixed(2)}`]);
  rows.push(['Abonos de pedidos', `$${report.pedidos_pendientes_abonos.toFixed(2)}`]);
  rows.push(['Anticipos de pedidos', `$${report.pedidos_pendientes_anticipos.toFixed(2)}`]);
  rows.push([]);

  rows.push(['Ventas Activas']);
  rows.push(['Efectivo de contado', `$${report.total_efectivo_contado.toFixed(2)}`]);
  rows.push(['Subtotal tarjeta', `$${report.subtotal_venta_tarjeta.toFixed(2)}`]);
  rows.push(['Tarjeta con descuento (-3%)', `$${report.total_tarjeta_neto.toFixed(2)}`]);
  rows.push([]);

  rows.push(['Piezas']);
  rows.push(['Piezas vendidas', report.num_piezas_vendidas]);
  rows.push(['Piezas entregadas', report.num_piezas_entregadas]);
  rows.push(['Piezas apartadas pagadas', report.num_piezas_apartadas_pagadas]);
  rows.push(['Piezas de pedidos pagados', report.num_piezas_pedidos_pagados]);
  rows.push(['Pedidos apartados liquidados', report.num_piezas_pedidos_apartados_liquidados]);
  rows.push([]);

  rows.push(['Contadores']);
  rows.push(['Solicitudes apartado', report.num_solicitudes_apartado]);
  rows.push(['Pedidos hechos', report.num_pedidos_hechos]);
  rows.push(['Cancelaciones', report.num_cancelaciones]);
  rows.push(['Apartados vencidos', report.num_apartados_vencidos]);
  rows.push(['Pedidos vencidos', report.num_pedidos_vencidos]);
  rows.push([]);

  rows.push(['Reembolsos y Saldos Vencidos']);
  rows.push(['Reembolso apartados cancelados', `$${(report.reembolso_apartados_cancelados ?? 0).toFixed(2)}`]);
  rows.push(['Reembolso pedidos cancelados', `$${(report.reembolso_pedidos_cancelados ?? 0).toFixed(2)}`]);
  rows.push(['Saldo vencido apartados', `$${(report.saldo_vencido_apartados ?? 0).toFixed(2)}`]);
  rows.push(['Saldo vencido pedidos', `$${(report.saldo_vencido_pedidos ?? 0).toFixed(2)}`]);
  rows.push([]);

  rows.push(['RESUMEN DE VENTAS ACTIVAS']);
  rows.push(['Tipo de movimiento', 'Método de pago', 'Cantidad', 'Subtotal', 'Total']);
  report.resumen_ventas_activas.forEach(row => {
    rows.push([
      row.tipo_movimiento,
      row.metodo_pago,
      row.cantidad_operaciones,
      `$${row.subtotal.toFixed(2)}`,
      `$${row.total.toFixed(2)}`,
    ]);
  });
  rows.push([]);

  rows.push(['RESUMEN DE PAGOS - VENTAS PASIVAS']);
  rows.push(['Tipo de movimiento', 'Método de pago', 'Cantidad', 'Subtotal', 'Total']);
  report.resumen_pagos.forEach(row => {
    rows.push([
      row.tipo_movimiento,
      row.metodo_pago,
      row.cantidad_operaciones,
      `$${row.subtotal.toFixed(2)}`,
      `$${row.total.toFixed(2)}`,
    ]);
  });
  rows.push([]);

  if (report.resumen_piezas && report.resumen_piezas.length > 0) {
    rows.push(['RESUMEN DE PIEZAS']);
    rows.push(['Nombre', 'Modelo', 'Quilataje', 'Vendidas', 'Pedidas', 'Apartadas', 'Liquidadas', 'Total']);
    report.resumen_piezas.forEach(p => {
      rows.push([
        p.nombre,
        p.modelo || 'N/A',
        p.quilataje || 'N/A',
        p.piezas_vendidas,
        p.piezas_pedidas,
        p.piezas_apartadas,
        p.piezas_liquidadas,
        p.total_piezas,
      ]);
    });
    rows.push([]);
  }

  if (report.vendedores.length > 0) {
    rows.push(['RESUMEN POR VENDEDORES']);
    rows.push([
      'Vendedor',
      'Total Contado',
      'Total Tarjeta',
      'Anticipos Apartados',
      'Anticipos Pedidos',
      'Abonos Apartados',
      'Abonos Pedidos',
      'Ventas Total Activa',
      'Venta Total Pasiva',
      'Cuentas por Cobrar',
      'Productos Liquidados',
    ]);
    report.vendedores.forEach(v => {
      rows.push([
        v.vendedor_name,
        `$${v.total_efectivo_contado.toFixed(2)}`,
        `$${v.total_tarjeta_neto.toFixed(2)}`,
        `$${v.anticipos_apartados.toFixed(2)}`,
        `$${v.anticipos_pedidos.toFixed(2)}`,
        `$${v.abonos_apartados.toFixed(2)}`,
        `$${v.abonos_pedidos.toFixed(2)}`,
        `$${v.ventas_total_activa.toFixed(2)}`,
        `$${v.venta_total_pasiva.toFixed(2)}`,
        `$${v.cuentas_por_cobrar.toFixed(2)}`,
        `$${(v.productos_liquidados ?? 0).toFixed(2)}`,
      ]);
    });
    rows.push([]);
  }

  const csvLines = rows
    .map(row => row.map(cell => csvEscape(cell)).join(','))
    .join('\n');

  return '\ufeff' + csvLines;
};

