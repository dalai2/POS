import React, { useState, useEffect, useMemo } from 'react';
import { Pie, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);
import { api } from '../utils/api';
import Layout from '../components/Layout';

interface ProductoPedido {
  id: number;
  name: string;
  price: number;
  codigo?: string;
  marca?: string;
  modelo?: string;
  color?: string;
  quilataje?: string;
  talla?: string;
  peso_gramos?: number;
  milimetros?: string;
}

interface Pedido {
  id: number;
  cliente_nombre: string;
  cliente_telefono?: string;
  cliente_email?: string;
  cantidad: number;
  precio_unitario: number;
  total: number;
  anticipo_pagado: number;
  saldo_pendiente: number;
  estado: string;
  fecha_entrega_estimada?: string;
  fecha_entrega_real?: string;
  notas_cliente?: string;
  created_at: string;
  producto: ProductoPedido;
  user?: { id: number; email?: string };
  pagos: Array<{
    id: number;
    monto: number;
    metodo_pago: string;
    tipo_pago: string;
    created_at: string;
  }>;
}

const DashboardPedidosPage: React.FC = () => {
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtros
  const [filtroCliente, setFiltroCliente] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [filtroFechaDesde, setFiltroFechaDesde] = useState('');
  const [filtroFechaHasta, setFiltroFechaHasta] = useState('');
  const [rango, setRango] = useState<'7' | '30' | '90' | 'custom'>('30');
  const [segmento, setSegmento] = useState<'estado' | 'vendedor'>('estado');
  const [filtroUserId, setFiltroUserId] = useState<string>('');
  
  // Estados disponibles
  const estados = [
    { value: '', label: 'Todos los estados' },
    { value: 'pendiente', label: 'Pendiente' },
    { value: 'confirmado', label: 'Confirmado' },
    { value: 'en_proceso', label: 'En Proceso' },
    { value: 'entregado', label: 'Entregado' },
    { value: 'cancelado', label: 'Cancelado' }
  ];

  const loadPedidos = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (filtroCliente) params.append('cliente', filtroCliente);
      if (filtroEstado) params.append('estado', filtroEstado);
      if (filtroFechaDesde) params.append('fecha_desde', filtroFechaDesde);
      if (filtroFechaHasta) params.append('fecha_hasta', filtroFechaHasta);
      if (filtroUserId) params.append('user_id', filtroUserId);
      
      const response = await api.get(`/productos-pedido/pedidos/dashboard?${params.toString()}`);
      setPedidos(response.data);
    } catch (err: any) {
      console.error('Error loading pedidos:', err);
      setError('Error al cargar los pedidos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPedidos();
  }, []);

  // Recargar pedidos cuando cambien los filtros
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadPedidos();
    }, 500); // Debounce de 500ms

    return () => clearTimeout(timeoutId);
  }, [filtroCliente, filtroEstado, filtroFechaDesde, filtroFechaHasta]);
  
  // Ajustar rango rápido 7/30/90 días
  useEffect(() => {
    if (rango === 'custom') return;
    const days = parseInt(rango, 10);
    const now = new Date();
    const desde = new Date(now);
    desde.setDate(now.getDate() - (days - 1));
    setFiltroFechaDesde(desde.toISOString().slice(0, 10));
    setFiltroFechaHasta(now.toISOString().slice(0, 10));
  }, [rango]);

  const actualizarEstado = async (pedidoId: number, nuevoEstado: string) => {
    try {
      await api.put(`/productos-pedido/pedidos/${pedidoId}/estado`, {
        estado: nuevoEstado
      });
      
      setPedidos(prevPedidos => 
        prevPedidos.map(pedido => 
          pedido.id === pedidoId 
            ? { ...pedido, estado: nuevoEstado }
            : pedido
        )
      );
    } catch (err: any) {
      console.error('Error updating estado:', err);
      setError('Error al actualizar el estado');
    }
  };

  const actualizarFechaEntrega = async (pedidoId: number, fecha: string, tipo: 'estimada' | 'real') => {
    try {
      const field = tipo === 'estimada' ? 'fecha_entrega_estimada' : 'fecha_entrega_real';
      await api.put(`/productos-pedido/pedidos/${pedidoId}/fechas`, {
        [field]: fecha ? new Date(fecha).toISOString() : null
      });
      
      setPedidos(prevPedidos => 
        prevPedidos.map(pedido => 
          pedido.id === pedidoId 
            ? { 
                ...pedido, 
                [field]: fecha ? new Date(fecha).toISOString() : null 
              }
            : pedido
        )
      );
    } catch (err: any) {
      console.error('Error updating fecha:', err);
      setError('Error al actualizar la fecha');
    }
  };

  // Los pedidos ya vienen filtrados del backend
  const pedidosFiltrados = pedidos;

  // Datasets
  const statusChart = useMemo(() => {
    if (segmento === 'estado') {
      const counts: Record<string, number> = { pendiente: 0, confirmado: 0, en_proceso: 0, entregado: 0, cancelado: 0 };
      for (const p of pedidosFiltrados) counts[p.estado] = (counts[p.estado] || 0) + 1;
      return {
        labels: ['Pendiente', 'Confirmado', 'En Proceso', 'Entregado', 'Cancelado'],
        datasets: [
          {
            data: [counts.pendiente, counts.confirmado, counts.en_proceso, counts.entregado, counts.cancelado],
            backgroundColor: ['#f59e0b', '#3b82f6', '#fb923c', '#22c55e', '#ef4444'],
            borderWidth: 0,
          },
        ],
      };
    }
    // segmento vendedor
    const counts: Record<string, number> = {};
    for (const p of pedidosFiltrados) {
      const key = p.user?.email || `Vendedor ${p.user?.id ?? 'N/A'}`;
      counts[key] = (counts[key] || 0) + 1;
    }
    const entries = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,6);
    return {
      labels: entries.map(e=>e[0]),
      datasets: [
        {
          data: entries.map(e=>e[1]),
          backgroundColor: ['#3b82f6','#22c55e','#f59e0b','#ef4444','#6366f1','#06b6d4'],
          borderWidth: 0,
        },
      ],
    };
  }, [pedidosFiltrados, segmento]);

  const last30DaysLabels = useMemo(() => {
    const days: string[] = [];
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);
      days.push(d.toISOString().slice(0, 10));
    }
    return days;
  }, []);

  const perDayChart = useMemo(() => {
    const map: Record<string, number> = Object.fromEntries(last30DaysLabels.map(d => [d, 0]));
    for (const p of pedidosFiltrados) {
      const d = new Date(p.created_at).toISOString().slice(0, 10);
      if (d in map) map[d] += 1;
    }
    return {
      labels: last30DaysLabels.map(d => d.slice(5)),
      datasets: [
        {
          label: 'Pedidos',
          data: last30DaysLabels.map(d => map[d]),
          backgroundColor: '#3b82f6',
          borderRadius: 4,
        },
      ],
    };
  }, [pedidosFiltrados, last30DaysLabels]);

  const cashFlowChart = useMemo(() => {
    let anticipos = 0;
    let saldos = 0;
    for (const p of pedidosFiltrados) {
      anticipos += Number(p.anticipo_pagado || 0);
      saldos += Number(p.saldo_pendiente || 0);
    }
    return {
      labels: ['Anticipos', 'Saldos'],
      datasets: [
        {
          label: 'MXN',
          data: [anticipos, saldos],
          backgroundColor: ['#10b981', '#f97316'],
          borderRadius: 6,
        },
      ],
    };
  }, [pedidosFiltrados]);

  const topClientsChart = useMemo(() => {
    const map: Record<string, number> = {};
    for (const p of pedidosFiltrados) map[p.cliente_nombre] = (map[p.cliente_nombre] || 0) + p.total;
    const entries = Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, 5);
    return {
      labels: entries.map(e => e[0]),
      datasets: [
        {
          label: 'Total MXN',
          data: entries.map(e => e[1]),
          backgroundColor: '#6366f1',
          borderRadius: 6,
        },
      ],
    };
  }, [pedidosFiltrados]);

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'pendiente': return 'bg-yellow-100 text-yellow-800';
      case 'confirmado': return 'bg-blue-100 text-blue-800';
      case 'en_proceso': return 'bg-orange-100 text-orange-800';
      case 'entregado': return 'bg-green-100 text-green-800';
      case 'cancelado': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getEstadoLabel = (estado: string) => {
    const estadoObj = estados.find(e => e.value === estado);
    return estadoObj ? estadoObj.label : estado;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Cargando pedidos...</div>
      </div>
    );
  }

  return (
    <Layout>
      <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Dashboard de Pedidos
        </h1>
        <p className="text-gray-600">
          Gestiona y actualiza el estado de los pedidos por cliente
        </p>
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">Filtros</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cliente
            </label>
            <input
              type="text"
              placeholder="Nombre, teléfono o email"
              value={filtroCliente}
              onChange={(e) => setFiltroCliente(e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vendedor</label>
            <input
              type="number"
              placeholder="ID usuario"
              value={filtroUserId}
              onChange={(e)=> setFiltroUserId(e.target.value)}
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rango</label>
            <select value={rango} onChange={(e)=> setRango(e.target.value as any)} className="input w-full">
              <option value="7">Últimos 7 días</option>
              <option value="30">Últimos 30 días</option>
              <option value="90">Últimos 90 días</option>
              <option value="custom">Personalizado</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Segmentar por</label>
            <select value={segmento} onChange={(e)=> setSegmento(e.target.value as any)} className="input w-full">
              <option value="estado">Estado</option>
              <option value="vendedor">Vendedor</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estado
            </label>
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              className="input w-full"
            >
              {estados.map(estado => (
                <option key={estado.value} value={estado.value}>
                  {estado.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Desde
            </label>
            <input
              type="date"
              value={filtroFechaDesde}
              onChange={(e) => setFiltroFechaDesde(e.target.value)}
              className="input w-full"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Hasta
            </label>
            <input
              type="date"
              value={filtroFechaHasta}
              onChange={(e) => setFiltroFechaHasta(e.target.value)}
              className="input w-full"
            />
          </div>
        </div>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-blue-600">
            {pedidosFiltrados.length}
          </div>
          <div className="text-sm text-gray-600">Total Pedidos</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-yellow-600">
            {pedidosFiltrados.filter(p => p.estado === 'pendiente').length}
          </div>
          <div className="text-sm text-gray-600">Pendientes</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-orange-600">
            {pedidosFiltrados.filter(p => p.estado === 'en_proceso').length}
          </div>
          <div className="text-sm text-gray-600">En Proceso</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-2xl font-bold text-green-600">
            {pedidosFiltrados.filter(p => p.estado === 'entregado').length}
          </div>
          <div className="text-sm text-gray-600">Entregados</div>
        </div>
      </div>

      {/* Gráficas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-semibold mb-3">Pedidos por Estado</h3>
          <Pie data={statusChart} />
        </div>
        <div className="bg-white p-4 rounded-lg shadow lg:col-span-2">
          <h3 className="text-sm font-semibold mb-3">Pedidos en últimos 30 días</h3>
          <Bar data={perDayChart} options={{ responsive: true, plugins: { legend: { display: false } } }} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-semibold mb-3">Anticipos vs Saldos</h3>
          <Bar data={cashFlowChart} options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: (v) => String(v) } } } }} />
        </div>
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-sm font-semibold mb-3">Top 5 Clientes por Total</h3>
          <Bar data={topClientsChart} options={{ responsive: true, plugins: { legend: { display: false } } }} />
        </div>
      </div>

      {/* Tabla de Pedidos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cliente
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Producto
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha Entrega
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha Creación
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {pedidosFiltrados.map((pedido) => (
                <tr key={pedido.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{pedido.id}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {pedido.cliente_nombre}
                    </div>
                    {pedido.cliente_telefono && (
                      <div className="text-sm text-gray-500">
                        {pedido.cliente_telefono}
                      </div>
                    )}
                    {pedido.cliente_email && (
                      <div className="text-sm text-gray-500">
                        {pedido.cliente_email}
                      </div>
                    )}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {pedido.producto.name}
                    </div>
                    {pedido.producto.codigo && (
                      <div className="text-sm text-gray-500">
                        Código: {pedido.producto.codigo}
                      </div>
                    )}
                    <div className="text-sm text-gray-500">
                      Cantidad: {pedido.cantidad}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <select
                      value={pedido.estado}
                      onChange={(e) => actualizarEstado(pedido.id, e.target.value)}
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoColor(pedido.estado)} border-0`}
                    >
                      {estados.filter(e => e.value).map(estado => (
                        <option key={estado.value} value={estado.value}>
                          {estado.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="font-medium">{formatCurrency(pedido.total)}</div>
                    <div className="text-xs text-gray-500">
                      Anticipo: {formatCurrency(pedido.anticipo_pagado)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Saldo: {formatCurrency(pedido.saldo_pendiente)}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="space-y-1">
                      <div>
                        <label className="text-xs text-gray-500">Estimada:</label>
                        <input
                          type="datetime-local"
                          value={pedido.fecha_entrega_estimada ? 
                            new Date(pedido.fecha_entrega_estimada).toISOString().slice(0, 16) : ''}
                          onChange={(e) => actualizarFechaEntrega(pedido.id, e.target.value, 'estimada')}
                          className="text-xs border rounded px-1 py-0.5 w-full"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-gray-500">Real:</label>
                        <input
                          type="datetime-local"
                          value={pedido.fecha_entrega_real ? 
                            new Date(pedido.fecha_entrega_real).toISOString().slice(0, 16) : ''}
                          onChange={(e) => actualizarFechaEntrega(pedido.id, e.target.value, 'real')}
                          className="text-xs border rounded px-1 py-0.5 w-full"
                        />
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(pedido.created_at)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          // Aquí podrías abrir un modal con más detalles del pedido
                          console.log('Ver detalles del pedido:', pedido.id);
                        }}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Ver
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {pedidosFiltrados.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No hay pedidos que coincidan con los filtros seleccionados
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      </div>
    </Layout>
  );
};

export default DashboardPedidosPage;
