import React from 'react';

interface Apartado {
  id: string;
  fecha: string;
  cliente: string;
  total: number;
  anticipo: number;
  saldo: number;
  estado: string;
  vendedor: string;
  codigo_producto?: string;
  costo?: number;
  ganancia?: number;
  is_parent?: boolean;
}

interface Pedido {
  id: string;
  fecha: string;
  cliente: string;
  producto: string;
  cantidad: number;
  total: number;
  anticipo: number;
  saldo: number;
  estado: string;
  vendedor: string;
  codigo_producto?: string;
  costo?: number;
  ganancia?: number;
  is_parent?: boolean;
}

interface AbonoApartado {
  id: number;
  fecha: string;
  cliente: string;
  monto: number;
  metodo_pago: string;
  vendedor: string;
  codigo_producto?: string;
}

interface AbonoPedido {
  id: number;
  fecha: string;
  cliente: string;
  producto: string;
  monto: number;
  metodo_pago: string;
  vendedor: string;
  codigo_producto?: string;
}

interface ApartadoCanceladoVencido {
  id: string;
  fecha: string;
  cliente: string;
  total: number;
  anticipo: number;
  saldo: number;
  estado: string;
  vendedor: string;
  codigo_producto?: string;
  costo?: number;
  ganancia?: number;
  is_parent?: boolean;
}

interface PedidoCanceladoVencido {
  id: string;
  fecha: string;
  cliente: string;
  producto: string;
  cantidad: number;
  total: number;
  anticipo: number;
  saldo: number;
  estado: string;
  vendedor: string;
  codigo_producto?: string;
  costo?: number;
  ganancia?: number;
  is_parent?: boolean;
}

interface HistorialesSectionProps {
  historialApartados?: Apartado[];
  historialPedidos?: Pedido[];
  historialAbonosApartados?: AbonoApartado[];
  historialAbonosPedidos?: AbonoPedido[];
  apartadosCanceladosVencidos?: ApartadoCanceladoVencido[];
  pedidosCanceladosVencidos?: PedidoCanceladoVencido[];
}

export const HistorialesSection: React.FC<HistorialesSectionProps> = ({
  historialApartados,
  historialPedidos,
  historialAbonosApartados,
  historialAbonosPedidos,
  apartadosCanceladosVencidos,
  pedidosCanceladosVencidos,
}) => {
  return (
    <>
      {/* Historial de Apartados Realizados */}
      {historialApartados && historialApartados.length > 0 && (
        <div className="p-6 border-b-2 border-gray-300">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Apartados Realizados</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Costo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Ganancia</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Anticipo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {historialApartados.map((apartado) => (
                  <tr 
                    key={apartado.id} 
                    className={`border-t ${apartado.is_parent ? 'bg-gray-50 font-semibold' : 'bg-white'}`}
                  >
                    <td className="px-2 py-2 text-xs">{new Date(apartado.fecha).toLocaleString()}</td>
                    <td className="px-2 py-2 text-xs">{apartado.cliente}</td>
                    <td className="px-2 py-2 text-xs">
                      {apartado.is_parent ? (
                        <span className="font-semibold">{apartado.codigo_producto || 'Apartado'}</span>
                      ) : (
                        <span className="pl-4 text-gray-600">{apartado.codigo_producto || 'N/A'}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-right text-xs font-bold">${apartado.total.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs">${(apartado.costo || 0).toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs font-semibold" style={{ color: (apartado.ganancia || 0) >= 0 ? '#059669' : '#dc2626' }}>
                      ${(apartado.ganancia || 0).toFixed(2)}
                    </td>
                    {apartado.is_parent ? (
                      <>
                        <td className="px-2 py-2 text-right text-xs text-green-600">${apartado.anticipo.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right text-xs text-orange-600">${apartado.saldo.toFixed(2)}</td>
                      </>
                    ) : (
                      <>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                      </>
                    )}
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
      {historialPedidos && historialPedidos.length > 0 && (
        <div className="p-6 border-b-2 border-gray-300">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Pedidos Realizados</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Producto</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Cant</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Costo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Ganancia</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Anticipo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {historialPedidos.map((pedido) => (
                  <tr 
                    key={pedido.id} 
                    className={`border-t ${pedido.is_parent ? 'bg-gray-50 font-semibold' : 'bg-white'}`}
                  >
                    <td className="px-2 py-2 text-xs">{new Date(pedido.fecha).toLocaleString()}</td>
                    <td className="px-2 py-2 text-xs">{pedido.cliente}</td>
                    <td className="px-2 py-2 text-xs">
                      {pedido.is_parent ? (
                        <span className="font-semibold">{pedido.producto || 'Pedido'}</span>
                      ) : (
                        <span className="pl-4 text-gray-600">{pedido.producto}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-xs">
                      {pedido.is_parent ? (
                        <span className="font-semibold">{pedido.codigo_producto || 'Pedido'}</span>
                      ) : (
                        <span className="pl-4 text-gray-600">{pedido.codigo_producto || 'N/A'}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-center text-xs">{pedido.cantidad}</td>
                    <td className="px-2 py-2 text-right text-xs font-bold">${pedido.total.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs">${(pedido.costo || 0).toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs font-semibold" style={{ color: (pedido.ganancia || 0) >= 0 ? '#059669' : '#dc2626' }}>
                      ${(pedido.ganancia || 0).toFixed(2)}
                    </td>
                    {pedido.is_parent ? (
                      <>
                        <td className="px-2 py-2 text-right text-xs text-green-600">${pedido.anticipo.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right text-xs text-orange-600">${pedido.saldo.toFixed(2)}</td>
                      </>
                    ) : (
                      <>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                      </>
                    )}
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
      {historialAbonosApartados && historialAbonosApartados.length > 0 && (
        <div className="p-6 border-b-2 border-gray-300">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Abonos de Apartados</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Método de Pago</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {historialAbonosApartados.map((abono) => (
                  <tr key={abono.id} className="border-t">
                    <td className="px-2 py-2 text-xs">{new Date(abono.fecha).toLocaleString()}</td>
                    <td className="px-2 py-2 text-xs">{abono.cliente}</td>
                    <td className="px-2 py-2 text-xs">{abono.codigo_producto || 'N/A'}</td>
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
      {historialAbonosPedidos && historialAbonosPedidos.length > 0 && (
        <div className="p-6 border-b-2 border-gray-300">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Historial de Abonos para Pedidos</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Producto</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Método de Pago</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {historialAbonosPedidos.map((abono) => (
                  <tr key={abono.id} className="border-t">
                    <td className="px-2 py-2 text-xs">{new Date(abono.fecha).toLocaleString()}</td>
                    <td className="px-2 py-2 text-xs">{abono.cliente}</td>
                    <td className="px-2 py-2 text-xs">{abono.producto}</td>
                    <td className="px-2 py-2 text-xs">{abono.codigo_producto || 'N/A'}</td>
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
      {apartadosCanceladosVencidos && apartadosCanceladosVencidos.length > 0 && (
        <div className="p-6 border-b-2 border-gray-300">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Apartados Cancelados y Vencidos</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Costo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Ganancia</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total Pagado</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo Pendiente</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Tipo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {apartadosCanceladosVencidos.map((apartado) => (
                  <tr 
                    key={apartado.id} 
                    className={`border-t ${apartado.is_parent ? 'bg-gray-50 font-semibold' : 'bg-white'}`}
                  >
                    <td className="px-2 py-2 text-xs">{new Date(apartado.fecha).toLocaleString()}</td>
                    <td className="px-2 py-2 text-xs">{apartado.cliente}</td>
                    <td className="px-2 py-2 text-xs">
                      {apartado.is_parent ? (
                        <span className="font-semibold">{apartado.codigo_producto || 'Apartado'}</span>
                      ) : (
                        <span className="pl-4 text-gray-600">{apartado.codigo_producto || 'N/A'}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-right text-xs font-bold">${apartado.total.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs">${(apartado.costo || 0).toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs font-semibold" style={{ color: (apartado.ganancia || 0) >= 0 ? '#059669' : '#dc2626' }}>
                      ${(apartado.ganancia || 0).toFixed(2)}
                    </td>
                    {apartado.is_parent ? (
                      <>
                        <td className="px-2 py-2 text-right text-xs text-green-600">${apartado.anticipo.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right text-xs text-gray-600">${apartado.saldo.toFixed(2)}</td>
                        <td className="px-2 py-2 text-center text-xs">{apartado.estado}</td>
                        <td className={`px-2 py-2 text-center text-xs font-semibold ${apartado.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                          {apartado.estado === 'cancelado' ? 'Reembolso' : 'Saldo Vencido'}
                        </td>
                        <td className={`px-2 py-2 text-right text-xs font-bold ${apartado.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                          ${apartado.anticipo.toFixed(2)}
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                        <td className="px-2 py-2 text-center text-xs">{apartado.estado}</td>
                        <td className="px-2 py-2 text-center text-xs">-</td>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                      </>
                    )}
                    <td className="px-2 py-2 text-xs">{apartado.vendedor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pedidos Cancelados y Vencidos */}
      {pedidosCanceladosVencidos && pedidosCanceladosVencidos.length > 0 && (
        <div className="p-6 border-b-2 border-gray-300">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Pedidos Cancelados y Vencidos</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Producto</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Cant</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Costo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Ganancia</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total Pagado</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Saldo Pendiente</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
                  <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Tipo</th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Monto</th>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {pedidosCanceladosVencidos.map((pedido) => (
                  <tr 
                    key={pedido.id} 
                    className={`border-t ${pedido.is_parent ? 'bg-gray-50 font-semibold' : 'bg-white'}`}
                  >
                    <td className="px-2 py-2 text-xs">{new Date(pedido.fecha).toLocaleString()}</td>
                    <td className="px-2 py-2 text-xs">{pedido.cliente}</td>
                    <td className="px-2 py-2 text-xs">
                      {pedido.is_parent ? (
                        <span className="font-semibold">{pedido.producto || 'Pedido'}</span>
                      ) : (
                        <span className="pl-4 text-gray-600">{pedido.producto}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-xs">
                      {pedido.is_parent ? (
                        <span className="font-semibold">{pedido.codigo_producto || 'Pedido'}</span>
                      ) : (
                        <span className="pl-4 text-gray-600">{pedido.codigo_producto || 'N/A'}</span>
                      )}
                    </td>
                    <td className="px-2 py-2 text-center text-xs">{pedido.cantidad}</td>
                    <td className="px-2 py-2 text-right text-xs font-bold">${pedido.total.toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs">${(pedido.costo || 0).toFixed(2)}</td>
                    <td className="px-2 py-2 text-right text-xs font-semibold" style={{ color: (pedido.ganancia || 0) >= 0 ? '#059669' : '#dc2626' }}>
                      ${(pedido.ganancia || 0).toFixed(2)}
                    </td>
                    {pedido.is_parent ? (
                      <>
                        <td className="px-2 py-2 text-right text-xs text-green-600">${pedido.anticipo.toFixed(2)}</td>
                        <td className="px-2 py-2 text-right text-xs text-gray-600">${pedido.saldo.toFixed(2)}</td>
                        <td className="px-2 py-2 text-center text-xs">{pedido.estado}</td>
                        <td className={`px-2 py-2 text-center text-xs font-semibold ${pedido.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                          {pedido.estado === 'cancelado' ? 'Reembolso' : 'Saldo Vencido'}
                        </td>
                        <td className={`px-2 py-2 text-right text-xs font-bold ${pedido.estado === 'cancelado' ? 'text-red-600' : 'text-amber-600'}`}>
                          ${pedido.anticipo.toFixed(2)}
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                        <td className="px-2 py-2 text-center text-xs">{pedido.estado}</td>
                        <td className="px-2 py-2 text-center text-xs">-</td>
                        <td className="px-2 py-2 text-right text-xs">-</td>
                      </>
                    )}
                    <td className="px-2 py-2 text-xs">{pedido.vendedor}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
};

