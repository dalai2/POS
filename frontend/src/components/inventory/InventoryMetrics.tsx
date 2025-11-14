import React from 'react';
import { InventoryReport } from '../../types/inventory';

interface InventoryMetricsProps {
  report: InventoryReport;
  totalAgrupaciones?: number;
  stockDate?: string;
}

export const InventoryMetrics: React.FC<InventoryMetricsProps> = ({ report, totalAgrupaciones, stockDate }) => {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-MX', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold mb-4" style={{ color: '#2e4354' }}>
        Métricas de Inventario
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-xl shadow-lg p-6" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <div className="text-sm font-medium mb-1" style={{ color: '#2e4354', opacity: 0.7 }}>
            Total Entradas
          </div>
          <div className="text-3xl font-bold" style={{ color: '#2e4354' }}>
            {report.total_entradas}
          </div>
        </div>
        <div className="rounded-xl shadow-lg p-6" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <div className="text-sm font-medium mb-1" style={{ color: '#2e4354', opacity: 0.7 }}>
            Total Salidas
          </div>
          <div className="text-3xl font-bold" style={{ color: '#2e4354' }}>
            {report.total_salidas}
          </div>
        </div>
        <div className="rounded-xl shadow-lg p-6" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <div className="text-sm font-medium mb-1" style={{ color: '#2e4354', opacity: 0.7 }}>
            Piezas Devueltas
          </div>
          <div className="text-3xl font-bold" style={{ color: '#2e4354' }}>
            {report.piezas_devueltas_total || 0}
          </div>
        </div>
        {totalAgrupaciones !== undefined && (
          <div className="rounded-xl shadow-lg p-6" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
            <div className="text-sm font-medium mb-1" style={{ color: '#2e4354', opacity: 0.7 }}>
              Stock Actual Agrupado
            </div>
            <div className="text-3xl font-bold" style={{ color: '#2e4354' }}>
              {totalAgrupaciones}
            </div>
            <div className="text-xs mt-1" style={{ color: '#2e4354', opacity: 0.6 }}>
              grupos por nombre y quilataje
            </div>
            {stockDate && (
              <div className="text-xs mt-2 font-medium" style={{ color: '#2e4354', opacity: 0.7 }}>
                📅 Stock al {formatDate(stockDate)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

