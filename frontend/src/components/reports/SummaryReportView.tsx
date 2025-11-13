import { CorteDeCajaReport } from '../../types/reports';

interface SummaryReportViewProps {
  report: CorteDeCajaReport;
}

export function SummaryReportView({ report }: SummaryReportViewProps) {
  return (
    <div
      className="rounded-xl shadow-xl p-8"
      style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}
    >
      <div className="text-center mb-8">
        <h2
          className="text-2xl font-['Exo_2',sans-serif] font-bold"
          style={{ color: '#2e4354' }}
        >
          CORTE DE CAJA
        </h2>
        <p className="mt-2" style={{ color: '#2e4354', opacity: 0.8 }}>
          Del {new Date(report.start_date).toLocaleDateString()} {' al '}
          {new Date(report.end_date).toLocaleDateString()}
        </p>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
          RESUMEN DE VENTAS
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div
            className="p-4 rounded-lg shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)' }}
          >
            <p className="text-sm" style={{ color: '#2e4354', opacity: 0.75 }}>Ventas activas totales</p>
            <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>
              {report.ventas_contado_count}
            </p>
            <p className="text-lg font-semibold" style={{ color: '#2e4354' }}>
              ${report.ventas_contado_total.toFixed(2)}
            </p>
          </div>
          <div
            className="p-4 rounded-lg shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)' }}
          >
            <p className="text-sm" style={{ color: '#2e4354', opacity: 0.75 }}>Ventas a Crédito</p>
            <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>
              {report.ventas_credito_count}
            </p>
            <p className="text-lg font-semibold" style={{ color: '#2e4354' }}>
              ${report.ventas_credito_total.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
          POR MÉTODO DE PAGO
        </h3>
        <div className="space-y-3">
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Efectivo (Ventas)</span>
            <span className="text-lg font-bold">
              ${report.efectivo_ventas.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Tarjeta (Ventas)</span>
            <span className="text-lg font-bold">
              ${report.tarjeta_ventas.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Crédito</span>
            <span className="text-lg font-bold">
              ${report.credito_ventas.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
          ABONOS A CRÉDITOS
        </h3>
        <div className="space-y-3">
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Abonos en Efectivo</span>
            <span className="text-lg font-bold">
              ${report.abonos_efectivo.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Abonos con Tarjeta</span>
            <span className="text-lg font-bold">
              ${report.abonos_tarjeta.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#2e4354', color: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.3)' }}
          >
            <span className="font-semibold">Total Abonos</span>
            <span className="text-xl font-bold">
              ${report.abonos_total.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
          PEDIDOS ESPECIALES
        </h3>
        <div className="space-y-3">
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Cantidad de Pedidos</span>
            <span className="text-lg font-bold">
              {report.pedidos_count}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Total Pedidos</span>
            <span className="text-lg font-bold">
              ${report.pedidos_total.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Anticipos</span>
            <span className="text-lg font-bold">
              ${report.pedidos_anticipos.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Saldo Pendiente</span>
            <span className="text-lg font-bold">
              ${report.pedidos_saldo.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Pagos en Efectivo</span>
            <span className="text-lg font-bold">
              ${report.pedidos_efectivo.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)', color: '#2e4354' }}
          >
            <span className="font-medium">Pagos con Tarjeta</span>
            <span className="text-lg font-bold">
              ${report.pedidos_tarjeta.toFixed(2)}
            </span>
          </div>
          <div
            className="flex justify-between items-center p-3 rounded-lg shadow transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg"
            style={{ backgroundColor: '#2e4354', color: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.3)' }}
          >
            <span className="font-semibold">Total Pagos Registrados</span>
            <span className="text-xl font-bold">
              ${report.pedidos_pagos_total.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
          INGRESOS TOTALES
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div
            className="p-4 rounded-lg text-center shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)' }}
          >
            <p className="text-sm" style={{ color: '#2e4354', opacity: 0.75 }}>Total Ingresos Efectivo</p>
            <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>
              ${report.total_efectivo.toFixed(2)}
            </p>
          </div>
          <div
            className="p-4 rounded-lg text-center shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)' }}
          >
            <p className="text-sm" style={{ color: '#2e4354', opacity: 0.75 }}>Total Ingresos Tarjeta</p>
            <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>
              ${report.total_tarjeta.toFixed(2)}
            </p>
          </div>
          <div
            className="p-4 rounded-lg text-center shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#2e4354', color: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.3)' }}
          >
            <p className="text-sm font-semibold">Total Ingresos</p>
            <p className="text-3xl font-bold">
              ${report.total_revenue.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
          COSTOS Y UTILIDADES
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div
            className="p-4 rounded-lg text-center shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.08)' }}
          >
            <p className="text-sm" style={{ color: '#2e4354', opacity: 0.75 }}>Costos Totales</p>
            <p className="text-2xl font-bold" style={{ color: '#b91c1c' }}>
              ${report.total_cost.toFixed(2)}
            </p>
          </div>
          <div
            className="p-4 rounded-lg text-center shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(46, 67, 84, 0.08)' }}
          >
            <p className="text-sm" style={{ color: '#2e4354', opacity: 0.75 }}>Utilidad Total</p>
            <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>
              ${report.total_profit.toFixed(2)}
            </p>
          </div>
          <div
            className="p-4 rounded-lg text-center shadow-md transition-transform duration-200 hover:-translate-y-1 hover:shadow-xl"
            style={{ backgroundColor: '#2e4354', color: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.3)' }}
          >
            <p className="text-sm">Margen de Utilidad</p>
            <p className="text-2xl font-bold">
              {report.profit_margin.toFixed(2)}%
            </p>
          </div>
        </div>
      </div>

      {report.returns_count > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
            DEVOLUCIONES
          </h3>
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="font-medium">
                Total Devoluciones ({report.returns_count})
              </span>
              <span className="text-lg font-bold text-orange-600">
                ${report.returns_total.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}

      {report.vendedores && report.vendedores.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b-2 border-gray-300 pb-2">
            RESUMEN DE VENDEDORES
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-gray-500">
                    Vendedor
                  </th>
                  <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">
                    #Ventas
                  </th>
                  <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">
                    Contado
                  </th>
                  <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">
                    Crédito
                  </th>
                  <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">
                    Total Contado ($)
                  </th>
                  <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">
                    Total Crédito ($)
                  </th>
                  <th className="px-4 py-2 text-center text-sm font-medium text-gray-500">
                    Total ($)
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {report.vendedores.map((vendedor, idx) => (
                  <tr
                    key={`${vendedor.vendedor_id}-${idx}`}
                    className="border-t"
                  >
                    <td className="px-4 py-2 text-sm font-medium">
                      {vendedor.vendedor_name}
                    </td>
                    <td className="px-4 py-2 text-center text-sm">
                      {vendedor.sales_count}
                    </td>
                    <td className="px-4 py-2 text-center text-sm">
                      {vendedor.contado_count}
                    </td>
                    <td className="px-4 py-2 text-center text-sm">
                      {vendedor.credito_count}
                    </td>
                    <td className="px-4 py-2 text-center text-sm font-bold text-green-600">
                      ${vendedor.total_contado.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-center text-sm font-bold text-yellow-600">
                      ${vendedor.total_credito.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-center text-sm font-bold text-blue-600">
                      ${(vendedor.total_contado + vendedor.total_credito).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

