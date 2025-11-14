import { useCallback, useEffect, useState } from 'react';
import { api } from '../utils/api';
import {
  CorteDeCajaReport,
  DetailedCorteCajaReport,
} from '../types/reports';
import { buildDetailedReportCsv } from '../utils/reportExport';

export interface UseCorteCajaReportOptions {
  initialStartDate?: string;
  initialEndDate?: string;
  initialReportType?: 'summary' | 'detailed';
}

export interface UseCorteCajaReport {
  startDate: string;
  endDate: string;
  reportType: 'summary' | 'detailed';
  loading: boolean;
  report: CorteDeCajaReport | null;
  detailedReport: DetailedCorteCajaReport | null;
  closeMsg: string | null;
  closing: boolean;
  isDayClosed: boolean | null;
  usingClosure: boolean;
  setStartDate: (value: string) => void;
  setEndDate: (value: string) => void;
  setReportType: (value: 'summary' | 'detailed') => void;
  generateReport: () => Promise<void>;
  downloadCsv: () => void;
  closeDay: () => Promise<void>;
  viewClosedDay: () => Promise<void>;
  resetCloseMessage: () => void;
  setDetailedReport: (report: DetailedCorteCajaReport | null) => void;
  setReport: (report: CorteDeCajaReport | null) => void;
}

const todayIso = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const useCorteCajaReport = (
  options: UseCorteCajaReportOptions = {},
): UseCorteCajaReport => {
  const {
    initialStartDate = todayIso(),
    initialEndDate = todayIso(),
    initialReportType = 'detailed',
  } = options;

  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<CorteDeCajaReport | null>(null);
  const [detailedReport, setDetailedReport] = useState<DetailedCorteCajaReport | null>(null);
  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
  const [reportType, setReportType] = useState<'summary' | 'detailed'>(initialReportType);
  const [closing, setClosing] = useState(false);
  const [closeMsg, setCloseMsg] = useState<string | null>(null);
  const [isDayClosed, setIsDayClosed] = useState<boolean | null>(null);
  const [usingClosure, setUsingClosure] = useState(false);

  const resetCloseMessage = useCallback(() => setCloseMsg(null), []);

  const generateReport = useCallback(async () => {
    resetCloseMessage();
    setLoading(true);
    try {
      setUsingClosure(false);
      if (reportType === 'summary') {
        const response = await api.get('/reports/corte-de-caja', {
          params: { start_date: startDate, end_date: endDate },
        });
        setReport(response.data);
        setDetailedReport(null);
        return;
      }

      setReport(null);
      if (startDate === endDate) {
        try {
          const closureRes = await api.get('/reports/closure', { params: { for_date: startDate } });
          setDetailedReport(closureRes.data);
          setUsingClosure(true);
          return;
        } catch {
          // ignore 404 and continue with calculation
        }
      }

      const response = await api.get('/reports/detailed-corte-caja', {
        params: { start_date: startDate, end_date: endDate },
      });
      setDetailedReport(response.data);
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Error al generar reporte');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, reportType, resetCloseMessage]);

  const downloadCsv = useCallback(() => {
    if (!detailedReport) return;
    const csvContent = buildDetailedReportCsv(detailedReport, startDate, endDate);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `corte_caja_${startDate}_${endDate}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [detailedReport, startDate, endDate]);

  const closeDay = useCallback(async () => {
    resetCloseMessage();
    setClosing(true);
    try {
      await api.post('/reports/close-day', null, { params: { for_date: startDate } });
      setCloseMsg('✅ Cierre guardado correctamente');
      alert('Cierre de caja realizado correctamente');
      setIsDayClosed(true);
      setUsingClosure(true);
      try {
        const closureRes = await api.get('/reports/closure', { params: { for_date: startDate } });
        setDetailedReport(closureRes.data);
      } catch {
        /* ignore */
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      const msg = detail || 'Error al cerrar caja';
      setCloseMsg(typeof msg === 'string' ? msg : 'Error al cerrar caja');
      alert(typeof msg === 'string' ? msg : 'Error al cerrar caja');
    } finally {
      setClosing(false);
    }
  }, [startDate, resetCloseMessage]);

  const viewClosedDay = useCallback(async () => {
    setLoading(true);
    resetCloseMessage();
    try {
      const res = await api.get('/reports/closure', { params: { for_date: startDate } });
      setDetailedReport(res.data);
      setUsingClosure(true);
    } catch {
      alert('No hay cierre para este día');
    } finally {
      setLoading(false);
    }
  }, [startDate, resetCloseMessage]);

  useEffect(() => {
    resetCloseMessage();
  }, [startDate, endDate, reportType, resetCloseMessage]);

  useEffect(() => {
    let cancelled = false;
    setIsDayClosed(null);
    (async () => {
      try {
        await api.get('/reports/closure', { params: { for_date: startDate } });
        if (!cancelled) setIsDayClosed(true);
      } catch (error: any) {
        const status = error?.response?.status;
        if (!cancelled) setIsDayClosed(status === 404 ? false : false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [startDate]);

  return {
    startDate,
    endDate,
    reportType,
    loading,
    report,
    detailedReport,
    closeMsg,
    closing,
    isDayClosed,
    usingClosure,
    setStartDate,
    setEndDate,
    setReportType,
    generateReport,
    downloadCsv,
    closeDay,
    viewClosedDay,
    resetCloseMessage,
    setDetailedReport,
    setReport,
  };
};

