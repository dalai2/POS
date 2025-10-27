import React, { useState } from 'react'
import axios from 'axios'
import { api } from '../utils/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function LoginPage() {
  const [tenant, setTenant] = useState('brazo')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await api.post(`/auth/login`, { email, password }, { headers: { 'X-Tenant-ID': tenant } })
      localStorage.setItem('access', res.data.access_token)
      localStorage.setItem('refresh', res.data.refresh_token)
      localStorage.setItem('tenant', tenant)
      localStorage.setItem('role', res.data.role || 'cashier')
      window.location.href = '/products'
    } catch (err: any) {
      setMessage(err?.response?.data?.detail || 'Inicio de sesión fallido')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form className="w-full max-w-sm space-y-3" onSubmit={onSubmit}>
        <h1 className="text-2xl font-bold">Iniciar sesión</h1>
        <input className="input" placeholder="Tenant" value={tenant} onChange={e => setTenant(e.target.value)} />
        <input className="input" placeholder="Correo" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="input" placeholder="Contraseña" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        <button className="btn" type="submit">Entrar</button>
        {message && <p className="text-red-600 text-sm">{message}</p>}
      </form>
    </div>
  )
}


