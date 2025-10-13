import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

export default function BillingPage() {
  const [priceId, setPriceId] = useState('')
  const [msg, setMsg] = useState('')
  const [plans, setPlans] = useState<any[]>([])
  const [status, setStatus] = useState<any>(null)

  const startCheckout = async () => {
    try {
      const r = await api.post('/billing/checkout-session', { price_id: priceId })
      const url = r.data.url
      if (url) window.location.href = url
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error starting checkout')
    }
  }

  const load = async () => {
    try {
      const p = await api.get('/billing/plans')
      setPlans(p.data.plans)
      const s = await api.get('/billing/status')
      setStatus(s.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error loading billing info')
    }
  }

  useEffect(() => { load() }, [])

  return (
    <Layout>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Facturación</h1>
        {status && (
          <div className="p-3 bg-slate-50 rounded border text-sm">
            <div><b>Estado:</b> {status.is_active ? 'Activo' : 'Inactivo'}</div>
            <div><b>Plan:</b> {status.plan || '—'}</div>
          </div>
        )}
        <div className="grid md:grid-cols-2 gap-4">
          {plans.map(pl => (
            <div key={pl.key} className="border rounded p-4 bg-white">
              <div className="text-lg font-semibold">{pl.name}</div>
              <div className="text-2xl font-bold mt-1">${(pl.amount/100).toFixed(2)} <span className="text-sm text-slate-500">/{pl.interval}</span></div>
              <button className="btn mt-3" onClick={() => { setPriceId(pl.price_month); startCheckout() }}>Suscribirse</button>
            </div>
          ))}
        </div>
        {msg && <p className="text-sm text-red-600">{msg}</p>}
      </div>
    </Layout>
  )
}


