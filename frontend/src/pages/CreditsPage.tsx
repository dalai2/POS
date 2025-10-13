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

interface CreditSale {
  id: number;
  customer_name: string | null;
  customer_phone: string | null;
  total: number;
  amount_paid: number;
  balance: number;
  credit_status: string;
  vendedor_id: number | null;
  created_at: string;
  payments: CreditPayment[];
}

export default function CreditsPage() {
  const [credits, setCredits] = useState<CreditSale[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedCredit, setSelectedCredit] = useState<CreditSale | null>(null);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_method: 'efectivo',
    notes: '',
  });

  useEffect(() => {
    loadCredits();
  }, [statusFilter]);

  const loadCredits = async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const response = await api.get(`/credits/sales${params}`);
      setCredits(response.data);
    } catch (error) {
      console.error('Error loading credits:', error);
      alert('Error al cargar créditos');
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
      console.error('Error registering payment:', error);
      alert(error.response?.data?.detail || 'Error al registrar pago');
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
          <h1 className="text-3xl font-bold text-gray-800">Gestión de Créditos</h1>
          
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2"
            >
              <option value="">Todos los estados</option>
              <option value="pendiente">Pendientes</option>
              <option value="pagado">Pagados</option>
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
                <p><strong>Pagado:</strong> ${selectedCredit.amount_paid.toFixed(2)}</p>
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Cliente
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Teléfono
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Total
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Pagado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Saldo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Fecha
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {credits.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                      No hay créditos registrados
                    </td>
                  </tr>
                ) : (
                  credits.map((credit) => (
                    <tr key={credit.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-gray-900">
                          {credit.customer_name || 'Sin nombre'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {credit.customer_phone || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        ${credit.total.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                        ${credit.amount_paid.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">
                        ${credit.balance.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            credit.credit_status === 'pagado'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {credit.credit_status === 'pagado' ? 'Pagado' : 'Pendiente'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(credit.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {credit.credit_status === 'pendiente' && (
                          <button
                            onClick={() => openPaymentForm(credit)}
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            Registrar Abono
                          </button>
                        )}
                        <button
                          className="text-gray-600 hover:text-gray-900"
                          onClick={() => {
                            alert(`Pagos registrados: ${credit.payments.length}\n\n${credit.payments.map(
                              p => `${new Date(p.created_at).toLocaleDateString()}: $${p.amount.toFixed(2)} (${p.payment_method})`
                            ).join('\n')}`);
                          }}
                        >
                          Ver Historial ({credit.payments.length})
                        </button>
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
            <h3 className="text-sm font-medium text-gray-500">Total Créditos</h3>
            <p className="text-2xl font-bold text-gray-900">
              ${credits.reduce((sum, c) => sum + c.total, 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Total Pagado</h3>
            <p className="text-2xl font-bold text-green-600">
              ${credits.reduce((sum, c) => sum + c.amount_paid, 0).toFixed(2)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Saldo Pendiente</h3>
            <p className="text-2xl font-bold text-red-600">
              ${credits.reduce((sum, c) => sum + c.balance, 0).toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}

