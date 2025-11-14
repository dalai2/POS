import React from 'react';

interface SummaryCardsProps {
  detailedReport: {
    contado_count: number;
    total_contado: number;
    liquidacion_count: number;
    liquidacion_total: number;
    ventas_pasivas_total: number;
    cuentas_por_cobrar: number;
  };
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ detailedReport }) => {
  return (
    <div className="p-6" style={{ borderBottom: '2px solid rgba(46, 67, 84, 0.1)' }}>
      <h3 className="text-xl font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Resumen General</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Ventas activas totales</p>
          <p className="text-lg font-semibold" style={{ color: '#000000' }}>{detailedReport.contado_count} ventas</p>
          <p className="text-2xl font-bold" style={{ color: '#000000' }}>${detailedReport.total_contado.toFixed(2)}</p>
        </div>
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(224, 253, 255, 0.6)' }}>
          <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Ventas de liquidación</p>
          <p className="text-lg font-semibold" style={{ color: '#000000' }}>{detailedReport.liquidacion_count} (Apartados + Pedidos)</p>
          <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>${detailedReport.liquidacion_total.toFixed(2)}</p>
        </div>
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Ventas pasivas totales</p>
          <p className="text-2xl font-bold" style={{ color: '#000000' }}>${detailedReport.ventas_pasivas_total.toFixed(2)}</p>
        </div>
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#2e4354', border: '1px solid rgba(46, 67, 84, 0.8)' }}>
          <p className="text-sm font-medium" style={{ color: '#ffffff', opacity: 0.9 }}>Cuentas por Cobrar</p>
          <p className="text-2xl font-bold" style={{ color: '#ffffff' }}>${detailedReport.cuentas_por_cobrar.toFixed(2)}</p>
          <p className="text-xs font-medium mt-1" style={{ color: '#ffffff', opacity: 0.8 }}>Saldo pendiente</p>
        </div>
      </div>
    </div>
  );
};

