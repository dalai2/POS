import React from 'react';

interface PiecesTotalCardsProps {
  totalPiezasPorNombre: Record<string, number>;
}

export const PiecesTotalCards: React.FC<PiecesTotalCardsProps> = ({ totalPiezasPorNombre }) => {
  if (!totalPiezasPorNombre || Object.keys(totalPiezasPorNombre).length === 0) {
    return null;
  }

  return (
    <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
      <h4 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Total de Piezas por Nombre (Excluyendo Liquidadas)</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(totalPiezasPorNombre)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([nombre, total]) => (
            <div 
              key={nombre}
              className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" 
              style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}
            >
              <p className="text-sm font-medium mb-2" style={{ color: '#2e4354' }}>{nombre}</p>
              <p className="text-2xl font-bold" style={{ color: '#000000' }}>{total}</p>
              <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>piezas</p>
            </div>
          ))}
      </div>
    </div>
  );
};

