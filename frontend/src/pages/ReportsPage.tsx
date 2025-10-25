import { useState } from 'react';
import Layout from '../components/Layout';
import { api } from '../utils/api';

interface CorteDeCajaReport {
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

interface DetailedCorteCajaReport {
  start_date: string;
  end_date: string;
  generated_at: string;
  ventas_validas: number;
  contado_count: number;
  credito_count: number;
  total_vendido: number;
  costo_total: number;
  utilidad_total: number;
  piezas_vendidas: number;
  pendiente_credito: number;
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
  }>;
}

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<CorteDeCajaReport | null>(null);
  const [detailedReport, setDetailedReport] = useState<DetailedCorteCajaReport | null>(null);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [reportType, setReportType] = useState<'summary' | 'detailed'>('summary');

  const generateReport = async () => {
    setLoading(true);
    try {
      if (reportType === 'detailed') {
        const response = await api.get('/reports/detailed-corte-caja', {
          params: { start_date: startDate, end_date: endDate }
        });
        setDetailedReport(response.data);
      } else {
      const response = await api.get('/reports/corte-de-caja', {
        params: { start_date: startDate, end_date: endDate }
      });
      setReport(response.data);
      }
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Error al generar reporte');
    } finally {
      setLoading(false);
    }
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
<style>
  @media print {
    @page {
      size: A4;
      margin: 1cm;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      font-size: 11px;
    }
  }
  body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    font-size: 11px;
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
          <th>Crédito</th>
          <th>Total Contado</th>
          <th>Total Crédito</th>
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
<style>
  @media print {
    @page {
      size: A4;
      margin: 1cm;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      font-size: 10px;
    }
  }
  body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
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
    color: #666;
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
      <span>Período:</span>
      <span>${new Date(detailedReport.start_date).toLocaleDateString('es-ES')} - ${new Date(detailedReport.end_date).toLocaleDateString('es-ES')}</span>
    </div>
    <div class="row">
      <span>Ventas Válidas:</span>
      <span>${detailedReport.ventas_validas}</span>
    </div>
    <div class="row">
      <span>Ventas Contado:</span>
      <span>${detailedReport.contado_count}</span>
    </div>
    <div class="row">
      <span>Ventas Crédito:</span>
      <span>${detailedReport.credito_count}</span>
    </div>
    <div class="row">
      <span>Total Vendido:</span>
      <span>$${detailedReport.total_vendido.toFixed(2)}</span>
    </div>
    <div class="row">
      <span>Costo Total:</span>
      <span>$${detailedReport.costo_total.toFixed(2)}</span>
    </div>
    <div class="row total">
      <span>Utilidad Total:</span>
      <span>$${detailedReport.utilidad_total.toFixed(2)}</span>
    </div>
  </div>

  ${detailedReport.vendedores.length > 0 ? `
  <div class="section">
    <div class="section-title">VENTAS POR VENDEDOR</div>
    <table>
      <thead>
        <tr>
          <th>Vendedor</th>
          <th>Ventas</th>
          <th>Contado</th>
          <th>Crédito</th>
          <th>Total Contado</th>
          <th>Total Crédito</th>
          <th>Total Venta</th>
          <th>Utilidad</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.vendedores.map(v => `
        <tr>
          <td>${v.vendedor_name}</td>
          <td>${v.sales_count}</td>
          <td>${v.contado_count}</td>
          <td>${v.credito_count}</td>
          <td>$${v.total_contado.toFixed(2)}</td>
          <td>$${v.total_credito.toFixed(2)}</td>
          <td><strong>$${(v.total_contado + v.total_credito).toFixed(2)}</strong></td>
          <td>$${v.total_profit.toFixed(2)}</td>
        </tr>
        `).join('')}
      </tbody>
    </table>
  </div>
  ` : ''}

  ${detailedReport.daily_summaries.length > 0 ? `
  <div class="section">
    <div class="section-title">RESUMEN DIARIO</div>
    <table>
      <thead>
        <tr>
          <th>Fecha</th>
          <th>Costo</th>
          <th>Venta</th>
          <th>Utilidad</th>
        </tr>
      </thead>
      <tbody>
        ${detailedReport.daily_summaries.map(d => `
        <tr>
          <td>${new Date(d.fecha).toLocaleDateString('es-ES')}</td>
          <td>$${d.costo.toFixed(2)}</td>
          <td>$${d.venta.toFixed(2)}</td>
          <td>$${d.utilidad.toFixed(2)}</td>
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
          <td>${s.estado}</td>
          <td>${s.tipo}</td>
          <td>${s.vendedor}</td>
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
    }

    w.document.write(html);
    w.document.close();
    setTimeout(() => w.print(), 100);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Corte de Caja</h1>

        {/* Date Selection */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6 print:hidden">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Reporte
              </label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value as 'summary' | 'detailed')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="summary">Resumen</option>
                <option value="detailed">Detallado</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fecha Inicio
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fecha Fin
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={generateReport}
                disabled={loading}
                className="w-full bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {loading ? 'Generando...' : 'Generar Reporte'}
              </button>
            </div>
          </div>

          {(report || detailedReport) && (
            <div className="flex gap-2">
              <button
                onClick={printReport}
                className="bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-gray-900"
              >
                🖨️ Imprimir Reporte
              </button>
            </div>
          )}
        </div>

        {/* Report */}
        {report && reportType === 'summary' && (
          <div className="bg-white rounded-lg shadow-md p-8">
            {/* Header */}
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900">CORTE DE CAJA</h2>
              <p className="text-gray-600 mt-2">
                Del {new Date(report.start_date).toLocaleDateString()} 
                {' al '}
                {new Date(report.end_date).toLocaleDateString()}
              </p>
            </div>

            {/* Sales Summary */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                RESUMEN DE VENTAS
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Ventas de Contado</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {report.ventas_contado_count}
                  </p>
                  <p className="text-lg text-green-600">
                    ${report.ventas_contado_total.toFixed(2)}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Ventas a Crédito</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {report.ventas_credito_count}
                  </p>
                  <p className="text-lg text-amber-600">
                    ${report.ventas_credito_total.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>

            {/* Payment Methods */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                POR MÉTODO DE PAGO
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Efectivo (Ventas)</span>
                  <span className="text-lg font-bold text-green-600">
                    ${report.efectivo_ventas.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Tarjeta (Ventas)</span>
                  <span className="text-lg font-bold text-blue-600">
                    ${report.tarjeta_ventas.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Crédito</span>
                  <span className="text-lg font-bold text-amber-600">
                    ${report.credito_ventas.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Credit Payments (Abonos) */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                ABONOS A CRÉDITOS
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Abonos en Efectivo</span>
                  <span className="text-lg font-bold text-green-600">
                    ${report.abonos_efectivo.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium">Abonos con Tarjeta</span>
                  <span className="text-lg font-bold text-blue-600">
                    ${report.abonos_tarjeta.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-100 rounded-lg">
                  <span className="font-semibold">Total Abonos</span>
                  <span className="text-xl font-bold text-blue-800">
                    ${report.abonos_total.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Totals */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                TOTALES EN CAJA
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                  <span className="text-lg font-semibold">Total Efectivo</span>
                  <span className="text-2xl font-bold text-green-700">
                    ${report.total_efectivo.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
                  <span className="text-lg font-semibold">Total Tarjeta</span>
                  <span className="text-2xl font-bold text-blue-700">
                    ${report.total_tarjeta.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-center p-4 bg-purple-50 rounded-lg border-2 border-purple-300">
                  <span className="text-xl font-bold">INGRESO TOTAL</span>
                  <span className="text-3xl font-bold text-purple-700">
                    ${report.total_revenue.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Profit Analysis */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                ANÁLISIS DE UTILIDAD
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Costo Total</p>
                  <p className="text-2xl font-bold text-red-600">
                    ${report.total_cost.toFixed(2)}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Utilidad Total</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${report.total_profit.toFixed(2)}
                  </p>
                </div>
              </div>
              <div className="mt-4 p-4 bg-indigo-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-lg font-semibold">Margen de Utilidad</span>
                  <span className="text-2xl font-bold text-indigo-700">
                    {report.profit_margin.toFixed(2)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Returns */}
            {report.returns_count > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                  DEVOLUCIONES
                </h3>
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Total Devoluciones ({report.returns_count})</span>
                    <span className="text-lg font-bold text-orange-600">
                      ${report.returns_total.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Vendors Summary */}
            {report.vendedores && report.vendedores.length > 0 && (
              <div className="mb-8">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
                  RESUMEN DE VENDEDORES
                </h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">Vendedor</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">#Ventas</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Contado</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Crédito</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Total Contado ($)</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Total Crédito ($)</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Total ($)</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {report.vendedores.map((vendedor) => (
                        <tr key={vendedor.vendedor_id} className="border-t">
                          <td className="px-4 py-2 text-sm font-medium">{vendedor.vendedor_name}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.sales_count}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.contado_count}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.credito_count}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold text-green-600">${vendedor.total_contado.toFixed(2)}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold text-yellow-600">${vendedor.total_credito.toFixed(2)}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold text-blue-600">${(vendedor.total_contado + vendedor.total_credito).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Print Button */}
            <div className="mt-8 pt-6 border-t-2 border-gray-200 print:hidden">
              <button
                onClick={printReport}
                className="w-full bg-gray-800 text-white px-6 py-3 rounded-lg hover:bg-gray-900"
              >
                🖨️ Imprimir Reporte
              </button>
            </div>
          </div>
        )}

        {/* Detailed Report */}
        {detailedReport && reportType === 'detailed' && (
          <div className="bg-white shadow-md">
            {/* Header */}
            <div className="text-center p-8 border-b-4 border-gray-800">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">CORTE DE CAJA</h2>
              <p className="text-lg text-gray-600">
                Rango: {new Date(detailedReport.start_date).toLocaleDateString()} a {new Date(detailedReport.end_date).toLocaleDateString()}
              </p>
              <p className="text-sm text-gray-500">
                Generado: {detailedReport.generated_at}
              </p>
            </div>

            {/* Resumen General */}
            <div className="p-6 border-b-2 border-gray-300">
              <h3 className="text-xl font-bold text-gray-800 mb-4">Resumen General</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-gray-100 rounded">
                  <p className="text-sm text-gray-600">Ventas válidas</p>
                  <p className="text-2xl font-bold text-gray-900">{detailedReport.ventas_validas}</p>
                </div>
                <div className="text-center p-3 bg-green-100 rounded">
                  <p className="text-sm text-gray-600">Contado</p>
                  <p className="text-2xl font-bold text-green-700">{detailedReport.contado_count}</p>
                </div>
                <div className="text-center p-3 bg-yellow-100 rounded">
                  <p className="text-sm text-gray-600">Crédito</p>
                  <p className="text-2xl font-bold text-yellow-700">{detailedReport.credito_count}</p>
                </div>
                <div className="text-center p-3 bg-blue-100 rounded">
                  <p className="text-sm text-gray-600">Total vendido</p>
                  <p className="text-2xl font-bold text-blue-700">${detailedReport.total_vendido.toFixed(2)}</p>
                </div>
                <div className="text-center p-3 bg-red-100 rounded">
                  <p className="text-sm text-gray-600">Costo total</p>
                  <p className="text-2xl font-bold text-red-700">${detailedReport.costo_total.toFixed(2)}</p>
                </div>
                <div className="text-center p-3 bg-green-100 rounded">
                  <p className="text-sm text-gray-600">Utilidad total</p>
                  <p className="text-2xl font-bold text-green-700">${detailedReport.utilidad_total.toFixed(2)}</p>
                </div>
                <div className="text-center p-3 bg-purple-100 rounded">
                  <p className="text-sm text-gray-600">Piezas vendidas</p>
                  <p className="text-2xl font-bold text-purple-700">{detailedReport.piezas_vendidas}</p>
                </div>
                <div className="text-center p-3 bg-orange-100 rounded">
                  <p className="text-sm text-gray-600">Pendiente crédito</p>
                  <p className="text-2xl font-bold text-orange-700">${detailedReport.pendiente_credito.toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Vendedores */}
            {detailedReport.vendedores.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Vendedores (conteo e importes)</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">Vendedor</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">#Ventas</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Contado</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Crédito</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Total Contado ($)</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Total Crédito ($)</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Total ($)</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.vendedores.map((vendedor) => (
                        <tr key={vendedor.vendedor_id} className="border-t">
                          <td className="px-4 py-2 text-sm font-medium">{vendedor.vendedor_name}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.sales_count}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.contado_count}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.credito_count}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold text-green-600">${vendedor.total_contado.toFixed(2)}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold text-yellow-600">${vendedor.total_credito.toFixed(2)}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold text-blue-600">${(vendedor.total_contado + vendedor.total_credito).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Costo/Venta/Utilidad por Día */}
            {detailedReport.daily_summaries.length > 0 && (
              <div className="p-6 border-b-2 border-gray-300">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Costo / Venta / Utilidad por Día</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">Fecha</th>
                        <th className="px-4 py-2 text-right text-sm font-medium text-gray-500">Costo</th>
                        <th className="px-4 py-2 text-right text-sm font-medium text-gray-500">Venta</th>
                        <th className="px-4 py-2 text-right text-sm font-medium text-gray-500">Utilidad</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.daily_summaries.map((daily) => (
                        <tr key={daily.fecha} className="border-t">
                          <td className="px-4 py-2 text-sm">{new Date(daily.fecha).toLocaleDateString()}</td>
                          <td className="px-4 py-2 text-right text-sm">${daily.costo.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right text-sm">${daily.venta.toFixed(2)}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold">${daily.utilidad.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

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
          </div>
        )}

        {!report && !detailedReport && !loading && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
            Seleccione las fechas y haga clic en "Generar Reporte" para ver el corte de caja
          </div>
        )}

        {/* Print Styles */}
        <style jsx>{`
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

