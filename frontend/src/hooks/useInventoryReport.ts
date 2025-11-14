import { useCallback, useEffect, useState } from 'react';
import { api } from '../utils/api';
import { InventoryReport, StockGrouped, StockApartado } from '../types/inventory';

export interface UseInventoryReportOptions {
  initialStartDate?: string;
  initialEndDate?: string;
}

export interface UseInventoryReport {
  startDate: string;
  endDate: string;
  loading: boolean;
  report: InventoryReport | null;
  stockGrouped: StockGrouped[] | null;
  stockPedidos: StockGrouped[] | null;
  stockEliminado: StockGrouped[] | null;
  stockDevuelto: StockGrouped[] | null;
  stockApartado: StockApartado[] | null;
  closeMsg: string | null;
  closing: boolean;
  isDayClosed: boolean | null;
  usingClosure: boolean;
  setStartDate: (value: string) => void;
  setEndDate: (value: string) => void;
  generateReport: () => Promise<void>;
  closeDay: () => Promise<void>;
  viewClosedDay: () => Promise<void>;
  removePieces: (productId: number, quantity: number, notes: string) => Promise<void>;
  getStockGrouped: (forDate?: string) => Promise<void>;
  getStockPedidos: () => Promise<void>;
  getStockEliminado: () => Promise<void>;
  getStockDevuelto: () => Promise<void>;
  getStockApartado: () => Promise<void>;
  resetCloseMessage: () => void;
  setReport: (report: InventoryReport | null) => void;
}

const todayIso = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const useInventoryReport = (
  options: UseInventoryReportOptions = {},
): UseInventoryReport => {
  const {
    initialStartDate = todayIso(),
    initialEndDate = todayIso(),
  } = options;

  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<InventoryReport | null>(null);
  const [stockGrouped, setStockGrouped] = useState<StockGrouped[] | null>(null);
  const [stockPedidos, setStockPedidos] = useState<StockGrouped[] | null>(null);
  const [stockEliminado, setStockEliminado] = useState<StockGrouped[] | null>(null);
  const [stockDevuelto, setStockDevuelto] = useState<StockGrouped[] | null>(null);
  const [stockApartado, setStockApartado] = useState<StockApartado[] | null>(null);
  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
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
      if (startDate === endDate) {
        try {
          const closureRes = await api.get('/inventory/closure', { params: { for_date: startDate } });
          setReport(closureRes.data.report_data || closureRes.data);
          setUsingClosure(true);
          setIsDayClosed(true);
          return;
        } catch {
          // ignore 404 and continue with calculation
          setIsDayClosed(false);
        }
      }

      const response = await api.get('/inventory/report', {
        params: { start_date: startDate, end_date: endDate },
      });
      setReport(response.data);
    } catch (error) {
      console.error('Error generating inventory report:', error);
      alert('Error al generar reporte de inventario');
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, resetCloseMessage]);

  const closeDay = useCallback(async () => {
    setClosing(true);
    setCloseMsg(null);
    try {
      const response = await api.post('/inventory/close-day', null, {
        params: { for_date: startDate },
      });
      setCloseMsg(response.data.message || 'Cierre de inventario guardado');
      setIsDayClosed(true);
      // Reload report to show closure
      await generateReport();
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Error al cerrar inventario';
      setCloseMsg(message);
      console.error('Error closing inventory day:', error);
    } finally {
      setClosing(false);
    }
  }, [startDate, generateReport]);

  const viewClosedDay = useCallback(async () => {
    resetCloseMessage();
    setLoading(true);
    try {
      const response = await api.get('/inventory/closure', {
        params: { for_date: startDate },
      });
      setReport(response.data.report_data || response.data);
      setUsingClosure(true);
      setIsDayClosed(true);
    } catch (error: any) {
      if (error?.response?.status === 404) {
        setCloseMsg('No hay cierre de inventario para este día');
        setIsDayClosed(false);
      } else {
        console.error('Error viewing closed day:', error);
        alert('Error al ver cierre de inventario');
      }
    } finally {
      setLoading(false);
    }
  }, [startDate, resetCloseMessage]);

  const removePieces = useCallback(async (productId: number, quantity: number, notes: string) => {
    try {
      await api.post('/inventory/remove-pieces', null, {
        params: { product_id: productId, quantity, notes },
      });
      // Reload report after removing pieces
      await generateReport();
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Error al sacar piezas';
      alert(message);
      console.error('Error removing pieces:', error);
    }
  }, [generateReport]);

  const getStockGrouped = useCallback(async (forDate?: string) => {
    setLoading(true);
    try {
      const params: any = {};
      if (forDate) {
        params.for_date = forDate;
      }
      const response = await api.get('/inventory/stock-grouped', { params });
      setStockGrouped(response.data);
    } catch (error) {
      console.error('Error getting stock grouped:', error);
      alert('Error al obtener stock agrupado');
    } finally {
      setLoading(false);
    }
  }, []);

  const getStockPedidos = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/inventory/stock-pedidos');
      setStockPedidos(response.data);
    } catch (error) {
      console.error('Error getting stock pedidos:', error);
      alert('Error al obtener stock de pedidos');
    } finally {
      setLoading(false);
    }
  }, []);

  const getStockEliminado = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/inventory/stock-eliminado');
      setStockEliminado(response.data);
    } catch (error) {
      console.error('Error getting stock eliminado:', error);
      alert('Error al obtener stock eliminado');
    } finally {
      setLoading(false);
    }
  }, []);

  const getStockDevuelto = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/inventory/stock-devuelto');
      setStockDevuelto(response.data);
    } catch (error) {
      console.error('Error getting stock devuelto:', error);
      alert('Error al obtener stock devuelto');
    } finally {
      setLoading(false);
    }
  }, []);

  const getStockApartado = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/inventory/stock-apartado');
      setStockApartado(response.data);
    } catch (error) {
      console.error('Error getting stock apartado:', error);
      alert('Error al obtener stock de apartado');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    startDate,
    endDate,
    loading,
    report,
    stockGrouped,
    stockPedidos,
    stockEliminado,
    stockDevuelto,
    stockApartado,
    closeMsg,
    closing,
    isDayClosed,
    usingClosure,
    setStartDate,
    setEndDate,
    generateReport,
    closeDay,
    viewClosedDay,
    removePieces,
    getStockGrouped,
    getStockPedidos,
    getStockEliminado,
    getStockDevuelto,
    getStockApartado,
    resetCloseMessage,
    setReport,
  };
};

