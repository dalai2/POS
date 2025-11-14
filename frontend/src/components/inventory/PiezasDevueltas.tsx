import React from 'react';
import { PiezaDevuelta } from '../../types/inventory';

interface PiezasDevueltasProps {
  devueltas: PiezaDevuelta[];
}

export const PiezasDevueltas: React.FC<PiezasDevueltasProps> = ({ devueltas }) => {
  if (devueltas.length === 0) {
    return (
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
          Piezas Devueltas
        </h2>
        <p className="text-gray-500">No hay piezas devueltas en este período</p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Piezas Devueltas ({devueltas.length})
      </h2>
      <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead style={{ backgroundColor: '#f0f7f7' }}>
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Fecha</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Tipo</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Folio</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Cliente</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Producto</th>
                <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>Cantidad</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Motivo</th>
              </tr>
            </thead>
            <tbody>
              {devueltas.map((devuelta) => (
                <tr key={devuelta.id} className="border-t" style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>
                    {new Date(devuelta.fecha).toLocaleDateString('es-ES')}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="px-2 py-1 rounded text-xs font-semibold" style={{ 
                      backgroundColor: devuelta.tipo === 'venta' ? '#dbeafe' : '#fef3c7',
                      color: devuelta.tipo === 'venta' ? '#1e40af' : '#92400e'
                    }}>
                      {devuelta.tipo === 'venta' ? 'Venta' : 'Pedido'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm font-mono" style={{ color: '#2e4354' }}>
                    {devuelta.folio || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{devuelta.cliente_nombre || '-'}</td>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{devuelta.producto_nombre}</td>
                  <td className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>{devuelta.cantidad}</td>
                  <td className="px-4 py-3 text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>{devuelta.motivo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

