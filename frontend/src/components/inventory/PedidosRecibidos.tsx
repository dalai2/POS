import React from 'react';
import { PedidoRecibido } from '../../types/inventory';
import { cleanFolio } from '../../utils/folioHelper';

interface PedidosRecibidosProps {
  pedidos: PedidoRecibido[];
}

export const PedidosRecibidos: React.FC<PedidosRecibidosProps> = ({ pedidos }) => {
  if (pedidos.length === 0) {
    return (
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
          Pedidos Recibidos
        </h2>
        <p className="text-gray-500">No hay pedidos recibidos en este período</p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Pedidos Recibidos ({pedidos.length})
      </h2>
      <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead style={{ backgroundColor: '#f0f7f7' }}>
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Fecha</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Folio</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Cliente</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Producto</th>
                <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>Cantidad</th>
                <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>Total</th>
              </tr>
            </thead>
            <tbody>
              {pedidos.map((pedido) => (
                <tr key={pedido.id} className="border-t" style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>
                    {new Date(pedido.fecha_recepcion).toLocaleDateString('es-ES')}
                  </td>
                  <td className="px-4 py-3 text-sm font-mono" style={{ color: '#2e4354' }}>
                    {cleanFolio(pedido.folio_pedido)}
                  </td>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{pedido.cliente_nombre}</td>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>
                    {pedido.producto_nombre} - {pedido.producto_modelo}
                  </td>
                  <td className="px-4 py-3 text-right text-sm" style={{ color: '#2e4354' }}>{pedido.cantidad}</td>
                  <td className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>
                    ${pedido.total.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

