import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import Layout from '../components/Layout'

type Product = {
  id: number
  name: string
  price: string
  cost_price?: string
  stock: number
  category?: string
  active?: boolean
  // Jewelry fields
  codigo?: string
  marca?: string
  modelo?: string
  color?: string
  quilataje?: string
  base?: string
  tipo_joya?: string
  talla?: string
  peso_gramos?: string
  descuento_porcentaje?: string
  precio_manual?: string
  costo?: string
  precio_venta?: string
}

type MetalRate = {
  id: number
  metal_type: string
  rate_per_gram: number
}

const metalTypes = [
  { value: '', label: 'Sin quilataje' },
  { value: '10k', label: '10K' },
  { value: '14k', label: '14K' },
  { value: '18k', label: '18K' },
  { value: 'oro_italiano', label: 'Oro Italiano' },
  { value: 'plata_gold', label: 'Plata Gold' },
  { value: 'plata_silver', label: 'Plata Silver' },
]

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [allProducts, setAllProducts] = useState<Product[]>([])
  const [metalRates, setMetalRates] = useState<MetalRate[]>([])
  const [message, setMessage] = useState('')
  const [query, setQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'archived'>('all')
  const [tallaFilter, setTallaFilter] = useState('')
  const [modeloFilter, setModeloFilter] = useState('')
  const [quilatajeFilter, setQuilatajeFilter] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [userRole, setUserRole] = useState<'owner' | 'admin' | 'cashier'>(
    (localStorage.getItem('role') as 'owner' | 'admin' | 'cashier') || 'cashier'
  )
  const [showImportModal, setShowImportModal] = useState(false)
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importMode, setImportMode] = useState<'add' | 'replace'>('add')
  const [importResult, setImportResult] = useState<any>(null)
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([])
  const [showBulkUpdateModal, setShowBulkUpdateModal] = useState(false)
  const [bulkUpdateForm, setBulkUpdateForm] = useState({
    stock_adjustment: '',
    descuento_porcentaje: '',
    quilataje: '',
  })
  const [loadLimit, setLoadLimit] = useState<number>(50)

  // Form state
  const [form, setForm] = useState({
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
    descuento_porcentaje: '',
    precio_manual: '',
    costo: '',
    stock: '0',
  })

  const hasSession = () => Boolean(localStorage.getItem('access'))

  useEffect(() => {
    if (!hasSession()) {
      window.location.href = '/login'
      return
    }
    load()
    loadMetalRates()
  }, [])

  const loadMetalRates = async () => {
    try {
      const res = await api.get('/metal-rates')
      setMetalRates(res.data)
    } catch (e) {
      console.error('Error loading metal rates:', e)
    }
  }

  const applyLocalFilters = (productList: Product[]) => {
    let filtered = productList

    // Filtrar por talla
    if (tallaFilter.trim()) {
      filtered = filtered.filter(p => 
        p.talla && p.talla.toLowerCase().includes(tallaFilter.toLowerCase())
      )
    }

    // Filtrar por modelo
    if (modeloFilter.trim()) {
      filtered = filtered.filter(p => 
        p.modelo && p.modelo.toLowerCase().includes(modeloFilter.toLowerCase())
      )
    }

    // Filtrar por quilataje
    if (quilatajeFilter) {
      filtered = filtered.filter(p => p.quilataje === quilatajeFilter)
    }

    setProducts(filtered)
  }

  const load = async () => {
    try {
      const qs = new URLSearchParams()
      if (query.trim()) qs.set('q', query.trim())
      if (activeFilter !== 'all') qs.set('active', String(activeFilter === 'active'))
      qs.set('limit', String(loadLimit))
      const res = await api.get(`/products/?${qs.toString()}`)
      setAllProducts(res.data)
      applyLocalFilters(res.data)
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Error loading products')
    }
  }

  useEffect(() => {
    applyLocalFilters(allProducts)
  }, [tallaFilter, modeloFilter, quilatajeFilter])

  useEffect(() => {
    if (hasSession()) {
      load()
    }
  }, [loadLimit])

  const calculatePrice = (quilataje: string, pesoGramos: string, descuento: string): number => {
    if (!quilataje || !pesoGramos) return 0
    const rate = metalRates.find(r => r.metal_type === quilataje)
    if (!rate) return 0

    const basePrice = Math.round((rate.rate_per_gram * parseFloat(pesoGramos)) * 100) / 100
    const discount = parseFloat(descuento || '0')
    const discountAmount = Math.round((basePrice * discount / 100) * 100) / 100
    const finalPrice = Math.round((basePrice - discountAmount) * 100) / 100
    return finalPrice
  }

  const getCalculatedPrice = () => {
    if (form.precio_manual) return parseFloat(form.precio_manual)
    return calculatePrice(form.quilataje, form.peso_gramos, form.descuento_porcentaje)
  }

  const resetForm = () => {
    setForm({
      name: '', codigo: '', marca: '', modelo: '', color: '', quilataje: '',
      base: '', tipo_joya: '', talla: '', peso_gramos: '', descuento_porcentaje: '',
      precio_manual: '', costo: '', stock: '0'
    })
  }

  const add = async () => {
    try {
      const calculatedPrice = getCalculatedPrice()
      const roundedPrice = Math.round(calculatedPrice * 100) / 100
      await api.post('/products/', {
        name: form.name,
        codigo: form.codigo || undefined,
        marca: form.marca || undefined,
        modelo: form.modelo || undefined,
        color: form.color || undefined,
        quilataje: form.quilataje || undefined,
        base: form.base || undefined,
        tipo_joya: form.tipo_joya || undefined,
        talla: form.talla || undefined,
        peso_gramos: parseFloat(form.peso_gramos) || undefined,
        descuento_porcentaje: parseFloat(form.descuento_porcentaje) || undefined,
        precio_manual: form.precio_manual ? parseFloat(form.precio_manual) : undefined,
        costo: parseFloat(form.costo) || undefined,
        cost_price: parseFloat(form.costo) || 0,
        precio_venta: roundedPrice,
        price: roundedPrice,
        stock: parseInt(form.stock) || 0,
        active: true
      })
      resetForm()
      setShowAddForm(false)
      await load()
      setMessage('Producto creado exitosamente')
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Error al crear producto')
    }
  }

  const updateProduct = async (id: number) => {
    try {
      const calculatedPrice = getCalculatedPrice()
      const roundedPrice = Math.round(calculatedPrice * 100) / 100
      await api.put(`/products/${id}`, {
        name: form.name,
        codigo: form.codigo || undefined,
        marca: form.marca || undefined,
        modelo: form.modelo || undefined,
        color: form.color || undefined,
        quilataje: form.quilataje || undefined,
        base: form.base || undefined,
        tipo_joya: form.tipo_joya || undefined,
        talla: form.talla || undefined,
        peso_gramos: parseFloat(form.peso_gramos) || undefined,
        descuento_porcentaje: parseFloat(form.descuento_porcentaje) || undefined,
        precio_manual: form.precio_manual ? parseFloat(form.precio_manual) : undefined,
        costo: parseFloat(form.costo) || undefined,
        cost_price: parseFloat(form.costo) || 0,
        precio_venta: roundedPrice,
        price: roundedPrice,
        stock: parseInt(form.stock) || 0,
        active: true
      })
      setEditingId(null)
      resetForm()
      await load()
      setMessage('Producto actualizado')
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Error al actualizar')
    }
  }

  const startEdit = (p: Product) => {
    setEditingId(p.id)
    setForm({
      name: p.name,
      codigo: p.codigo || '',
      marca: p.marca || '',
      modelo: p.modelo || '',
      color: p.color || '',
      quilataje: p.quilataje || '',
      base: p.base || '',
      tipo_joya: p.tipo_joya || '',
      talla: p.talla || '',
      peso_gramos: p.peso_gramos || '',
      descuento_porcentaje: p.descuento_porcentaje || '',
      precio_manual: p.precio_manual || '',
      costo: p.costo || p.cost_price || '',
      stock: String(p.stock),
    })
    setShowAddForm(true)
  }

  const remove = async (id: number) => {
    if (!confirm('¿Eliminar este producto?')) return
    try {
      await api.delete(`/products/${id}`)
      await load()
      setMessage('Producto eliminado')
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Error al eliminar')
    }
  }

  const calculatedPrice = getCalculatedPrice()
  const isManualPrice = !!form.precio_manual

  const handleExportProducts = async () => {
    try {
      const response = await api.get('/import/products/export', {
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'productos_exportados.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error: any) {
      console.error('Error exporting products:', error)
      if (error.response?.status === 404) {
        alert('No hay productos para exportar')
      } else {
        alert('Error al exportar productos')
      }
    }
  }

  const handleImport = async () => {
    if (!importFile) {
      alert('Por favor seleccione un archivo')
      return
    }

    const formData = new FormData()
    formData.append('file', importFile)
    formData.append('mode', importMode)
    
    console.log('DEBUG: Import mode =', importMode)

    try {
      const response = await api.post('/import/products/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      setImportResult(response.data)
      setImportFile(null)
      load()
      setMessage(`✅ Importación exitosa: ${response.data.added} agregados, ${response.data.updated} actualizados`)
    } catch (error: any) {
      console.error('Error importing:', error)
      alert(error.response?.data?.detail || 'Error al importar productos')
    }
  }

  const toggleProductSelection = (productId: number) => {
    setSelectedProductIds(prev => 
      prev.includes(productId) 
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedProductIds.length === products.length) {
      setSelectedProductIds([])
    } else {
      setSelectedProductIds(products.map(p => p.id))
    }
  }

  const selectAllFiltered = () => {
    const visibleIds = products.map(p => p.id)
    setSelectedProductIds(visibleIds)
  }

  const clearSelection = () => {
    setSelectedProductIds([])
  }

  const archive = async (id: number) => {
    if (!confirm('¿Archivar este producto con stock 0?')) return
    try {
      const product = products.find(p => p.id === id)
      if (!product) return
      await api.put(`/products/${id}`, { ...product, active: false })
      setMessage('Producto archivado exitosamente')
      load()
    } catch (e: any) {
      setMessage(e?.response?.data?.detail || 'Error al archivar producto')
    }
  }

  const handleBulkUpdate = async () => {
    if (selectedProductIds.length === 0) {
      alert('Por favor selecciona al menos un producto')
      return
    }

    const payload: any = {
      product_ids: selectedProductIds
    }

    if (bulkUpdateForm.stock_adjustment) {
      payload.stock_adjustment = parseInt(bulkUpdateForm.stock_adjustment)
    }
    if (bulkUpdateForm.descuento_porcentaje) {
      payload.descuento_porcentaje = parseFloat(bulkUpdateForm.descuento_porcentaje)
    }
    if (bulkUpdateForm.quilataje) {
      payload.quilataje = bulkUpdateForm.quilataje
    }

    if (!payload.stock_adjustment && !payload.descuento_porcentaje && !payload.quilataje) {
      alert('Por favor ingresa al menos un valor para actualizar')
      return
    }

    try {
      const response = await api.post('/products/bulk-update', payload)
      setMessage(`✅ ${response.data.message}`)
      setShowBulkUpdateModal(false)
      setBulkUpdateForm({ stock_adjustment: '', descuento_porcentaje: '', quilataje: '' })
      setSelectedProductIds([])
      await load()
    } catch (error: any) {
      console.error('Error bulk updating:', error)
      alert(error.response?.data?.detail || 'Error al actualizar productos')
    }
  }

  return (
    <Layout>
    <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">💍 Inventario</h1>
          <div className="flex gap-2">
            {(userRole === 'owner' || userRole === 'admin') && (
              <>
                {selectedProductIds.length > 0 && (
                  <button
                    onClick={() => setShowBulkUpdateModal(true)}
                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
                  >
                    🔄 Actualizar {selectedProductIds.length} producto(s)
                  </button>
                )}
                <button
                  onClick={handleExportProducts}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  📤 Exportar Productos
                </button>
                <button
                  onClick={() => setShowImportModal(true)}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
                >
                  📤 Importar Excel
                </button>
                <button
                  onClick={() => { setShowAddForm(!showAddForm); resetForm(); setEditingId(null); }}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                >
                  {showAddForm ? 'Cancelar' : '+ Nuevo Producto'}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="space-y-3">
          {/* Main search bar */}
          <div className="flex gap-2">
            <input
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2"
              placeholder="Buscar por nombre, código, modelo, color..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') load() }}
            />
            <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700" onClick={load}>
              🔍 Buscar
            </button>
            <select
              className="border border-gray-300 rounded-lg px-4 py-2"
              value={activeFilter}
              onChange={e => { setActiveFilter(e.target.value as any); load(); }}
            >
              <option value="all">Todos</option>
              <option value="active">Activos</option>
              <option value="archived">Archivados</option>
            </select>
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
                  setTallaFilter('')
                  setModeloFilter('')
                  setQuilatajeFilter('')
                }}
              >
                🔄 Limpiar Filtros
              </button>
            </div>
          </div>
        </div>

        {/* Selector de Límite y Botones de Selección */}
        <div className="bg-white rounded-lg shadow p-4 mb-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-4 items-center">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Mostrar productos</label>
                <select
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
                  value={loadLimit}
                  onChange={(e) => setLoadLimit(Number(e.target.value))}
                >
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={2000}>Todos</option>
                </select>
              </div>
              <div className="text-sm text-gray-600">
                Mostrando {products.length} de {allProducts.length} productos
              </div>
            </div>

            {(userRole === 'owner' || userRole === 'admin') && (
              <div className="flex gap-2 items-center">
                <button
                  onClick={selectAllFiltered}
                  disabled={products.length === 0}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  ✓ Seleccionar todos visibles ({products.length})
                </button>
                <button
                  onClick={clearSelection}
                  disabled={selectedProductIds.length === 0}
                  className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  ✗ Limpiar selección
                </button>
                {selectedProductIds.length > 0 && (
                  <span className="text-sm font-medium text-gray-700 bg-yellow-100 px-3 py-2 rounded-lg">
                    {selectedProductIds.length} seleccionado(s)
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Import Modal */}
        {showImportModal && (userRole === 'owner' || userRole === 'admin') && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
              <h2 className="text-xl font-semibold mb-4">Importar Productos desde Excel</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Modo de Importación
                  </label>
                  <select
                    value={importMode}
                    onChange={(e) => setImportMode(e.target.value as 'add' | 'replace')}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  >
                    <option value="add">Agregar nuevos (mantener existentes)</option>
                    <option value="replace">Reemplazar existentes</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {importMode === 'add' 
                      ? 'Solo agrega productos nuevos, ignora códigos duplicados' 
                      : 'Actualiza productos existentes con el mismo código'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Archivo Excel
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  />
                  {importFile && (
                    <p className="text-sm text-green-600 mt-1">
                      ✓ {importFile.name}
                    </p>
                  )}
                </div>

                {importResult && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm">
                      <strong>Resultado:</strong><br/>
                      ✅ Agregados: {importResult.added}<br/>
                      🔄 Actualizados: {importResult.updated}<br/>
                      📋 Total filas: {importResult.total_rows}
                    </p>
                    {importResult.errors.length > 0 && (
                      <details className="mt-2">
                        <summary className="text-xs text-red-600 cursor-pointer">
                          ⚠️ {importResult.errors.length} errores
                        </summary>
                        <div className="text-xs text-red-600 mt-1">
                          {importResult.errors.map((err: string, i: number) => (
                            <div key={i}>{err}</div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={handleImport}
                    disabled={!importFile}
                    className="flex-1 bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
                  >
                    Importar
                  </button>
                  <button
                    onClick={() => { setShowImportModal(false); setImportFile(null); setImportResult(null); }}
                    className="flex-1 bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Update Modal */}
        {showBulkUpdateModal && (userRole === 'owner' || userRole === 'admin') && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
              <h2 className="text-xl font-semibold mb-4">Actualización Masiva</h2>
              <p className="text-sm text-gray-600 mb-4">
                Actualizando {selectedProductIds.length} producto(s). Deja en blanco los campos que no deseas modificar.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ajuste de Stock
                  </label>
                  <input
                    type="number"
                    value={bulkUpdateForm.stock_adjustment}
                    onChange={(e) => setBulkUpdateForm({...bulkUpdateForm, stock_adjustment: e.target.value})}
                    placeholder="Ej: +10 o -5"
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Este valor se suma al stock actual (puede ser negativo)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Descuento %
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={bulkUpdateForm.descuento_porcentaje}
                    onChange={(e) => setBulkUpdateForm({...bulkUpdateForm, descuento_porcentaje: e.target.value})}
                    placeholder="Ej: 10.5"
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Este valor reemplaza el descuento actual
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quilataje
                  </label>
                  <select
                    value={bulkUpdateForm.quilataje}
                    onChange={(e) => setBulkUpdateForm({...bulkUpdateForm, quilataje: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  >
                    <option value="">-- No modificar --</option>
                    {metalTypes.map(mt => (
                      <option key={mt.value} value={mt.value}>{mt.label}</option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Este valor reemplaza el quilataje actual
                  </p>
                </div>

                <div className="flex gap-2 mt-6">
                  <button
                    onClick={handleBulkUpdate}
                    className="flex-1 bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700"
                  >
                    Actualizar
                  </button>
                  <button
                    onClick={() => {
                      setShowBulkUpdateModal(false);
                      setBulkUpdateForm({ stock_adjustment: '', descuento_porcentaje: '', quilataje: '' });
                    }}
                    className="flex-1 bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Add/Edit Form */}
        {showAddForm && (userRole === 'owner' || userRole === 'admin') && (
          <div className="bg-white rounded-lg shadow-lg p-4">
            <h2 className="text-lg font-semibold mb-3">
              {editingId ? 'Editar Producto' : 'Nuevo Producto'}
            </h2>

            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.name}
                  onChange={e => setForm({...form, name: e.target.value})}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Código</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.codigo}
                  onChange={e => setForm({...form, codigo: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Modelo</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.modelo}
                  onChange={e => setForm({...form, modelo: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.color}
                  onChange={e => setForm({...form, color: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Talla</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.talla}
                  onChange={e => setForm({...form, talla: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quilataje</label>
                <select
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.quilataje}
                  onChange={e => setForm({...form, quilataje: e.target.value})}
                >
                  <option value="">Sin quilataje</option>
                  {metalRates.map(mr => (
                    <option key={mr.id} value={mr.metal_type}>
                      {mr.metal_type} - ${mr.rate_per_gram.toFixed(2)}/g
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Peso (gramos)</label>
                <input
                  type="number"
                  step="0.001"
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.peso_gramos}
                  onChange={e => setForm({...form, peso_gramos: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descuento %</label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.descuento_porcentaje}
                  onChange={e => setForm({...form, descuento_porcentaje: e.target.value})}
                />
              </div>

              <div className="col-span-3 bg-blue-50 p-3 rounded-lg">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      💰 Precio Calculado
                    </label>
                    <div className="text-xl font-bold text-blue-600">
                      ${calculatedPrice.toFixed(2)}
                    </div>
                    {form.quilataje && form.peso_gramos && (
                      <div className="text-xs text-gray-600 mt-1">
                        Tasa: {metalRates.find(r => r.metal_type === form.quilataje)?.rate_per_gram.toFixed(2) || 0} × {form.peso_gramos}g
                        {form.descuento_porcentaje && ` - ${form.descuento_porcentaje}%`}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      ✏️ Precio Manual (override)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                      placeholder="Dejar vacío para auto-calcular"
                      value={form.precio_manual}
                      onChange={e => setForm({...form, precio_manual: e.target.value})}
                    />
                    {isManualPrice && (
                      <div className="text-xs text-amber-600 mt-1">
                        ⚠️ Precio manual activo. No se auto-calculará con cambios de tasa.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Costo</label>
                <input
                  type="number"
                  step="0.01"
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.costo}
                  onChange={e => setForm({...form, costo: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Existencia
                </label>
                <input
                  type="number"
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.stock}
                  onChange={e => setForm({...form, stock: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Base</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5"
                  value={form.base}
                  onChange={e => setForm({...form, base: e.target.value})}
                />
              </div>

            </div>

            <div className="mt-4 flex gap-2">
              <button
                onClick={() => editingId ? updateProduct(editingId) : add()}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 font-semibold"
              >
                {editingId ? 'Actualizar' : 'Crear Producto'}
              </button>
              <button
                onClick={() => { setShowAddForm(false); resetForm(); setEditingId(null); }}
                className="bg-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
      </div>
        )}

        {/* Products Table */}
        <div className="bg-white rounded-lg shadow overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {(userRole === 'owner' || userRole === 'admin') && (
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    <div className="flex flex-col items-center">
                      <span>Descuento</span>
                      <input
                        type="checkbox"
                        checked={products.length > 0 && selectedProductIds.length === products.length}
                        onChange={toggleSelectAll}
                        className="w-4 h-4 text-blue-600 rounded mt-1"
                      />
                    </div>
                  </th>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quilataje</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Peso (g)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {products.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                    No hay productos
                </td>
                </tr>
              ) : (
                products.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    {(userRole === 'owner' || userRole === 'admin') && (
                      <td className="px-4 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={selectedProductIds.includes(p.id)}
                          onChange={() => toggleProductSelection(p.id)}
                          className="w-4 h-4 text-blue-600 rounded"
                        />
                      </td>
                    )}
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{p.codigo || '-'}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{p.name}</div>
                      <div className="text-xs text-gray-500">{p.modelo}</div>
                </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {p.quilataje ? (
                        <div>
                          <div>{p.quilataje}</div>
                          <div className="text-xs text-gray-500">
                            ${metalRates.find(r => r.metal_type === p.quilataje)?.rate_per_gram.toFixed(2) || '0.00'}/g
                          </div>
                        </div>
                      ) : '-'}
                </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{p.peso_gramos || '-'}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-lg font-bold text-green-600">
                        ${parseFloat(p.price || '0').toFixed(2)}
                      </div>
                      {p.precio_manual && (
                        <div className="text-xs text-amber-600">Manual</div>
                  )}
                </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">{p.stock}</td>
                    {(userRole === 'owner' || userRole === 'admin') && (
                      <td className="px-4 py-3 whitespace-nowrap text-sm">
                        <button
                          onClick={() => startEdit(p)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          Editar
                        </button>
                        {p.stock === 0 && (
                          <button
                            onClick={() => archive(p.id)}
                            className="text-orange-600 hover:text-orange-900 mr-3"
                          >
                            Archivar
                          </button>
                        )}
                        <button
                          onClick={() => remove(p.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Eliminar
                        </button>
                      </td>
                    )}
                    {userRole === 'cashier' && (
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-400">
                        Solo lectura
                      </td>
                    )}
              </tr>
                ))
              )}
        </tbody>
      </table>
        </div>

        {message && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            {message}
          </div>
        )}
    </div>
    </Layout>
  )
}
