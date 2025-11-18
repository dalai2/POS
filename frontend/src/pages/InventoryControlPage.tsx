import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useInventoryReport } from '../hooks/useInventoryReport';
import { InventoryReportView } from '../components/inventory/InventoryReportView';
import { StockGroupedView } from '../components/inventory/StockGroupedView';
import { StockApartadoView } from '../components/inventory/StockApartadoView';
import { RemovePiecesModal } from '../components/inventory/RemovePiecesModal';

export default function InventoryControlPage() {
  const userRole = localStorage.getItem('role') || '';
  const [activeTab, setActiveTab] = useState<'control' | 'stock' | 'pedidos' | 'pedidos-estado-pedido' | 'pedidos-recibidos' | 'eliminado' | 'devuelto' | 'apartado'>('control');
  const [showRemoveModal, setShowRemoveModal] = useState(false);

  const {
    startDate,
    endDate,
    loading,
    report,
    stockGrouped,
    stockPedidos,
    stockEliminado,
    stockDevuelto,
    stockApartado,
    stockPedidosEstadoPedido,
    pedidosRecibidosApartados,
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
    getStockPedidosEstadoPedido,
    getPedidosRecibidosApartados,
    resetCloseMessage,
  } = useInventoryReport();

  useEffect(() => {
    if (activeTab === 'stock') {
      // En tab stock, no pasar fecha (mostrar stock actual)
      getStockGrouped();
    } else if (activeTab === 'pedidos-estado-pedido') {
      getStockPedidosEstadoPedido();
    } else if (activeTab === 'pedidos-recibidos') {
      getPedidosRecibidosApartados();
    } else if (activeTab === 'eliminado') {
      getStockEliminado();
    } else if (activeTab === 'devuelto') {
      getStockDevuelto();
    } else if (activeTab === 'apartado') {
      getStockApartado();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Cargar stock agrupado cuando se genera un reporte
  useEffect(() => {
    if (report && activeTab === 'control') {
      // Pasar endDate para calcular stock histórico
      getStockGrouped(endDate);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [report]);

  // Verificar permisos
  if (userRole !== 'admin' && userRole !== 'owner') {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">⛔ Acceso Denegado</h2>
            <p className="text-gray-600">No tienes permisos para ver el control de inventario.</p>
            <p className="text-gray-600">Solo administradores y dueños pueden acceder.</p>
          </div>
        </div>
      </Layout>
    );
  }

  const handleRemovePieces = async (productId: number, quantity: number, notes: string) => {
    await removePieces(productId, quantity, notes);
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6" style={{ color: '#2e4354' }}>
          Control de Inventario
        </h1>

        {/* Tabs */}
        <div className="mb-6 border-b" style={{ borderColor: 'rgba(46, 67, 84, 0.1)' }}>
          <div className="flex gap-4 flex-wrap">
            <button
              onClick={() => setActiveTab('control')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'control'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'control' ? '#2e4354' : 'transparent',
              }}
            >
              Control de Inventario
            </button>
            <button
              onClick={() => setActiveTab('stock')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'stock'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'stock' ? '#2e4354' : 'transparent',
              }}
            >
              Stock Actual
            </button>
            <button
              onClick={() => setActiveTab('pedidos-estado-pedido')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'pedidos-estado-pedido'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'pedidos-estado-pedido' ? '#2e4354' : 'transparent',
              }}
            >
              Stock de Pedidos
            </button>
            <button
              onClick={() => setActiveTab('pedidos-recibidos')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'pedidos-recibidos'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'pedidos-recibidos' ? '#2e4354' : 'transparent',
              }}
            >
              Pedidos Recibidos
            </button>
            <button
              onClick={() => setActiveTab('eliminado')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'eliminado'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'eliminado' ? '#2e4354' : 'transparent',
              }}
            >
              Stock Eliminado
            </button>
            <button
              onClick={() => setActiveTab('devuelto')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'devuelto'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'devuelto' ? '#2e4354' : 'transparent',
              }}
            >
              Stock Devuelto
            </button>
            <button
              onClick={() => setActiveTab('apartado')}
              className={`px-6 py-3 font-medium transition-all ${
                activeTab === 'apartado'
                  ? 'border-b-2'
                  : 'opacity-60 hover:opacity-100'
              }`}
              style={{
                color: '#2e4354',
                borderBottomColor: activeTab === 'apartado' ? '#2e4354' : 'transparent',
              }}
            >
              Stock de Apartado
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'control' && (
          <div>
            {/* Date Selector */}
            <div className="rounded-xl shadow-lg p-6 mb-6 print:hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
                    Fecha Inicio
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full rounded-lg px-3 py-2 transition-all"
                    style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
                    onFocus={(e) => (e.target.style.border = '2px solid #2e4354')}
                    onBlur={(e) => (e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)')}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1" style={{ color: '#2e4354' }}>
                    Fecha Fin
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full rounded-lg px-3 py-2 transition-all"
                    style={{ border: '2px solid rgba(46, 67, 84, 0.2)', outline: 'none' }}
                    onFocus={(e) => (e.target.style.border = '2px solid #2e4354')}
                    onBlur={(e) => (e.target.style.border = '2px solid rgba(46, 67, 84, 0.2)')}
                  />
                </div>

                <div className="flex items-end">
                  <button
                    onClick={generateReport}
                    disabled={loading || (isDayClosed === true && startDate === endDate)}
                    className="w-full text-white px-6 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg disabled:cursor-not-allowed"
                    style={{
                      backgroundColor: '#2e4354',
                      opacity: loading || (isDayClosed === true && startDate === endDate) ? 0.7 : 1,
                    }}
                  >
                    {loading ? 'Generando...' : 'Generar Reporte'}
                  </button>
                </div>

                {(isDayClosed === true && startDate === endDate) && (
                  <div className="flex items-end">
                    <button
                      onClick={viewClosedDay}
                      disabled={loading}
                      className="w-full text-white px-6 py-2.5 rounded-lg transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                      style={{ backgroundColor: '#ffe98e', color: '#000000' }}
                    >
                      📦 Ver Cierre
                    </button>
                  </div>
                )}
              </div>

              <div className="flex gap-3 items-center">
                {startDate === endDate && !isDayClosed && (
                  <button
                    onClick={closeDay}
                    disabled={closing || !report}
                    className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg hover:scale-105 disabled:opacity-50"
                    style={{ backgroundColor: '#10b981', color: '#ffffff' }}
                  >
                    {closing ? 'Cerrando...' : '🔒 Cerrar Día'}
                  </button>
                )}
                <button
                  onClick={() => setShowRemoveModal(true)}
                  className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg hover:scale-105"
                  style={{ backgroundColor: '#ef4444', color: '#ffffff' }}
                >
                  ➖ Sacar Piezas
                </button>
              </div>

              {closeMsg && (
                <div className={`mt-4 p-3 rounded-lg ${closeMsg.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                  {closeMsg}
                  <button onClick={resetCloseMessage} className="ml-2 text-sm underline">
                    Cerrar
                  </button>
                </div>
              )}

              {usingClosure && (
                <div className="mt-4 p-3 rounded-lg bg-yellow-100 text-yellow-700">
                  📦 Mostrando cierre guardado (no se recalcula)
                </div>
              )}
            </div>

            {/* Report */}
            {report && <InventoryReportView report={report} stockGrouped={stockGrouped} stockDate={endDate} />}
          </div>
        )}

        {activeTab === 'stock' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <button
                onClick={() => getStockGrouped()}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                {loading ? 'Cargando...' : '🔄 Actualizar'}
              </button>
            </div>

            {/* Total Agrupaciones Card */}
            {stockGrouped && stockGrouped.length > 0 && (
              <div className="mb-6">
                <div className="rounded-xl shadow-lg p-6" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                  <div className="text-sm font-medium mb-1" style={{ color: '#2e4354', opacity: 0.7 }}>
                    Total de Agrupaciones
                  </div>
                  <div className="text-4xl font-bold" style={{ color: '#2e4354' }}>
                    {stockGrouped.length}
                  </div>
                  <div className="text-xs mt-2" style={{ color: '#2e4354', opacity: 0.6 }}>
                    grupos por nombre y quilataje
                  </div>
                  <div className="text-xs mt-1" style={{ color: '#2e4354', opacity: 0.6 }}>
                    Total piezas: {stockGrouped.reduce((sum, group) => sum + group.cantidad_total, 0)}
                  </div>
                </div>
              </div>
            )}

            {stockGrouped && <StockGroupedView stock={stockGrouped} loading={loading} />}
          </div>
        )}

        {activeTab === 'pedidos-estado-pedido' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <button
                onClick={getStockPedidosEstadoPedido}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                {loading ? 'Cargando...' : '🔄 Actualizar'}
              </button>
            </div>
            {stockPedidosEstadoPedido && stockPedidosEstadoPedido.length > 0 ? (
              <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead style={{ backgroundColor: '#2e4354' }}>
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Modelo
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Nombre
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Quilataje
                        </th>
                        <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Cantidad
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Folio Pedido
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Cliente
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {stockPedidosEstadoPedido.map((item: any, index: number) => (
                        <tr
                          key={index}
                          className="transition-all"
                          style={{
                            backgroundColor: index % 2 === 0 ? '#ffffff' : '#f0f7f7',
                            borderBottom: '1px solid rgba(46, 67, 84, 0.08)'
                          }}
                        >
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {item.modelo || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {item.nombre || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {item.quilataje || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center" style={{ color: '#2e4354' }}>
                            {item.cantidad}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {item.folio_pedido || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {item.cliente_nombre || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center">
                <span className="text-6xl mb-4 block">📭</span>
                <p className="text-xl font-medium" style={{ color: '#2e4354' }}>No hay pedidos con estado 'pedido'</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'pedidos-recibidos' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <button
                onClick={getPedidosRecibidosApartados}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                {loading ? 'Cargando...' : '🔄 Actualizar'}
              </button>
            </div>
            {pedidosRecibidosApartados && pedidosRecibidosApartados.length > 0 ? (
              <div className="rounded-xl shadow-lg overflow-hidden" style={{ backgroundColor: '#ffffff', border: '1px solid rgba(46, 67, 84, 0.1)' }}>
                <div className="overflow-x-auto">
                  <table className="min-w-full">
                    <thead style={{ backgroundColor: '#2e4354' }}>
                      <tr>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Folio
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Cliente
                        </th>
                        <th className="px-6 py-4 text-center text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Cantidad
                        </th>
                        <th className="px-6 py-4 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Total
                        </th>
                        <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff' }}>
                          Items
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {pedidosRecibidosApartados.map((pedido: any, index: number) => (
                        <tr
                          key={pedido.id}
                          className="transition-all"
                          style={{
                            backgroundColor: index % 2 === 0 ? '#ffffff' : '#f0f7f7',
                            borderBottom: '1px solid rgba(46, 67, 84, 0.08)'
                          }}
                        >
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {pedido.folio_pedido || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {pedido.cliente_nombre || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center" style={{ color: '#2e4354' }}>
                            {pedido.cantidad || 0}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right" style={{ color: '#2e4354' }}>
                            ${pedido.total?.toFixed(2) || '0.00'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap" style={{ color: '#2e4354' }}>
                            {pedido.items && pedido.items.length > 0 ? (
                              <div>
                                {pedido.items.map((item: any, idx: number) => (
                                  <div key={idx} className="text-sm">
                                    {item.nombre} {item.modelo ? `(${item.modelo})` : ''} ({item.cantidad})
                                  </div>
                                ))}
                              </div>
                            ) : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center">
                <span className="text-6xl mb-4 block">📭</span>
                <p className="text-xl font-medium" style={{ color: '#2e4354' }}>No hay pedidos recibidos</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'eliminado' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <button
                onClick={getStockEliminado}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                {loading ? 'Cargando...' : '🔄 Actualizar'}
              </button>
            </div>
            {stockEliminado && <StockGroupedView stock={stockEliminado} loading={loading} />}
          </div>
        )}

        {activeTab === 'devuelto' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <button
                onClick={getStockDevuelto}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                {loading ? 'Cargando...' : '🔄 Actualizar'}
              </button>
            </div>
            {stockDevuelto && <StockGroupedView stock={stockDevuelto} loading={loading} />}
          </div>
        )}

        {activeTab === 'apartado' && (
          <div>
            <div className="mb-4 flex justify-between items-center">
              <button
                onClick={getStockApartado}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg font-medium transition-all shadow-md hover:shadow-lg disabled:opacity-50"
                style={{ backgroundColor: '#2e4354', color: '#ffffff' }}
              >
                {loading ? 'Cargando...' : '🔄 Actualizar'}
              </button>
            </div>
            <StockApartadoView stockApartado={stockApartado} loading={loading} />
          </div>
        )}

        {/* Remove Pieces Modal */}
        <RemovePiecesModal
          isOpen={showRemoveModal}
          onClose={() => setShowRemoveModal(false)}
          onSuccess={() => {
            setShowRemoveModal(false);
            if (report) {
              generateReport();
            }
          }}
        />
      </div>
    </Layout>
  );
}

