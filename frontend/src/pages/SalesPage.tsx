import { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'
import { cleanFolio } from '../utils/folioHelper'

type Product = { 
  id: number
  name: string
  codigo?: string
  modelo?: string
  talla?: string
  sku?: string
  price: string
  cost_price?: string
  costo?: string
  active?: boolean
  stock?: number
  peso_gramos?: number
  color?: string
  quilataje?: string
  descuento_porcentaje?: number
  default_discount_pct?: number
}

type CartItem = { 
  product: Product
  quantity: number
  discount_pct?: number
}

type User = {
  id: number
  email: string
}

export default function SalesPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [allProducts, setAllProducts] = useState<Product[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [cart, setCart] = useState<CartItem[]>([])
  const [msg, setMsg] = useState('')
  const [cash, setCash] = useState('')
  const [card, setCard] = useState('')
  const [discount, setDiscount] = useState('0')
  const [isProcessing, setIsProcessing] = useState(false)

  // Estados para descuento VIP
  const [showVipModal, setShowVipModal] = useState(false)
  const [vipDiscount, setVipDiscount] = useState('')
  
  // Filtros
  const [modeloFilter, setModeloFilter] = useState('')
  const [quilatajeFilter, setQuilatajeFilter] = useState('')
  const [tallaFilter, setTallaFilter] = useState('')
  
  // Jewelry store fields
  const [saleType, setSaleType] = useState<'contado' | 'credito'>('contado')
  const [vendedorId, setVendedorId] = useState<number | null>(null)
  const [customerName, setCustomerName] = useState('PUBLICO GENERAL')
  const [customerPhone, setCustomerPhone] = useState('')
  
  // Pagos separados para apartados (similar a pedidos apartados)
  const [apartadoCash, setApartadoCash] = useState('')
  const [apartadoCard, setApartadoCard] = useState('')
  
  // Modal de confirmación
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [productToAdd, setProductToAdd] = useState<Product | null>(null)
  
  const searchRef = useRef<HTMLInputElement | null>(null)
  const barcodeRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!localStorage.getItem('access')) {
      window.location.href = '/login'
      return
    }
    loadProducts()
    loadUsers()
  }, [])

  useEffect(() => {
    applyLocalFilters(allProducts)
  }, [modeloFilter, quilatajeFilter, tallaFilter])

  const loadProducts = async (q = '') => {
    const qs = new URLSearchParams()
    qs.set('limit', '200')
    qs.set('active', 'true')
    if (q) qs.set('q', q)
    try {
      const r = await api.get(`/products/?${qs.toString()}`)
      setAllProducts(r.data)
      applyLocalFilters(r.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error cargando productos')
    }
  }

  const applyLocalFilters = (productList: Product[]) => {
    let filtered = [...productList]
    
    // Filtrar productos con stock > 0 (no mostrar productos sin stock)
    filtered = filtered.filter(p => (p.stock ?? 0) > 0)
    
    if (modeloFilter) {
      const modeloLower = modeloFilter.toLowerCase()
      filtered = filtered.filter(p => 
        p.modelo?.toLowerCase().includes(modeloLower)
      )
    }
    
    if (quilatajeFilter) {
      const quilatajeLower = quilatajeFilter.toLowerCase()
      filtered = filtered.filter(p => 
        p.quilataje?.toLowerCase().includes(quilatajeLower)
      )
    }
    
    if (tallaFilter) {
      const tallaLower = tallaFilter.toLowerCase()
      filtered = filtered.filter(p => 
        p.talla?.toLowerCase().includes(tallaLower)
      )
    }
    
    setProducts(filtered)
  }

  const loadUsers = async () => {
    try {
      const r = await api.get('/admin/users')
      setUsers(r.data || [])
    } catch (e) {
      console.error('Error loading users:', e)
    }
  }

  const addByBarcodeOrSku = async (code: string) => {
    if (!code) return
    try {
      const r = await api.get(`/products/lookup`, { params: { barcode: code } })
      addToCart(r.data)
    } catch {
      try {
        const r2 = await api.get(`/products/lookup`, { params: { sku: code } })
        addToCart(r2.data)
      } catch {
        setMsg('Producto no encontrado')
      }
    }
    if (barcodeRef.current) {
      barcodeRef.current.value = ''
      barcodeRef.current.focus()
    }
  }

  const addToCart = (p: Product) => {
    setCart(prev => {
      const idx = prev.findIndex(ci => ci.product.id === p.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = { ...next[idx], quantity: next[idx].quantity + 1 }
        return next
      }
      return [...prev, { product: p, quantity: 1, discount_pct: p.descuento_porcentaje || p.default_discount_pct || 0 }]
    })
  }

  const confirmCheckout = () => {
    setShowConfirmModal(false)
    performCheckout()
  }

  const cancelCheckout = () => {
    setShowConfirmModal(false)
  }

  const updateQty = (id: number, qty: number) => {
    setCart(prev => prev.map(ci => 
      ci.product.id === id ? { ...ci, quantity: Math.max(1, qty) } : ci
    ))
  }

  const updateLineDiscountPct = (id: number, pct: string) => {
    const pctNum = parseFloat(pct || '0')
    setCart(prev => prev.map(ci =>
      ci.product.id === id ? { ...ci, discount_pct: isNaN(pctNum) ? 0 : pctNum } : ci
    ))
  }

  const removeItem = (id: number) => setCart(prev => prev.filter(ci => ci.product.id !== id))

  // Calculate totals
  const subtotal = Math.round(cart.reduce((sum, ci) => {
    const unit = parseFloat(ci.product.price || '0')
    const lineSub = unit * ci.quantity
    // El precio ya incluye el descuento, no aplicar nuevamente
    return sum + lineSub
  }, 0) * 100) / 100

  // Calcular subtotal base (sin descuentos individuales)
  const subtotalBase = Math.round(cart.reduce((sum, ci) => {
    const unit = parseFloat(ci.product.price || '0')
    const discountPct = ci.product.descuento_porcentaje || ci.product.default_discount_pct || 0
    const unitBase = discountPct > 0 ? unit / (1 - discountPct / 100) : unit
    return sum + (unitBase * ci.quantity)
  }, 0) * 100) / 100

  // Calcular descuento total de productos individuales
  const productDiscountTotal = subtotalBase - subtotal

  const totalCost = Math.round(cart.reduce((sum, ci) => {
    const cost = parseFloat(ci.product.costo || ci.product.cost_price || '0') || 0
    return sum + (cost * ci.quantity)
  }, 0) * 100) / 100

  // Usar cálculo más preciso similar al backend (usando Decimal-like precision)
  const discountPct = parseFloat(discount || '0') || 0

  // Calcular con la misma precisión que el backend usa Decimal
  const discountAmountCalc = Math.round((subtotal * (discountPct / 100)) * 100) / 100
  const total = Math.max(0, Math.round((subtotal - discountAmountCalc) * 100) / 100)
  const profit = total - totalCost

  const cashNumCalc = Math.round((parseFloat(cash || '0') || 0) * 100) / 100
  const cardNumCalc = Math.round((parseFloat(card || '0') || 0) * 100) / 100
  const paid = Math.round((cashNumCalc + cardNumCalc) * 100) / 100
  const change = Math.max(0, Math.round((paid - total) * 100) / 100)

  // Funciones para descuento VIP
  const getTotalWithVipDiscount = () => {
    const totalValue = total
    const discountAmount = vipDiscount ? (totalValue * parseFloat(vipDiscount) / 100) : 0
    return Math.round((totalValue - discountAmount) * 100) / 100
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

  // Reset calculations when dependencies change
  useEffect(() => {
    // This effect runs when any calculation dependency changes
  }, [subtotal, discountPct, cashNumCalc, cardNumCalc, saleType])

  // Limpiar campos cuando se cambia el tipo de venta
  useEffect(() => {
    if (saleType === 'credito') {
      // Limpiar campos de contado
      setCash('')
      setCard('')
    } else {
      // Limpiar campos de apartado
      setApartadoCash('')
      setApartadoCard('')
    }
  }, [saleType])

  const getLogoAsBase64 = async (): Promise<string> => {
    try {
      const response = await fetch('/logo.png?v=' + Date.now())
      const blob = await response.blob()
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onloadend = () => {
          resolve(reader.result as string)
        }
        reader.onerror = () => {
          resolve('')
        }
        reader.readAsDataURL(blob)
      })
    } catch (error) {
      console.error('Error loading logo:', error)
      return ''
    }
  }

  const printSaleTicket = async (saleData: any, cartItems: CartItem[], subtotal: number, discountAmount: number, total: number, paid: number, change: number, initialPayment: number = 0) => {
    try {
      const logoBase64 = await getLogoAsBase64()
      const w = window.open('', '_blank')
      if (!w) return
      
      await new Promise(resolve => setTimeout(resolve, 100))

      const items = cartItems.map((ci, index) => {
        // Build description from multiple fields
        const descParts = []
        if (ci.product.name) descParts.push(ci.product.name)
        if (ci.product.modelo) descParts.push(ci.product.modelo)
        if (ci.product.color) descParts.push(ci.product.color)
        if (ci.product.quilataje) descParts.push(ci.product.quilataje)
        if (ci.product.peso_gramos) {
          // Format weight to avoid unnecessary decimals
          const peso = Number(ci.product.peso_gramos) || 0
          let pesoFormatted
          if (peso === Math.floor(peso)) {
            pesoFormatted = `${peso}g`
          } else {
            // Convert to string and remove trailing zeros, then add 'g'
            pesoFormatted = peso.toFixed(3).replace(/\.?0+$/, '') + 'g'
          }
          descParts.push(pesoFormatted)
        }
        if (ci.product.talla) descParts.push(ci.product.talla)
        const description = descParts.length > 0 ? descParts.join('-') : 'Producto sin descripción'
        
        const precioConDescuento = parseFloat(ci.product.price || '0')
        const descuentoPct = Number(ci.discount_pct) || 0
        // Si hay descuento, calcular precio original: precio_con_descuento / (1 - desc%/100)
        const precioOriginal = descuentoPct > 0 && descuentoPct < 100 ? precioConDescuento / (1 - descuentoPct / 100) : precioConDescuento
        
        return {
          index: index + 1,
          code: ci.product.codigo || '',
          name: description,
          quantity: ci.quantity,
          unit: 'Pz',
          price: precioOriginal,  // Precio ORIGINAL (sin descuento) - más alto
          discount_pct: descuentoPct,
          discount_amount: 0,
          netPrice: precioConDescuento,
          total: precioConDescuento * ci.quantity  // Importe con descuento ya aplicado
        }
      })

      const date = new Date(saleData.created_at || new Date())
      const formattedDate = date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })

      const customerInfo = saleData.customer_name || 'PUBLICO GENERAL'
      const customerPhoneInfo = saleData.customer_phone || ''
      // Find vendedor name from users list - try vendedor_id first, then user_id as fallback
      const vendedorUserId = saleData.vendedor_id || saleData.user_id
      const vendedorUser = vendedorUserId ? users.find(u => u.id === vendedorUserId) : null
      const vendedorInfo = vendedorUser ? (vendedorUser.email.split('@')[0].toUpperCase()) : 'N/A'
      
      // Get payment information
      const paymentInfo = saleData.payments || []
      console.log('Payment info:', paymentInfo)
      const efectivoPaid = paymentInfo.filter((p: any) => p.method === 'cash' || p.method === 'efectivo').reduce((sum: number, p: any) => sum + parseFloat(p.amount), 0)
      const tarjetaPaid = paymentInfo.filter((p: any) => p.method === 'card' || p.method === 'tarjeta').reduce((sum: number, p: any) => sum + parseFloat(p.amount), 0)
      console.log('Efectivo paid:', efectivoPaid, 'Tarjeta paid:', tarjetaPaid, 'Initial payment:', initialPayment)
      
      // Calculate abono and saldo based on sale type
      let abonoInicial = 0
      let totalAbonos = 0
      let saldoAmount = 0
      
      console.log('DEBUG Ticket:', { tipo_venta: saleData.tipo_venta, initialPayment, efectivoPaid, tarjetaPaid, total })
      
      if (saleData.tipo_venta === 'contado') {
        // For contado sales, don't show abono/saldo
        abonoInicial = 0
        totalAbonos = 0
        saldoAmount = 0
      } else {
        // For credito sales, abono inicial es lo que se pagó al crear la venta
        abonoInicial = Number(initialPayment) || 0
        // Total de abonos es solo el inicial por ahora (en el ticket al momento de venta)
        totalAbonos = abonoInicial
        saldoAmount = Number(total) - totalAbonos
      }
      
      console.log('DEBUG Calculated:', { abonoInicial, totalAbonos, saldoAmount })

      const html = `
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ticket ${saleData.id}</title>
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
        ${saleData.tipo_venta === 'credito' ? `<div><strong>FOLIO DE APARTADO :</strong> ${cleanFolio(saleData.folio_apartado) || 'AP-' + String(saleData.id).padStart(6, '0')}</div>` : `<div><strong>FOLIO :</strong> ${cleanFolio(saleData.folio_venta) || 'V-' + String(saleData.id).padStart(6, '0')}</div>`}
        <div><strong>FECHA VENTA :</strong> ${formattedDate}</div>
        ${saleData.tipo_venta === 'contado' ? `<div><strong>MÉTODO DE PAGO :</strong> ${efectivoPaid > 0 && tarjetaPaid > 0 ? 'EFECTIVO / TARJETA' : (efectivoPaid > 0 ? 'EFECTIVO' : 'TARJETA')}</div>` : ''}
        ${saleData.tipo_venta === 'credito' && (efectivoPaid > 0 || tarjetaPaid > 0) ? `<div><strong>MÉTODO DE PAGO :</strong> ${efectivoPaid > 0 && tarjetaPaid > 0 ? 'EFECTIVO / TARJETA' : (efectivoPaid > 0 ? 'EFECTIVO' : 'TARJETA')}</div>` : ''}
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
        <td><strong>Vendedor:</strong></td>
        <td>${vendedorInfo}</td>
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
          <th style="width: 12%;">Precio x gramo</th>
          <th style="width: 10%;">Desc%</th>
          <th style="width: 12%;">Importe</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(item => `
          <tr>
            <td>${item.quantity}</td>
            <td>${item.code}</td>
            <td>${item.name}</td>
            <td>$${item.price.toFixed(2)}</td>
            <td>${item.discount_pct > 0 ? item.discount_pct.toFixed(1) + '%' : '-'}</td>
            <td>$${item.total.toFixed(2)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    <!-- Totals -->
    <div class="totals">
      <div><strong>TOTAL :</strong> $${total.toFixed(2)}</div>
      ${saleData.tipo_venta === 'contado' && efectivoPaid > 0 ? `<div><strong>EFECTIVO :</strong> $${efectivoPaid.toFixed(2)}</div>` : ''}
      ${saleData.tipo_venta === 'contado' && tarjetaPaid > 0 ? `<div><strong>TARJETA :</strong> $${tarjetaPaid.toFixed(2)}</div>` : ''}
      ${saleData.tipo_venta === 'credito' && abonoInicial > 0 ? `<div><strong>ABONO INICIAL :</strong> $${abonoInicial.toFixed(2)}</div>` : ''}
      ${saleData.tipo_venta === 'credito' && efectivoPaid > 0 && tarjetaPaid > 0 ? `<div style="margin-left: 20px;"><strong>EFECTIVO :</strong> $${efectivoPaid.toFixed(2)}</div>` : ''}
      ${saleData.tipo_venta === 'credito' && efectivoPaid > 0 && tarjetaPaid > 0 ? `<div style="margin-left: 20px;"><strong>TARJETA :</strong> $${tarjetaPaid.toFixed(2)}</div>` : ''}
      ${saleData.tipo_venta === 'credito' && totalAbonos > 0 ? `<div><strong>TOTAL DE ABONOS :</strong> $${totalAbonos.toFixed(2)}</div>` : ''}
      ${saleData.tipo_venta === 'credito' && saldoAmount > 0 ? `<div><strong>SALDO PENDIENTE :</strong> $${saldoAmount.toFixed(2)}</div>` : ''}
    </div>

    <!-- Footer Section -->
    <div class="footer-section">
      <!-- Footer -->
      <div class="footer-info">
        <div>${items.length} Articulos</div>
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

      // Persist ticket HTML on the backend
      try {
        await api.post('/tickets', {
          // Usar el campo correcto según el tipo de venta
          ...(saleData.tipo_venta === 'credito' 
            ? { apartado_id: saleData.id }
            : { venta_contado_id: saleData.id }
          ),
          kind: saleData.tipo_venta === 'credito' ? 'payment' : 'sale',
          html
        })
      } catch (persistErr) {
        console.warn('No se pudo guardar el ticket:', persistErr)
      }
      
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

  const checkout = async () => {
    // Prevenir doble ejecución
    if (isProcessing) {
      return
    }

    if (cart.length === 0) {
      setMsg('No hay artículos')
      return
    }

    // Mostrar modal de confirmación antes de procesar
    setShowConfirmModal(true)
  }

  const performCheckout = async () => {
    // Prevenir doble ejecución
    if (isProcessing) {
      return
    }

    try {
      setIsProcessing(true)  // Bloquear mientras procesa

      // Validate sale type specific requirements
      if (saleType === 'credito' && !vendedorId) {
        setMsg('Por favor seleccione un vendedor para ventas a crédito')
        setIsProcessing(false)
        return
      }

      if (saleType === 'credito' && !customerName.trim()) {
        setMsg('Por favor ingrese el nombre del cliente para venta a crédito')
        setIsProcessing(false)
        return
      }

      // Validar anticipo para apartados
      if (saleType === 'credito') {
        const apartadoTotal = (parseFloat(apartadoCash || '0') + parseFloat(apartadoCard || '0'))
        if (apartadoTotal <= 0) {
          setMsg('El anticipo inicial debe ser mayor a 0 para apartados')
          setIsProcessing(false)
          return
        }
      }

      // Verificar pago con tolerancia mínima para errores de redondeo
      const tolerance = 0.001 // 0.1 centavo de tolerancia
      const finalTotal = getTotalWithVipDiscount()
      if (saleType === 'contado' && (paid - finalTotal) < -tolerance) {
        setMsg(`Pago insuficiente. Total: $${finalTotal.toFixed(2)}, Pagado: $${paid.toFixed(2)}`)
        setIsProcessing(false)
        return
      }

      const items = cart.map(ci => ({
        product_id: ci.product.id,
        quantity: ci.quantity,
        discount_pct: 0  // El precio del producto ya tiene el descuento aplicado
      }))

      let payments = null
      // Para contado y crédito, enviamos los pagos iniciales en el array payments
      if (saleType === 'contado') {
        payments = []
        if (cashNumCalc > 0) payments.push({ method: 'cash', amount: parseFloat(cashNumCalc.toFixed(2)) })
        if (cardNumCalc > 0) payments.push({ method: 'card', amount: parseFloat(cardNumCalc.toFixed(2)) })
      } else if (saleType === 'credito') {
        // Para apartados, usar los campos separados
        payments = []
        const apartadoCashNum = parseFloat(apartadoCash || '0')
        const apartadoCardNum = parseFloat(apartadoCard || '0')
        if (apartadoCashNum > 0) payments.push({ method: 'cash', amount: parseFloat(apartadoCashNum.toFixed(2)) })
        if (apartadoCardNum > 0) payments.push({ method: 'card', amount: parseFloat(apartadoCardNum.toFixed(2)) })
      }

      // Calcular total con descuento VIP aplicado
      const subtotalValue = subtotal
      const vipDiscountAmount = vipDiscount ? (subtotalValue * parseFloat(vipDiscount) / 100) : 0
      const totalWithVipDiscount = subtotalValue - vipDiscountAmount

      const saleData: any = {
        items,
        discount_amount: parseFloat(discountAmountCalc.toFixed(2)),
        tax_rate: 0,  // IVA siempre 0
        tipo_venta: saleType,  // Ya es 'credito' directamente
        // Enviar subtotal sin descuento, el backend calculará el total final
        total: Math.round(subtotalValue * 100) / 100
      }

      // Add vendedor_id if selected
      if (vendedorId) {
        saleData.vendedor_id = vendedorId
      }

      // Add payments only if there are any
      if (payments && payments.length > 0) {
        saleData.payments = payments
      }

      // Add VIP discount for apartados
      if (saleType === 'credito') {
        saleData.vip_discount_pct = vipDiscount ? parseFloat(vipDiscount) : 0
      }

      // Add customer info
      if (customerName.trim()) {
        saleData.customer_name = customerName.trim()
      }

      // Add phone for all sales
      if (customerPhone.trim()) {
        saleData.customer_phone = customerPhone.trim()
      }

      // Usar endpoint correcto según el tipo de venta
      let r
      if (saleType === 'credito') {
        // Para apartados, usar el endpoint dedicado
        r = await api.post('/apartados/', saleData)
      } else {
        // Para ventas de contado
        r = await api.post('/ventas/', saleData)
      }

      // Guardar valores ANTES de limpiar los estados
      const cashAmount = saleType === 'contado' ? parseFloat(cash || '0') : parseFloat(apartadoCash || '0')
      const cardAmount = saleType === 'contado' ? parseFloat(card || '0') : parseFloat(apartadoCard || '0')
      const initialPaymentAmount = cashAmount + cardAmount
      const currentCart = [...cart]

      console.log('===== Initial payment info =====')
      console.log('saleType:', saleType)
      console.log('cashAmount:', cashAmount)
      console.log('cardAmount:', cardAmount)
      console.log('initialPaymentAmount:', initialPaymentAmount)
      console.log('================================')

      // Ya no necesitamos registrar pagos adicionales - se envían en el array payments al crear la venta

      setCart([])
      setCash('')
      setCard('')
      setApartadoCash('')
      setApartadoCard('')
      setDiscount('0')
      setCustomerName('')
      setCustomerPhone('')
      setVipDiscount('')

      // Mostrar folio correcto según el tipo de venta
      const folio = saleType === 'credito'
        ? (cleanFolio(r.data.folio_apartado) || `AP-${r.data.id}`)
        : (cleanFolio(r.data.folio_venta) || `V-${r.data.id}`)
      setMsg(`✅ ${saleType === 'credito' ? 'Apartado' : 'Venta'} realizada. Folio ${folio}. Total $${getTotalWithVipDiscount().toFixed(2)}`)

      // Generar ticket de venta - usar el valor calculado ANTES de limpiar
      const finalInitialPayment = saleType === 'credito' ? initialPaymentAmount : 0
      console.log('CALLING printSaleTicket with initialPayment:', finalInitialPayment)
      // Asegurar que saleData tenga tipo_venta para que printSaleTicket sepa qué folio usar
      const saleDataForTicket = {
        ...r.data,
        tipo_venta: saleType  // Asegurar que tipo_venta esté presente
      }
      // Usar el total con descuento VIP para el ticket
      const ticketTotal = vipDiscount ? getTotalWithVipDiscount() : total
      printSaleTicket(saleDataForTicket, currentCart, subtotal, discountAmountCalc + vipDiscountAmount, ticketTotal, paid, change, finalInitialPayment)

      setIsProcessing(false)  // Desbloquear después de completar
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error al crear venta')
      setIsProcessing(false)  // Desbloquear en caso de error
    }
  }

  const openPrint = (sale: any) => {
    try {
      const w = window.open('', '_blank', 'width=400,height=600')
      if (!w) return
      const items = (sale.items || []) as Array<any>
      const date = sale.created_at ? new Date(sale.created_at) : new Date()
      const html = `
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ticket ${sale.id}</title>
<style>
  body { font-family: monospace; margin: 20px; }
  .center { text-align: center; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; }
  td { padding: 4px 0; font-size: 12px; }
  .total { font-weight: 700; font-size: 16px; border-top: 2px solid #000; padding-top: 8px; }
  hr { border: 1px dashed #000; }
</style></head>
<body onload="window.print()">
  <div class="center">
    <h2>TICKET DE VENTA</h2>
    <p>Folio: ${sale.id}</p>
    <p>${date.toLocaleString()}</p>
  </div>
  <hr/>
  <table>
    ${items.map(it => `
      <tr>
        <td>${it.quantity} x ${it.name}</td>
        <td style="text-align:right;">$${Number(it.total_price || 0).toFixed(2)}</td>
      </tr>
      ${Number(it.discount_pct || 0) > 0 ? `<tr><td colspan="2" style="font-size:10px;padding-left:20px;">Desc: ${Number(it.discount_pct).toFixed(2)}%</td></tr>` : ''}
    `).join('')}
  </table>
  <hr/>
  <table>
    <tr><td>Subtotal:</td><td style="text-align:right;">$${Number(sale.subtotal || 0).toFixed(2)}</td></tr>
    ${Number(sale.discount_amount || 0) > 0 ? `<tr><td>Descuento:</td><td style="text-align:right;">-$${Number(sale.discount_amount).toFixed(2)}</td></tr>` : ''}
    <tr class="total"><td>TOTAL:</td><td style="text-align:right;">$${Number(sale.total || 0).toFixed(2)}</td></tr>
  </table>
  <div class="center" style="margin-top:20px;">
    <p>¡Gracias por su compra!</p>
  </div>
</body></html>`
      w.document.write(html)
      w.document.close()
    } catch (e) {
      console.error('Error opening print window:', e)
    }
  }

  return (
    <Layout>
      <div className="grid grid-cols-12 gap-6 h-[calc(100vh-100px)]">
        {/* Left: Cart & Checkout */}
        <div className="col-span-8 flex flex-col space-y-4">
          {/* Sale Type & Vendor */}
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Tipo de Venta</label>
                <select
                  value={saleType}
                  onChange={e => setSaleType(e.target.value as any)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="contado">💵 Contado</option>
                  <option value="credito">💳 Apartado</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Vendedor</label>
                <select
                  value={vendedorId || ''}
                  onChange={e => setVendedorId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">Seleccionar...</option>
                  {users.map(u => (
                    <option key={u.id} value={u.id}>{u.email}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Customer Info */}
            <div className="bg-amber-50 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-semibold">
                {saleType === 'credito' ? 'Información del Cliente' : 'Cliente'}
              </h3>
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
                  placeholder="Nombre *"
                  value={customerName}
                  onChange={e => setCustomerName(e.target.value)}
                />
                <input
                  className="border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="Teléfono"
                  value={customerPhone}
                  onChange={e => setCustomerPhone(e.target.value)}
                />
            </div>
            </div>

          {/* Cart Items */}
          <div className="">
            <table className="w-full">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="px-4 py-4 text-left text-lg font-bold">Producto</th>
                  <th className="px-4 py-4 text-center text-lg font-bold">Cant</th>
                  <th className="px-4 py-4 text-right text-lg font-bold">Precio</th>
                  <th className="px-4 py-4 text-right text-lg font-bold">Desc%</th>
                  <th className="px-4 py-4 text-right text-lg font-bold">Total</th>
                  <th className="px-4 py-4"></th>
                </tr>
              </thead>
              <tbody>
                {cart.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-gray-400 text-lg">
                      Carrito vacío
                    </td>
                  </tr>
                ) : (
                  cart.map(ci => {
                    const precioActual = parseFloat(ci.product.price || '0')
                    const discPct = Number(ci.discount_pct) || 0
                    // Si hay descuento, calcular precio original antes del descuento
                    const precioOriginal = discPct > 0 && discPct < 100 ? precioActual / (1 - discPct / 100) : precioActual
                    const lineTotal = precioActual * ci.quantity  // El precio ya tiene el descuento aplicado
                    
                    return (
                      <tr key={ci.product.id} className="border-t">
                        <td className="px-4 py-4 text-lg">{ci.product.name}</td>
                        <td className="px-4 py-4 text-center text-lg">
                          <input
                            type="number"
                            min="1"
                            value={ci.quantity}
                            onChange={e => updateQty(ci.product.id, Number(e.target.value))}
                            className="w-20 border rounded px-3 py-2 text-center text-lg"
                          />
                        </td>
                        <td className="px-4 py-4 text-right text-lg">${precioOriginal.toFixed(2)}</td>
                        <td className="px-4 py-4 text-right text-lg text-gray-600">
                          {discPct > 0 ? `${discPct.toFixed(1)}%` : '-'}
                        </td>
                        <td className="px-4 py-4 text-right font-bold text-lg">
                          ${lineTotal.toFixed(2)}
                        </td>
                        <td className="px-4 py-4">
                          <button
                            onClick={() => removeItem(ci.product.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Totals & Payment */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <div className="flex justify-between text-lg">
              <span>Subtotal:</span>
              <span className="font-bold">${subtotalBase.toFixed(2)}</span>
            </div>

            {productDiscountTotal > 0 && (
              <div className="flex justify-between text-red-600">
                <span>Descuento productos:</span>
                <span>-${productDiscountTotal.toFixed(2)}</span>
              </div>
            )}

            <div className="flex justify-between text-lg border-t border-gray-200 pt-2">
              <span>Subtotal neto:</span>
              <span className="font-bold">${subtotal.toFixed(2)}</span>
            </div>

            {discountAmountCalc > 0 && (
              <div className="flex justify-between text-red-600">
                <span>Descuento general:</span>
                <span>-${discountAmountCalc.toFixed(2)}</span>
              </div>
            )}

            {vipDiscount && (
              <div className="flex justify-between text-red-600">
                <span>Descuento VIP ({vipDiscount}%):</span>
                <span>-${(total * parseFloat(vipDiscount) / 100).toFixed(2)}</span>
              </div>
            )}

            <div className="border-t-2 border-gray-300 pt-2 flex justify-between text-2xl font-bold">
              <span>TOTAL:</span>
              <span className="text-green-600">${getTotalWithVipDiscount().toFixed(2)}</span>
            </div>

            {/* Payment fields */}
            {saleType === 'credito' ? (
              <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">Anticipo Inicial (opcional)</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Efectivo</label>
                    <input
                      type="number"
                      step="0.01"
                      value={apartadoCash}
                      onChange={e => setApartadoCash(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="0.00"
                    />
            </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Tarjeta</label>
                    <input
                      type="number"
                      step="0.01"
                      value={apartadoCard}
                      onChange={e => setApartadoCard(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="0.00"
                    />
                  </div>
                </div>
                <div className="bg-orange-50 p-3 rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Anticipo:</span>
                    <span className="font-bold text-orange-700">
                      ${((parseFloat(apartadoCash || '0') || 0) + (parseFloat(apartadoCard || '0') || 0)).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="font-medium">Saldo pendiente:</span>
                    <span className="font-bold text-red-700">
                      ${(getTotalWithVipDiscount() - ((parseFloat(apartadoCash || '0') || 0) + (parseFloat(apartadoCard || '0') || 0))).toFixed(2)}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-500">Puedes dejar en $0.00 si no hay anticipo inicial</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm font-medium">Efectivo</label>
                    <input
                      type="number"
                      step="0.01"
                      value={cash}
                      onChange={e => setCash(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Tarjeta</label>
                    <input
                      type="number"
                      step="0.01"
                      value={card}
                      onChange={e => setCard(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                {paid > 0 && (
                  <div className="flex justify-between">
                    <span>Cambio:</span>
                    <span className="font-bold text-blue-600">${change.toFixed(2)}</span>
                  </div>
                )}
              </>
            )}

            {/* Checkout Button */}
            <button
              onClick={checkout}
              disabled={cart.length === 0 || isProcessing}
              className="w-full bg-green-600 text-white py-4 rounded-lg text-xl font-bold hover:bg-green-700 disabled:bg-gray-400"
            >
              {isProcessing 
                ? '⏳ Procesando...' 
                : (saleType === 'credito' ? '💳 Vender a Abonos' : '💵 Cobrar')
              }
            </button>
          </div>

          {/* Messages */}
          {msg && (
            <div className={`p-3 rounded-lg ${msg.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {msg}
            </div>
          )}
        </div>

        {/* Right: Product Selection */}
        <div className="col-span-4 flex flex-col space-y-4">
          <h1 className="text-2xl font-bold">🛒 Punto de Venta</h1>
          {/* Product Search */}
          <div>
            <label className="block text-sm font-medium mb-1">Buscar producto</label>
            <input
              ref={searchRef}
              className="w-full border border-gray-300 rounded-lg px-4 py-2"
              placeholder="Buscar por nombre, código, modelo o talla"
              onChange={e => loadProducts(e.target.value)}
            />
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow p-3">
            <div className="grid grid-cols-4 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Modelo</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-2 py-1 text-sm"
                  placeholder="Filtrar..."
                  value={modeloFilter}
                  onChange={e => setModeloFilter(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Quilataje</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-2 py-1 text-sm"
                  placeholder="Filtrar..."
                  value={quilatajeFilter}
                  onChange={e => setQuilatajeFilter(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Talla</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-2 py-1 text-sm"
                  placeholder="Filtrar..."
                  value={tallaFilter}
                  onChange={e => setTallaFilter(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <button
                  className="w-full bg-gray-500 text-white px-2 py-1 rounded-lg hover:bg-gray-600 text-xs"
                  onClick={() => {
                    setModeloFilter('')
                    setQuilatajeFilter('')
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
            <div className="grid grid-cols-2 gap-2">
              {products.map(p => (
                <button
                  key={p.id}
                  onClick={() => addToCart(p)}
                  className="bg-white border border-gray-300 rounded-lg p-3 hover:bg-blue-50 text-left"
                >
                  <div className="font-medium text-sm">{p.name}</div>
                  {p.modelo && <div className="text-xs text-gray-600 font-medium">Modelo: {p.modelo}</div>}
                  <div className="text-green-600 font-bold">${parseFloat(p.price || '0').toFixed(2)}</div>
                  {p.codigo && <div className="text-xs text-gray-500">Código: {p.codigo}</div>}
                  <div className="flex gap-2 text-xs text-gray-500 mt-1">
                    {p.quilataje && <span>🔶 {p.quilataje}</span>}
                    {p.talla && <span>📏 {p.talla}</span>}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modal de Confirmación de Checkout */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Confirmar Venta</h3>

            {/* Resumen del carrito */}
            <div className="mb-4">
              <h4 className="font-medium mb-2">Productos en el carrito:</h4>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {cart.map((ci, index) => (
                  <div key={ci.product.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">{ci.product.name}</div>
                      {ci.product.modelo && <div className="text-sm text-gray-600">Modelo: {ci.product.modelo}</div>}
                      {ci.product.codigo && <div className="text-sm text-gray-600">Código: {ci.product.codigo}</div>}
                      <div className="text-sm">Cantidad: {ci.quantity}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">${(parseFloat(ci.product.price || '0') * ci.quantity).toFixed(2)}</div>
                      {ci.discount_pct > 0 && <div className="text-sm text-red-600">Desc: {ci.discount_pct.toFixed(1)}%</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Totales */}
            <div className="border-t pt-4 mb-4">
              <div className="flex justify-between font-medium">
                <span>Subtotal:</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              {productDiscountTotal > 0 && (
                <div className="flex justify-between text-red-600">
                  <span>Descuento productos:</span>
                  <span>-${productDiscountTotal.toFixed(2)}</span>
                </div>
              )}
              {vipDiscount && (
                <div className="flex justify-between text-red-600">
                  <span>Descuento VIP ({vipDiscount}%):</span>
                  <span>-${(total * parseFloat(vipDiscount) / 100).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-lg border-t pt-2">
                <span>TOTAL:</span>
                <span>${getTotalWithVipDiscount().toFixed(2)}</span>
              </div>
            </div>

            <p className="text-gray-600 mb-6">
              ¿Confirmas que deseas procesar esta venta?
            </p>

            <div className="flex gap-3">
              <button
                onClick={cancelCheckout}
                className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
              >
                Cancelar
              </button>
              <button
                onClick={confirmCheckout}
                className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700"
              >
                Confirmar Venta
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
                    <strong>Base para descuento:</strong> ${total.toFixed(2)}<br/>
                    <strong>Descuento VIP ({vipDiscount}%):</strong> -${(total * parseFloat(vipDiscount) / 100).toFixed(2)}<br/>
                    <strong>Total final:</strong> ${getTotalWithVipDiscount().toFixed(2)}
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
    </Layout>
  )
}
