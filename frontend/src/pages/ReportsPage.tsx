import Layout from '../components/Layout';
import { useCorteCajaReport } from '../hooks/useCorteCajaReport';
import { SummaryReportView } from '../components/reports/SummaryReportView';
import { AnalyticsDashboard } from '../components/reports/AnalyticsDashboard';

export default function ReportsPage() {
  const userRole = localStorage.getItem('role') || '';
  const {
    startDate,
    endDate,
    reportType,
    loading,
    report,
    detailedReport,
    closeMsg,
    closing,
    isDayClosed,
    usingClosure,
    setStartDate,
    setEndDate,
    generateReport,
    downloadCsv,
    closeDay,
    viewClosedDay,
  } = useCorteCajaReport();

  // Verificar permisos
  if (userRole !== 'admin' && userRole !== 'owner') {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">⛔ Acceso Denegado</h2>
            <p className="text-gray-600">No tienes permisos para ver los reportes.</p>
            <p className="text-gray-600">Solo administradores y dueños pueden acceder.</p>
          </div>
        </div>
      </Layout>
    )
  }

  const printReport = () => {
    const w = window.open('', '_blank');
    if (!w) return;

    const now = new Date();
    const formattedDate = now.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
    const formattedTime = now.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    });

    let html = '';
    
    if (report) {
      // Summary Report HTML
      html = `
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Corte de Caja - ${formattedDate}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  @media print {
    @page {
      size: A4;
      margin: 1cm;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: 'Poppins', sans-serif;
      font-size: 11px;
    }
  }
  body {
    margin: 0;
    padding: 20px;
    font-family: 'Poppins', sans-serif;
    font-size: 11px;
    color: #000;
  }
  .header {
    text-align: center;
    border-bottom: 3px solid #000;
    padding-bottom: 15px;
    margin-bottom: 20px;
  }
  .header h1 {
    margin: 0;
    font-size: 22px;
    font-weight: bold;
  }
  .header .date {
    margin-top: 5px;
    font-size: 12px;
  }
  .section {
    margin-bottom: 25px;
    page-break-inside: avoid;
  }
  .section-title {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 10px;
    border-bottom: 2px solid #666;
    padding-bottom: 5px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #ddd;
  }
  .row.total {
    font-weight: bold;
    font-size: 13px;
    border-top: 2px solid #000;
    border-bottom: 2px solid #000;
    margin-top: 10px;
    padding-top: 10px;
  }
  .label {
    font-weight: 600;
  }
  .value {
    font-weight: bold;
  }
  .footer {
    margin-top: 30px;
    text-align: center;
    font-size: 10px;
    color: #666;
    border-top: 1px solid #ddd;
    padding-top: 10px;
  }
</style>
</head>
<body>
  <div class="header">
    <h1>CORTE DE CAJA</h1>
    <div class="date">${formattedDate} - ${formattedTime}</div>
  </div>

  <div class="section">
    <div class="section-title">PERÍODO DEL REPORTE</div>
    <div class="row">
      <span class="label">Fecha Inicio:</span>
      <span class="value">${new Date(report.start_date).toLocaleDateString('es-ES')}</span>
    </div>
    <div class="row">
      <span class="label">Fecha Fin:</span>
      <span class="value">${new Date(report.end_date).toLocaleDateString('es-ES')}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">VENTAS CONTADO</div>
    <div class="row">
      <span>Cantidad de Ventas:</span>
      <span>${report.ventas_contado_count}</span>
    </div>
    <div class="row">
      <span>Total Ventas Contado:</span>
      <span>$${report.ventas_contado_total.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">VENTAS CRÉDITO</div>
    <div class="row">
      <span>Cantidad de Ventas:</span>
      <span>${report.ventas_credito_count}</span>
    </div>
    <div class="row">
      <span>Total Ventas Crédito:</span>
      <span>$${report.ventas_credito_total.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">INGRESOS POR MÉTODO DE PAGO</div>
    <div class="row">
      <span>Efectivo:</span>
      <span>$${report.efectivo_ventas.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Tarjeta:</span>
      <span>$${report.tarjeta_ventas.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Crédito:</span>
      <span>$${report.credito_ventas.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">ABONOS</div>
    <div class="row">
      <span>Abonos en Efectivo:</span>
      <span>$${report.abonos_efectivo.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Abonos con Tarjeta:</span>
      <span>$${report.abonos_tarjeta.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Total Abonos:</span>
      <span>$${report.abonos_total.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">PEDIDOS</div>
    <div class="row">
      <span>Cantidad de Pedidos:</span>
      <span>${report.pedidos_count}</span>
    </div>
    <div class="row">
      <span>Total Pedidos:</span>
      <span>$${report.pedidos_total.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Anticipos Pagados:</span>
      <span>$${report.pedidos_anticipos.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Saldo Pendiente:</span>
      <span>$${report.pedidos_saldo.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Pagos Pedidos Efectivo:</span>
      <span>$${report.pedidos_efectivo.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Pagos Pedidos Tarjeta:</span>
      <span>$${report.pedidos_tarjeta.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Total Pagos Pedidos:</span>
      <span>$${report.pedidos_pagos_total.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">TOTALES EN CAJA</div>
    <div class="row">
      <span>Total Efectivo:</span>
      <span>$${report.total_efectivo.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Total Tarjeta:</span>
      <span>$${report.total_tarjeta.toFixed(2)}</span>
    </div>
    <div class="row total">
      <span>INGRESO TOTAL:</span>
      <span>$${report.total_revenue.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">ANÁLISIS FINANCIERO</div>
    <div class="row">
      <span>Costo Total:</span>
      <span>$${report.total_cost.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Utilidad Total:</span>
      <span>$${report.total_profit.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Margen de Utilidad:</span>
      <span>${report.profit_margin.toFixed(2)}%</span>
    </div>
  </div>

  ${report.returns_count > 0 ? `
  <div class="section">
    <div class="section-title">DEVOLUCIONES</div>
    <div class="row">
      <span>Cantidad:</span>
      <span>${report.returns_count}</span>
    </div>
    <div class="row">
      <span>Total:</span>
      <span>$${report.returns_total.toFixed(2)}</span>
    </div>
  </div>
  ` : ''}

  ${report.vendedores && report.vendedores.length > 0 ? `
  <div class="section">
    <div class="section-title">RESUMEN DE VENDEDORES</div>
    <table>
      <thead>
        <tr>
          <th>Vendedor</th>
          <th>Ventas</th>
          <th>Contado</th>
          <th>Abono</th>
          <th>Total Contado</th>
          <th>Total Abono</th>
          <th>Total Venta</th>
        </tr>
      </thead>
      <tbody>
        ${report.vendedores.map(v => `
        <tr>
          <td>${v.vendedor_name}</td>
          <td>${v.sales_count}</td>
          <td>${v.contado_count}</td>
          <td>${v.credito_count}</td>
          <td>$${v.total_contado.toFixed(2)}</td>
          <td>$${v.total_credito.toFixed(2)}</td>
          <td><strong>$${(v.total_contado + v.total_credito).toFixed(2)}</strong></td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}

  <div class="footer">
    Reporte generado el ${formattedDate} a las ${formattedTime}
  </div>
</body></html>`;
    } else if (detailedReport) {
      // Detailed Report HTML
      html = `
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Reporte Detallado - ${formattedDate}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  @media print {
    @page {
      size: A4;
      margin: 1cm;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: 'Poppins', sans-serif;
      font-size: 10px;
    }
  }
  body {
    margin: 0;
    padding: 20px;
    font-family: 'Poppins', sans-serif;
    font-size: 10px;
    color: #333;
  }
  .header {
    text-align: center;
    border-bottom: 3px solid #000;
    padding-bottom: 15px;
    margin-bottom: 20px;
  }
  .header h1 {
    margin: 0;
    font-size: 20px;
    font-weight: bold;
  }
  .header .date {
    margin-top: 5px;
    font-size: 11px;
  }
  .section {
    margin-bottom: 20px;
    page-break-inside: avoid;
  }
  .section-title {
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 8px;
    border-bottom: 2px solid #666;
    padding-bottom: 3px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 15px;
  }
  th {
    background-color: #f0f0f0;
    font-weight: bold;
    padding: 6px;
    text-align: left;
    border: 1px solid #ddd;
    font-size: 9px;
  }
  td {
    padding: 5px;
    border: 1px solid #ddd;
    font-size: 9px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #ddd;
  }
  .row.total {
    font-weight: bold;
    font-size: 11px;
    border-top: 2px solid #000;
    border-bottom: 2px solid #000;
    margin-top: 8px;
    padding-top: 8px;
  }
  .footer {
    margin-top: 25px;
    text-align: center;
    font-size: 9px;
    color: #000;
    border-top: 1px solid #ddd;
    padding-top: 8px;
  }
</style>
</head>
<body>
  <div class="header">
    <h1>REPORTE DETALLADO DE CORTE DE CAJA</h1>
    <div class="date">${formattedDate} - ${formattedTime}</div>
  </div>

  <div class="section">
    <div class="section-title">RESUMEN GENERAL</div>
    <div class="row">
      <span>Ventas Activas totales (Contado):</span>
      <span>$${detailedReport.total_contado.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Ventas de liquidación (Apartados + Pedidos):</span>
      <span>$${detailedReport.liquidacion_total.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Ventas Pasivas totales:</span>
      <span>$${detailedReport.ventas_pasivas_total.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Cuentas por Cobrar (Saldo Pendiente):</span>
      <span>$${detailedReport.cuentas_por_cobrar.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">COSTOS Y UTILIDADES</div>
    <div class="row">
      <span>Costos Total de Ventas Activas:</span>
      <span>$${detailedReport.costo_ventas_contado.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Costo de Apartados y Pedidos Liquidados/Entregados:</span>
      <span>$${detailedReport.costo_apartados_pedidos_liquidados.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Utilidades de Productos Liquidados (Apartados + Pedidos):</span>
      <span>$${detailedReport.utilidad_productos_liquidados.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Utilidades de Ventas Activas:</span>
      <span>$${detailedReport.utilidad_ventas_activas.toFixed(2)}</span>
    </div>
  </div>

  <div class="section">
    <div class="section-title">PEDIDOS</div>
    <div class="row">
      <span>Total Pedidos:</span>
      <span>${detailedReport.pedidos_count}</span>
    </div>
    <div class="row">
      <span>Total Pedidos:</span>
      <span>$${detailedReport.pedidos_total.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Anticipos:</span>
      <span>$${detailedReport.pedidos_anticipos.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Saldo Pendiente:</span>
      <span>$${detailedReport.pedidos_saldo.toFixed(2)}</span>
    </div>
  </div>

  ${detailedReport.vendedores.length > 0 ? `
  <div class="section">
    <div class="section-title">VENTAS POR VENDEDOR</div>
    <table>
      <thead>
        <tr>
          <th>Vendedor</th>
          <th>#Ventas</th>
          <th>#Contado</th>
          <th>#Crédito</th>
          <th>Total Contado</th>
          <th>Total Crédito</th>
          <th>Efectivo Contado</th>
          <th>Tarjeta Neto (-3%)</th>
          <th>Anticipo Apartado</th>
          <th>Anticipo Pedido</th>
          <th>Abonos Apartado</th>
          <th>Abonos Pedido</th>
          <th>Ventas Activas</th>
          <th>Ventas Pasivas</th>
          <th>Ctas por Cobrar</th>
          <th>Productos Liquidados</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.vendedores.map(v => `
        <tr>
          <td>${v.vendedor_name}</td>
          <td style="text-align:center;">${v.sales_count}</td>
          <td style="text-align:center;">${v.contado_count}</td>
          <td style="text-align:center;">${v.credito_count}</td>
          <td style="text-align:right;">$${(v.total_contado ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.total_credito ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.total_efectivo_contado ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.total_tarjeta_neto ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.anticipos_apartados ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.anticipos_pedidos ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.abonos_apartados ?? 0).toFixed(2)}</td>
          <td style="text-align:right;">$${(v.abonos_pedidos ?? 0).toFixed(2)}</td>
          <td style="text-align:right; font-weight:600;">$${(v.ventas_total_activa ?? 0).toFixed(2)}</td>
          <td style="text-align:right; font-weight:600;">$${(v.venta_total_pasiva ?? 0).toFixed(2)}</td>
          <td style="text-align:right; font-weight:600;">$${(v.cuentas_por_cobrar ?? 0).toFixed(2)}</td>
          <td style="text-align:right; font-weight:600;">$${(v.productos_liquidados ?? 0).toFixed(2)}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}

  ${detailedReport.resumen_piezas && detailedReport.resumen_piezas.length > 0 ? `
  <div class="section">
    <div class="section-title">📦 RESUMEN DE PIEZAS</div>
    <table>
      <thead>
        <tr>
          <th style="text-align: left;">Nombre</th>
          <th style="text-align: left;">Modelo</th>
          <th style="text-align: left;">Quilataje</th>
          <th style="text-align: center; background-color: #f0fdf4;">Vendidas</th>
          <th style="text-align: center; background-color: #eff6ff;">Pedidas</th>
          <th style="text-align: center; background-color: #faf5ff;">Apartadas</th>
          <th style="text-align: center; background-color: #fefce8;">Liquidadas</th>
          <th style="text-align: center; background-color: #e5e7eb; font-weight: bold;">Total</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.resumen_piezas.map((p, idx) => `
        <tr style="background-color: ${idx % 2 === 0 ? '#fff' : '#f9fafb'};">
          <td style="font-weight: 600;">${p.nombre}</td>
          <td>${p.modelo || 'N/A'}</td>
          <td>${p.quilataje || 'N/A'}</td>
          <td style="text-align: center; background-color: #f0fdf4;">${p.piezas_vendidas}</td>
          <td style="text-align: center; background-color: #eff6ff;">${p.piezas_pedidas}</td>
          <td style="text-align: center; background-color: #faf5ff;">${p.piezas_apartadas}</td>
          <td style="text-align: center; background-color: #fefce8;">${p.piezas_liquidadas}</td>
          <td style="text-align: center; background-color: #f3f4f6; font-weight: bold;">${p.total_piezas}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}

  ${detailedReport.sales_details.length > 0 ? `
  <div class="section">
    <div class="section-title">DETALLE DE VENTAS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Piezas</th>
          <th>Total</th>
          <th>Efectivo</th>
          <th>Tarjeta</th>
          <th>Estado</th>
          <th>Tipo</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.sales_details.map(s => `
        <tr>
          <td>${new Date(s.fecha).toLocaleDateString('es-ES')}</td>
          <td>${s.cliente}</td>
          <td>${s.piezas}</td>
          <td>$${s.total.toFixed(2)}</td>
          <td>$${s.efectivo.toFixed(2)}</td>
          <td>$${s.tarjeta.toFixed(2)}</td>
          <td>${s.estado}</td>
          <td>${s.tipo}</td>
          <td>${s.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}

  ${detailedReport.historial_apartados && detailedReport.historial_apartados.length > 0 ? `
  <div class="section">
    <div class="section-title">HISTORIAL DE APARTADOS REALIZADOS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Total</th>
          <th>Anticipo</th>
          <th>Saldo</th>
          <th>Estado</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.historial_apartados.map(a => `
        <tr>
          <td>${new Date(a.fecha).toLocaleDateString('es-ES')}</td>
          <td>${a.cliente}</td>
          <td>$${a.total.toFixed(2)}</td>
          <td>$${a.anticipo.toFixed(2)}</td>
          <td>$${a.saldo.toFixed(2)}</td>
          <td>${a.estado}</td>
          <td>${a.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.historial_pedidos && detailedReport.historial_pedidos.length > 0 ? `
  <div class="section">
    <div class="section-title">HISTORIAL DE PEDIDOS REALIZADOS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Producto</th>
          <th>Cant</th>
          <th>Total</th>
          <th>Anticipo</th>
          <th>Saldo</th>
          <th>Estado</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.historial_pedidos.map(p => `
        <tr>
          <td>${new Date(p.fecha).toLocaleDateString('es-ES')}</td>
          <td>${p.cliente}</td>
          <td>${p.producto}</td>
          <td>${p.cantidad}</td>
          <td>$${p.total.toFixed(2)}</td>
          <td>$${p.anticipo.toFixed(2)}</td>
          <td>$${p.saldo.toFixed(2)}</td>
          <td>${p.estado}</td>
          <td>${p.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.historial_abonos_apartados && detailedReport.historial_abonos_apartados.length > 0 ? `
  <div class="section">
    <div class="section-title">HISTORIAL DE ABONOS DE APARTADOS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Monto</th>
          <th>Método de Pago</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.historial_abonos_apartados.map(a => `
        <tr>
          <td>${new Date(a.fecha).toLocaleDateString('es-ES')}</td>
          <td>${a.cliente}</td>
          <td>$${a.monto.toFixed(2)}</td>
          <td>${a.metodo_pago}</td>
          <td>${a.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.historial_abonos_pedidos && detailedReport.historial_abonos_pedidos.length > 0 ? `
  <div class="section">
    <div class="section-title">HISTORIAL DE ABONOS PARA PEDIDOS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Producto</th>
          <th>Monto</th>
          <th>Método de Pago</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.historial_abonos_pedidos.map(a => `
        <tr>
          <td>${new Date(a.fecha).toLocaleDateString('es-ES')}</td>
          <td>${a.cliente}</td>
          <td>${a.producto}</td>
          <td>$${a.monto.toFixed(2)}</td>
          <td>${a.metodo_pago}</td>
          <td>${a.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.resumen_ventas_activas && detailedReport.resumen_ventas_activas.length > 0 ? `
  <div class="section">
    <div class="section-title">RESUMEN DE VENTAS ACTIVAS</div>
    <table>
      <thead>
        <tr>
          <th>Tipo de movimiento</th>
          <th>Método de pago</th>
          <th>Operaciones</th>
          <th>Subtotal</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.resumen_ventas_activas.map(r => `
        <tr>
          <td>${r.tipo_movimiento}</td>
          <td>${r.metodo_pago}</td>
          <td style="text-align: center;">${r.cantidad_operaciones}</td>
          <td style="text-align: right;">$${r.subtotal.toFixed(2)}</td>
          <td style="text-align: right;">$${r.total.toFixed(2)}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.resumen_pagos && detailedReport.resumen_pagos.length > 0 ? `
  <div class="section">
    <div class="section-title">💳 RESUMEN DE PAGOS - VENTAS PASIVAS</div>
    <table>
      <thead>
        <tr>
          <th>Tipo de movimiento</th>
          <th>Método de pago</th>
          <th>Operaciones</th>
          <th>Subtotal</th>
          <th>Total</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.resumen_pagos.map(r => `
        <tr>
          <td>${r.tipo_movimiento}</td>
          <td>${r.metodo_pago}</td>
          <td style="text-align: center;">${r.cantidad_operaciones}</td>
          <td style="text-align: right;">$${r.subtotal.toFixed(2)}</td>
          <td style="text-align: right;">$${r.total.toFixed(2)}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.apartados_cancelados_vencidos && detailedReport.apartados_cancelados_vencidos.length > 0 ? `
  <div class="section">
    <div class="section-title">APARTADOS CANCELADOS Y VENCIDOS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Total</th>
          <th>Total Pagado</th>
          <th>Saldo Pendiente</th>
          <th>Estado</th>
          <th>Tipo</th>
          <th>Monto</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.apartados_cancelados_vencidos.map(a => `
        <tr>
          <td>${new Date(a.fecha).toLocaleDateString('es-ES')}</td>
          <td>${a.cliente}</td>
          <td>$${a.total.toFixed(2)}</td>
          <td style="color: green;">$${a.anticipo.toFixed(2)}</td>
          <td style="color: gray;">$${a.saldo.toFixed(2)}</td>
          <td>${a.estado}</td>
          <td style="color: ${a.estado === 'cancelado' ? '#dc2626' : '#f59e0b'}; font-weight: bold;">
            ${a.estado === 'cancelado' ? 'Reembolso' : 'Saldo Vencido'}
          </td>
          <td style="color: ${a.estado === 'cancelado' ? '#dc2626' : '#f59e0b'}; font-weight: bold;">
            $${a.anticipo.toFixed(2)}
          </td>
          <td>${a.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
  
  ${detailedReport.pedidos_cancelados_vencidos && detailedReport.pedidos_cancelados_vencidos.length > 0 ? `
  <div class="section">
    <div class="section-title">PEDIDOS CANCELADOS Y VENCIDOS</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Cliente</th>
          <th>Producto</th>
          <th>Cant</th>
          <th>Total</th>
          <th>Total Pagado</th>
          <th>Saldo Pendiente</th>
          <th>Estado</th>
          <th>Tipo</th>
          <th>Monto</th>
          <th>Vendedor</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.pedidos_cancelados_vencidos.map(p => `
        <tr>
          <td>${new Date(p.fecha).toLocaleDateString('es-ES')}</td>
          <td>${p.cliente}</td>
          <td>${p.producto}</td>
          <td>${p.cantidad}</td>
          <td>$${p.total.toFixed(2)}</td>
          <td style="color: green;">$${p.anticipo.toFixed(2)}</td>
          <td style="color: gray;">$${p.saldo.toFixed(2)}</td>
          <td>${p.estado}</td>
          <td style="color: ${p.estado === 'cancelado' ? '#dc2626' : '#f59e0b'}; font-weight: bold;">
            ${p.estado === 'cancelado' ? 'Reembolso' : 'Saldo Vencido'}
          </td>
          <td style="color: ${p.estado === 'cancelado' ? '#dc2626' : '#f59e0b'}; font-weight: bold;">
            $${p.anticipo.toFixed(2)}
          </td>
          <td>${p.vendedor}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}
</body></html>`;
    }

    w.document.write(html);
    w.document.close();
    setTimeout(() => w.print(), 100);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto font-['Poppins',sans-serif]" style={{ backgroundColor: '#f0f7f7', minHeight: 'calc(100vh - 64px)', padding: '2rem', borderRadius: '8px' }}>
        <h1 className="text-3xl font-['Exo_2',sans-serif] font-bold mb-8" style={{ color: '#2e4354' }}>Corte de Caja</h1>

        {/* Date Selection */}
        <div className="rounded-xl shadow-lg p-6 mb-6 print:hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">

            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
                Fecha Inicio
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-lg px-3 py-2 transition-all"
                style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
                onFocus={(e) => e.target.style.border = '2px solid #2e4354'}
                onBlur={(e) => e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)'}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
                Fecha Fin
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-lg px-3 py-2 transition-all"
                style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
                onFocus={(e) => e.target.style.border = '2px solid #2e4354'}
                onBlur={(e) => e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)'}
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={generateReport}
                disabled={loading || (isDayClosed === true && startDate === endDate)}
                className="w-full text-white px-6 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg disabled:cursor-not-allowed"
                style={{ backgroundColor: (isDayClosed === true && startDate === endDate) || loading ? '#2e4354' : '#2e4354', opacity: loading || (isDayClosed === true && startDate === endDate) ? 0.7 : 1 }}
              >
                {loading ? 'Generando...' : 'Generar Reporte'}
              </button>
            </div>

            {(isDayClosed === true && startDate === endDate) && (
              <div className="flex items-end">
                <button
                  onClick={viewClosedDay}
                  disabled={loading}
                  className="w-full text-white px-6 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                  style={{ backgroundColor: '#ffe98e', color: '#000000' }}
                >
                  📦 Ver Caja Cerrada
                </button>
              </div>
            )}
          </div>

          {(report || detailedReport) && (
            <div className="flex gap-3">
              <button
                onClick={printReport}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg hover:scale-105"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                🖨️ Imprimir Reporte
              </button>
              <button
                onClick={downloadCsv}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg hover:scale-105"
                style={{ backgroundColor: '#ffe98e', color: '#000000' }}
              >
                📥 Descargar CSV
              </button>
            </div>
          )}
        </div>

        {/* Report */}
        {report && reportType === 'summary' && (
          <SummaryReportView report={report} />
        )}

        {/* Detailed Report */}
        {detailedReport && reportType === 'detailed' && (
          <div className="rounded-xl shadow-xl" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
            {/* Header */}
            <div className="text-center p-8" style={{ borderBottom: '3px solid #2e4354' }}>
              <h2 className="text-3xl font-['Exo_2',sans-serif] font-bold mb-2" style={{ color: '#2e4354' }}>CORTE DE CAJA</h2>
              <p className="text-lg" style={{ color: '#2e4354', opacity: 0.8 }}>
                Rango: {new Date(detailedReport.start_date).toLocaleDateString()} a {new Date(detailedReport.end_date).toLocaleDateString()}
              </p>
              <p className="text-sm" style={{ color: '#2e4354', opacity: 0.6 }}>
                Generado: {detailedReport.generated_at}
              </p>

              {isDayClosed === true && (
                <div className="mt-3 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium shadow-sm" style={{ backgroundColor: 'rgba(255, 233, 142, 0.3)', color: '#000000', border: '1px solid rgba(255, 233, 142, 0.6)' }}>
                  ✅ Caja cerrada
                </div>
              )}
              {usingClosure && (
                <div className="mt-3 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium shadow-sm" style={{ backgroundColor: 'rgba(46, 67, 84, 0.1)', color: '#2e4354' }}>
                  📦 Mostrando cierre guardado
                </div>
              )}

              {(userRole === 'admin' || userRole === 'owner') && (
                <div className="mt-4 flex justify-center gap-3">
                  <button
                    onClick={closeDay}
                    disabled={closing || isDayClosed === true}
                    className="px-6 py-2.5 rounded-lg text-white font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                    style={{ backgroundColor: (closing || isDayClosed === true) ? '#2e4354' : '#2e4354' }}
                  >
                    {closing ? 'Cerrando...' : (isDayClosed === true ? '✅ Cash Register Closed' : '🔒 Cerrar Caja (día actual)')}
                  </button>
                </div>
              )}
              {closeMsg && (
                <div className="mt-3 text-sm font-medium" style={{ color: '#2e4354' }}>{closeMsg}</div>
              )}
            </div>

            {/* Resumen General */}
            <div className="p-6" style={{ borderBottom: '2px solid rgba(46, 67, 84, 0.1)' }}>
              <h3 className="text-xl font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Resumen General</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                  <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Ventas activas totales</p>
                  <p className="text-lg font-semibold" style={{ color: '#000000' }}>{detailedReport.contado_count} ventas</p>
                  <p className="text-2xl font-bold" style={{ color: '#000000' }}>${detailedReport.total_contado.toFixed(2)}</p>
                </div>
                <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(224, 253, 255, 0.6)' }}>
                  <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Ventas de liquidación</p>
                  <p className="text-lg font-semibold" style={{ color: '#000000' }}>{detailedReport.liquidacion_count} (Apartados + Pedidos)</p>
                  <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>${detailedReport.liquidacion_total.toFixed(2)}</p>
                </div>
                <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                  <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Ventas pasivas totales</p>
                  <p className="text-2xl font-bold" style={{ color: '#000000' }}>${detailedReport.ventas_pasivas_total.toFixed(2)}</p>
                </div>
                <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#2e4354', border: '1px solid rgba(46, 67, 84, 0.8)' }}>
                  <p className="text-sm font-medium" style={{ color: '#ffffff', opacity: 0.9 }}>Cuentas por Cobrar</p>
                  <p className="text-2xl font-bold" style={{ color: '#ffffff' }}>${detailedReport.cuentas_por_cobrar.toFixed(2)}</p>
                  <p className="text-xs font-medium mt-1" style={{ color: '#ffffff', opacity: 0.8 }}>Saldo pendiente</p>
              </div>
            </div>

              {/* Costos y Utilidades */}
              <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
                <h4 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Costos y Utilidades</h4>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                    <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Costos Total de Ventas Activas</p>
                    <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>${detailedReport.costo_ventas_contado.toFixed(2)}</p>
                    <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>Productos vendidos</p>
                </div>
                  <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(224, 253, 255, 0.6)' }}>
                    <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Costo de productos liquidados</p>
                    <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>${detailedReport.costo_apartados_pedidos_liquidados.toFixed(2)}</p>
                    <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>Status liquidado/entregado</p>
                </div>
                  <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                    <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Utilidades de productos liquidados</p>
                    <p className="text-2xl font-bold" style={{ color: '#000000' }}>${detailedReport.utilidad_productos_liquidados.toFixed(2)}</p>
                    <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>Apartados + Pedidos</p>
                </div>
                  <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#2e4354', border: '1px solid rgba(46, 67, 84, 0.8)' }}>
                    <p className="text-sm font-medium" style={{ color: '#ffffff', opacity: 0.9 }}>Utilidades de Ventas Activas</p>
                    <p className="text-2xl font-bold" style={{ color: '#ffffff' }}>${detailedReport.utilidad_ventas_activas.toFixed(2)}</p>
                    <p className="text-xs font-medium mt-1" style={{ color: '#ffffff', opacity: 0.8 }}>(Efectivo + Tarjeta -3%) - Costos</p>
              </div>
            </div>

                {/* Total de Piezas por Nombre (sin liquidadas) */}
            {detailedReport.total_piezas_por_nombre_sin_liquidadas && Object.keys(detailedReport.total_piezas_por_nombre_sin_liquidadas).length > 0 && (
              <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
                <h4 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Total de Piezas por Nombre (Excluyendo Liquidadas)</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(detailedReport.total_piezas_por_nombre_sin_liquidadas)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([nombre, total]) => (
                      <div 
                        key={nombre}
                        className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" 
                        style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}
                      >
                        <p className="text-sm font-medium mb-2" style={{ color: '#2e4354' }}>{nombre}</p>
                        <p className="text-2xl font-bold" style={{ color: '#000000' }}>{total}</p>
                        <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>piezas</p>
                      </div>
                    ))}
                </div>
              </div>
            )}

                {/* Resumen de Piezas */}
            {detailedReport.resumen_piezas && detailedReport.resumen_piezas.length > 0 ? (
                  <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
                    <h5 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>📦 Resumen de Piezas ({detailedReport.resumen_piezas.length} registros)</h5>
                <div className="overflow-x-auto">
                      <table className="min-w-full border-collapse rounded-lg overflow-hidden shadow-sm" style={{ border: '1px solid rgba(46, 67, 84, 0.2)' }}>
                        <thead style={{ backgroundColor: '#2e4354' }}>
                      <tr>
                            <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Nombre</th>
                            <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Modelo</th>
                            <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Quilataje</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Vendidas</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Pedidas</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Apartadas</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Liquidadas</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>Total</th>
                      </tr>
                    </thead>
                        <tbody>
                          {detailedReport.resumen_piezas.map((pieza, idx) => (
                            <tr key={`${pieza.nombre}-${pieza.modelo}-${pieza.quilataje}-${idx}`} style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f0f7f7', borderBottom: '1px solid rgba(46, 67, 84, 0.08)' }}>
                              <td className="px-4 py-3 text-sm font-semibold" style={{ color: '#000000', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.nombre}</td>
                              <td className="px-4 py-3 text-sm" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.modelo || 'N/A'}</td>
                              <td className="px-4 py-3 text-sm" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.quilataje || 'N/A'}</td>
                              <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_vendidas}</td>
                              <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_pedidas}</td>
                              <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_apartadas}</td>
                              <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_liquidadas}</td>
                              <td className="px-4 py-3 text-sm text-right font-bold" style={{ color: '#000000', backgroundColor: 'rgba(46, 67, 84, 0.1)' }}>{pieza.total_piezas}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
                <h5 className="text-lg font-['Exo_2',sans-serif] font-bold mb-3" style={{ color: '#2e4354' }}>📦 Resumen de Piezas</h5>
                <p className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>No hay datos de piezas para mostrar en este período. (Debug: {detailedReport.resumen_piezas ? `Array con ${detailedReport.resumen_piezas.length} elementos` : 'resumen_piezas es undefined'})</p>
          </div>
        )}

                {/* Resumen por Vendedores */}
            {detailedReport.vendedores.length > 0 && (
                  <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
                    <h5 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>👥 Resumen por Vendedores</h5>
                <div className="overflow-x-auto">
                      <table className="min-w-full border-collapse rounded-lg overflow-hidden shadow-sm" style={{ border: '1px solid rgba(46, 67, 84, 0.2)' }}>
                        <thead style={{ backgroundColor: '#2e4354' }}>
                      <tr>
                            <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Vendedor</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Efectivo</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Tarjeta (-3%)</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Antic. Apart.</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Antic. Ped.</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Abono Apart.</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Abono Ped.</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Cuentas x Cobrar</th>
                            <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>Prod. Liquidados</th>
                      </tr>
                    </thead>
                        <tbody>
                          {detailedReport.vendedores.map((vendedor, idx) => (
                            <tr key={`${vendedor.vendedor_id}-${idx}`} style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f0f7f7', borderBottom: '1px solid rgba(46, 67, 84, 0.08)' }}>
                              <td className="px-4 py-3 text-sm font-semibold" style={{ color: '#000000', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{vendedor.vendedor_name}</td>
                              <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.total_efectivo_contado.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.total_tarjeta_neto.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.anticipos_apartados.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.anticipos_pedidos.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.abonos_apartados.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.abonos_pedidos.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right font-bold" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.cuentas_por_cobrar.toFixed(2)}</td>
                              <td className="px-4 py-3 text-sm text-right font-bold" style={{ color: '#2e4354', backgroundColor: 'rgba(46, 67, 84, 0.1)' }}>${(vendedor.productos_liquidados ?? 0).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
              </div>

              {/* Resumen Detallado */}
              <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
                <h4 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Resumen Detallado</h4>
                <AnalyticsDashboard dashboard={detailedReport.dashboard} />

              </div>
            </div>

            {/* Detalle de Ventas */}
            {detailedReport.sales_details.length > 0 && (
              <div className="p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Detalle de Ventas</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Piezas</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Efectivo</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Tarjeta</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Tipo</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.sales_details.map((sale) => (
                        <tr key={sale.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(sale.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{sale.cliente}</td>
                          <td className="px-2 py-2 text-center text-xs">{sale.piezas}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold">${sale.total.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs">${sale.efectivo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs">${sale.tarjeta.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{sale.estado}</td>
                          <td className="px-2 py-2 text-center text-xs">{sale.tipo}</td>
                          <td className="px-2 py-2 text-xs">{sale.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Historial de Apartados Realizados */}
            {detailedReport.historial_apartados && detailedReport.historial_apartados.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Apartados Realizados</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Anticipo</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.historial_apartados.map((apartado) => (
                        <tr key={apartado.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(apartado.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{apartado.cliente}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold">${apartado.total.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-green-600">${apartado.anticipo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-orange-600">${apartado.saldo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{apartado.estado}</td>
                          <td className="px-2 py-2 text-xs">{apartado.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Historial de Pedidos Realizados */}
            {detailedReport.historial_pedidos && detailedReport.historial_pedidos.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Pedidos Realizados</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Producto</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Cant</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Anticipo</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.historial_pedidos.map((pedido) => (
                        <tr key={pedido.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(pedido.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{pedido.cliente}</td>
                          <td className="px-2 py-2 text-xs">{pedido.producto}</td>
                          <td className="px-2 py-2 text-center text-xs">{pedido.cantidad}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold">${pedido.total.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-green-600">${pedido.anticipo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-orange-600">${pedido.saldo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{pedido.estado}</td>
                          <td className="px-2 py-2 text-xs">{pedido.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Historial de Abonos de Apartados */}
            {detailedReport.historial_abonos_apartados && detailedReport.historial_abonos_apartados.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Abonos de Apartados</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Método de Pago</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.historial_abonos_apartados.map((abono) => (
                        <tr key={abono.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(abono.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{abono.cliente}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold text-green-600">${abono.monto.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{abono.metodo_pago}</td>
                          <td className="px-2 py-2 text-xs">{abono.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Historial de Abonos para Pedidos */}
            {detailedReport.historial_abonos_pedidos && detailedReport.historial_abonos_pedidos.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Abonos para Pedidos</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Producto</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Método de Pago</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.historial_abonos_pedidos.map((abono) => (
                        <tr key={abono.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(abono.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{abono.cliente}</td>
                          <td className="px-2 py-2 text-xs">{abono.producto}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold text-green-600">${abono.monto.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{abono.metodo_pago}</td>
                          <td className="px-2 py-2 text-xs">{abono.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Apartados Cancelados y Vencidos */}
            {detailedReport.apartados_cancelados_vencidos && detailedReport.apartados_cancelados_vencidos.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Apartados Cancelados y Vencidos</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total Pagado</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo Pendiente</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Tipo</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.apartados_cancelados_vencidos.map((apartado) => (
                        <tr key={apartado.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(apartado.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{apartado.cliente}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold">${apartado.total.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-green-600">${apartado.anticipo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-gray-600">${apartado.saldo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{apartado.estado}</td>
                          <td className={`px-2 py-2 text-center text-xs font-semibold ${apartado.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                            {apartado.estado === 'cancelado' ? 'Reembolso' : 'Saldo Vencido'}
                          </td>
                          <td className={`px-2 py-2 text-right text-xs font-bold ${apartado.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                            ${apartado.anticipo.toFixed(2)}
                          </td>
                          <td className="px-2 py-2 text-xs">{apartado.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Pedidos Cancelados y Vencidos */}
            {detailedReport.pedidos_cancelados_vencidos && detailedReport.pedidos_cancelados_vencidos.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Pedidos Cancelados y Vencidos</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Producto</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Cant</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total Pagado</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo Pendiente</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                        <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Tipo</th>
                        <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                        <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.pedidos_cancelados_vencidos.map((pedido) => (
                        <tr key={pedido.id} className="border-t">
                          <td className="px-2 py-2 text-xs">{new Date(pedido.fecha).toLocaleString()}</td>
                          <td className="px-2 py-2 text-xs">{pedido.cliente}</td>
                          <td className="px-2 py-2 text-xs">{pedido.producto}</td>
                          <td className="px-2 py-2 text-center text-xs">{pedido.cantidad}</td>
                          <td className="px-2 py-2 text-right text-xs font-bold">${pedido.total.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-green-600">${pedido.anticipo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-right text-xs text-gray-600">${pedido.saldo.toFixed(2)}</td>
                          <td className="px-2 py-2 text-center text-xs">{pedido.estado}</td>
                          <td className={`px-2 py-2 text-center text-xs font-semibold ${pedido.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                            {pedido.estado === 'cancelado' ? 'Reembolso' : 'Saldo Vencido'}
                          </td>
                          <td className={`px-2 py-2 text-right text-xs font-bold ${pedido.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                            ${pedido.anticipo.toFixed(2)}
                          </td>
                          <td className="px-2 py-2 text-xs">{pedido.vendedor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {!report && !detailedReport && !loading && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
            Seleccione las fechas y haga clic en "Generar Reporte" para ver el corte de caja
          </div>
        )}

        {/* Print Styles */}
        <style>{`
          @media print {
            .print\\:hidden { display: none !important; }
            body { margin: 0; padding: 10mm; }
            .bg-white { background-color: white !important; }
            .shadow-md { box-shadow: none !important; }
            .rounded-lg { border-radius: 0 !important; }
            .border-gray-300 { border-color: #d1d5db !important; }
            table { page-break-inside: avoid; }
            thead { display: table-header-group; }
            tbody { display: table-row-group; }
          }
        `}</style>
      </div>
    </Layout>
  );
}

