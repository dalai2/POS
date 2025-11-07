import React, { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type Sale = { id: number; total: string; created_at: string; user_id?: number | null; vendedor_id?: number | null; tipo_venta?: string; user?: { email: string } }
type User = { id: number; email: string }

export default function SalesHistoryPage() {
  const [sales, setSales] = useState<Sale[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [msg, setMsg] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [userId, setUserId] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 20

  const loadUsers = async () => {
    try {
      const r = await api.get('/admin/users')
      setUsers(r.data || [])
    } catch (e) {
      console.error('Error loading users:', e)
    }
  }

  const load = async (nextPage = page) => {
    try {
      const qs = new URLSearchParams()
      if (dateFrom) qs.set('date_from', new Date(dateFrom).toISOString())
      if (dateTo) qs.set('date_to', new Date(dateTo).toISOString())
      if (userId && userId.trim() && !isNaN(Number(userId))) qs.set('user_id', userId)
      qs.set('skip', String(nextPage * pageSize))
      qs.set('limit', String(pageSize))
      const r = await api.get(`/sales?${qs.toString()}`)
      setSales(r.data)
    } catch (e: any) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Error cargando ventas'
      setMsg(typeof errorMsg === 'string' ? errorMsg : 'Error cargando ventas')
    }
  }

  useEffect(() => { 
    load()
    loadUsers()
  }, [])

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

  const printSaleTicket = async (saleData: any) => {
    try {
      const logoBase64 = await getLogoAsBase64()
      const w = window.open('', '_blank')
      if (!w) return
      
      await new Promise(resolve => setTimeout(resolve, 100))

      const items = saleData.items || []
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
      const efectivoPaid = paymentInfo.filter((p: any) => p.method === 'cash' || p.method === 'efectivo').reduce((sum: number, p: any) => sum + parseFloat(p.amount), 0)
      const tarjetaPaid = paymentInfo.filter((p: any) => p.method === 'card' || p.method === 'tarjeta').reduce((sum: number, p: any) => sum + parseFloat(p.amount), 0)

      const subtotal = parseFloat(saleData.subtotal || '0')
      const discountAmount = parseFloat(saleData.discount_amount || '0')
      const taxAmount = parseFloat(saleData.tax_amount || '0')
      const total = parseFloat(saleData.total || '0')
      
      // Calculate abono and saldo based on sale type
      let abonoAmount = 0
      let saldoAmount = 0
      
      if (saleData.tipo_venta === 'contado') {
        // For contado sales, show total paid and saldo = 0
        abonoAmount = efectivoPaid + tarjetaPaid
        saldoAmount = 0
      } else {
        // For abono sales, show total paid and remaining balance
        abonoAmount = efectivoPaid + tarjetaPaid
        saldoAmount = total - abonoAmount
      }

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
          <th style="width: 12%;">Precio x gramo</th>
          <th style="width: 10%;">Desc%</th>
          <th style="width: 12%;">Importe</th>
        </tr>
      </thead>
      <tbody>
        ${items.map((item: any) => {
          const precioConDescuento = parseFloat(item.unit_price || '0')
          const discountPct = parseFloat(item.discount_pct || '0')
          const quantity = parseInt(item.quantity || '1')
          // Si hay descuento, calcular precio original
          const precioOriginal = discountPct > 0 && discountPct < 100 ? precioConDescuento / (1 - discountPct / 100) : precioConDescuento
          const importe = precioConDescuento * quantity
          
          return `
          <tr>
            <td>${quantity}</td>
            <td>${item.codigo || ''}</td>
            <td>${item.name || 'Producto sin descripción'}</td>
            <td>$${precioOriginal.toFixed(2)}</td>
            <td>${discountPct > 0 ? discountPct.toFixed(1) + '%' : '-'}</td>
            <td>$${importe.toFixed(2)}</td>
          </tr>
        `}).join('')}
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

  const ticket = async (id: number) => {
    try {
      const r = await api.get(`/sales/${id}`)
      printSaleTicket(r.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error al cargar ticket')
    }
  }

  return (
    <Layout>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Historial de ventas</h1>
        <div className="flex flex-wrap gap-2 items-end">
          <div>
            <div className="text-xs text-slate-600">Desde</div>
            <input className="input" type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          </div>
          <div>
            <div className="text-xs text-slate-600">Hasta</div>
            <input className="input" type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          </div>
          <div>
            <div className="text-xs text-slate-600">Usuario</div>
            <select className="input" value={userId} onChange={e => setUserId(e.target.value)}>
              <option value="">Todos los usuarios</option>
              {users.map(user => (
                <option key={user.id} value={user.id.toString()}>
                  {user.email.split('@')[0]} (ID: {user.id})
                </option>
              ))}
            </select>
          </div>
          <button className="btn" onClick={() => { setPage(0); load(0) }}>Filtrar</button>
          <button className="btn" onClick={async () => {
            try {
            const qs = new URLSearchParams()
            if (dateFrom) qs.set('date_from', new Date(dateFrom).toISOString())
            if (dateTo) qs.set('date_to', new Date(dateTo).toISOString())
            if (userId && userId.trim() && !isNaN(Number(userId))) qs.set('user_id', userId)
              
              const response = await api.get(`/sales/export?${qs.toString()}`, {
                responseType: 'blob'
              })
              
              // Create blob and download
              const blob = new Blob([response.data], { type: 'text/csv' })
              const url = window.URL.createObjectURL(blob)
              const link = document.createElement('a')
              link.href = url
              link.download = 'ventas.csv'
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
              window.URL.revokeObjectURL(url)
            } catch (e: any) {
              const errorMsg = e?.response?.data?.detail || e?.message || 'Error al exportar CSV'
              setMsg(typeof errorMsg === 'string' ? errorMsg : 'Error al exportar CSV')
            }
          }}>Exportar CSV</button>
        </div>
        <table className="w-full text-left">
          <thead><tr><th className="p-2">Folio</th><th className="p-2">Fecha</th><th className="p-2">Total</th><th className="p-2">Tipo</th><th className="p-2">Usuario</th><th className="p-2">Acciones</th></tr></thead>
          <tbody>
            {sales.map(s => (
              <tr key={s.id} className="border-t">
                <td className="p-2">{s.id}</td>
                <td className="p-2">{new Date(s.created_at).toLocaleString()}</td>
                <td className="p-2">${Number(s.total).toFixed(2)}</td>
                <td className="p-2">{s.tipo_venta === 'credito' ? 'abono' : (s.tipo_venta || 'contado')}</td>
                <td className="p-2">{s.user?.email ? s.user.email.split('@')[0] : 'N/A'}</td>
                <td className="p-2 flex gap-2">
                  <button className="btn" onClick={() => ticket(s.id)}>Ticket</button>
                  <button className="btn" onClick={async () => { if (!confirm('¿Devolver venta completa?')) return; try { await api.post(`/sales/${s.id}/return`); await load(0); setMsg('Venta devuelta exitosamente') } catch (e:any) { setMsg(e?.response?.data?.detail || 'Error al devolver venta') } }}>Devolver</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {msg && <p className="text-sm text-red-600">{msg}</p>}
        <div className="flex items-center gap-2">
          <button className="btn disabled:opacity-50" disabled={page === 0} onClick={() => { const np = Math.max(0, page - 1); setPage(np); load(np) }}>Anterior</button>
          <span>Página {page + 1}</span>
          <button className="btn disabled:opacity-50" disabled={sales.length < pageSize} onClick={() => { const np = page + 1; setPage(np); load(np) }}>Siguiente</button>
        </div>
      </div>
    </Layout>
  )
}


