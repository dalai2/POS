import React from 'react';

interface DateSelectorProps {
  startDate: string;
  endDate: string;
  loading: boolean;
  isDayClosed: boolean | null;
  usingClosure: boolean;
  report: any;
  detailedReport: any;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onGenerateReport: () => void;
  onViewClosedDay: () => void;
  onDownloadCsv: () => void;
  onPrintReport: () => void;
}

export const DateSelector: React.FC<DateSelectorProps> = ({
  startDate,
  endDate,
  loading,
  isDayClosed,
  usingClosure,
  report,
  detailedReport,
  onStartDateChange,
  onEndDateChange,
  onGenerateReport,
  onViewClosedDay,
  onDownloadCsv,
  onPrintReport,
}) => {
  return (
    <div className="rounded-xl shadow-lg p-6 mb-6 print:hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
            Fecha Inicio
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => onStartDateChange(e.target.value)}
            className="w-full rounded-lg px-3 py-2 transition-all"
            style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
            onFocus={(e) => e.target.style.border = '2px solid #2e4354'}
            onBlur={(e) => e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)'}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
            Fecha Fin
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onEndDateChange(e.target.value)}
            className="w-full rounded-lg px-3 py-2 transition-all"
            style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
            onFocus={(e) => e.target.style.border = '2px solid #2e4354'}
            onBlur={(e) => e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)'}
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={onGenerateReport}
            disabled={loading || (isDayClosed === true && startDate === endDate)}
            className="w-full text-white px-6 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg disabled:cursor-not-allowed"
            style={{ backgroundColor: (isDayClosed === true && startDate === endDate) || loading ? '#2e4354' : '#2e4354', opacity: loading || (isDayClosed === true && startDate === endDate) ? 0.7 : 1 }}
          >
            {loading ? 'Generando...' : 'Generar Reporte'}
          </button>
        </div>

        {(isDayClosed === true && startDate === endDate) && (
          <div className="flex items-end">
            <button
              onClick={onViewClosedDay}
              disabled={loading}
              className="w-full text-white px-6 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg disabled:opacity-50"
              style={{ backgroundColor: '#ffe98e', color: '#000000' }}
            >
              📦 Ver Caja Cerrada
            </button>
          </div>
        )}
      </div>

      {(report || detailedReport) && (
        <div className="flex gap-3">
          <button
            onClick={onPrintReport}
            className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg hover:scale-105"
            style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
          >
            🖨️ Imprimir Reporte
          </button>
          <button
            onClick={onDownloadCsv}
            className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg hover:scale-105"
            style={{ backgroundColor: '#ffe98e', color: '#000000' }}
          >
            📥 Descargar CSV
          </button>
        </div>
      )}
    </div>
  );
};

