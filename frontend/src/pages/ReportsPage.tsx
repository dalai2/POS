import Layout from '../components/Layout';
import { useCorteCajaReport } from '../hooks/useCorteCajaReport';
import { SummaryReportView } from '../components/reports/SummaryReportView';
import { DetailedReportView } from '../components/reports/DetailedReportView';
import { DateSelector } from '../components/reports/DateSelector';

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

  // Helper function to parse date string as local date (not UTC)
  const formatLocalDateForPrint = (dateStr: string): string => {
    if (!dateStr) return '';
    // Parse YYYY-MM-DD as local date, not UTC
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

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
      <span class="value">${formatLocalDateForPrint(report.start_date)}</span>
    </div>
    <div class="row">
      <span class="label">Fecha Fin:</span>
      <span class="value">${formatLocalDateForPrint(report.end_date)}</span>
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
        <DateSelector
          startDate={startDate}
          endDate={endDate}
          loading={loading}
          isDayClosed={isDayClosed}
          usingClosure={usingClosure}
          report={report}
          detailedReport={detailedReport}
          onStartDateChange={setStartDate}
          onEndDateChange={setEndDate}
          onGenerateReport={generateReport}
          onViewClosedDay={viewClosedDay}
          onDownloadCsv={downloadCsv}
          onPrintReport={printReport}
        />

        {/* Report */}
        {report && reportType === 'summary' && (
          <SummaryReportView report={report} />
        )}

        {/* Detailed Report */}
        {detailedReport && reportType === 'detailed' && (
          <DetailedReportView
            detailedReport={detailedReport}
            isDayClosed={isDayClosed}
            usingClosure={usingClosure}
            userRole={userRole}
            closing={closing}
            closeMsg={closeMsg}
            onCloseDay={closeDay}
          />
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

