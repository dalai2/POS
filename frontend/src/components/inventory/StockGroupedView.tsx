import React, { useState } from 'react';
import { StockGrouped } from '../../types/inventory';

interface StockGroupedViewProps {
  stock: StockGrouped[];
  loading: boolean;
}

export const StockGroupedView: React.FC<StockGroupedViewProps> = ({ stock, loading }) => {
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set());

  const toggleGroup = (index: number) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedGroups(newExpanded);
  };

  if (loading) {
    return <div className="text-center py-8">Cargando stock...</div>;
  }

  if (stock.length === 0) {
    return (
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
          Stock Actual Agrupado
        </h2>
        <p className="text-gray-500">No hay productos en stock</p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Stock Actual Agrupado ({stock.length} grupos)
      </h2>
      <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead style={{ backgroundColor: '#f0f7f7' }}>
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}></th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Nombre</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Modelo</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Quilataje</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Marca</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Color</th>
                <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Talla</th>
                <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>Cantidad Total</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((group, idx) => (
                <React.Fragment key={idx}>
                  <tr 
                    className="border-t cursor-pointer hover:bg-gray-50" 
                    style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}
                    onClick={() => toggleGroup(idx)}
                  >
                    <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>
                      {expandedGroups.has(idx) ? '▼' : '▶'}
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold" style={{ color: '#2e4354' }}>{group.nombre || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.modelo || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.quilataje || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.marca || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.color || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.talla || 'N/A'}</td>
                    <td className="px-4 py-3 text-right text-sm font-bold" style={{ color: '#2e4354' }}>{group.cantidad_total}</td>
                  </tr>
                  {expandedGroups.has(idx) && group.productos.map((producto, pIdx) => (
                    <tr key={`${idx}-${pIdx}`} className="bg-gray-50">
                      <td></td>
                      <td colSpan={6} className="px-4 py-2 text-xs" style={{ color: '#2e4354', opacity: 0.7 }}>
                        {producto.codigo ? `Código: ${producto.codigo}` : `ID: ${producto.id}`} - 
                        Stock: {producto.stock} - 
                        Precio: ${producto.precio.toFixed(2)} - 
                        Costo: ${producto.costo.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right text-xs" style={{ color: '#2e4354' }}>{producto.stock}</td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

