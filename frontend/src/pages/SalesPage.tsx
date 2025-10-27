import { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type Product = { 
  id: number
  name: string
  sku?: string
  price: string
  cost_price?: string
  costo?: string
  active?: boolean
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
  const [users, setUsers] = useState<User[]>([])
  const [cart, setCart] = useState<CartItem[]>([])
  const [msg, setMsg] = useState('')
  const [cash, setCash] = useState('')
  const [card, setCard] = useState('')
  const [discount, setDiscount] = useState('0')
  const [taxRate, setTaxRate] = useState('0')
  
  // Jewelry store fields
  const [saleType, setSaleType] = useState<'contado' | 'credito'>('contado')
  const [vendedorId, setVendedorId] = useState<number | null>(null)
  const [customerName, setCustomerName] = useState('PUBLICO GENERAL')
  const [customerPhone, setCustomerPhone] = useState('')
  const [customerAddress, setCustomerAddress] = useState('')
  const [initialPayment, setInitialPayment] = useState('')
  const [initialPaymentMethod, setInitialPaymentMethod] = useState('efectivo')
  
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

  const loadProducts = async (q = '') => {
    const qs = new URLSearchParams()
    qs.set('limit', '50')
    qs.set('active', 'true')
    if (q) qs.set('q', q)
    try {
      const r = await api.get(`/products/?${qs.toString()}`)
      setProducts(r.data)
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
      return [...prev, { product: p, quantity: 1, discount_pct: 0 }]
    })
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
    const discPct = ci.discount_pct || 0
    const discAmt = lineSub * (discPct / 100)
    return sum + (lineSub - discAmt)
  }, 0) * 100) / 100

  const totalCost = Math.round(cart.reduce((sum, ci) => {
    const cost = parseFloat(ci.product.costo || ci.product.cost_price || '0') || 0
    return sum + (cost * ci.quantity)
  }, 0) * 100) / 100

  // Usar cálculo más preciso similar al backend (usando Decimal-like precision)
  const discountPct = parseFloat(discount || '0') || 0
  const taxRateNum = parseFloat(taxRate || '0') || 0

  // Calcular con la misma precisión que el backend usa Decimal
  const discountAmountCalc = Math.round((subtotal * (discountPct / 100)) * 100) / 100
  const taxable = Math.max(0, Math.round((subtotal - discountAmountCalc) * 100) / 100)
  const taxAmount = taxRateNum > 0 ? Math.round((taxable * (taxRateNum / 100)) * 100) / 100 : 0
  const total = Math.round((taxable + taxAmount) * 100) / 100
  const profit = total - totalCost

  const cashNumCalc = Math.round((parseFloat(cash || '0') || 0) * 100) / 100
  const cardNumCalc = Math.round((parseFloat(card || '0') || 0) * 100) / 100
  const paid = Math.round((cashNumCalc + cardNumCalc) * 100) / 100
  const change = Math.max(0, Math.round((paid - total) * 100) / 100)

  // Reset calculations when dependencies change
  useEffect(() => {
    // This effect runs when any calculation dependency changes
  }, [subtotal, discountPct, taxRateNum, cashNumCalc, cardNumCalc, saleType])

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

  const printSaleTicket = async (saleData: any, cartItems: CartItem[], subtotal: number, discountAmount: number, taxAmount: number, total: number, paid: number, change: number, initialPayment: number = 0) => {
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
          const peso = parseFloat(ci.product.peso_gramos)
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
        
        return {
          index: index + 1,
          code: ci.product.codigo || '',
          name: description,
          quantity: ci.quantity,
          unit: 'Pz', // Unidad por defecto
          price: parseFloat(ci.product.price || '0'),
          discount_pct: ci.discount_pct || 0,
          discount_amount: parseFloat(ci.product.price || '0') * (ci.discount_pct || 0) / 100,
          netPrice: parseFloat(ci.product.price || '0') * (1 - (ci.discount_pct || 0) / 100),
          total: parseFloat(ci.product.price || '0') * ci.quantity * (1 - (ci.discount_pct || 0) / 100)
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
      
      // Calculate abono from initial payment or payments
      const abonoAmount = initialPayment > 0 ? initialPayment : (efectivoPaid + tarjetaPaid)
      const saldoAmount = total - abonoAmount

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
        <div><strong>FOLIO :</strong> ${String(saleData.id).padStart(6, '0')}</div>
        <div><strong>FECHA VENTA :</strong> ${formattedDate}</div>
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
        <td><strong>Dirección:</strong></td>
        <td></td>
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
          <th style="width: 12%;">P.Unitario</th>
          <th style="width: 10%;">Desc.</th>
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
            <td>$${item.discount_amount.toFixed(2)}</td>
            <td>$${item.total.toFixed(2)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    <!-- Totals -->
    <div class="totals">
      <div><strong>TOTAL :</strong> $${total.toFixed(2)}</div>
      ${efectivoPaid > 0 ? `<div><strong>EFECTIVO :</strong> $${efectivoPaid.toFixed(2)}</div>` : ''}
      ${tarjetaPaid > 0 ? `<div><strong>TARJETA :</strong> $${tarjetaPaid.toFixed(2)}</div>` : ''}
      ${abonoAmount > 0 ? `<div><strong>ABONOS/ANTICIPO :</strong> $${abonoAmount.toFixed(2)}</div>` : ''}
      ${saldoAmount > 0 ? `<div><strong>SALDO :</strong> $${saldoAmount.toFixed(2)}</div>` : ''}
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
    try {
      if (cart.length === 0) {
        setMsg('No hay artículos')
        return
      }

      // Validate sale type specific requirements
      if (saleType === 'credito' && !vendedorId) {
        setMsg('Por favor seleccione un vendedor para ventas a crédito')
        return
      }

      if (saleType === 'credito' && !customerName.trim()) {
        setMsg('Por favor ingrese el nombre del cliente para venta a crédito')
        return
      }

      // Verificar pago con tolerancia mínima para errores de redondeo
      const tolerance = 0.001 // 0.1 centavo de tolerancia
      if (saleType === 'contado' && (paid - total) < -tolerance) {
        setMsg(`Pago insuficiente. Total: $${total.toFixed(2)}, Pagado: $${paid.toFixed(2)}`)
        return
      }

      const items = cart.map(ci => ({
        product_id: ci.product.id,
        quantity: ci.quantity,
        discount_pct: parseFloat(ci.discount_pct || 0) || 0
      }))

      let payments = null
      if (saleType === 'contado') {
        payments = []
        if (cashNumCalc > 0) payments.push({ method: 'cash', amount: parseFloat(cashNumCalc.toFixed(2)) })
        if (cardNumCalc > 0) payments.push({ method: 'card', amount: parseFloat(cardNumCalc.toFixed(2)) })
      }

      const saleData: any = {
        items,
        discount_amount: parseFloat(discountAmountCalc.toFixed(2)),
        tax_rate: parseFloat(taxRateNum.toFixed(2)) || 0,
        tipo_venta: saleType
      }

      // Add vendedor_id if selected
      if (vendedorId) {
        saleData.vendedor_id = vendedorId
      }

      // Add payments only if there are any
      if (payments && payments.length > 0) {
        saleData.payments = payments
      }

      // Add customer info
      if (customerName.trim()) {
        saleData.customer_name = customerName.trim()
      }
      
      // Add phone for all sales
      if (customerPhone.trim()) {
        saleData.customer_phone = customerPhone.trim()
      }

      const r = await api.post('/sales/', saleData)
      
      // If it's a credit sale with initial payment, register it
      if (saleType === 'credito' && initialPayment && parseFloat(initialPayment) > 0) {
        try {
          await api.post('/credits/payments', {
            sale_id: r.data.id,
            amount: parseFloat(initialPayment),
            payment_method: initialPaymentMethod,
            notes: 'Abono inicial'
          })
        } catch (paymentError) {
          console.error('Error registering initial payment:', paymentError)
          // Continue anyway - the sale was created successfully
        }
      }
      
      setCart([])
      setCash('')
      setCard('')
      setDiscount('0')
      setCustomerName('')
      setCustomerPhone('')
      setCustomerAddress('')
      setInitialPayment('')
      setInitialPaymentMethod('efectivo')
      
      setMsg(`✅ Venta realizada. Folio ${r.data.id}. Total $${r.data.total}`)
      
      // Generar ticket de venta
      const initialPaymentAmount = saleType === 'credito' && initialPayment ? parseFloat(initialPayment) : 0
      printSaleTicket(r.data, cart, subtotal, discountAmountCalc, taxAmount, total, paid, change, initialPaymentAmount)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error al crear venta')
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
    ${Number(sale.tax_amount || 0) > 0 ? `<tr><td>IVA (${Number(sale.tax_rate || 0).toFixed(1)}%):</td><td style="text-align:right;">$${Number(sale.tax_amount).toFixed(2)}</td></tr>` : ''}
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
        {/* Left: Product Selection */}
        <div className="col-span-5 flex flex-col space-y-4">
          <h1 className="text-2xl font-bold">🛒 Punto de Venta</h1>
          
          {/* Barcode Scanner */}
          <div>
            <label className="block text-sm font-medium mb-1">Escanear Código / SKU</label>
            <input
              ref={barcodeRef}
              className="w-full border border-gray-300 rounded-lg px-4 py-2"
              placeholder="Escanee o escriba código..."
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  addByBarcodeOrSku(e.currentTarget.value)
                }
              }}
            />
          </div>

          {/* Product Search */}
          <div>
            <input
              ref={searchRef}
              className="w-full border border-gray-300 rounded-lg px-4 py-2"
              placeholder="Buscar productos..."
              onChange={e => loadProducts(e.target.value)}
            />
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
                  <div className="text-green-600 font-bold">${parseFloat(p.price || '0').toFixed(2)}</div>
                  {p.sku && <div className="text-xs text-gray-500">SKU: {p.sku}</div>}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Cart & Checkout */}
        <div className="col-span-7 flex flex-col space-y-4">
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
                  <option value="credito">💳 Abonos</option>
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
            <h3 className="font-semibold mb-2">
              {saleType === 'credito' ? 'Información del Cliente' : 'Cliente'}
            </h3>
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
            {saleType === 'credito' && (
              <div className="grid grid-cols-2 gap-3 mt-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Abono Inicial</label>
                <input
                    type="number"
                    step="0.01"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="0.00"
                    value={initialPayment}
                    onChange={e => setInitialPayment(e.target.value)}
                />
              </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Método de Pago</label>
                  <select
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    value={initialPaymentMethod}
                    onChange={e => setInitialPaymentMethod(e.target.value)}
                  >
                    <option value="efectivo">Efectivo</option>
                    <option value="tarjeta">Tarjeta</option>
                  </select>
              </div>
            </div>
          )}
            </div>

          {/* Cart Items */}
          <div className="">
            <table className="w-full">
              <thead className="bg-gray-100 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-left text-sm">Producto</th>
                  <th className="px-3 py-2 text-center text-sm">Cant</th>
                  <th className="px-3 py-2 text-right text-sm">Precio</th>
                  <th className="px-3 py-2 text-right text-sm">Desc%</th>
                  <th className="px-3 py-2 text-right text-sm">Total</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {cart.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-400">
                      Carrito vacío
                    </td>
                  </tr>
                ) : (
                  cart.map(ci => {
                    const unit = parseFloat(ci.product.price || '0')
                    const lineSub = unit * ci.quantity
                    const discPct = ci.discount_pct || 0
                    const discAmt = lineSub * (discPct / 100)
                    const lineTotal = lineSub - discAmt
                    
                    return (
                      <tr key={ci.product.id} className="border-t">
                        <td className="px-3 py-2 text-sm">{ci.product.name}</td>
                        <td className="px-3 py-2 text-center">
                          <input
                            type="number"
                            min="1"
                            value={ci.quantity}
                            onChange={e => updateQty(ci.product.id, Number(e.target.value))}
                            className="w-16 border rounded px-2 py-1 text-center"
                          />
                        </td>
                        <td className="px-3 py-2 text-right text-sm">${unit.toFixed(2)}</td>
                        <td className="px-3 py-2">
                          <input
                            type="number"
                            step="0.01"
                            value={discPct}
                            onChange={e => updateLineDiscountPct(ci.product.id, e.target.value)}
                            className="w-16 border rounded px-2 py-1 text-right"
                          />
                        </td>
                        <td className="px-3 py-2 text-right font-bold">
                          ${lineTotal.toFixed(2)}
                        </td>
                        <td className="px-3 py-2">
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
              <span className="font-bold">${subtotal.toFixed(2)}</span>
            </div>

              <div>
                <label className="text-sm">IVA %</label>
                <input
                  type="number"
                  step="0.01"
                  value={taxRate}
                  onChange={e => setTaxRate(e.target.value)}
                  className="w-full border rounded px-3 py-1"
                />
            </div>

            {discountAmountCalc > 0 && (
              <div className="flex justify-between text-red-600">
                <span>Descuento:</span>
                <span>-${discountAmountCalc.toFixed(2)}</span>
              </div>
            )}

            {taxAmount > 0 && (
              <div className="flex justify-between text-sm">
                <span>IVA:</span>
                <span>${taxAmount.toFixed(2)}</span>
              </div>
            )}

            <div className="border-t-2 border-gray-300 pt-2 flex justify-between text-2xl font-bold">
              <span>TOTAL:</span>
              <span className="text-green-600">${total.toFixed(2)}</span>
            </div>

            {/* Profit Display */}
            <div className="bg-purple-100 rounded p-2 flex justify-between">
              <span className="font-medium">💰 Utilidad:</span>
              <span className="font-bold text-purple-700">${profit.toFixed(2)}</span>
            </div>

            {/* Payment fields (only for contado) */}
            {saleType === 'contado' && (
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
              disabled={cart.length === 0}
              className="w-full bg-green-600 text-white py-4 rounded-lg text-xl font-bold hover:bg-green-700 disabled:bg-gray-400"
            >
              {saleType === 'credito' ? '💳 Vender a Abonos' : '💵 Cobrar'}
            </button>
          </div>

          {/* Messages */}
          {msg && (
            <div className={`p-3 rounded-lg ${msg.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {msg}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
