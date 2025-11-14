import React from 'react';

interface CostsAndProfitsProps {
  detailedReport: {
    costo_ventas_contado: number;
    costo_apartados_pedidos_liquidados: number;
    utilidad_productos_liquidados: number;
    utilidad_ventas_activas: number;
  };
}

export const CostsAndProfits: React.FC<CostsAndProfitsProps> = ({ detailedReport }) => {
  return (
    <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
      <h4 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Costos y Utilidades</h4>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Costos Total de Ventas Activas</p>
          <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>${detailedReport.costo_ventas_contado.toFixed(2)}</p>
          <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>Productos vendidos</p>
        </div>
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#e0fdff', border: '1px solid rgba(224, 253, 255, 0.6)' }}>
          <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Costo de productos liquidados</p>
          <p className="text-2xl font-bold" style={{ color: '#2e4354' }}>${detailedReport.costo_apartados_pedidos_liquidados.toFixed(2)}</p>
          <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>Status liquidado/entregado</p>
        </div>
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#f0f7f7', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <p className="text-sm font-medium" style={{ color: '#2e4354' }}>Utilidades de productos liquidados</p>
          <p className="text-2xl font-bold" style={{ color: '#000000' }}>${detailedReport.utilidad_productos_liquidados.toFixed(2)}</p>
          <p className="text-xs font-medium mt-1" style={{ color: '#2e4354', opacity: 0.7 }}>Apartados + Pedidos</p>
        </div>
        <div className="text-center p-4 rounded-xl shadow-lg transition-all duration-200 hover:shadow-xl hover:-translate-y-1" style={{ backgroundColor: '#2e4354', border: '1px solid rgba(46, 67, 84, 0.8)' }}>
          <p className="text-sm font-medium" style={{ color: '#ffffff', opacity: 0.9 }}>Utilidades de Ventas Activas</p>
          <p className="text-2xl font-bold" style={{ color: '#ffffff' }}>${detailedReport.utilidad_ventas_activas.toFixed(2)}</p>
          <p className="text-xs font-medium mt-1" style={{ color: '#ffffff', opacity: 0.8 }}>(Efectivo + Tarjeta -3%) - Costos</p>
        </div>
      </div>
    </div>
  );
};

