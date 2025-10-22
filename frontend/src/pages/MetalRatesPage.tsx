import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { api } from '../utils/api';

interface MetalRate {
  id: number;
  metal_type: string;
  rate_per_gram: number;
  created_at: string;
  updated_at: string;
}

// Metal types are now free text input

export default function MetalRatesPage() {
  const [rates, setRates] = useState<MetalRate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingRate, setEditingRate] = useState<MetalRate | null>(null);
  const [formData, setFormData] = useState({
    metal_type: '',
    rate_per_gram: '',
  });

  useEffect(() => {
    loadRates();
  }, []);

  const loadRates = async () => {
    try {
      const response = await api.get('/metal-rates');
      setRates(response.data);
    } catch (error: any) {
      console.error('Error loading metal rates:', error);
      alert('Error al cargar tasas de metal');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingRate) {
        // Update existing rate
        await api.put(`/metal-rates/${editingRate.id}?recalculate_prices=true`, {
          rate_per_gram: parseFloat(formData.rate_per_gram),
        });
        alert('Tasa actualizada. Los precios de productos se han recalculado automáticamente.');
      } else {
        // Create new rate
        await api.post('/metal-rates', {
          metal_type: formData.metal_type,
          rate_per_gram: parseFloat(formData.rate_per_gram),
        });
        alert('Tasa creada exitosamente');
      }
      loadRates();
      setShowForm(false);
      setEditingRate(null);
      setFormData({ metal_type: '', rate_per_gram: '' });
    } catch (error: any) {
      console.error('Error saving metal rate:', error);
      if (error.response?.status === 403) {
        const action = editingRate ? 'editar' : 'crear';
        alert(`No tienes permisos para ${action} tasas de metal. Solo los administradores pueden realizar esta acción.`);
      } else {
        alert(error.response?.data?.detail || 'Error al guardar tasa');
      }
    }
  };

  const handleEdit = (rate: MetalRate) => {
    setEditingRate(rate);
    setFormData({
      metal_type: rate.metal_type,
      rate_per_gram: rate.rate_per_gram.toString(),
    });
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('¿Está seguro de eliminar esta tasa?')) return;

    try {
      await api.delete(`/metal-rates/${id}`);
      loadRates();
      alert('Tasa eliminada exitosamente');
    } catch (error: any) {
      console.error('Error deleting metal rate:', error);
      if (error.response?.status === 403) {
        alert('No tienes permisos para eliminar tasas de metal. Solo los administradores pueden realizar esta acción.');
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
          <h1 className="text-3xl font-bold text-gray-800">Tasas de Metal</h1>
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
                  disabled={!!editingRate}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Ingrese el tipo de metal (ej: 14k, Plata Gold, Oro Italiano)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tasa por Gramo ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.rate_per_gram}
                  onChange={(e) => setFormData({ ...formData, rate_per_gram: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
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

              {editingRate && (
                <p className="text-sm text-amber-600">
                  ⚠️ Al actualizar esta tasa, todos los productos con quilataje "{getMetalTypeLabel(editingRate.metal_type)}" 
                  sin precio manual serán recalculados automáticamente.
                </p>
              )}
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
                  Tasa por Gramo
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
                    No hay tasas registradas
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
                      <span className="text-green-600 font-semibold">
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
      </div>
    </Layout>
  );
}

