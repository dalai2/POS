import React from 'react';
import { InventoryMovement } from '../../types/inventory';

interface InventoryHistoryProps {
  entradas: InventoryMovement[];
  salidas: InventoryMovement[];
}

export const InventoryHistory: React.FC<InventoryHistoryProps> = ({ entradas, salidas }) => {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Historial de Inventario
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Entradas */}
        <div>
          <h3 className="text-xl font-semibold mb-3" style={{ color: '#2e4354' }}>
            Entradas ({entradas.length})
          </h3>
          <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#f0f7f7', position: 'sticky', top: 0 }}>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: '#2e4354' }}>Fecha</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: '#2e4354' }}>Producto</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: '#2e4354' }}>Cantidad</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: '#2e4354' }}>Notas</th>
                  </tr>
                </thead>
                <tbody>
                  {entradas.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-3 text-center text-sm text-gray-500">
                        No hay entradas en este período
                      </td>
                    </tr>
                  ) : (
                    entradas.map((mov) => (
                      <tr key={mov.id} className="border-t" style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}>
                        <td className="px-4 py-2 text-xs" style={{ color: '#2e4354' }}>
                          {new Date(mov.created_at).toLocaleDateString('es-ES')}
                        </td>
                        <td className="px-4 py-2 text-xs" style={{ color: '#2e4354' }}>
                          {mov.product_name} {mov.product_codigo ? `(${mov.product_codigo})` : ''}
                        </td>
                        <td className="px-4 py-2 text-right text-xs font-semibold" style={{ color: '#10b981' }}>
                          +{mov.quantity}
                        </td>
                        <td className="px-4 py-2 text-xs" style={{ color: '#2e4354', opacity: 0.7 }}>
                          {mov.notes || '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Salidas */}
        <div>
          <h3 className="text-xl font-semibold mb-3" style={{ color: '#2e4354' }}>
            Salidas ({salidas.length})
          </h3>
          <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead style={{ backgroundColor: '#f0f7f7', position: 'sticky', top: 0 }}>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: '#2e4354' }}>Fecha</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: '#2e4354' }}>Producto</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold" style={{ color: '#2e4354' }}>Cantidad</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold" style={{ color: '#2e4354' }}>Motivo</th>
                  </tr>
                </thead>
                <tbody>
                  {salidas.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-4 py-3 text-center text-sm text-gray-500">
                        No hay salidas en este período
                      </td>
                    </tr>
                  ) : (
                    salidas.map((mov) => (
                      <tr key={mov.id} className="border-t" style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}>
                        <td className="px-4 py-2 text-xs" style={{ color: '#2e4354' }}>
                          {new Date(mov.created_at).toLocaleDateString('es-ES')}
                        </td>
                        <td className="px-4 py-2 text-xs" style={{ color: '#2e4354' }}>
                          {mov.product_name} {mov.product_codigo ? `(${mov.product_codigo})` : ''}
                        </td>
                        <td className="px-4 py-2 text-right text-xs font-semibold" style={{ color: '#ef4444' }}>
                          -{mov.quantity}
                        </td>
                        <td className="px-4 py-2 text-xs" style={{ color: '#2e4354', opacity: 0.7 }}>
                          {mov.notes || '-'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

