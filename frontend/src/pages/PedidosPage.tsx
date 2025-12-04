import { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'
import { getLogoAsBase64, generatePedidoTicketHTML, openAndPrintTicket, saveTicket } from '../utils/ticketGenerator'

type ProductoPedido = { 
  id: number
  modelo: string  // Renombrado de "name"
  nombre?: string  // Renombrado de "tipo_joya"
  precio: number  // Renombrado de "price"
  cost_price?: number
  milimetros?: string
  default_discount_pct?: number
  // Campos específicos de joyería
  codigo: string  // Requerido
  marca?: string
  color?: string
  quilataje?: string
  base?: string
  talla?: string
  peso?: string
  peso_gramos?: number
  precio_manual?: number
  // Campos específicos para pedidos
  anticipo_sugerido?: number
  disponible: boolean
  active: boolean
}

type PedidoItem = { 
  producto: ProductoPedido
  cantidad: number
}

type User = {
  id: number
  email: string
}

type MetalRate = {
  id: number
  metal_type: string
  tipo: string
  rate_per_gram: number
}

export default function PedidosPage() {
  const [productos, setProductos] = useState<ProductoPedido[]>([])
  const [allProductos, setAllProductos] = useState<ProductoPedido[]>([])
  const [metalRates, setMetalRates] = useState<MetalRate[]>([])
  const [metalRatesPedido, setMetalRatesPedido] = useState<MetalRate[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [cart, setCart] = useState<PedidoItem[]>([])
  const [msg, setMsg] = useState('')
  
  // Filtros
  const [quilatajeFilter, setQuilatajeFilter] = useState('')
  const [modeloFilter, setModeloFilter] = useState('')
  const [tallaFilter, setTallaFilter] = useState('')
  
  // Información del cliente
  const [clienteNombre, setClienteNombre] = useState('')
  const [clienteTelefono, setClienteTelefono] = useState('')
  const [notasCliente, setNotasCliente] = useState('')
  
  // Vendedor
  const [vendedorId, setVendedorId] = useState('')
  
  // Tipo de pedido y métodos de pago
  const [tipoPedido, setTipoPedido] = useState<'contado' | 'apartado'>('apartado')
  const [metodoPagoEfectivo, setMetodoPagoEfectivo] = useState('')
  const [metodoPagoTarjeta, setMetodoPagoTarjeta] = useState('')
  
  // Modal de confirmación para agregar producto
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [productoToAdd, setProductoToAdd] = useState<ProductoPedido | null>(null)
  
  // Modal de confirmación para crear pedido
  const [showCheckoutModal, setShowCheckoutModal] = useState(false)
  
  // Modal para crear producto
  const [showCreateProductModal, setShowCreateProductModal] = useState(false)
  const [editingProduct, setEditingProduct] = useState<ProductoPedido | null>(null)
  // Estados para importación/exportación
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importMode, setImportMode] = useState<'add' | 'replace'>('add')
  const [importing, setImporting] = useState(false)
  const [userRole, setUserRole] = useState<string>('')

  // Estados para descuento VIP
  const [showVipModal, setShowVipModal] = useState(false)
  const [vipDiscount, setVipDiscount] = useState('')
  
  const [newProduct, setNewProduct] = useState({
    modelo: '',
    nombre: '',
    precio: '',
    cost_price: '',
    milimetros: '',
    default_discount_pct: '',
    // Campos específicos de joyería
    codigo: '',
    marca: '',
    color: '',
    quilataje: '',
    base: '',
    talla: '',
    peso: '',
    peso_gramos: '',
    precio_manual: '',
    // Campos específicos para pedidos
    anticipo_sugerido: '',
    disponible: true
  })
  
  const searchRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    console.log('PedidosPage useEffect - checking auth...')
    console.log('Access token exists:', !!localStorage.getItem('access'))
    console.log('Refresh token exists:', !!localStorage.getItem('refresh'))
    console.log('Tenant:', localStorage.getItem('tenant'))
    console.log('Role:', localStorage.getItem('role'))
    
    if (!localStorage.getItem('access')) {
      console.log('No access token, redirecting to login...')
      window.location.href = '/login'
      return
    }
    
    // Verificar si el token es válido haciendo una petición de prueba
    const verifyAuth = async () => {
      try {
        await api.get('/products/')
        console.log('Auth verification successful')
      } catch (error: any) {
        console.log('Auth verification failed:', error.response?.status)
        if (error.response?.status === 401) {
          console.log('Token invalid, redirecting to login...')
          localStorage.clear()
          window.location.href = '/login'
          return
        }
      }
    }
    
    verifyAuth()
    setUserRole(localStorage.getItem('role') || '')
    loadProductos()
    loadUsers()
    loadMetalRates()
  }, [])
  
  useEffect(() => {
    applyLocalFilters(allProductos)
  }, [quilatajeFilter, modeloFilter, tallaFilter])

  // Calcular precio y costo automáticamente cuando cambie quilataje o peso
  useEffect(() => {
    if (!newProduct.quilataje || !newProduct.peso_gramos) {
      return
    }

    const peso = parseFloat(newProduct.peso_gramos.toString())
    if (isNaN(peso) || peso <= 0) return

    // Buscar tasa de precio para el quilataje seleccionado
    const tasaPrecio = metalRatesPedido.find(
      r => r.tipo === 'precio' && r.metal_type === newProduct.quilataje
    )

    // Buscar tasa de costo para el quilataje seleccionado
    const tasaCosto = metalRatesPedido.find(
      r => r.tipo === 'costo' && r.metal_type === newProduct.quilataje
    )

    const updates: any = {}
    
    if (tasaPrecio) {
      const precioCalculado = peso * tasaPrecio.rate_per_gram
      updates.precio = precioCalculado.toFixed(2)
    }
    
    if (tasaCosto) {
      const costoCalculado = peso * tasaCosto.rate_per_gram
      updates.cost_price = costoCalculado.toFixed(2)
    }

    if (Object.keys(updates).length > 0) {
      setNewProduct(prev => ({
        ...prev,
        ...updates
      }))
    }
  }, [newProduct.quilataje, newProduct.peso_gramos, metalRatesPedido])

  const loadMetalRates = async () => {
    try {
      const r = await api.get('/metal-rates')
      setMetalRates(r.data || [])
      
      // También cargar tasas de pedido
      const rPedido = await api.get('/tasas-pedido/')
      setMetalRatesPedido(rPedido.data || [])
    } catch (e) {
      console.error('Error loading metal rates:', e)
    }
  }
  
  const applyLocalFilters = (productList: ProductoPedido[]) => {
    let filtered = productList

    // Filtrar por quilataje
    if (quilatajeFilter) {
      filtered = filtered.filter(p => p.quilataje === quilatajeFilter)
    }

    // Filtrar por modelo
    if (modeloFilter.trim()) {
      filtered = filtered.filter(p => 
        p.modelo && p.modelo.toLowerCase().includes(modeloFilter.toLowerCase())
      )
    }

    // Filtrar por talla
    if (tallaFilter.trim()) {
      const tallaSearch = tallaFilter.trim().toLowerCase()
      filtered = filtered.filter(p => {
        if (!p.talla) return false
        const tallaStr = String(p.talla).toLowerCase()
        return tallaStr.includes(tallaSearch)
      })
    }

    setProductos(filtered)
  }

  const loadProductos = async (q = '') => {
    const qs = new URLSearchParams()
    qs.set('limit', '1000')  // Límite muy alto para cargar todos los productos
    qs.set('activo', 'true')
    if (q) qs.set('q', q)
    try {
      const r = await api.get(`/productos-pedido/?${qs.toString()}`)
      console.log('Productos cargados:', r.data.length)
      setAllProductos(r.data)
      applyLocalFilters(r.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error cargando productos')
    }
  }

  const loadUsers = async () => {
    try {
      const r = await api.get('/admin/users')
      setUsers(r.data || [])
    } catch (e) {
      console.error('Error loading users:', e)
    }
  }

  const addToCart = (p: ProductoPedido) => {
    setProductoToAdd(p)
    setShowConfirmModal(true)
  }

  const confirmAddToCart = () => {
    if (!productoToAdd) return
    
    setCart(prev => {
      const idx = prev.findIndex(ci => ci.producto.id === productoToAdd.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = { ...next[idx], cantidad: next[idx].cantidad + 1 }
        return next
      }
      return [...prev, { producto: productoToAdd, cantidad: 1 }]
    })
    
    setShowConfirmModal(false)
    setProductoToAdd(null)
  }

  const cancelAddToCart = () => {
    setShowConfirmModal(false)
    setProductoToAdd(null)
  }

  const updateQty = (id: number, qty: number) => {
    setCart(prev => prev.map(ci => 
      ci.producto.id === id ? { ...ci, cantidad: Math.max(1, qty) } : ci
    ))
  }

  const removeFromCart = (id: number) => {
    setCart(prev => prev.filter(ci => ci.producto.id !== id))
  }

  const clearCart = () => {
    setCart([])
  }

  const getTotal = () => {
    return Math.ceil(cart.reduce((sum, ci) => sum + (parseFloat(ci.producto.precio.toString()) * ci.cantidad), 0))
  }

  const getTotalWithDiscount = () => {
    const subtotal = getTotal()
    const discountAmount = vipDiscount ? (subtotal * parseFloat(vipDiscount) / 100) : 0
    return Math.ceil(subtotal - discountAmount)
  }

  const applyVipDiscount = () => {
    const discount = parseFloat(vipDiscount)
    if (isNaN(discount) || discount < 0 || discount > 100) {
      setMsg('El descuento VIP debe ser un porcentaje entre 0 y 100')
      return
    }
    setShowVipModal(false)
    setMsg(`✅ Descuento VIP del ${discount}% aplicado`)
    setTimeout(() => setMsg(''), 3000)
  }

  const removeVipDiscount = () => {
    setVipDiscount('')
    setMsg('✅ Descuento VIP removido')
    setTimeout(() => setMsg(''), 3000)
  }

  const createProduct = async () => {
    if (!newProduct.codigo.trim()) {
      setMsg('El código es requerido')
      return
    }

    try {
      const productData = {
        modelo: newProduct.modelo,
        nombre: newProduct.nombre || null,
        codigo: newProduct.codigo,  // Ahora es requerido
        marca: newProduct.marca || null,
        color: newProduct.color || null,
        quilataje: newProduct.quilataje || null,
        base: newProduct.base || null,
        talla: newProduct.talla || null,
        peso: newProduct.peso || null,
        peso_gramos: newProduct.peso_gramos ? parseFloat(newProduct.peso_gramos) : null,
        precio: newProduct.precio ? parseFloat(newProduct.precio) : 0,
        cost_price: newProduct.cost_price ? parseFloat(newProduct.cost_price) : null,
        precio_manual: newProduct.precio_manual ? parseFloat(newProduct.precio_manual) : null,
        milimetros: newProduct.milimetros || null,
        default_discount_pct: newProduct.default_discount_pct ? parseFloat(newProduct.default_discount_pct) : null,
        anticipo_sugerido: newProduct.anticipo_sugerido ? parseFloat(newProduct.anticipo_sugerido) : null,
        disponible: newProduct.disponible
      }
      
      if (editingProduct) {
        // Editar producto existente
        await api.put(`/productos-pedido/${editingProduct.id}`, productData)
        setMsg('✅ Producto actualizado exitosamente')
      } else {
        // Crear nuevo producto
        await api.post('/productos-pedido/', productData)
        setMsg('✅ Producto creado exitosamente')
      }
      
      setShowCreateProductModal(false)
      setEditingProduct(null)
      setNewProduct({
        modelo: '',
        nombre: '',
        codigo: '',
        marca: '',
        color: '',
        quilataje: '',
        base: '',
        talla: '',
        peso: '',
        peso_gramos: '',
        precio: '',
        cost_price: '',
        precio_manual: '',
        milimetros: '',
        default_discount_pct: '',
        anticipo_sugerido: '',
        disponible: true
      })
      
      loadProductos()
      
      setTimeout(() => setMsg(''), 3000)
      
    } catch (e: any) {
      console.error('Error creating/updating product:', e?.response?.data)
      const detail = e?.response?.data?.detail
      if (Array.isArray(detail)) {
        // Manejar errores de validación de Pydantic
        const errorMessages = detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join(', ')
        setMsg(`Error de validación: ${errorMessages}`)
      } else {
        setMsg(detail || 'Error procesando producto')
      }
    }
  }

  const editProduct = (product: ProductoPedido) => {
    setEditingProduct(product)
    setNewProduct({
      modelo: product.modelo,
      nombre: product.nombre || '',
      precio: product.precio.toString(),
      cost_price: product.cost_price?.toString() || '',
      milimetros: product.milimetros || '',
      default_discount_pct: product.default_discount_pct?.toString() || '',
      codigo: product.codigo || '',
      marca: product.marca || '',
      color: product.color || '',
      quilataje: product.quilataje || '',
      base: product.base || '',
      talla: product.talla || '',
      peso: product.peso || '',
      peso_gramos: product.peso_gramos?.toString() || '',
      precio_manual: product.precio_manual?.toString() || '',
      anticipo_sugerido: product.anticipo_sugerido?.toString() || '',
      disponible: product.disponible
    })
    setShowCreateProductModal(true)
  }

  const deleteProduct = async (id: number) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este producto?')) return
    
    try {
      await api.delete(`/productos-pedido/${id}`)
      setMsg('✅ Producto eliminado exitosamente')
      loadProductos()
      setTimeout(() => setMsg(''), 3000)
    } catch (error) {
      console.error('Error deleting product:', error)
      setMsg('Error al eliminar el producto')
    }
  }

  const handleImport = async () => {
    if (!importFile) {
      setMsg('Selecciona un archivo Excel')
      return
    }

    setImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', importFile)
      formData.append('mode', importMode)

      const response = await api.post('/productos-pedido/import/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setMsg(`✅ ${response.data.message}`)
      setShowImportModal(false)
      setImportFile(null)
      loadProductos()
      
      setTimeout(() => setMsg(''), 5000)
      
    } catch (e: any) {
      console.error('Import error:', e?.response?.data)
      const detail = e?.response?.data?.detail
      if (Array.isArray(detail)) {
        const errorMessages = detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join(', ')
        setMsg(`Error de validación: ${errorMessages}`)
      } else {
        setMsg(detail || 'Error importando productos')
      }
    } finally {
      setImporting(false)
    }
  }

  const handleExport = async () => {
    try {
      const response = await api.get('/productos-pedido/export/', {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'productos_pedido.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      setMsg('✅ Archivo exportado exitosamente')
      setTimeout(() => setMsg(''), 3000)
      
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error exportando productos')
    }
  }

  const checkout = async () => {
    if (cart.length === 0) {
      setMsg('El carrito está vacío')
      return
    }
    
    if (!clienteNombre.trim()) {
      setMsg('El nombre del cliente es requerido')
      return
    }
    
    if (!vendedorId) {
      setMsg('Debe seleccionar un vendedor')
      return
    }

    // Validar anticipo para pedidos apartados
    if (tipoPedido === 'apartado') {
      const anticipo = (parseFloat(metodoPagoEfectivo) || 0) + (parseFloat(metodoPagoTarjeta) || 0)
      if (anticipo <= 0) {
        setMsg('El anticipo inicial debe ser mayor a 0 para pedidos apartados')
        return
      }
    }

    try {
      console.log('Starting checkout process...')
      console.log('Access token:', localStorage.getItem('access'))
      console.log('Tenant:', localStorage.getItem('tenant'))
      
      // Crear un solo pedido con todos los productos del carrito
      const subtotal = cart.reduce((sum, item) => sum + (item.producto.precio * item.cantidad), 0)
      const totalConDescuento = vipDiscount ? subtotal * (1 - parseFloat(vipDiscount) / 100) : subtotal

      const pedidoData = {
        items: cart.map(item => ({
          producto_pedido_id: item.producto.id,
          cantidad: item.cantidad
        })),
        cliente_nombre: clienteNombre,
        cliente_telefono: clienteTelefono || null,
        tipo_pedido: tipoPedido,
        anticipo_pagado: (parseFloat(metodoPagoEfectivo) || 0) + (parseFloat(metodoPagoTarjeta) || 0),
        metodo_pago_efectivo: parseFloat(metodoPagoEfectivo) || 0,
        metodo_pago_tarjeta: parseFloat(metodoPagoTarjeta) || 0,
        notas_cliente: notasCliente || null,
        user_id: vendedorId ? parseInt(vendedorId) : undefined,
        // El total ya incluye el descuento VIP aplicado
        total: Math.ceil(totalConDescuento)
      }
      
      console.log('Sending pedido data:', pedidoData)
      const response = await api.post('/pedidos/', pedidoData)
      
      // Generate ticket for the pedido (both apartado and contado)
      if (response.data) {
        try {
          const pedido = response.data
          
          const logoBase64 = await getLogoAsBase64()
          const vendedorEmail = users.find(u => u.id === pedido.user_id)?.email
          
          // Determine payment method for initial ticket
          const efectivo = parseFloat(metodoPagoEfectivo) || 0
          const tarjeta = parseFloat(metodoPagoTarjeta) || 0
          let paymentMethod = 'N/A'
          
          if (efectivo > 0 && tarjeta > 0) {
            paymentMethod = 'mixto'
          } else if (efectivo > 0) {
            paymentMethod = 'efectivo'
          } else if (tarjeta > 0) {
            paymentMethod = 'tarjeta'
          }
          
          const ticketHTML = generatePedidoTicketHTML({
            pedido,
            items: pedido.items || (pedido.producto ? [pedido.producto] : []),
            vendedorEmail,
            paymentData: tipoPedido === 'apartado' ? {
              amount: pedido.anticipo_pagado,
              method: paymentMethod,
              previousPaid: 0,
              newPaid: pedido.anticipo_pagado,
              previousBalance: pedido.total,
              newBalance: pedido.saldo_pendiente,
              efectivo: efectivo > 0 ? efectivo : undefined,
              tarjeta: tarjeta > 0 ? tarjeta : undefined
            } : {
              amount: pedido.total,
              method: paymentMethod,
              previousPaid: 0,
              newPaid: pedido.total,
              previousBalance: pedido.total,
              newBalance: 0,
              efectivo: efectivo > 0 ? efectivo : undefined,
              tarjeta: tarjeta > 0 ? tarjeta : undefined
            },
            logoBase64
          })
          
          // Save ticket to database
          await saveTicket({
            pedidoId: pedido.id,
            kind: 'payment',
            html: ticketHTML
          })
          
          // Print ticket
          openAndPrintTicket(ticketHTML)
        } catch (ticketError) {
          console.error('Error generating initial ticket:', ticketError)
          // Don't fail the order if ticket fails
        }
      }
      
      setMsg('✅ Pedido creado exitosamente')
      clearCart()
      setClienteNombre('')
      setClienteTelefono('')
      setNotasCliente('')
      setVendedorId('')
      setMetodoPagoEfectivo('')
      setMetodoPagoTarjeta('')
      setTipoPedido('apartado')
      setVipDiscount('')
      
      // Limpiar mensaje después de 3 segundos
      setTimeout(() => setMsg(''), 3000)
      
    } catch (e: any) {
      console.error('Checkout error:', e)
      console.error('Error response:', e?.response)
      const detail = e?.response?.data?.detail
      if (Array.isArray(detail)) {
        // Manejar errores de validación de Pydantic
        const errorMessages = detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join(', ')
        setMsg(`Error de validación: ${errorMessages}`)
      } else {
        setMsg(detail || 'Error creando pedido')
      }
    }
  }

  return (
    <Layout>
      <div className="grid grid-cols-12 gap-6">
        {/* Left: Cart & Checkout */}
        <div className="col-span-8 space-y-4">
          {/* Header */}
          <div className="bg-purple-50 rounded-lg p-4">
            <h1 className="text-2xl font-bold text-purple-800">📋 Productos sobre Pedido</h1>
            <p className="text-purple-600">Venta de productos que requieren pedido especial</p>
          </div>

          {/* Customer Info */}
          <div className="bg-amber-50 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-semibold">Información del Cliente</h3>
              <button
                onClick={() => setShowVipModal(true)}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                  vipDiscount
                    ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                    : 'bg-gray-600 text-white hover:bg-gray-700'
                }`}
              >
                {vipDiscount ? `VIP -${vipDiscount}%` : 'VIP'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input
                className="border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Nombre del cliente *"
                value={clienteNombre}
                onChange={e => setClienteNombre(e.target.value)}
              />
              <input
                className="border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Teléfono"
                value={clienteTelefono}
                onChange={e => setClienteTelefono(e.target.value)}
              />
              <select
                className="border border-gray-300 rounded-lg px-3 py-2"
                value={vendedorId}
                onChange={e => setVendedorId(e.target.value)}
              >
                <option value="">Seleccionar vendedor *</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>
                    {u.email}
                  </option>
                ))}
              </select>
              <input
                className="border border-gray-300 rounded-lg px-3 py-2 col-span-2"
                placeholder="Notas del cliente"
                value={notasCliente}
                onChange={e => setNotasCliente(e.target.value)}
              />
            </div>
          </div>

          {/* Tipo de Pedido y Pago */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-semibold mb-3">Tipo de Pedido</h3>
            
            {/* Selector de Tipo */}
            <div className="flex gap-4 mb-4">
              <button
                onClick={() => setTipoPedido('contado')}
                className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                  tipoPedido === 'contado'
                    ? 'bg-green-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-green-400'
                }`}
              >
                💵 Pedido de Contado
              </button>
              <button
                onClick={() => setTipoPedido('apartado')}
                className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                  tipoPedido === 'apartado'
                    ? 'bg-orange-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-orange-400'
                }`}
              >
                📌 Pedido Apartado
              </button>
            </div>

            {/* Campos de Pago según tipo */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Efectivo
                </label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="$0.00"
                  type="number"
                  step="0.01"
                  value={metodoPagoEfectivo}
                  onChange={e => setMetodoPagoEfectivo(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tarjeta
                </label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="$0.00"
                  type="number"
                  step="0.01"
                  value={metodoPagoTarjeta}
                  onChange={e => setMetodoPagoTarjeta(e.target.value)}
                />
              </div>
              <div className={`col-span-2 p-3 rounded-lg ${tipoPedido === 'contado' ? 'bg-green-100' : 'bg-orange-100'}`}>
                {vipDiscount && (
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium">Subtotal:</span>
                    <span className="font-bold">${getTotal()}</span>
                  </div>
                )}
                {vipDiscount && (
                  <div className="flex justify-between text-sm mb-1 text-red-600">
                    <span className="font-medium">Descuento VIP (-{vipDiscount}%):</span>
                    <span className="font-bold">-${Math.ceil(getTotal() * parseFloat(vipDiscount) / 100)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="font-medium">Total del pedido:</span>
                  <span className="font-bold">${getTotalWithDiscount()}</span>
                </div>
                <div className="flex justify-between text-sm mt-1">
                  <span className="font-medium">{tipoPedido === 'contado' ? 'Total pagado:' : 'Anticipo:'}</span>
                  <span className={`font-bold ${tipoPedido === 'contado' ? 'text-green-700' : 'text-orange-700'}`}>
                    ${Math.ceil((parseFloat(metodoPagoEfectivo) || 0) + (parseFloat(metodoPagoTarjeta) || 0))}
                  </span>
                </div>
                {tipoPedido === 'apartado' && (
                  <div className="flex justify-between text-sm mt-1">
                    <span className="font-medium">Saldo pendiente:</span>
                    <span className="font-bold text-red-700">
                      ${Math.ceil(getTotalWithDiscount() - ((parseFloat(metodoPagoEfectivo) || 0) + (parseFloat(metodoPagoTarjeta) || 0)))}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Cart */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Carrito de Pedidos</h3>
              {cart.length > 0 && (
                <button
                  onClick={clearCart}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Limpiar carrito
                </button>
              )}
            </div>
            
            {cart.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                No hay productos en el carrito
              </div>
            ) : (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {cart.map(ci => (
                  <div key={ci.producto.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">{ci.producto.modelo}</div>
                      <div className="text-sm text-gray-600">
                        {ci.producto.nombre && `${ci.producto.nombre} - `}
                        {ci.producto.codigo && `${ci.producto.codigo} - `}
                        {ci.producto.marca && `${ci.producto.marca} - `}
                        {ci.producto.color && `${ci.producto.color} - `}
                        {ci.producto.quilataje && `${ci.producto.quilataje} - `}
                        {ci.producto.talla && `Talla ${ci.producto.talla}`}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => updateQty(ci.producto.id, ci.cantidad - 1)}
                          className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300"
                        >
                          -
                        </button>
                        <span className="w-8 text-center">{ci.cantidad}</span>
                        <button
                          onClick={() => updateQty(ci.producto.id, ci.cantidad + 1)}
                          className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center hover:bg-gray-300"
                        >
                          +
                        </button>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">${(parseFloat(ci.producto.precio?.toString() || '0') * ci.cantidad).toFixed(2)}</div>
                        <div className="text-xs text-gray-500">${ci.producto.precio || 0} c/u</div>
                      </div>
                      <button
                        onClick={() => removeFromCart(ci.producto.id)}
                        className="text-red-600 hover:text-red-800 ml-2"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Checkout Button */}
          {cart.length > 0 && (
            <button
              onClick={() => {
                if (!clienteNombre.trim()) {
                  setMsg('El nombre del cliente es requerido')
                  return
                }
                if (!vendedorId) {
                  setMsg('Debe seleccionar un vendedor')
                  return
                }
                setShowCheckoutModal(true)
              }}
              disabled={cart.length === 0 || !clienteNombre.trim() || !vendedorId}
              className="w-full bg-purple-600 text-white py-4 rounded-lg text-xl font-bold hover:bg-purple-700 disabled:bg-gray-400"
            >
              📋 Crear Pedido
            </button>
          )}

          {/* Messages */}
          {msg && (
            <div className={`p-3 rounded-lg ${msg.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {msg}
            </div>
          )}
        </div>

        {/* Right: Product Selection */}
        <div className="col-span-4 flex flex-col space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Productos Disponibles</h2>
            <div className="flex space-x-2">
              {(userRole === 'admin' || userRole === 'owner') && (
                <>
                  <button
                    onClick={() => setShowImportModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                  >
                    📥 Importar Excel
                  </button>
                  <button
                    onClick={handleExport}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                  >
                    📤 Exportar Excel
                  </button>
                </>
              )}
              {(userRole === 'admin' || userRole === 'owner') && (
                <button
                  onClick={() => {
                    setEditingProduct(null)
                    setNewProduct({
                      modelo: '',
                      nombre: '',
                      precio: '',
                      cost_price: '',
                      milimetros: '',
                      default_discount_pct: '',
                      codigo: '',
                      marca: '',
                      color: '',
                      quilataje: '',
                      base: '',
                      talla: '',
                      peso: '',
                      peso_gramos: '',
                      precio_manual: '',
                      anticipo_sugerido: '',
                      disponible: true
                    })
                    setShowCreateProductModal(true)
                  }}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                >
                  + Crear Producto
                </button>
              )}
            </div>
          </div>
          
          {/* Product Search and Filters */}
          <div className="space-y-3">
            {/* Main search bar */}
            <div>
              <label className="block text-sm font-medium mb-1">Buscar producto</label>
              <input
                ref={searchRef}
                className="w-full border border-gray-300 rounded-lg px-4 py-2"
                placeholder="Buscar por nombre, código, modelo, color..."
                onChange={e => loadProductos(e.target.value)}
              />
            </div>

            {/* Specific filters */}
            <div className="grid grid-cols-4 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Quilataje</label>
                <select
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  value={quilatajeFilter}
                  onChange={e => setQuilatajeFilter(e.target.value)}
                >
                  <option value="">Todos</option>
                  {metalRates.map(mr => (
                    <option key={mr.id} value={mr.metal_type}>
                      {mr.metal_type}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Modelo</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="Filtrar por modelo..."
                  value={modeloFilter}
                  onChange={e => setModeloFilter(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Talla</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="Filtrar por talla..."
                  value={tallaFilter}
                  onChange={e => setTallaFilter(e.target.value)}
                />
              </div>

              <div className="flex items-end">
                <button
                  className="w-full bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 text-sm"
                  onClick={() => {
                    setQuilatajeFilter('')
                    setModeloFilter('')
                    setTallaFilter('')
                  }}
                >
                  🔄 Limpiar
                </button>
              </div>
            </div>
          </div>
          
          {/* Product List */}
          <div className="flex-1 overflow-y-auto border rounded-lg p-2 bg-gray-50">
            <div className="grid grid-cols-1 gap-2">
              {productos.map(p => (
                <div
                  key={p.id}
                  className="bg-white border border-gray-300 rounded-lg p-3 hover:bg-purple-50"
                >
                  <div className="flex justify-between items-start">
                    <button
                      onClick={() => addToCart(p)}
                      disabled={!p.disponible}
                      className="flex-1 text-left disabled:cursor-not-allowed"
                    >
                      <div className="font-medium text-sm">{p.modelo}</div>
                      <div className="text-purple-600 font-bold">${p.precio}</div>
                      <div className="text-xs text-gray-500">
                        {p.nombre && `${p.nombre} - `}
                        {p.codigo && `${p.codigo} - `}
                        {p.marca && `${p.marca} - `}
                        {p.color && `${p.color} - `}
                        {p.quilataje && `${p.quilataje}`}
                        {p.talla && ` - Talla: ${p.talla}`}
                      </div>
                      {!p.disponible && (
                        <div className="text-xs text-red-600 font-bold">No disponible</div>
                      )}
                    </button>
                    
                    {/* Botones de administrador */}
                    {(userRole === 'admin' || userRole === 'owner') && (
                      <div className="flex space-x-1 ml-2">
                        <button
                          onClick={() => editProduct(p)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                          title="Editar producto"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => deleteProduct(p.id)}
                          className="text-red-600 hover:text-red-800 text-sm"
                          title="Eliminar producto"
                        >
                          🗑️
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modal de Confirmación - Agregar Producto */}
      {showConfirmModal && productoToAdd && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirmar Producto sobre Pedido</h3>
            <div className="mb-4">
              <p className="text-gray-700 mb-2">
                <strong>Producto:</strong> {productoToAdd.nombre}
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Precio:</strong> ${productoToAdd.precio || 0}
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Tiempo de entrega:</strong> A convenir
              </p>
              {productoToAdd.modelo && (
                <p className="text-gray-700">
                  <strong>Modelo:</strong> {productoToAdd.modelo}
                </p>
              )}
            </div>
            <p className="text-gray-600 mb-6">
              ¿Deseas agregar este producto al carrito de pedidos?
            </p>
            <div className="flex gap-3">
              <button
                onClick={cancelAddToCart}
                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                onClick={confirmAddToCart}
                className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700"
              >
                Agregar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmación - Crear Pedido */}
      {showCheckoutModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">⚠️ Confirmar Creación de Pedido</h3>
            <div className="mb-4 space-y-2">
              <p className="text-gray-700">
                <strong>Cliente:</strong> {clienteNombre}
              </p>
              {clienteTelefono && (
                <p className="text-gray-700">
                  <strong>Teléfono:</strong> {clienteTelefono}
                </p>
              )}
              <p className="text-gray-700">
                <strong>Vendedor:</strong> {users.find(u => u.id.toString() === vendedorId)?.email || 'N/A'}
              </p>
              <p className="text-gray-700">
                <strong>Tipo:</strong> {tipoPedido === 'contado' ? 'Contado' : 'Apartado'}
              </p>
              <p className="text-gray-700">
                <strong>Productos:</strong> {cart.length} {cart.length === 1 ? 'producto' : 'productos'}
              </p>
              {vipDiscount && (
                <p className="text-gray-700">
                  <strong>Descuento VIP aplicado:</strong> -{vipDiscount}%
                </p>
              )}
              <p className="text-gray-700">
                <strong>Total final:</strong> ${getTotalWithDiscount()}
              </p>
              {(parseFloat(metodoPagoEfectivo) > 0 || parseFloat(metodoPagoTarjeta) > 0) && (
                <p className="text-gray-700">
                  <strong>Anticipo:</strong> ${Math.ceil((parseFloat(metodoPagoEfectivo) || 0) + (parseFloat(metodoPagoTarjeta) || 0))}
                </p>
              )}
            </div>
            <p className="text-gray-600 mb-6">
              ¿Confirmas que deseas crear este pedido? Esta acción generará el ticket correspondiente.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCheckoutModal(false)}
                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  setShowCheckoutModal(false)
                  checkout()
                }}
                className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700"
              >
                ✅ Confirmar Pedido
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Modal para descuento VIP */}
      {showVipModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">🎁 Descuento VIP</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Porcentaje de descuento (%)
              </label>
              <input
                type="number"
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="0"
                min="0"
                max="100"
                step="0.01"
                value={vipDiscount}
                onChange={e => setVipDiscount(e.target.value)}
              />
              {vipDiscount && (
                <div className="mt-3 p-3 bg-yellow-50 rounded-lg">
                  <div className="text-sm text-yellow-800">
                    <strong>Subtotal:</strong> ${getTotal()}<br/>
                    <strong>Descuento ({vipDiscount}%):</strong> -${Math.ceil(getTotal() * parseFloat(vipDiscount) / 100)}<br/>
                    <strong>Total con descuento:</strong> ${getTotalWithDiscount()}
                  </div>
                </div>
              )}
            </div>
            <div className="flex gap-3">
              {vipDiscount && (
                <button
                  onClick={removeVipDiscount}
                  className="flex-1 bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600"
                >
                  Remover Descuento
                </button>
              )}
              <button
                onClick={() => setShowVipModal(false)}
                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                onClick={applyVipDiscount}
                className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded-lg hover:bg-yellow-700"
              >
                Aplicar Descuento
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal para crear producto */}
      {showCreateProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-sm sm:max-w-md md:max-w-lg lg:max-w-xl w-full h-[95vh] sm:h-[90vh] flex flex-col">
            <div className="flex-shrink-0 p-3 sm:p-6 border-b">
              <h3 className="text-lg sm:text-xl font-semibold">
                {editingProduct ? 'Editar Producto' : 'Crear Nuevo Producto'}
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-3 sm:p-6 min-h-0">
              <div className="space-y-3">
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Modelo"
                value={newProduct.modelo}
                onChange={e => setNewProduct({...newProduct, modelo: e.target.value})}
              />
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Nombre (tipo de joya)"
                value={newProduct.nombre}
                onChange={e => setNewProduct({...newProduct, nombre: e.target.value})}
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Código *"
                  value={newProduct.codigo}
                  onChange={e => setNewProduct({...newProduct, codigo: e.target.value})}
                  required
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Peso (gramos)"
                  type="number"
                  step="0.001"
                  value={newProduct.peso_gramos}
                  onChange={e => setNewProduct({...newProduct, peso_gramos: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Quilataje (ej: 10k, 14k)"
                  value={newProduct.quilataje}
                  onChange={e => setNewProduct({...newProduct, quilataje: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Color"
                  value={newProduct.color}
                  onChange={e => setNewProduct({...newProduct, color: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Talla"
                  value={newProduct.talla}
                  onChange={e => setNewProduct({...newProduct, talla: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Anticipo sugerido"
                  type="number"
                  step="0.01"
                  value={newProduct.anticipo_sugerido}
                  onChange={e => setNewProduct({...newProduct, anticipo_sugerido: e.target.value})}
                />
              </div>
              
              {/* Tasas de Metal (Dropdowns) */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-green-700 mb-1">Tasa de Precio</label>
                  <select
                    className="w-full border border-green-300 rounded-lg px-3 py-2 bg-green-50"
                    value={newProduct.quilataje}
                    onChange={e => setNewProduct({...newProduct, quilataje: e.target.value})}
                  >
                    <option value="">Seleccionar tasa de precio</option>
                    {metalRatesPedido.filter(r => r.tipo === 'precio').map(rate => (
                      <option key={rate.id} value={rate.metal_type}>
                        {rate.metal_type} - ${rate.rate_per_gram}/g
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-blue-700 mb-1">Tasa de Costo</label>
                  <select
                    className="w-full border border-blue-300 rounded-lg px-3 py-2 bg-blue-50"
                    value={newProduct.quilataje}
                    onChange={e => setNewProduct({...newProduct, quilataje: e.target.value})}
                  >
                    <option value="">Seleccionar tasa de costo</option>
                    {metalRatesPedido.filter(r => r.tipo === 'costo').map(rate => (
                      <option key={rate.id} value={rate.metal_type}>
                        {rate.metal_type} - ${rate.rate_per_gram}/g
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Campos calculados */}
              <div className="grid grid-cols-2 gap-3">
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2 bg-green-50"
                  placeholder="Precio (auto)"
                  type="number"
                  step="0.01"
                  value={newProduct.precio}
                  onChange={e => setNewProduct({...newProduct, precio: e.target.value})}
                  title="Se calcula automáticamente si hay tasa de precio para el quilataje"
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2 bg-blue-50"
                  placeholder="Costo (auto)"
                  type="number"
                  step="0.01"
                  value={newProduct.cost_price}
                  onChange={e => setNewProduct({...newProduct, cost_price: e.target.value})}
                  title="Se calcula automáticamente si hay tasa de costo para el quilataje"
                />
              </div>
              <div className="text-xs text-purple-600 bg-purple-50 p-2 rounded">
                💡 <strong>Cálculo automático:</strong> Precio y costo se calculan automáticamente cuando ingresas quilataje y peso en gramos (si existen tasas registradas)
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="disponible"
                  checked={newProduct.disponible}
                  onChange={e => setNewProduct({...newProduct, disponible: e.target.checked})}
                />
                <label htmlFor="disponible" className="text-sm">Disponible para pedidos</label>
              </div>

            {/* Tasas de Metal de Pedidos */}
            {metalRatesPedido.length > 0 && (
              <div className="mt-4 space-y-3 border-t pt-4">
                <h4 className="text-sm font-semibold text-gray-700">📊 Tasas de Metal (Referencia)</h4>
                
                {/* Tasas de Precio */}
                {metalRatesPedido.filter(r => r.tipo === 'precio').length > 0 && (
                  <div className="bg-green-50 p-3 rounded-lg">
                    <h5 className="text-xs font-semibold text-green-800 mb-2">💰 Precio (Venta)</h5>
                    <div className="grid grid-cols-2 gap-2">
                      {metalRatesPedido.filter(r => r.tipo === 'precio').map(rate => (
                        <div key={rate.id} className="flex justify-between text-xs">
                          <span className="text-gray-700">{rate.metal_type}:</span>
                          <span className="font-semibold text-green-700">${rate.rate_per_gram.toFixed(2)}/g</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tasas de Costo */}
                {metalRatesPedido.filter(r => r.tipo === 'costo').length > 0 && (
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <h5 className="text-xs font-semibold text-blue-800 mb-2">🏭 Costo (Producción)</h5>
                    <div className="grid grid-cols-2 gap-2">
                      {metalRatesPedido.filter(r => r.tipo === 'costo').map(rate => (
                        <div key={rate.id} className="flex justify-between text-xs">
                          <span className="text-gray-700">{rate.metal_type}:</span>
                          <span className="font-semibold text-blue-700">${rate.rate_per_gram.toFixed(2)}/g</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            </div>

            <div className="flex-shrink-0 border-t p-3 sm:p-6 bg-gray-50 flex flex-col sm:flex-row gap-2 sm:justify-end">
                <button
                  onClick={() => setShowCreateProductModal(false)}
                  className="bg-gray-300 text-gray-700 px-4 sm:px-6 py-2 rounded-lg hover:bg-gray-400 order-2 sm:order-1"
                >
                  Cancelar
                </button>
                <button
                  onClick={createProduct}
                  className="bg-green-600 text-white px-4 sm:px-6 py-2 rounded-lg hover:bg-green-700 font-semibold order-1 sm:order-2"
                >
                  {editingProduct ? 'Actualizar Producto' : 'Crear Producto'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Modal para importar productos */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Importar Productos desde Excel</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Archivo Excel</label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Formatos soportados: .xlsx, .xls
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Modo de importación</label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="add"
                      checked={importMode === 'add'}
                      onChange={(e) => setImportMode(e.target.value as 'add' | 'replace')}
                      className="mr-2"
                    />
                    <span className="text-sm">Agregar productos (mantener existentes)</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="replace"
                      checked={importMode === 'replace'}
                      onChange={(e) => setImportMode(e.target.value as 'add' | 'replace')}
                      className="mr-2"
                    />
                    <span className="text-sm">Reemplazar productos (eliminar existentes)</span>
                  </label>
                </div>
              </div>
              
              <div className="bg-blue-50 p-3 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">Columnas requeridas:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• <strong>name</strong> - Nombre del producto</li>
                  <li>• <strong>price</strong> - Precio</li>
                </ul>
                <h4 className="font-medium text-blue-800 mb-2 mt-3">Columnas opcionales:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• codigo, marca, modelo, color, quilataje</li>
                  <li>• talla, milimetros, anticipo_sugerido</li>
                </ul>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowImportModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleImport}
                disabled={!importFile || importing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {importing ? 'Importando...' : 'Importar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}
