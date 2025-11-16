/**
 * Ticket Generator Utility
 * Provides functions to generate professional tickets for sales, pedidos, and payments
 */

import { api } from './api'

/**
 * Load company logo as base64
 */
export const getLogoAsBase64 = async (): Promise<string> => {
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

/**
 * Open and print HTML ticket
 */
export const openAndPrintTicket = (html: string) => {
  const w = window.open('', '_blank')
  if (!w) {
    console.error('Could not open print window')
    return
  }
  w.document.write(html)
  w.document.close()
  w.addEventListener('load', () => setTimeout(() => w.print(), 300))
  setTimeout(() => {
    if (!w.closed) w.print()
  }, 1000)
}

/**
 * Generate HTML for pedido ticket (initial or payment)
 */
export const generatePedidoTicketHTML = (params: {
  pedido: any
  producto?: any  // Opcional para compatibilidad hacia atrás
  items?: any[]   // Array de items para múltiples productos
  vendedorEmail?: string
  paymentData?: {
    amount: number
    method: string
    previousPaid: number
    newPaid: number
    previousBalance: number
    newBalance: number
    efectivo?: number
    tarjeta?: number
  }
  logoBase64: string
}): string => {
  const { pedido, producto, items, vendedorEmail, paymentData, logoBase64 } = params

  // Determinar si usar items o producto (compatibilidad hacia atrás)
  const itemsToShow = items && items.length > 0 ? items : (producto ? [producto] : [])

  // Build items HTML
  let itemsHTML = ''
  let totalItems = 0

  itemsToShow.forEach((item) => {
    const descParts = []
    if (item.nombre) descParts.push(item.nombre)
    if (item.modelo) descParts.push(item.modelo)
    if (item.color) descParts.push(item.color)
    if (item.quilataje) descParts.push(item.quilataje)
    if (item.peso_gramos) {
      const peso = Number(item.peso_gramos)
      if (peso === Math.floor(peso)) {
        descParts.push(`${peso}g`)
      } else {
        descParts.push(peso.toFixed(3).replace(/\.?0+$/, '') + 'g')
      }
    }
    if (item.talla) descParts.push(item.talla)
    const description = descParts.length > 0 ? descParts.join('-') : 'Producto sin descripción'

    const unitPrice = Number(item.precio_unitario || item.precio || pedido.precio_unitario || 0)
    const quantity = Number(item.cantidad || pedido.cantidad || 1)
    totalItems += quantity
    const itemTotal = unitPrice * quantity

    itemsHTML += `
      <tr>
        <td>${quantity}</td>
        <td>${item.codigo || ''}</td>
        <td>${description}</td>
        <td>$${unitPrice.toFixed(2)}</td>
        <td>-</td>
        <td>$${itemTotal.toFixed(2)}</td>
      </tr>`
  })

  const vendedorInfo = vendedorEmail ? vendedorEmail.split('@')[0].toUpperCase() : 'N/A'
  const formattedDate = new Date(pedido.created_at).toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })

  const total = Number(pedido.total)
  const abonoInicial = Number(pedido.anticipo_pagado || 0)
  const saldoPendiente = total - abonoInicial

  // Build payment details section
  let paymentDetailsHTML = ''
  if (paymentData) {
    // This is a payment ticket
    const desglose = paymentData.method.toUpperCase() === 'MIXTO' && paymentData.efectivo !== undefined && paymentData.tarjeta !== undefined
      ? `
      <div style="margin-left: 20px;"><strong>- EFECTIVO :</strong> $${paymentData.efectivo.toFixed(2)}</div>
      <div style="margin-left: 20px;"><strong>- TARJETA :</strong> $${paymentData.tarjeta.toFixed(2)}</div>
      `
      : ''
    
    paymentDetailsHTML = `
      <div><strong>TOTAL :</strong> $${total.toFixed(2)}</div>
      <div><strong>PAGADO PREVIO :</strong> $${paymentData.previousPaid.toFixed(2)}</div>
      <div><strong>ABONO ACTUAL :</strong> $${paymentData.amount.toFixed(2)} (${paymentData.method.toUpperCase()})</div>
      ${desglose}
      <div><strong>NUEVO TOTAL ABONADO :</strong> $${paymentData.newPaid.toFixed(2)}</div>
      <div><strong>SALDO PENDIENTE :</strong> $${Math.max(paymentData.newBalance, 0).toFixed(2)}</div>
    `
  } else {
    // This is an initial ticket
    paymentDetailsHTML = `
      <div><strong>TOTAL :</strong> $${total.toFixed(2)}</div>
      <div><strong>ABONO INICIAL :</strong> $${abonoInicial.toFixed(2)}</div>
      <div><strong>TOTAL DE ABONOS :</strong> $${abonoInicial.toFixed(2)}</div>
      <div><strong>SALDO PENDIENTE :</strong> $${saldoPendiente.toFixed(2)}</div>
    `
  }

  return `<!DOCTYPE html>
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
        <div><strong>FOLIO DE PEDIDO :</strong> ${pedido.folio_pedido || 'PED-' + String(pedido.id).padStart(6, '0')}</div>
        <div><strong>FECHA PEDIDO :</strong> ${formattedDate}</div>
        <div><strong>MÉTODO DE PAGO :</strong> ${paymentData ? (paymentData.method.toUpperCase() === 'MIXTO' ? 'EFECTIVO / TARJETA' : (paymentData.method.toUpperCase() === 'CASH' || paymentData.method.toUpperCase() === 'EFECTIVO' ? 'EFECTIVO' : (paymentData.method.toUpperCase() === 'CARD' || paymentData.method.toUpperCase() === 'TARJETA' ? 'TARJETA' : 'N/A'))) : 'N/A'}</div>
        <div>HIDALGO #112 ZONA CENTRO, LOCAL 12, 23 Y 24 C.P: 37000. LEÓN, GTO.</div>
        <div>WhatsApp: 4776621788</div>
      </div>
    </div>

    <!-- Customer Info -->
    <table class="customer-info">
      <tr>
        <td><strong>Cliente:</strong></td>
        <td>${pedido.cliente_nombre || 'Sin nombre'}</td>
      </tr>
      <tr>
        <td><strong>Teléfono:</strong></td>
        <td>${pedido.cliente_telefono || ''}</td>
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
        ${itemsHTML}
      </tbody>
    </table>

    <!-- Totals -->
    <div class="totals">
      ${paymentDetailsHTML}
    </div>

    <!-- Footer Section -->
    <div class="footer-section">
      <!-- Footer -->
      <div class="footer-info">
        <div>${totalItems || pedido.cantidad || 1} Articulo(s)</div>
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
}

/**
 * Save ticket to database
 */
export const saveTicket = async (params: {
  saleId?: number
  pedidoId?: number
  kind: string
  html: string
}): Promise<void> => {
  try {
    await api.post('/tickets', {
      sale_id: params.saleId,
      pedido_id: params.pedidoId,
      kind: params.kind,
      html: params.html
    })
    console.log('Ticket saved successfully')
  } catch (error) {
    console.error('Error saving ticket:', error)
    // Don't throw - ticket was printed, saving is secondary
  }
}

/**
 * Generate HTML for apartado/credit payment ticket
 */
export const generateApartadoPaymentTicketHTML = (params: {
  sale: any
  saleItems: any[]
  paymentData: {
    amount: number
    method: string
    previousPaid: number
    newPaid: number
    newBalance: number
    efectivo?: number
    tarjeta?: number
  }
  vendedorEmail?: string
  logoBase64: string
}): string => {
  const { sale, saleItems, paymentData, vendedorEmail, logoBase64 } = params

  // Build items HTML
  let itemsHTML = ''
  let totalItems = 0

  saleItems.forEach((item) => {
    // Get product data from either product or product_snapshot
    const product = item.product || item.product_snapshot || {}
    
    const descParts = []
    if (product.name) descParts.push(product.name)
    if (product.modelo) descParts.push(product.modelo)
    if (product.nombre) descParts.push(product.nombre)
    if (product.color) descParts.push(product.color)
    if (product.quilataje) descParts.push(product.quilataje)
    if (product.peso_gramos) {
      const peso = Number(product.peso_gramos)
      if (peso === Math.floor(peso)) {
        descParts.push(`${peso}g`)
      } else {
        descParts.push(peso.toFixed(3).replace(/\.?0+$/, '') + 'g')
      }
    }
    if (product.talla) descParts.push(product.talla)
    // If no description parts, use item.name as fallback
    const description = descParts.length > 0 ? descParts.join('-') : (item.name || 'Producto sin descripción')

    const unitPrice = Number(item.unit_price || 0)
    const discountPct = Number(item.discount_pct || 0)
    const quantity = Number(item.quantity || 1)
    totalItems += quantity

    // Calculate original price if there's a discount
    let originalPrice = unitPrice
    if (discountPct > 0 && discountPct < 100) {
      originalPrice = unitPrice / (1 - discountPct / 100)
    }

    const itemTotal = unitPrice * quantity
    const discountDisplay = discountPct > 0 ? `${discountPct.toFixed(1)}%` : '-'
    const codigo = product.codigo || item.codigo || ''

    itemsHTML += `
      <tr>
        <td>${quantity}</td>
        <td>${codigo}</td>
        <td>${description}</td>
        <td>$${originalPrice.toFixed(2)}</td>
        <td>${discountDisplay}</td>
        <td>$${itemTotal.toFixed(2)}</td>
      </tr>`
  })

  const vendedorInfo = vendedorEmail ? vendedorEmail.split('@')[0].toUpperCase() : 'N/A'
  const formattedDate = new Date().toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })

  const saleTotal = Number(sale.total)

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Ticket Abono ${sale.id}</title>
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
        <div><strong>FOLIO DE APARTADO :</strong> ${sale.folio_apartado || 'APT-' + String(sale.id).padStart(6, '0')}</div>
        <div><strong>FECHA VENTA :</strong> ${formattedDate}</div>
        <div><strong>MÉTODO DE PAGO :</strong> ${paymentData.method.toUpperCase() === 'MIXTO' ? 'EFECTIVO / TARJETA' : (paymentData.method.toUpperCase() === 'CASH' || paymentData.method.toUpperCase() === 'EFECTIVO' ? 'EFECTIVO' : (paymentData.method.toUpperCase() === 'CARD' || paymentData.method.toUpperCase() === 'TARJETA' ? 'TARJETA' : 'N/A'))}</div>
        <div>HIDALGO #112 ZONA CENTRO, LOCAL 12, 23 Y 24 C.P: 37000. LEÓN, GTO.</div>
        <div>WhatsApp: 4776621788</div>
      </div>
    </div>

    <!-- Customer Info -->
    <table class="customer-info">
      <tr>
        <td><strong>Cliente:</strong></td>
        <td>${sale.customer_name || 'Sin nombre'}</td>
      </tr>
      <tr>
        <td><strong>Teléfono:</strong></td>
        <td>${sale.customer_phone || ''}</td>
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
        ${itemsHTML}
      </tbody>
    </table>

    <!-- Totals -->
    <div class="totals">
      <div><strong>TOTAL :</strong> $${saleTotal.toFixed(2)}</div>
      <div><strong>PAGADO PREVIO :</strong> $${paymentData.previousPaid.toFixed(2)}</div>
      <div><strong>ABONO ACTUAL :</strong> $${paymentData.amount.toFixed(2)} (${paymentData.method.toUpperCase()})</div>
      ${paymentData.method.toUpperCase() === 'MIXTO' && paymentData.efectivo !== undefined && paymentData.tarjeta !== undefined ? `
      <div style="margin-left: 20px;"><strong>- EFECTIVO :</strong> $${paymentData.efectivo.toFixed(2)}</div>
      <div style="margin-left: 20px;"><strong>- TARJETA :</strong> $${paymentData.tarjeta.toFixed(2)}</div>
      ` : ''}
      <div><strong>NUEVO TOTAL ABONADO :</strong> $${paymentData.newPaid.toFixed(2)}</div>
      <div><strong>SALDO PENDIENTE :</strong> $${Math.max(paymentData.newBalance, 0).toFixed(2)}</div>
    </div>

    <!-- Footer Section -->
    <div class="footer-section">
      <!-- Footer -->
      <div class="footer-info">
        <div>${totalItems} Articulo(s)</div>
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
}

