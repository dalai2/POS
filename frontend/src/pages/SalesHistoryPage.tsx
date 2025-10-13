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

  const ticket = async (id: number) => {
    try {
      const r = await api.get(`/sales/${id}`)
      const w = window.open('', '_blank', 'width=400,height=600')
      if (!w) return
      const sale = r.data
      const items = sale.items || []
      const date = sale.created_at ? new Date(sale.created_at) : new Date()
      const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ticket ${sale.id}</title></head><body onload="window.print()">Folio ${sale.id} - ${date.toLocaleString()}<hr/>${items.map((it: any)=>`${it.quantity} x ${it.name} $${Number(it.total_price).toFixed(2)}`).join('<br/>')}<hr/>Total $${Number(sale.total).toFixed(2)}</body></html>`
      w.document.write(html)
      w.document.close()
    } catch {}
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
                  <button className="btn" onClick={async () => { if (!confirm('¿Devolver venta completa?')) return; try { await api.post(`/sales/${s.id}/return`); await load(0) } catch (e:any) { setMsg(e?.response?.data?.detail || 'Error al devolver') } }}>Devolver</button>
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


