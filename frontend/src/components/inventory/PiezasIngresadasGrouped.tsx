import React from 'react';
import { PiezasIngresadasGroup } from '../../types/inventory';

interface PiezasIngresadasGroupedProps {
  groups: PiezasIngresadasGroup[];
}

export const PiezasIngresadasGrouped: React.FC<PiezasIngresadasGroupedProps> = ({ groups }) => {
  if (groups.length === 0) {
    return (
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
          Piezas Ingresadas (Agrupadas)
        </h2>
        <p className="text-gray-500">No hay piezas ingresadas en este período</p>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Piezas Ingresadas (Agrupadas por Nombre, Modelo, Quilataje)
      </h2>
      <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
        <table className="w-full">
          <thead style={{ backgroundColor: '#f0f7f7' }}>
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Nombre</th>
              <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Modelo</th>
              <th className="px-4 py-3 text-left text-sm font-semibold" style={{ color: '#2e4354' }}>Quilataje</th>
              <th className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>Cantidad Total</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((group, idx) => (
              <tr key={idx} className="border-t" style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}>
                <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.nombre || 'N/A'}</td>
                <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.modelo || 'N/A'}</td>
                <td className="px-4 py-3 text-sm" style={{ color: '#2e4354' }}>{group.quilataje || 'N/A'}</td>
                <td className="px-4 py-3 text-right text-sm font-semibold" style={{ color: '#2e4354' }}>{group.cantidad_total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

