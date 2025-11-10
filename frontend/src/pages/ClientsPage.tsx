import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { api } from '../utils/api';

interface Customer {
  nombre: string;
  telefono: string;
  total_gastado: number;
  fecha_registro: string;
  num_ventas_contado: number;
  num_apartados: number;
  num_pedidos: number;
}

export default function ClientsPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [orderBy, setOrderBy] = useState<'nombre' | 'telefono' | 'total_gastado' | 'fecha_registro'>('nombre');
  const [orderDir, setOrderDir] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    fetchCustomers();
  }, [orderBy, orderDir]);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const response = await api.get('/customers/', {
        params: {
          search: searchTerm || undefined,
          order_by: orderBy,
          order_dir: orderDir,
        },
      });
      setCustomers(response.data);
    } catch (error) {
      console.error('Error fetching customers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchCustomers();
  };

  const handleSort = (field: 'nombre' | 'telefono' | 'total_gastado' | 'fecha_registro') => {
    if (orderBy === field) {
      setOrderDir(orderDir === 'asc' ? 'desc' : 'asc');
    } else {
      setOrderBy(field);
      setOrderDir('asc');
    }
  };

  const getSortIcon = (field: string) => {
    if (orderBy !== field) return '↕️';
    return orderDir === 'asc' ? '↑' : '↓';
  };

  const exportToExcel = () => {
    const headers = ['Nombre', 'Teléfono', 'Total Gastado', 'Fecha de Registro', 'Ventas Contado', 'Apartados', 'Pedidos'];
    const rows = customers.map(c => [
      c.nombre,
      c.telefono,
      `$${c.total_gastado.toFixed(2)}`,
      new Date(c.fecha_registro).toLocaleDateString('es-ES'),
      c.num_ventas_contado,
      c.num_apartados,
      c.num_pedidos
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `clientes_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto font-['Poppins',sans-serif]">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
            <span className="text-4xl">👥</span>
            Clientes
          </h1>
          <button
            onClick={exportToExcel}
            className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-green-600 text-white rounded-lg font-medium hover:from-emerald-700 hover:to-green-700 transition-all shadow-md flex items-center gap-2"
          >
            <span>📊</span>
            Exportar a Excel
          </button>
        </div>

        {/* Search and Stats */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Buscar por nombre o teléfono..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                onClick={handleSearch}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                🔍 Buscar
              </button>
            </div>
            
            <div className="flex gap-2 items-center justify-end">
              <span className="text-sm text-gray-600 font-medium">
                Total de clientes: <span className="text-2xl font-bold text-blue-600">{customers.length}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Cargando clientes...</p>
            </div>
          ) : customers.length === 0 ? (
            <div className="p-12 text-center">
              <span className="text-6xl mb-4 block">📭</span>
              <p className="text-xl text-gray-600">No se encontraron clientes</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
                  <tr>
                    <th
                      onClick={() => handleSort('nombre')}
                      className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span>Cliente</span>
                        <span className="text-sm">{getSortIcon('nombre')}</span>
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('telefono')}
                      className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <span>📱 Teléfono</span>
                        <span className="text-sm">{getSortIcon('telefono')}</span>
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('total_gastado')}
                      className="px-6 py-4 text-right text-xs font-bold uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                    >
                      <div className="flex items-center justify-end gap-2">
                        <span>💰 Total Gastado</span>
                        <span className="text-sm">{getSortIcon('total_gastado')}</span>
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('fecha_registro')}
                      className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider cursor-pointer hover:bg-blue-700 transition-colors"
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span>📅 Fecha de Registro</span>
                        <span className="text-sm">{getSortIcon('fecha_registro')}</span>
                      </div>
                    </th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider">
                      🛒 V. Contado
                    </th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider">
                      💳 Apartados
                    </th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider">
                      📦 Pedidos
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {customers.map((customer, index) => (
                    <tr
                      key={index}
                      className="hover:bg-blue-50 transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="flex-shrink-0 h-10 w-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold shadow-md">
                            {customer.nombre.charAt(0).toUpperCase()}
                          </div>
                          <div className="font-semibold text-gray-900">
                            {customer.nombre}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                        {customer.telefono || <span className="text-gray-400 italic">Sin teléfono</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border border-green-300">
                          ${customer.total_gastado.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-600">
                        {new Date(customer.fecha_registro).toLocaleDateString('es-ES', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-800 font-bold text-sm">
                          {customer.num_ventas_contado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-yellow-100 text-yellow-800 font-bold text-sm">
                          {customer.num_apartados}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-purple-100 text-purple-800 font-bold text-sm">
                          {customer.num_pedidos}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </Layout>
  );
}

