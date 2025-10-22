import React, { useEffect, useRef, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type Sale = { id: number; total: string; created_at: string; user_id?: number | null }

export default function SalesHistoryPage() {
  const [sales, setSales] = useState<Sale[]>([])
  const [msg, setMsg] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [userId, setUserId] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 20

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

  useEffect(() => { load() }, [])

  const printSaleTicket = (saleData: any) => {
    try {
      const w = window.open('', '_blank')
      if (!w) return

      const items = saleData.items || []
      const date = new Date(saleData.created_at || new Date())
      const formattedDate = date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      }).replace('.', '')

      const customerInfo = saleData.customer_name || 'Cliente Genérico'
      const vendedorInfo = 'Vendedor 1' // Esto debería venir del backend

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
      margin: 0.5cm;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: 'Courier New', monospace;
      font-size: 10px;
      line-height: 1.2;
    }
  }
  body {
    margin: 0;
    padding: 5px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    line-height: 1.2;
    width: 100%;
  }
  .center { text-align: center; }
  .right { text-align: right; }
  .left { text-align: left; }
  .bold { font-weight: bold; }
  .header-title { font-size: 14px; font-weight: bold; }
  .header-subtitle { font-size: 12px; }
  .info-section { margin: 8px 0; }
  .table-header { font-weight: bold; border-bottom: 1px solid #000; margin: 5px 0; }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 3px 0;
  }
  td {
    padding: 1px 2px;
    vertical-align: top;
    font-size: 9px;
  }
  .total-row { border-top: 1px solid #000; font-weight: bold; }
  .footer { text-align: center; margin-top: 10px; font-size: 8px; }
</style></head>
<body>
  <div style="max-width: 190mm; margin: 0 auto;">
    <!-- Header -->
    <div class="center info-section">
      <div class="header-title">Matriz Relación de Mercancía</div>
    </div>

    <!-- Sale Info -->
    <div class="info-section" style="display: flex; justify-content: space-between;">
      <div>
        <div><strong>Folio</strong> ${saleData.id}</div>
        <div><strong>Fecha</strong> ${formattedDate}</div>
      </div>
      <div style="text-align: right;">
        <div><strong>Vence</strong> ${formattedDate}</div>
        <div><strong>Alm</strong> Matriz Almacén</div>
        <div><strong>Vend</strong> ${vendedorInfo}</div>
        <div><strong>Estatus</strong> Activo</div>
      </div>
    </div>

    <!-- Client Info -->
    <div class="info-section" style="margin-bottom: 10px;">
      <div><strong>Tipo C</strong> ${saleData.tipo_venta === 'credito' ? 'Crédito' : 'Contado'}</div>
      <div><strong>Base Oro</strong> 2135.00</div>
      <div><strong>Base Plata</strong> 19.50</div>
    </div>

    <!-- Items Table -->
    <table>
      <thead>
        <tr class="table-header">
          <td style="width: 8%;">Un</td>
          <td style="width: 8%;">Precio</td>
          <td style="width: 8%;">% Desc</td>
          <td style="width: 12%;">$ Neto</td>
          <td style="width: 12%;">Importe</td>
        </tr>
      </thead>
      <tbody>
        ${items.map((item: any) => `
          <tr>
            <td>${item.quantity}</td>
            <td>$${(parseFloat(item.unit_price || '0')).toFixed(2)}</td>
            <td>${(parseFloat(item.discount_pct || '0')).toFixed(2)}</td>
            <td>$${(parseFloat(item.unit_price || '0') * (1 - (parseFloat(item.discount_pct || '0')) / 100)).toFixed(2)}</td>
            <td>$${(parseFloat(item.total_price || '0')).toFixed(2)}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    <!-- Totals -->
    <div style="margin-top: 10px; text-align: right;">
      <div>Sub Total: $${subtotal.toFixed(2)}</div>
      ${discountAmount > 0 ? `<div>Descuento: $${discountAmount.toFixed(2)}</div>` : ''}
      ${taxAmount > 0 ? `<div>I.V.A.: $${taxAmount.toFixed(2)}</div>` : ''}
      <div style="font-size: 12px; font-weight: bold; border-top: 1px solid #000; padding-top: 3px;">
        Total: $${total.toFixed(2)}
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div>¡Gracias por su compra!</div>
      <div>JOYERÍA EL DIAMANTE</div>
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


