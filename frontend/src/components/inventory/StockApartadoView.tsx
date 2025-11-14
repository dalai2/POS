import React from 'react';
import { StockApartado } from '../../types/inventory';

interface StockApartadoViewProps {
  stockApartado: StockApartado[] | null;
  loading: boolean;
}

export const StockApartadoView: React.FC<StockApartadoViewProps> = ({ stockApartado, loading }) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-lg" style={{ color: '#2e4354' }}>Cargando...</div>
      </div>
    );
  }

  if (!stockApartado || stockApartado.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-lg" style={{ color: '#2e4354', opacity: 0.7 }}>
          No hay stock de apartado disponible
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Stock de Apartado
      </h2>
      
      {stockApartado.map((group, idx) => (
        <div
          key={idx}
          className="rounded-xl shadow-lg p-6 mb-6"
          style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}
        >
          <div className="mb-4">
            <div className="flex flex-wrap gap-4 items-center mb-2">
              {group.nombre && (
                <span className="font-semibold" style={{ color: '#2e4354' }}>
                  {group.nombre}
                </span>
              )}
              {group.modelo && (
                <span className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>
                  Modelo: {group.modelo}
                </span>
              )}
              {group.quilataje && (
                <span className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>
                  Quilataje: {group.quilataje}
                </span>
              )}
              {group.marca && (
                <span className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>
                  Marca: {group.marca}
                </span>
              )}
              {group.color && (
                <span className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>
                  Color: {group.color}
                </span>
              )}
            </div>
            <div className="text-lg font-bold" style={{ color: '#2e4354' }}>
              Cantidad Total: {group.cantidad_total}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr style={{ backgroundColor: 'rgba(46, 67, 84, 0.05)' }}>
                  <th className="px-4 py-2 text-left border" style={{ color: '#2e4354' }}>
                    Código
                  </th>
                  <th className="px-4 py-2 text-left border" style={{ color: '#2e4354' }}>
                    Cantidad
                  </th>
                  <th className="px-4 py-2 text-left border" style={{ color: '#2e4354' }}>
                    Precio
                  </th>
                  <th className="px-4 py-2 text-left border" style={{ color: '#2e4354' }}>
                    Folio Apartado
                  </th>
                  <th className="px-4 py-2 text-left border" style={{ color: '#2e4354' }}>
                    Cliente
                  </th>
                  <th className="px-4 py-2 text-left border" style={{ color: '#2e4354' }}>
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {group.productos.map((producto, pIdx) => (
                  <tr key={pIdx} className="hover:bg-gray-50">
                    <td className="px-4 py-2 border" style={{ color: '#2e4354' }}>
                      {producto.codigo || 'N/A'}
                    </td>
                    <td className="px-4 py-2 border" style={{ color: '#2e4354' }}>
                      {producto.cantidad}
                    </td>
                    <td className="px-4 py-2 border" style={{ color: '#2e4354' }}>
                      ${producto.precio.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 border" style={{ color: '#2e4354' }}>
                      {producto.folio_apartado}
                    </td>
                    <td className="px-4 py-2 border" style={{ color: '#2e4354' }}>
                      {producto.cliente}
                    </td>
                    <td className="px-4 py-2 border">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          producto.status === 'pagado'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {producto.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
};

