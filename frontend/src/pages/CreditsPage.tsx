import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { api } from '../utils/api';

interface CreditPayment {
  id: number;
  amount: number;
  payment_method: string;
  user_id: number;
  notes: string | null;
  created_at: string;
}

interface StatusHistoryEntry {
  id: number;
  old_status: string | null;
  new_status: string;
  user_email: string;
  notes: string | null;
  created_at: string;
}

interface CreditSale {
  id: number;
  customer_name: string | null;
  customer_phone: string | null;
  total: number;
  amount_paid: number;
  balance: number;
  credit_status: string;
  vendedor_id: number | null;
  vendedor_email: string | null;
  created_at: string;
  payments: CreditPayment[];
}

export default function CreditsPage() {
  const [credits, setCredits] = useState<CreditSale[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchFilter, setSearchFilter] = useState<string>('');
  const [selectedCredit, setSelectedCredit] = useState<CreditSale | null>(null);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [showHistorialModal, setShowHistorialModal] = useState(false);
  const [creditHistorial, setCreditHistorial] = useState<CreditSale | null>(null);
  const [statusHistory, setStatusHistory] = useState<StatusHistoryEntry[]>([]);
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_method: 'efectivo',
    notes: '',
  });
  const userRole = localStorage.getItem('role') || '';

  useEffect(() => {
    loadCredits();
  }, [statusFilter]);

  const loadCredits = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const response = await api.get(`/credits/sales${params}`);
      setCredits(response.data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        alert('No tienes permisos para ver los abonos. Solo los administradores pueden acceder a esta función.');
      } else {
        alert('Error al cargar abonos');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCredit) return;

    try {
      await api.post('/credits/payments', {
        sale_id: selectedCredit.id,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        notes: paymentData.notes || null,
      });

      alert('Pago registrado exitosamente');
      setShowPaymentForm(false);
      setSelectedCredit(null);
      setPaymentData({ amount: '', payment_method: 'efectivo', notes: '' });
      loadCredits();
    } catch (error: any) {
      if (error.response?.status === 403) {
        alert('No tienes permisos para registrar pagos. Solo los administradores pueden realizar esta acción.');
      } else {
        alert(error.response?.data?.detail || 'Error al registrar pago');
      }
    }
  };

  const openPaymentForm = (credit: CreditSale) => {
    setSelectedCredit(credit);
    setPaymentData({
      amount: credit.balance.toString(),
      payment_method: 'efectivo',
      notes: '',
    });
    setShowPaymentForm(true);
  };

  const abrirHistorial = async (credit: CreditSale) => {
    setCreditHistorial(credit);
    
    // Cargar historial de estados
    try {
      const response = await api.get(`/status-history/sale/${credit.id}`);
      setStatusHistory(response.data);
    } catch (error) {
      console.error('Error loading status history:', error);
      setStatusHistory([]);
    }
    
    setShowHistorialModal(true);
  };

  const marcarComoEntregado = async (saleId: number) => {
    if (!confirm('¿Marcar esta venta como entregada?')) return;
    
    try {
      await api.patch(`/credits/sales/${saleId}/entregado`);
      alert('Venta marcada como entregada exitosamente');
      loadCredits();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al marcar como entregado');
    }
  };

  const marcarComoCancelado = async (saleId: number) => {
    if (!confirm('¿Cancelar esta venta? Esta acción no se puede deshacer.')) return;
    
    try {
      await api.patch(`/credits/sales/${saleId}/cancelado`);
      alert('Venta cancelada exitosamente');
      loadCredits();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al cancelar venta');
    }
  };

  const cambiarEstado = async (saleId: number, nuevoEstado: string) => {
    try {
      // Usar endpoints específicos para cambios de estado
      if (nuevoEstado === 'entregado') {
        await api.patch(`/credits/sales/${saleId}/entregado`);
      } else if (nuevoEstado === 'cancelado') {
        if (!confirm('¿Cancelar esta venta?')) return;
        await api.patch(`/credits/sales/${saleId}/cancelado`);
      } else {
        // Para otros estados, usar endpoint genérico si existe
        await api.patch(`/credits/sales/${saleId}/status`, { status: nuevoEstado });
      }
      loadCredits();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al cambiar estado');
    }
  };

  // Filter credits by search term
  const filteredCredits = credits.filter(credit => {
    if (!searchFilter.trim()) return true;
    const searchLower = searchFilter.toLowerCase();
    const customerName = (credit.customer_name || '').toLowerCase();
    const customerPhone = (credit.customer_phone || '').toLowerCase();
    return customerName.includes(searchLower) || customerPhone.includes(searchLower);
  });

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Cargando...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Gestión de apartados</h1>
          
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Buscar por nombre o teléfono..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 min-w-[300px]"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2"
            >
              <option value="">Todos los estados</option>
              <option value="pendiente">Pendiente</option>
              <option value="pagado">Pagado</option>
              <option value="entregado">Entregado</option>
              <option value="vencido">Vencido</option>
              <option value="cancelado">Cancelado</option>
            </select>
          </div>
        </div>

        {/* Payment Form Modal */}
        {showPaymentForm && selectedCredit && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
              <h2 className="text-xl font-semibold mb-4">Registrar Abono</h2>
              
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p><strong>Cliente:</strong> {selectedCredit.customer_name || 'Sin nombre'}</p>
                <p><strong>Total:</strong> ${selectedCredit.total.toFixed(2)}</p>
                <p><strong>Abonado:</strong> ${selectedCredit.amount_paid.toFixed(2)}</p>
                <p className="text-lg font-bold text-red-600">
                  <strong>Saldo:</strong> ${selectedCredit.balance.toFixed(2)}
                </p>
              </div>

              <form onSubmit={handleRegisterPayment} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Monto del Abono
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={paymentData.amount}
                    onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    max={selectedCredit.balance}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Método de Pago
                  </label>
                  <select
                    value={paymentData.payment_method}
                    onChange={(e) => setPaymentData({ ...paymentData, payment_method: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="efectivo">Efectivo</option>
                    <option value="tarjeta">Tarjeta</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notas (opcional)
                  </label>
                  <textarea
                    value={paymentData.notes}
                    onChange={(e) => setPaymentData({ ...paymentData, notes: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    rows={3}
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="flex-1 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
                  >
                    Registrar Abono
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowPaymentForm(false);
                      setSelectedCredit(null);
                    }}
                    className="flex-1 bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Credits List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Folio
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Cliente
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Total
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Pagado
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Saldo
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Estado
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Vendedor
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Fecha
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {credits.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-3 py-4 text-center text-gray-500">
                      No hay abonos registrados
                    </td>
                  </tr>
                ) : filteredCredits.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-3 py-4 text-center text-gray-500">
                      No se encontraron resultados para tu búsqueda
                    </td>
                  </tr>
                ) : (
                  filteredCredits.map((credit) => (
                    <tr key={credit.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-600">
                        #{String(credit.id).padStart(4, '0')}
                      </td>
                      <td className="px-3 py-2 text-sm">
                        <div className="font-medium text-gray-900">
                          {credit.customer_name || 'Sin nombre'}
                        </div>
                        {credit.customer_phone && (
                          <div className="text-xs text-gray-500">{credit.customer_phone}</div>
                        )}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm">
                        ${credit.total.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-green-600">
                        ${credit.amount_paid.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm font-bold text-red-600">
                        ${credit.balance.toFixed(2)}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap">
                        {(userRole === 'admin' || userRole === 'owner') ? (
                          <select
                            value={credit.credit_status}
                            onChange={(e) => cambiarEstado(credit.id, e.target.value)}
                            className={`px-2 py-1 text-xs font-semibold rounded-full border-0 ${
                              credit.credit_status === 'pagado'
                                ? 'bg-green-100 text-green-800'
                                : credit.credit_status === 'entregado'
                                ? 'bg-blue-100 text-blue-800'
                                : credit.credit_status === 'vencido'
                                ? 'bg-red-100 text-red-800'
                                : credit.credit_status === 'cancelado'
                                ? 'bg-gray-100 text-gray-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            <option value="pendiente">Pendiente</option>
                            <option value="pagado">Pagado</option>
                            <option value="entregado">Entregado</option>
                            <option value="vencido">Vencido</option>
                            <option value="cancelado">Cancelado</option>
                          </select>
                        ) : (
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              credit.credit_status === 'pagado'
                                ? 'bg-green-100 text-green-800'
                                : credit.credit_status === 'entregado'
                                ? 'bg-blue-100 text-blue-800'
                                : credit.credit_status === 'vencido'
                                ? 'bg-red-100 text-red-800'
                                : credit.credit_status === 'cancelado'
                                ? 'bg-gray-100 text-gray-800'
                                : 'bg-yellow-100 text-yellow-800'
                            }`}
                          >
                            {credit.credit_status === 'pagado'
                              ? 'Pagado'
                              : credit.credit_status === 'entregado'
                              ? 'Entregado'
                              : credit.credit_status === 'vencido'
                              ? 'Vencido'
                              : credit.credit_status === 'cancelado'
                              ? 'Cancelado'
                              : 'Pendiente'}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-500">
                        <div className="max-w-[120px] truncate" title={credit.vendedor_email || '-'}>
                          {credit.vendedor_email || '-'}
                        </div>
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-xs text-gray-500">
                        {new Date(credit.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: '2-digit' })}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm">
                        <div className="flex flex-col gap-1">
                          {credit.credit_status === 'pendiente' && (
                            <>
                              <button
                                onClick={() => openPaymentForm(credit)}
                                className="text-blue-600 hover:text-blue-900 text-xs"
                              >
                                💰 Abonar
                              </button>
                              <button
                                onClick={() => marcarComoCancelado(credit.id)}
                                className="text-red-600 hover:text-red-900 text-xs"
                              >
                                ✕ Cancelar
                              </button>
                            </>
                          )}
                          {credit.credit_status === 'pagado' && (
                            <button
                              onClick={() => marcarComoEntregado(credit.id)}
                              className="text-green-600 hover:text-green-900 text-xs"
                            >
                              ✓ Marcar entregado
                            </button>
                          )}
                          <button
                            className="text-gray-600 hover:text-gray-900 text-xs"
                            onClick={() => abrirHistorial(credit)}
                          >
                            📋 Historial ({credit.payments.length})
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Summary */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">
              {searchFilter ? 'Total Abonos (Filtrados)' : 'Total Abonos'}
            </h3>
            <p className="text-2xl font-bold text-gray-900">
              ${filteredCredits.reduce((sum, c) => sum + c.total, 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">
              {searchFilter ? 'Total Pagado (Filtrado)' : 'Total Pagado'}
            </h3>
            <p className="text-2xl font-bold text-green-600">
              ${filteredCredits.reduce((sum, c) => sum + c.amount_paid, 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">
              {searchFilter ? 'Saldo Pendiente (Filtrado)' : 'Saldo Pendiente'}
            </h3>
            <p className="text-2xl font-bold text-red-600">
              ${filteredCredits.reduce((sum, c) => sum + c.balance, 0).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Modal de Historial de Pagos */}
        {showHistorialModal && creditHistorial && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Historial de Abonos</h3>
                <button
                  onClick={() => setShowHistorialModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="mb-4 space-y-2 bg-gray-50 p-3 rounded-lg">
                <p className="text-gray-700">
                  <strong>Cliente:</strong> {creditHistorial.customer_name || 'Sin nombre'}
                </p>
                <p className="text-gray-700">
                  <strong>Total:</strong> ${creditHistorial.total.toFixed(2)}
                </p>
                <p className="text-gray-700">
                  <strong>Total abonos:</strong> ${creditHistorial.amount_paid.toFixed(2)}
                </p>
                <p className="text-gray-700 font-bold">
                  <strong>Saldo pendiente:</strong> ${creditHistorial.balance.toFixed(2)}
                </p>
              </div>
              
              {creditHistorial.payments.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No hay abonos registrados para esta venta
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Monto</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Método</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Notas</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {creditHistorial.payments.map((pago) => (
                        <tr key={pago.id}>
                          <td className="px-4 py-3 text-sm">
                            {new Date(pago.created_at).toLocaleString('es-MX', { timeZone: 'America/Mexico_City' })}
                          </td>
                          <td className="px-4 py-3 text-sm font-medium text-green-600">
                            ${pago.amount.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-sm capitalize">
                            {pago.payment_method}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {pago.notes || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              
              {/* Historial de Estados */}
              {statusHistory.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">📊 Historial de Estados</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Usuario</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cambio</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Notas</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {statusHistory.map((history) => (
                          <tr key={history.id}>
                            <td className="px-4 py-3 text-sm">
                              {new Date(history.created_at).toLocaleString('es-MX', { timeZone: 'America/Mexico_City' })}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-700">
                              {history.user_email}
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <span className="text-gray-500">{history.old_status || 'Nuevo'}</span>
                              <span className="mx-2">→</span>
                              <span className="font-semibold text-blue-600">{history.new_status}</span>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {history.notes || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              
              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowHistorialModal(false)}
                  className="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

