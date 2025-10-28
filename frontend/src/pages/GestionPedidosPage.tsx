import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type Pedido = {
  id: number
  producto_pedido_id: number
  cliente_nombre: string
  cliente_telefono?: string
  cliente_email?: string
  cantidad: number
  precio_unitario: number
  total: number
  anticipo_pagado: number
  saldo_pendiente: number
  estado: string
  fecha_entrega_estimada?: string
  fecha_entrega_real?: string
  notas_cliente?: string
  notas_internas?: string
  created_at: string
  updated_at?: string
  producto: {
    id: number
    name: string
    modelo?: string
    color?: string
    quilataje?: string
    talla?: string
    price: number
    disponible: boolean
    anticipo_sugerido?: number
    peso_gramos?: number
    codigo?: string
  }
}

type PagoPedido = {
  id: number
  monto: number
  metodo_pago: string
  tipo_pago: string
  created_at: string
}

export default function GestionPedidosPage() {
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(true)
  const [userRole, setUserRole] = useState<string>('')
  
  // Filtros
  const [filtroEstado, setFiltroEstado] = useState('')
  const [filtroCliente, setFiltroCliente] = useState('')
  
  // Modal para pagos
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [pedidoSeleccionado, setPedidoSeleccionado] = useState<Pedido | null>(null)
  const [montoPago, setMontoPago] = useState('')
  const [metodoPago, setMetodoPago] = useState('efectivo')
  const [tipoPago, setTipoPago] = useState('saldo')

  useEffect(() => {
    if (!localStorage.getItem('access')) {
      window.location.href = '/login'
      return
    }
    setUserRole(localStorage.getItem('role') || '')
    loadPedidos()
  }, [])

  const loadPedidos = async () => {
    try {
      setLoading(true)
      const qs = new URLSearchParams()
      if (filtroEstado) qs.set('estado', filtroEstado)
      
      const r = await api.get(`/productos-pedido/pedidos/?${qs.toString()}`)
      let pedidosData = r.data || []
      
      // Filtrar por cliente si hay filtro
      if (filtroCliente) {
        pedidosData = pedidosData.filter((p: Pedido) => 
          p.cliente_nombre.toLowerCase().includes(filtroCliente.toLowerCase()) ||
          (p.cliente_telefono && p.cliente_telefono.includes(filtroCliente))
        )
      }
      
      // Ordenar por ID descendente (más recientes primero)
      pedidosData.sort((a: Pedido, b: Pedido) => b.id - a.id)
      setPedidos(pedidosData)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error cargando pedidos')
    } finally {
      setLoading(false)
    }
  }

  const reloadPedidos = async () => {
    const qs = new URLSearchParams()
    if (filtroEstado) qs.set('estado', filtroEstado)
    
    const r = await api.get(`/productos-pedido/pedidos/?${qs.toString()}`)
    let pedidosData = r.data || []
    
    if (filtroCliente) {
      pedidosData = pedidosData.filter((p: Pedido) => 
        p.cliente_nombre.toLowerCase().includes(filtroCliente.toLowerCase()) ||
        (p.cliente_telefono && p.cliente_telefono.includes(filtroCliente))
      )
    }
    
    // Ordenar por ID descendente (más recientes primero)
    pedidosData.sort((a: Pedido, b: Pedido) => b.id - a.id)
    setPedidos(pedidosData)
  }

  const abrirModalPago = (pedido: Pedido) => {
    setPedidoSeleccionado(pedido)
    setMontoPago(pedido.saldo_pendiente.toString())
    setTipoPago('saldo')
    setShowPagoModal(true)
  }

  const registrarPago = async () => {
    if (!pedidoSeleccionado || !montoPago) return
    
    try {
      const response = await api.post(`/productos-pedido/pedidos/${pedidoSeleccionado.id}/pagos`, {
        monto: parseFloat(montoPago),
        metodo_pago: metodoPago,
        tipo_pago: tipoPago
      })
      
      setMsg('✅ Pago registrado correctamente')
      setShowPagoModal(false)
      
      // Actualizar solo la fila específica con los nuevos datos del pago
      const nuevoAnticipo = pedidoSeleccionado.anticipo_pagado + parseFloat(montoPago)
      const nuevoSaldo = pedidoSeleccionado.saldo_pendiente - parseFloat(montoPago)
      
      setPedidos(prevPedidos => 
        prevPedidos.map(p => 
          p.id === pedidoSeleccionado.id 
            ? { 
                ...p, 
                anticipo_pagado: nuevoAnticipo,
                saldo_pendiente: nuevoSaldo
              }
            : p
        )
      )
      
      setTimeout(() => setMsg(''), 3000)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error registrando pago')
    }
  }

  const actualizarEstado = async (pedidoId: number, nuevoEstado: string) => {
    try {
      await api.put(`/productos-pedido/pedidos/${pedidoId}`, {
        estado: nuevoEstado
      })
      setMsg('✅ Estado actualizado exitosamente')
      
      // Actualizar solo la fila específica en lugar de recargar toda la lista
      setPedidos(prevPedidos => 
        prevPedidos.map(p => 
          p.id === pedidoId 
            ? { ...p, estado: nuevoEstado }
            : p
        )
      )
      
      setTimeout(() => setMsg(''), 3000)
    } catch (error: any) {
      setMsg(error?.response?.data?.detail || 'Error al actualizar el estado')
    }
  }

  const verTicket = async (pedido: Pedido) => {
    try {
      // Get logo as base64 (similar to SalesPage)
      const getLogoAsBase64 = async () => {
        try {
          const response = await fetch('/logo.png')
          if (!response.ok) throw new Error('Logo not found')
          const blob = await response.blob()
          return new Promise<string>((resolve) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result as string)
            reader.readAsDataURL(blob)
          })
        } catch (error) {
          console.warn('Could not load logo:', error)
          return ''
        }
      }

      const logoBase64 = await getLogoAsBase64()
      const w = window.open('', '_blank')
      if (!w) return
      
      await new Promise(resolve => setTimeout(resolve, 100))

      // Build product description similar to SalesPage
      const descParts = []
      if (pedido.producto?.name) descParts.push(pedido.producto.name)
      if (pedido.producto?.modelo) descParts.push(pedido.producto.modelo)
      if (pedido.producto?.color) descParts.push(pedido.producto.color)
      if (pedido.producto?.quilataje) descParts.push(pedido.producto.quilataje)
      if (pedido.producto?.peso_gramos) {
        const peso = typeof pedido.producto.peso_gramos === 'number' ? pedido.producto.peso_gramos : parseFloat(pedido.producto.peso_gramos.toString())
        let pesoFormatted
        if (peso === Math.floor(peso)) {
          pesoFormatted = `${peso}g`
        } else {
          pesoFormatted = peso.toFixed(3).replace(/\.?0+$/, '') + 'g'
        }
        descParts.push(pesoFormatted)
      }
      if (pedido.producto?.talla) descParts.push(pedido.producto.talla)
      const description = descParts.length > 0 ? descParts.join('-') : 'Producto sin descripción'

      const date = new Date(pedido.created_at)
      const formattedDate = date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })

      const customerInfo = pedido.cliente_nombre || 'PUBLICO GENERAL'
      const customerPhoneInfo = pedido.cliente_telefono || ''

      const html = `
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ticket Pedido ${pedido.id}</title>
<style>
  @media print {
    @page {
      size: A4;
      margin: 0;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      font-size: 12px;
      height: 100vh;
    }
    .gold-line {
      background: linear-gradient(to right, #000000 0%, #fff0bb 2%, #ffdd55 5%, #ffdd55 30%, #000000 35%, #fff0bb 50%, #ffdd55 65%, #000000 70%, #fff0bb 95%, #000000 100%) !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      color-adjust: exact;
    }
    th {
      background-color: #fff0bb !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      color-adjust: exact;
    }
  }
  body {
    margin: 0 auto;
    padding: 10px;
    font-family: Arial, sans-serif;
    font-size: 12px;
    color: #000;
    width: 210mm;
    height: 297mm;
    display: flex;
    flex-direction: column;
    page-break-after: avoid;
  }
  .gold-line { 
    background: linear-gradient(to right, #000000 0%, #fff0bb 2%, #ffdd55 5%, #ffdd55 30%, #000000 35%, #fff0bb 50%, #ffdd55 65%, #000000 70%, #fff0bb 95%, #000000 100%) !important; 
    height: 4px; 
    margin: 10px 0;
    border: none;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .logo-container {
    text-align: left;
    margin-bottom: 5px;
  }
  .header-section {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
  }
  .header-section .logo-container {
    flex-shrink: 0;
  }
  .header-section .header-info {
    margin-left: auto;
    margin-top: 0;
  }
  .company-name {
    font-size: 24px;
    font-weight: bold;
    color: #8B7355;
    margin-bottom: 3px;
  }
  .company-subtitle {
    font-size: 14px;
    font-weight: normal;
    color: #8B7355;
    text-align: center;
    margin-top: -5px;
  }
  .header-info {
    font-size: 9px;
    margin-top: 10px;
    text-align: right;
  }
  .header-info div {
    margin-bottom: 2px;
  }
  .customer-info {
    font-size: 11px;
    margin-top: 15px;
    width: 100%;
  }
  .customer-info td {
    padding: 2px 4px;
    border: 1px solid #ddd;
  }
  .customer-info td:first-child {
    width: 30%;
    font-weight: bold;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
  }
  th {
    background-color: #fff0bb;
    padding: 3px 4px;
    text-align: left;
    font-size: 10px;
    font-weight: bold;
  }
  td {
    padding: 2px 4px;
    font-size: 10px;
  }
  .totals {
    text-align: right;
    font-size: 11px;
    margin-top: 15px;
  }
  .footer-info {
    margin-top: 20px;
    font-size: 9px;
  }
  .policy {
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 10px;
  }
  img { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .container {
    width: 100%;
    margin: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    page-break-inside: avoid;
  }
  .main-content {
    flex: 1;
  }
  .footer-section {
    margin-top: auto;
  }
</style></head>
<body>
  <div class="container">
    <!-- Header Section (Logo + Folio) -->
    <div class="header-section">
      <!-- Company Logo -->
      <div class="logo-container">
        <img src="${logoBase64}" alt="Logo" style="max-width: 350px; max-height: 180px; display: block;" onerror="this.style.display='none'" />
      </div>

      <!-- Header Info -->
      <div class="header-info">
        <div><strong>FOLIO :</strong> ${String(pedido.id).padStart(6, '0')}</div>
        <div><strong>FECHA PEDIDO :</strong> ${formattedDate}</div>
        <div>HIDALGO #112 ZONA CENTRO, LOCAL 12, 23 Y 24 C.P: 37000. LEÓN, GTO.</div>
        <div>WhatsApp: 4776621788</div>
      </div>
    </div>

    <!-- Customer Info -->
    <table class="customer-info">
      <tr>
        <td><strong>Cliente:</strong></td>
        <td>${customerInfo}</td>
      </tr>
      <tr>
        <td><strong>Teléfono:</strong></td>
        <td>${customerPhoneInfo}</td>
      </tr>
      <tr>
        <td><strong>Estado:</strong></td>
        <td>${pedido.estado.toUpperCase()}</td>
      </tr>
      <tr>
        <td><strong>Entrega Est.:</strong></td>
        <td>${pedido.fecha_entrega_estimada ? new Date(pedido.fecha_entrega_estimada).toLocaleDateString('es-ES') : 'Por definir'}</td>
      </tr>
    </table>

    <!-- Golden Line 2 -->
    <div class="gold-line"></div>

    <!-- Items Table -->
    <table>
      <thead>
        <tr>
          <th style="width: 5%;">Cant.</th>
          <th style="width: 10%;">Código</th>
          <th style="width: 45%;">Descripción</th>
          <th style="width: 12%;">P.Unitario</th>
          <th style="width: 10%;">Desc.</th>
          <th style="width: 12%;">Importe</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>${pedido.cantidad}</td>
          <td>${pedido.producto?.codigo || ''}</td>
          <td>${description}</td>
          <td>$${pedido.precio_unitario.toFixed(2)}</td>
          <td>$0.00</td>
          <td>$${pedido.total.toFixed(2)}</td>
        </tr>
      </tbody>
    </table>

    <!-- Totals -->
    <div class="totals">
      <div><strong>TOTAL :</strong> $${pedido.total.toFixed(2)}</div>
      <div><strong>ANTICIPO :</strong> $${pedido.anticipo_pagado.toFixed(2)}</div>
      <div><strong>SALDO :</strong> $${pedido.saldo_pendiente.toFixed(2)}</div>
    </div>

    <!-- Footer Section -->
    <div class="footer-section">
      <!-- Footer -->
      <div class="footer-info">
        <div>1 Articulo</div>
        <div class="policy">
          SU PIEZA TIENE UNA GARANTÍA DE POR VIDA DE AUTENTICIDAD<br>
          NO SE ACEPTAN CAMBIOS NI DEVOLUCIONES EN MERCANCÍA DAÑADA
        </div>
      </div>

      <!-- Golden Line 3 -->
      <div class="gold-line" style="margin-top: 20px;"></div>
    </div>
    
    <!-- Watermark -->
    <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); opacity: 0.2; z-index: 0; pointer-events: none;">
      <img src="${logoBase64}" alt="Watermark" style="width: 200px; height: auto; filter: grayscale(100%);" />
    </div>
  </div>
</body></html>`

      w.document.write(html)
      w.document.close()
      
      // Wait for images to load before printing
      w.addEventListener('load', () => {
        setTimeout(() => {
          w.print()
        }, 500)
      })
      
      // Fallback timeout
      setTimeout(() => {
        if (!w.closed) {
          w.print()
        }
      }, 2000)
    } catch (e) {
      console.error('Error printing ticket:', e)
    }
  }

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'pendiente': return 'bg-yellow-100 text-yellow-800'
      case 'confirmado': return 'bg-blue-100 text-blue-800'
      case 'en_proceso': return 'bg-orange-100 text-orange-800'
      case 'entregado': return 'bg-green-100 text-green-800'
      case 'cancelado': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getEstadoTexto = (estado: string) => {
    switch (estado) {
      case 'pendiente': return 'Pendiente'
      case 'confirmado': return 'Confirmado'
      case 'en_proceso': return 'En Proceso'
      case 'entregado': return 'Entregado'
      case 'cancelado': return 'Cancelado'
      default: return estado
    }
  }

  useEffect(() => {
    loadPedidos()
  }, [filtroEstado])

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="text-lg">Cargando pedidos...</div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-purple-50 rounded-lg p-4">
          <h1 className="text-2xl font-bold text-purple-800">📋 Gestión de Pedidos</h1>
          <p className="text-purple-600">Administra y da seguimiento a los pedidos especiales</p>
        </div>

        {/* Filtros */}
        <div className="bg-white border rounded-lg p-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Estado</label>
              <select
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                value={filtroEstado}
                onChange={e => setFiltroEstado(e.target.value)}
              >
                <option value="">Todos los estados</option>
                <option value="pendiente">Pendiente</option>
                <option value="confirmado">Confirmado</option>
                <option value="en_proceso">En Proceso</option>
                <option value="entregado">Entregado</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cliente</label>
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Nombre o teléfono"
                value={filtroCliente}
                onChange={e => setFiltroCliente(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={loadPedidos}
                className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700"
              >
                🔍 Filtrar
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de Pedidos */}
        <div className="bg-white border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">ID</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Cliente</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Producto</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Cantidad</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Total</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Anticipo</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Saldo</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Estado</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pedidos.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                      No hay pedidos registrados
                    </td>
                  </tr>
                ) : (
                  pedidos.map(p => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium">#{p.id}</td>
                      <td className="px-4 py-3 text-sm">
                        <div>
                          <div className="font-medium">{p.cliente_nombre}</div>
                          {p.cliente_telefono && (
                            <div className="text-gray-500">{p.cliente_telefono}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div>
                          <div className="font-medium">{p.producto?.name || 'Producto no encontrado'}</div>
                          <div className="text-gray-500">
                            {p.producto?.modelo && `${p.producto.modelo} - `}
                            {p.producto?.color && `${p.producto.color} - `}
                            {p.producto?.quilataje && `${p.producto.quilataje}`}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">{p.cantidad}</td>
                      <td className="px-4 py-3 text-sm font-medium">${p.total.toFixed(2)}</td>
                      <td className="px-4 py-3 text-sm text-blue-600">${p.anticipo_pagado.toFixed(2)}</td>
                      <td className="px-4 py-3 text-sm text-green-600">${p.saldo_pendiente.toFixed(2)}</td>
                      <td className="px-4 py-3 text-sm">
                        {(userRole === 'admin' || userRole === 'owner') ? (
                          <select
                            value={p.estado}
                            onChange={(e) => actualizarEstado(p.id, e.target.value)}
                            className={`px-2 py-1 rounded-full text-xs font-medium border-0 ${getEstadoColor(p.estado)}`}
                          >
                            <option value="pendiente">Pendiente</option>
                            <option value="confirmado">Confirmado</option>
                            <option value="en_proceso">En Proceso</option>
                            <option value="listo">Listo</option>
                            <option value="entregado">Entregado</option>
                            <option value="cancelado">Cancelado</option>
                          </select>
                        ) : (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEstadoColor(p.estado)}`}>
                            {getEstadoTexto(p.estado)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => verTicket(p)}
                            className="text-purple-600 hover:text-purple-800 text-xs"
                            title="Ver ticket"
                          >
                            🎫 Ticket
                          </button>
                          {p.saldo_pendiente > 0 && (
                            <button
                              onClick={() => abrirModalPago(p)}
                              className="text-purple-600 hover:text-purple-800 text-xs"
                            >
                              Pagar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Messages */}
        {msg && (
          <div className={`p-3 rounded-lg ${msg.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {msg}
          </div>
        )}
      </div>

      {/* Modal de Pago */}
      {showPagoModal && pedidoSeleccionado && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Registrar Pago</h3>
            <div className="mb-4">
              <p className="text-gray-700 mb-2">
                <strong>Cliente:</strong> {pedidoSeleccionado.cliente_nombre}
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Producto:</strong> {pedidoSeleccionado.producto.name}
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Saldo pendiente:</strong> ${pedidoSeleccionado.saldo_pendiente.toFixed(2)}
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Monto</label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  value={montoPago}
                  onChange={e => setMontoPago(e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Método de pago</label>
                <select
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  value={metodoPago}
                  onChange={e => setMetodoPago(e.target.value)}
                >
                  <option value="efectivo">Efectivo</option>
                  <option value="tarjeta">Tarjeta</option>
                  <option value="transferencia">Transferencia</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Tipo de pago</label>
                <select
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  value={tipoPago}
                  onChange={e => setTipoPago(e.target.value)}
                >
                  <option value="saldo">Saldo pendiente</option>
                  <option value="anticipo">Anticipo adicional</option>
                  <option value="total">Pago total</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowPagoModal(false)}
                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                onClick={registrarPago}
                className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700"
              >
                Registrar Pago
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}

