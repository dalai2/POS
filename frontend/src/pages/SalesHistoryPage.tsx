import React, { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type Sale = { id: number; total: string; created_at: string; user_id?: number | null; vendedor_id?: number | null }
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
      if (userId) qs.set('user_id', userId)
      qs.set('skip', String(nextPage * pageSize))
      qs.set('limit', String(pageSize))
      const r = await api.get(`/sales?${qs.toString()}`)
      setSales(r.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error cargando ventas')
    }
  }

  useEffect(() => { 
    load()
    loadUsers()
  }, [])

  const printSaleTicket = (saleData: any) => {
    try {
      const w = window.open('', '_blank')
      if (!w) return

      const items = saleData.items || []
      const date = new Date(saleData.created_at || new Date())
      const formattedDate = date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      })

      const customerInfo = saleData.customer_name || 'PUBLICO GENERAL'
      // Find vendedor name from users list - try vendedor_id first, then user_id as fallback
      const vendedorUserId = saleData.vendedor_id || saleData.user_id
      const vendedorUser = vendedorUserId ? users.find(u => u.id === vendedorUserId) : null
      const vendedorInfo = vendedorUser ? (vendedorUser.email.split('@')[0].toUpperCase()) : 'N/A'

      const subtotal = parseFloat(saleData.subtotal || '0')
      const discountAmount = parseFloat(saleData.discount_amount || '0')
      const taxAmount = parseFloat(saleData.tax_amount || '0')
      const total = parseFloat(saleData.total || '0')

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
        <img src="/logo.png?v=1" alt="Logo" style="max-width: 450px; max-height: 250px; display: block;" onerror="this.style.display='none'" />
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
        <td></td>
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
        ${items.map((item: any) => {
          const unitPrice = parseFloat(item.unit_price || '0')
          const discountPct = parseFloat(item.discount_pct || '0')
          const discountAmount = unitPrice * discountPct / 100
          return `
          <tr>
            <td>${item.quantity}</td>
            <td>${item.product?.code || ''}</td>
            <td>${item.product?.name || ''}</td>
            <td>$${unitPrice.toFixed(2)}</td>
            <td>$${discountAmount.toFixed(2)}</td>
            <td>$${(parseFloat(item.total_price || '0')).toFixed(2)}</td>
          </tr>
        `}).join('')}
      </tbody>
    </table>

    <!-- Totals -->
    <div class="totals">
      <div><strong>TOTAL :</strong> $${total.toFixed(2)}</div>
      <div><strong>ABONOS/ANTICIPO :</strong> $0.00</div>
      <div><strong>SALDO :</strong> $${total.toFixed(2)}</div>
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
  </div>
</body></html>`

      w.document.write(html)
      w.document.close()
      w.print()
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
            <div className="text-xs text-slate-600">Usuario (ID)</div>
            <input className="input" value={userId} onChange={e => setUserId(e.target.value)} />
          </div>
          <button className="btn" onClick={() => { setPage(0); load(0) }}>Filtrar</button>
          <button className="btn" onClick={async () => {
            const qs = new URLSearchParams()
            if (dateFrom) qs.set('date_from', new Date(dateFrom).toISOString())
            if (dateTo) qs.set('date_to', new Date(dateTo).toISOString())
            if (userId) qs.set('user_id', userId)
            const url = `/sales/export?${qs.toString()}`
            const host = import.meta.env.VITE_API_URL || 'http://localhost:8000'
            window.open(`${host}${url}`, '_blank')
          }}>Exportar CSV</button>
        </div>
        <table className="w-full text-left">
          <thead><tr><th className="p-2">Folio</th><th className="p-2">Fecha</th><th className="p-2">Total</th><th className="p-2">Acciones</th></tr></thead>
          <tbody>
            {sales.map(s => (
              <tr key={s.id} className="border-t">
                <td className="p-2">{s.id}</td>
                <td className="p-2">{new Date(s.created_at).toLocaleString()}</td>
                <td className="p-2">${Number(s.total).toFixed(2)}</td>
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


