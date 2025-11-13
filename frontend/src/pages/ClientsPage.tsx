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
      <div className="max-w-7xl mx-auto font-['Poppins',sans-serif]" style={{ backgroundColor: '#f0f7f7', minHeight: 'calc(100vh - 64px)', padding: '2rem', borderRadius: '8px' }}>
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-['Exo_2',sans-serif] font-bold flex items-center gap-3" style={{ color: '#2e4354' }}>
            <span className="text-4xl">👥</span>
            Clientes
          </h1>
          <button
            onClick={exportToExcel}
            className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-lg flex items-center gap-2 hover:shadow-xl hover:scale-105"
            style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
          >
            <span>📊</span>
            Exportar a Excel
          </button>
        </div>

        {/* Search and Stats */}
        <div className="rounded-xl shadow-lg p-6 mb-6" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Buscar por nombre o teléfono..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 px-4 py-2.5 rounded-lg transition-all"
                style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
                onFocus={(e) => e.target.style.border = '2px solid #2e4354'}
                onBlur={(e) => e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)'}
              />
              <button
                onClick={handleSearch}
                className="px-6 py-2.5 rounded-lg font-medium transition-all hover:shadow-lg"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                🔍 Buscar
              </button>
            </div>
            
            <div className="flex gap-2 items-center justify-end">
              <span className="text-sm font-medium" style={{ color: '#2e4354' }}>
                Total de clientes: <span className="text-2xl font-bold" style={{ color: '#ffe98e' }}>{ customers.length}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="rounded-xl shadow-xl overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12" style={{ borderBottom: '3px solid #2e4354' }}></div>
              <p className="mt-4 font-medium" style={{ color: '#2e4354' }}>Cargando clientes...</p>
            </div>
          ) : customers.length === 0 ? (
            <div className="p-12 text-center">
              <span className="text-6xl mb-4 block">📭</span>
              <p className="text-xl font-medium" style={{ color: '#2e4354' }}>No se encontraron clientes</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead style={{ backgroundColor: '#2e4354' }}>
                  <tr>
                    <th
                      onClick={() => handleSort('nombre')}
                      className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider cursor-pointer transition-all"
                      style={{ color: '#ffffff' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1e2d3a'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <div className="flex items-center gap-2">
                        <span>Cliente</span>
                        <span className="text-sm">{getSortIcon('nombre')}</span>
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('telefono')}
                      className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider cursor-pointer transition-all"
                      style={{ color: '#ffffff' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1e2d3a'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <div className="flex items-center gap-2">
                        <span>📱 Teléfono</span>
                        <span className="text-sm">{getSortIcon('telefono')}</span>
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('total_gastado')}
                      className="px-6 py-4 text-right text-xs font-bold uppercase tracking-wider cursor-pointer transition-all"
                      style={{ color: '#ffffff' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1e2d3a'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <div className="flex items-center justify-end gap-2">
                        <span>💰 Total Gastado</span>
                        <span className="text-sm">{getSortIcon('total_gastado')}</span>
                      </div>
                    </th>
                    <th
                      onClick={() => handleSort('fecha_registro')}
                      className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider cursor-pointer transition-all"
                      style={{ color: '#ffffff' }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#1e2d3a'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span>📅 Fecha de Registro</span>
                        <span className="text-sm">{getSortIcon('fecha_registro')}</span>
                      </div>
                    </th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                      🛒 V. Contado
                    </th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                      💳 Apartados
                    </th>
                    <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                      📦 Pedidos
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map((customer, index) => (
                    <tr
                      key={index}
                      className="transition-all"
                      style={{ 
                        backgroundColor: index % 2 === 0 ? '#ffffff' : '#f0f7f7',
                        borderBottom: '1px solid rgba(46, 67, 84, 0.08)'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 233, 142, 0.15)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = index % 2 === 0 ? '#ffffff' : '#f0f7f7'}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-3">
                          <div className="flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center text-white font-bold shadow-md" style={{ backgroundColor: '#2e4354' }}>
                            {customer.nombre.charAt(0).toUpperCase()}
                          </div>
                          <div className="font-semibold" style={{ color: '#000000' }}>
                            {customer.nombre}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                        {customer.telefono || <span className="italic opacity-60">Sin teléfono</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold shadow-sm" style={{ backgroundColor: 'rgba(255, 233, 142, 0.3)', color: '#000000', border: '1px solid rgba(255, 233, 142, 0.6)' }}>
                          ${customer.total_gastado.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm" style={{ color: '#2e4354' }}>
                        {new Date(customer.fecha_registro).toLocaleDateString('es-ES', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm shadow-sm" style={{ backgroundColor: 'rgba(255, 233, 142, 0.4)', color: '#000000' }}>
                          {customer.num_ventas_contado}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm shadow-sm" style={{ backgroundColor: 'rgba(255, 233, 142, 0.4)', color: '#000000' }}>
                          {customer.num_apartados}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm shadow-sm" style={{ backgroundColor: 'rgba(255, 233, 142, 0.4)', color: '#000000' }}>
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

