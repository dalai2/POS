import React from 'react';
import { InventoryReport, StockGrouped } from '../../types/inventory';
import { InventoryMetrics } from './InventoryMetrics';
import { PiezasIngresadasGrouped } from './PiezasIngresadasGrouped';
import { InventoryHistory } from './InventoryHistory';
import { PedidosRecibidos } from './PedidosRecibidos';
import { PiezasDevueltas } from './PiezasDevueltas';

interface InventoryReportViewProps {
  report: InventoryReport;
  stockGrouped?: StockGrouped[] | null;
  stockDate?: string;
}

export const InventoryReportView: React.FC<InventoryReportViewProps> = ({ report, stockGrouped, stockDate }) => {
  const totalAgrupaciones = stockGrouped ? stockGrouped.length : undefined;
  
  return (
    <div>
      <InventoryMetrics report={report} totalAgrupaciones={totalAgrupaciones} stockDate={stockDate} />
      <PiezasIngresadasGrouped groups={report.piezas_ingresadas} />
      <InventoryHistory entradas={report.historial_entradas} salidas={report.historial_salidas} />
      <PedidosRecibidos pedidos={report.pedidos_recibidos} />
      <PiezasDevueltas devueltas={report.piezas_devueltas} />
    </div>
  );
};

