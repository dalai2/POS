import React from 'react';
import { SummaryCards } from './SummaryCards';
import { CostsAndProfits } from './CostsAndProfits';
import { PiecesTotalCards } from './PiecesTotalCards';
import { PiecesSummary } from './PiecesSummary';
import { VendorsTable } from './VendorsTable';
import { SalesDetailsTable } from './SalesDetailsTable';
import { HistorialesSection } from './HistorialesSection';
import { AnalyticsDashboard } from './AnalyticsDashboard';

// Helper function to parse date string as local date (not UTC)
const formatLocalDate = (dateStr: string): string => {
  if (!dateStr) return '';
  // Parse YYYY-MM-DD as local date, not UTC
  const [year, month, day] = dateStr.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

interface DetailedReportViewProps {
  detailedReport: any;
  isDayClosed: boolean | null;
  usingClosure: boolean;
  userRole: string;
  closing: boolean;
  closeMsg: string | null;
  onCloseDay: () => void;
}

export const DetailedReportView: React.FC<DetailedReportViewProps> = ({
  detailedReport,
  isDayClosed,
  usingClosure,
  userRole,
  closing,
  closeMsg,
  onCloseDay,
}) => {
  return (
    <div className="rounded-xl shadow-xl" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
      {/* Header */}
      <div className="text-center p-8" style={{ borderBottom: '3px solid #2e4354' }}>
        <h2 className="text-3xl font-['Exo_2',sans-serif] font-bold mb-2" style={{ color: '#2e4354' }}>CORTE DE CAJA</h2>
        <p className="text-lg" style={{ color: '#2e4354', opacity: 0.8 }}>
          Rango: {formatLocalDate(detailedReport.start_date)} a {formatLocalDate(detailedReport.end_date)}
        </p>
        <p className="text-sm" style={{ color: '#2e4354', opacity: 0.6 }}>
          Generado: {detailedReport.generated_at}
        </p>

        {isDayClosed === true && (
          <div className="mt-3 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium shadow-sm" style={{ backgroundColor: 'rgba(255, 233, 142, 0.3)', color: '#000000', border: '1px solid rgba(255, 233, 142, 0.6)' }}>
            ✅ Caja cerrada
          </div>
        )}
        {usingClosure && (
          <div className="mt-3 inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium shadow-sm" style={{ backgroundColor: 'rgba(46, 67, 84, 0.1)', color: '#2e4354' }}>
            📦 Mostrando cierre guardado
          </div>
        )}

        {(userRole === 'admin' || userRole === 'owner') && (
          <div className="mt-4 flex justify-center gap-3">
            <button
              onClick={onCloseDay}
              disabled={closing || isDayClosed === true}
              className="px-6 py-2.5 rounded-lg text-white font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
              style={{ backgroundColor: (closing || isDayClosed === true) ? '#2e4354' : '#2e4354' }}
            >
              {closing ? 'Cerrando...' : (isDayClosed === true ? '✅ Cash Register Closed' : '🔒 Cerrar Caja (día actual)')}
            </button>
          </div>
        )}
        {closeMsg && (
          <div className="mt-3 text-sm font-medium" style={{ color: '#2e4354' }}>{closeMsg}</div>
        )}
      </div>

      {/* Resumen General */}
      <SummaryCards detailedReport={detailedReport} />

      {/* Costos y Utilidades */}
      <div className="p-6">
        <CostsAndProfits detailedReport={detailedReport} />
      </div>

      {/* Total de Piezas por Nombre (sin liquidadas) */}
      {detailedReport.total_piezas_por_nombre_sin_liquidadas && (
        <div className="p-6">
          <PiecesTotalCards totalPiezasPorNombre={detailedReport.total_piezas_por_nombre_sin_liquidadas} />
        </div>
      )}

      {/* Resumen Detallado */}
      <div className="p-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
        <h4 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>Resumen Detallado</h4>
        <AnalyticsDashboard dashboard={detailedReport.dashboard} />
      </div>

      {/* Resumen de Piezas */}
      {detailedReport.resumen_piezas && (
        <div className="p-6">
          <PiecesSummary resumenPiezas={detailedReport.resumen_piezas} />
        </div>
      )}

      {/* Resumen por Vendedores */}
      {detailedReport.vendedores && detailedReport.vendedores.length > 0 && (
        <div className="p-6">
          <VendorsTable vendedores={detailedReport.vendedores} />
        </div>
      )}

      {/* Detalle de Ventas */}
      {detailedReport.sales_details && detailedReport.sales_details.length > 0 && (
        <SalesDetailsTable salesDetails={detailedReport.sales_details} />
      )}

      {/* Historiales */}
      <HistorialesSection
        historialApartados={detailedReport.historial_apartados}
        historialPedidos={detailedReport.historial_pedidos}
        historialAbonosApartados={detailedReport.historial_abonos_apartados}
        historialAbonosPedidos={detailedReport.historial_abonos_pedidos}
        apartadosCanceladosVencidos={detailedReport.apartados_cancelados_vencidos}
        pedidosCanceladosVencidos={detailedReport.pedidos_cancelados_vencidos}
      />
    </div>
  );
};

