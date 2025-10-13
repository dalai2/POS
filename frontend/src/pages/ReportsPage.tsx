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

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<CorteDeCajaReport | null>(null);
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const generateReport = async () => {
    setLoading(true);
    try {
      const response = await api.get('/reports/corte-de-caja', {
        params: { start_date: startDate, end_date: endDate }
      });
      setReport(response.data);
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
        </div>

        {/* Report */}
        {report && (
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

        {!report && !loading && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
            Seleccione las fechas y haga clic en "Generar Reporte" para ver el corte de caja
          </div>
        )}
      </div>
    </Layout>
  );
}

