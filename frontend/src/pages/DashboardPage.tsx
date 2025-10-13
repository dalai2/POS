import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

export default function DashboardPage() {
  const [status, setStatus] = useState<any>(null)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    (async () => {
      try {
        const s = await api.get('/billing/status')
        setStatus(s.data)
      } catch (e: any) {
        setMsg(e?.response?.data?.detail || 'Error loading status')
      }
    })()
  }, [])

  return (
    <Layout>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Inicio</h1>
        {status && (
          <div className="grid sm:grid-cols-3 gap-4">
            <div className="p-4 border rounded bg-white">
              <div className="text-sm text-slate-500">Plan</div>
              <div className="text-xl font-bold">{status.plan || '—'}</div>
            </div>
            <div className="p-4 border rounded bg-white">
              <div className="text-sm text-slate-500">Estado</div>
              <div className="text-xl font-bold">{status.is_active ? 'Activo' : 'Inactivo'}</div>
            </div>
            <div className="p-4 border rounded bg-white">
              <div className="text-sm text-slate-500">Tenant</div>
              <div className="text-xl font-bold">{status.tenant}</div>
            </div>
          </div>
        )}
        {msg && <p className="text-sm text-red-600">{msg}</p>}
      </div>
    </Layout>
  )
}



