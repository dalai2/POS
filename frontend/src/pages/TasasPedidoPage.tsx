import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { api } from '../utils/api';

interface TasaMetalPedido {
  id: number;
  metal_type: string;
  rate_per_gram: number;
  created_at: string;
  updated_at: string;
}

export default function TasasPedidoPage() {
  const [rates, setRates] = useState<TasaMetalPedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingRate, setEditingRate] = useState<TasaMetalPedido | null>(null);
  const [formData, setFormData] = useState({
    metal_type: '',
    rate_per_gram: '',
  });

  useEffect(() => {
    loadRates();
  }, []);

  const loadRates = async () => {
    try {
      const response = await api.get('/tasas-pedido/');
      setRates(response.data);
    } catch (error: any) {
      alert('Error al cargar tasas de metal para pedidos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingRate) {
        // Update existing rate
        await api.put(`/tasas-pedido/${editingRate.id}`, {
          metal_type: formData.metal_type,
          rate_per_gram: parseFloat(formData.rate_per_gram),
        });
        alert('Tasa de pedido actualizada exitosamente.');
      } else {
        // Create new rate
        await api.post('/tasas-pedido/', {
          metal_type: formData.metal_type,
          rate_per_gram: parseFloat(formData.rate_per_gram),
        });
        alert('Tasa de pedido creada exitosamente');
      }
      loadRates();
      setShowForm(false);
      setEditingRate(null);
      setFormData({ metal_type: '', rate_per_gram: '' });
    } catch (error: any) {
      if (error.response?.status === 403) {
        const action = editingRate ? 'editar' : 'crear';
        const detail = error.response?.data?.detail || 'Unknown error';
        alert(`No tienes permisos para ${action} tasas de metal de pedidos. Solo los administradores pueden realizar esta acción.\n\nDetalle: ${detail}`);
      } else {
      alert(error.response?.data?.detail || 'Error al guardar tasa');
      }
    }
  };

  const handleEdit = (rate: TasaMetalPedido) => {
    setEditingRate(rate);
    setFormData({
      metal_type: rate.metal_type,
      rate_per_gram: rate.rate_per_gram.toString(),
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Está seguro de eliminar esta tasa de pedido?')) return;
    
    try {
      await api.delete(`/tasas-pedido/${id}`);
      loadRates();
      alert('Tasa eliminada exitosamente');
    } catch (error: any) {
      if (error.response?.status === 403) {
        alert('No tienes permisos para eliminar tasas de metal de pedidos. Solo los administradores pueden realizar esta acción.');
      } else {
      alert('Error al eliminar tasa');
    }
    }
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
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Tasas de Metal - Pedidos</h1>
            <p className="text-sm text-gray-600 mt-1">
              Tasas específicas para productos de pedidos (órdenes personalizadas)
            </p>
          </div>
          <button
            onClick={() => {
              setShowForm(true);
              setEditingRate(null);
              setFormData({ metal_type: '', rate_per_gram: '' });
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + Nueva Tasa
          </button>
        </div>

        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              {editingRate ? 'Actualizar Tasa' : 'Nueva Tasa'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Metal
                </label>
                <input
                  type="text"
                  value={formData.metal_type}
                  onChange={(e) => setFormData({ ...formData, metal_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Ej: 14k, Plata Gold, Oro Italiano..."
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Ingrese el tipo de metal (ej: 14k, Plata Gold, Oro Italiano)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tasa por Gramo ($) - Para Pedidos
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.rate_per_gram}
                  onChange={(e) => setFormData({ ...formData, rate_per_gram: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Esta tasa se usa para calcular el costo de productos de pedidos personalizados
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                >
                  {editingRate ? 'Actualizar' : 'Crear'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingRate(null);
                    setFormData({ metal_type: '', rate_per_gram: '' });
                  }}
                  className="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo de Metal
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tasa por Gramo (Pedidos)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Última Actualización
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rates.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                    No hay tasas de pedidos registradas
                  </td>
                </tr>
              ) : (
                rates.map((rate) => (
                  <tr key={rate.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium text-gray-900">
                        {rate.metal_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-purple-600 font-semibold">
                        ${rate.rate_per_gram.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(rate.updated_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleEdit(rate)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleDelete(rate.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">ℹ️ Información</h3>
          <p className="text-sm text-blue-800">
            Las tasas de metal para pedidos se utilizan para calcular automáticamente el costo 
            de productos personalizados basándose en el peso en gramos y el quilataje del metal.
            <br />
            <strong>Fórmula:</strong> Costo = Peso (gramos) × Tasa por Gramo
          </p>
        </div>
      </div>
    </Layout>
  );
}








