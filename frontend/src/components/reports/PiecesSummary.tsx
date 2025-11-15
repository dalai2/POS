import React from 'react';

interface Pieza {
  nombre: string;
  modelo: string;
  quilataje: string;
  piezas_vendidas: number;
  piezas_pedidas: number;
  piezas_apartadas: number;
  piezas_liquidadas: number;
  total_piezas: number;
}

interface PiecesSummaryProps {
  resumenPiezas: Pieza[];
}

export const PiecesSummary: React.FC<PiecesSummaryProps> = ({ resumenPiezas }) => {
  if (!resumenPiezas || resumenPiezas.length === 0) {
    return (
      <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
        <h5 className="text-lg font-['Exo_2',sans-serif] font-bold mb-3" style={{ color: '#2e4354' }}>📦 Resumen de Piezas</h5>
        <p className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>No hay datos de piezas para mostrar en este período.</p>
      </div>
    );
  }

  return (
    <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
      <h5 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>📦 Resumen de Piezas ({resumenPiezas.length} registros)</h5>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse rounded-lg overflow-hidden shadow-sm" style={{ border: '1px solid rgba(46, 67, 84, 0.2)' }}>
          <thead style={{ backgroundColor: '#2e4354' }}>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Nombre</th>
              <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Modelo</th>
              <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Quilataje</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Vendidas</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Pedidas por el Cliente</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Apartadas</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Liquidadas</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {resumenPiezas.map((pieza, idx) => (
              <tr key={`${pieza.nombre}-${pieza.modelo}-${pieza.quilataje}-${idx}`} style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f0f7f7', borderBottom: '1px solid rgba(46, 67, 84, 0.08)' }}>
                <td className="px-4 py-3 text-sm font-semibold" style={{ color: '#000000', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.nombre}</td>
                <td className="px-4 py-3 text-sm" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.modelo || 'N/A'}</td>
                <td className="px-4 py-3 text-sm" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.quilataje || 'N/A'}</td>
                <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_vendidas}</td>
                <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_pedidas}</td>
                <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_apartadas}</td>
                <td className="px-4 py-3 text-sm text-right font-medium" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{pieza.piezas_liquidadas}</td>
                <td className="px-4 py-3 text-sm text-right font-bold" style={{ color: '#000000', backgroundColor: 'rgba(46, 67, 84, 0.1)' }}>{pieza.total_piezas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

