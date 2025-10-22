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
    window.print();
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
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">Venta ($)</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white">
                      {detailedReport.vendedores.map((vendedor) => (
                        <tr key={vendedor.vendedor_id} className="border-t">
                          <td className="px-4 py-2 text-sm font-medium">{vendedor.vendedor_name}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.sales_count}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.contado_count}</td>
                          <td className="px-4 py-2 text-center text-sm">{vendedor.credito_count}</td>
                          <td className="px-4 py-2 text-center text-sm font-bold">${vendedor.total_contado + vendedor.total_credito}</td>
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

