import { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type ProductoPedido = { 
  id: number
  name: string
  price: number
  cost_price?: number
  category?: string
  default_discount_pct?: number
  // Campos específicos de joyería
  codigo?: string
  marca?: string
  modelo?: string
  color?: string
  quilataje?: string
  base?: string
  tipo_joya?: string
  talla?: string
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

export default function PedidosPage() {
  const [productos, setProductos] = useState<ProductoPedido[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [cart, setCart] = useState<PedidoItem[]>([])
  const [msg, setMsg] = useState('')
  
  // Información del cliente
  const [clienteNombre, setClienteNombre] = useState('')
  const [clienteTelefono, setClienteTelefono] = useState('')
  const [clienteEmail, setClienteEmail] = useState('')
  const [notasCliente, setNotasCliente] = useState('')
  
  // Anticipo flexible
  const [anticipoPagado, setAnticipoPagado] = useState('')
  
  // Modal de confirmación
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [productoToAdd, setProductoToAdd] = useState<ProductoPedido | null>(null)
  
  // Modal para crear producto
  const [showCreateProductModal, setShowCreateProductModal] = useState(false)
  const [editingProduct, setEditingProduct] = useState<ProductoPedido | null>(null)
  // Estados para importación/exportación
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importMode, setImportMode] = useState<'add' | 'replace'>('add')
  const [importing, setImporting] = useState(false)
  const [userRole, setUserRole] = useState<string>('')
  
  const [newProduct, setNewProduct] = useState({
    name: '',
    price: '',
    cost_price: '',
    category: '',
    default_discount_pct: '',
    // Campos específicos de joyería
    codigo: '',
    marca: '',
    modelo: '',
    color: '',
    quilataje: '',
    base: '',
    tipo_joya: '',
    talla: '',
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
  }, [])

  const loadProductos = async (q = '') => {
    const qs = new URLSearchParams()
    qs.set('limit', '50')
    qs.set('activo', 'true')
    if (q) qs.set('q', q)
    try {
      const r = await api.get(`/productos-pedido/?${qs.toString()}`)
      setProductos(r.data)
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
    return cart.reduce((sum, ci) => sum + (parseFloat(ci.producto.price.toString()) * ci.cantidad), 0)
  }

  const getAnticipoRequerido = () => {
    const total = getTotal()
    if (cart.length === 0) return 0
    
    // Usar el anticipo sugerido del primer producto como referencia
    const primerProducto = cart[0].producto
    if (primerProducto.anticipo_sugerido) {
      return parseFloat(primerProducto.anticipo_sugerido.toString())
    }
    
    return 0 // Sin anticipo sugerido
  }

  const getSaldoPendiente = () => {
    const anticipo = parseFloat(anticipoPagado) || 0
    return getTotal() - anticipo
  }

  const createProduct = async () => {
    if (!newProduct.name.trim() || !newProduct.price) {
      setMsg('El nombre y precio son requeridos')
      return
    }

    try {
      const productData = {
        name: newProduct.name,
        codigo: newProduct.codigo || null,
        marca: newProduct.marca || null,
        modelo: newProduct.modelo || null,
        color: newProduct.color || null,
        quilataje: newProduct.quilataje || null,
        base: newProduct.base || null,
        tipo_joya: newProduct.tipo_joya || null,
        talla: newProduct.talla || null,
        peso_gramos: newProduct.peso_gramos ? parseFloat(newProduct.peso_gramos) : null,
        price: parseFloat(newProduct.price),
        cost_price: newProduct.cost_price ? parseFloat(newProduct.cost_price) : null,
        precio_manual: newProduct.precio_manual ? parseFloat(newProduct.precio_manual) : null,
        category: newProduct.category || null,
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
        name: '',
        codigo: '',
        marca: '',
        modelo: '',
        color: '',
        quilataje: '',
        base: '',
        tipo_joya: '',
        talla: '',
        peso_gramos: '',
        price: '',
        cost_price: '',
        precio_manual: '',
        category: '',
        default_discount_pct: '',
        anticipo_sugerido: '',
        disponible: true
      })
      
      loadProductos()
      
      setTimeout(() => setMsg(''), 3000)
      
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error procesando producto')
    }
  }

  const editProduct = (product: ProductoPedido) => {
    setEditingProduct(product)
    setNewProduct({
      name: product.name,
      price: product.price.toString(),
      cost_price: product.cost_price?.toString() || '',
      category: product.category || '',
      default_discount_pct: product.default_discount_pct?.toString() || '',
      codigo: product.codigo || '',
      marca: product.marca || '',
      modelo: product.modelo || '',
      color: product.color || '',
      quilataje: product.quilataje || '',
      base: product.base || '',
      tipo_joya: product.tipo_joya || '',
      talla: product.talla || '',
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
      setMsg(e?.response?.data?.detail || 'Error importando productos')
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

    try {
      console.log('Starting checkout process...')
      console.log('Access token:', localStorage.getItem('access'))
      console.log('Tenant:', localStorage.getItem('tenant'))
      
      // Crear pedido para cada producto en el carrito
      for (const item of cart) {
        const pedidoData = {
          producto_pedido_id: item.producto.id,
          cliente_nombre: clienteNombre,
          cliente_telefono: clienteTelefono || null,
          cliente_email: clienteEmail || null,
          cantidad: item.cantidad,
          anticipo_pagado: parseFloat(anticipoPagado) || 0,
          notas_cliente: notasCliente || null
        }
        
        console.log('Sending pedido data:', pedidoData)
        await api.post('/productos-pedido/pedidos/', pedidoData)
      }
      
      setMsg('✅ Pedido creado exitosamente')
      clearCart()
      setClienteNombre('')
      setClienteTelefono('')
      setClienteEmail('')
      setNotasCliente('')
      
      // Limpiar mensaje después de 3 segundos
      setTimeout(() => setMsg(''), 3000)
      
    } catch (e: any) {
      console.error('Checkout error:', e)
      console.error('Error response:', e?.response)
      setMsg(e?.response?.data?.detail || 'Error creando pedido')
    }
  }

  return (
    <Layout>
      <div className="grid grid-cols-12 gap-6 h-[calc(100vh-100px)]">
        {/* Left: Cart & Checkout */}
        <div className="col-span-8 flex flex-col space-y-4">
          {/* Header */}
          <div className="bg-purple-50 rounded-lg p-4">
            <h1 className="text-2xl font-bold text-purple-800">📋 Productos sobre Pedido</h1>
            <p className="text-purple-600">Venta de productos que requieren pedido especial</p>
          </div>

          {/* Customer Info */}
          <div className="bg-amber-50 rounded-lg p-4">
            <h3 className="font-semibold mb-2">Información del Cliente</h3>
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
              <input
                className="border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Email"
                type="email"
                value={clienteEmail}
                onChange={e => setClienteEmail(e.target.value)}
              />
              <input
                className="border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Anticipo pagado ($)"
                type="number"
                step="0.01"
                value={anticipoPagado}
                onChange={e => setAnticipoPagado(e.target.value)}
              />
              <input
                className="border border-gray-300 rounded-lg px-3 py-2 col-span-2"
                placeholder="Notas del cliente"
                value={notasCliente}
                onChange={e => setNotasCliente(e.target.value)}
              />
            </div>
          </div>

          {/* Cart */}
          <div className="flex-1 bg-white border rounded-lg p-4">
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
              <div className="space-y-3">
                {cart.map(ci => (
                  <div key={ci.producto.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium">{ci.producto.name}</div>
                      <div className="text-sm text-gray-600">
                        {ci.producto.codigo && `${ci.producto.codigo} - `}
                        {ci.producto.marca && `${ci.producto.marca} - `}
                        {ci.producto.modelo && `${ci.producto.modelo} - `}
                        {ci.producto.color && `${ci.producto.color} - `}
                        {ci.producto.quilataje && `${ci.producto.quilataje} - `}
                        {ci.producto.talla && `Talla ${ci.producto.talla}`}
                      </div>
                      <div className="text-sm text-gray-500">
                        {ci.producto.anticipo_sugerido && `Anticipo sugerido: $${ci.producto.anticipo_sugerido}`}
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
                        <div className="font-bold">${(parseFloat(ci.producto.price?.toString() || '0') * ci.cantidad).toFixed(2)}</div>
                        <div className="text-xs text-gray-500">${ci.producto.price || 0} c/u</div>
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

          {/* Totals */}
          {cart.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-bold">${getTotal().toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-blue-600">
                  <span>Anticipo pagado:</span>
                  <span className="font-bold">${(parseFloat(anticipoPagado) || 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-green-600">
                  <span>Saldo pendiente:</span>
                  <span className="font-bold">${getSaldoPendiente().toFixed(2)}</span>
                </div>
                {cart[0]?.producto.anticipo_sugerido && (
                  <div className="text-sm text-gray-600 mt-2">
                    Anticipo sugerido: ${cart[0].producto.anticipo_sugerido}
                  </div>
                )}
              </div>

              {/* Checkout Button */}
              <button
                onClick={checkout}
                disabled={cart.length === 0 || !clienteNombre.trim()}
                className="w-full bg-purple-600 text-white py-4 rounded-lg text-xl font-bold hover:bg-purple-700 disabled:bg-gray-400 mt-4"
              >
                📋 Crear Pedido
              </button>
            </div>
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
                  onClick={() => setShowCreateProductModal(true)}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                >
                  + Crear Producto
                </button>
              )}
            </div>
          </div>
          
          {/* Product Search */}
          <div>
            <label className="block text-sm font-medium mb-1">Buscar producto</label>
            <input
              ref={searchRef}
              className="w-full border border-gray-300 rounded-lg px-4 py-2"
              placeholder="Buscar por nombre, modelo o color"
              onChange={e => loadProductos(e.target.value)}
            />
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
                      <div className="font-medium text-sm">{p.name}</div>
                      <div className="text-purple-600 font-bold">${p.price}</div>
                      <div className="text-xs text-gray-500">
                        {p.codigo && `${p.codigo} - `}
                        {p.marca && `${p.marca} - `}
                        {p.modelo && `${p.modelo} - `}
                        {p.color && `${p.color} - `}
                        {p.quilataje && `${p.quilataje}`}
                      </div>
                      <div className="text-xs text-blue-600">
                        {p.anticipo_sugerido && `Anticipo sugerido: $${p.anticipo_sugerido}`}
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

      {/* Modal de Confirmación */}
      {showConfirmModal && productoToAdd && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirmar Producto sobre Pedido</h3>
            <div className="mb-4">
              <p className="text-gray-700 mb-2">
                <strong>Producto:</strong> {productoToAdd.nombre}
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Precio:</strong> ${productoToAdd.precio}
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Tiempo de entrega:</strong> {productoToAdd.tiempo_entrega_dias} días
              </p>
              <p className="text-gray-700 mb-2">
                <strong>Anticipo:</strong> {productoToAdd.anticipo_porcentaje}%
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
      {/* Modal para crear producto */}
      {showCreateProductModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">
              {editingProduct ? 'Editar Producto' : 'Crear Nuevo Producto'}
            </h3>
            
            <div className="space-y-3">
              <input
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
                placeholder="Nombre del producto *"
                value={newProduct.name}
                onChange={e => setNewProduct({...newProduct, name: e.target.value})}
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Código"
                  value={newProduct.codigo}
                  onChange={e => setNewProduct({...newProduct, codigo: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Precio *"
                  type="number"
                  step="0.01"
                  value={newProduct.price}
                  onChange={e => setNewProduct({...newProduct, price: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Costo"
                  type="number"
                  step="0.01"
                  value={newProduct.cost_price}
                  onChange={e => setNewProduct({...newProduct, cost_price: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Categoría"
                  value={newProduct.category}
                  onChange={e => setNewProduct({...newProduct, category: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Marca"
                  value={newProduct.marca}
                  onChange={e => setNewProduct({...newProduct, marca: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Modelo"
                  value={newProduct.modelo}
                  onChange={e => setNewProduct({...newProduct, modelo: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Color"
                  value={newProduct.color}
                  onChange={e => setNewProduct({...newProduct, color: e.target.value})}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Quilataje"
                  value={newProduct.quilataje}
                  onChange={e => setNewProduct({...newProduct, quilataje: e.target.value})}
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
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="disponible"
                  checked={newProduct.disponible}
                  onChange={e => setNewProduct({...newProduct, disponible: e.target.checked})}
                />
                <label htmlFor="disponible" className="text-sm">Disponible para pedidos</label>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateProductModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={createProduct}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                {editingProduct ? 'Actualizar Producto' : 'Crear Producto'}
              </button>
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
                  <li>• talla, categoria, anticipo_sugerido</li>
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
