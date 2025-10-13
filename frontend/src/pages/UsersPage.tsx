import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type User = { id: number; email: string; role: string }

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('cashier')
  const [msg, setMsg] = useState('')

  const load = async () => {
    try {
      const r = await api.get('/admin/users')
      setUsers(r.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error loading users')
    }
  }

  const add = async () => {
    try {
      await api.post('/admin/users', { email, password, role })
      setEmail(''); setPassword(''); setRole('cashier')
      await load()
      setMsg('User created')
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error creating user')
    }
  }

  useEffect(() => { load() }, [])

  return (
    <Layout>
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Usuarios</h1>
        <div className="flex gap-2">
          <input className="input" placeholder="Correo" value={email} onChange={e => setEmail(e.target.value)} />
          <input className="input" placeholder="Contraseña" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          <select className="input" value={role} onChange={e => setRole(e.target.value)}>
            <option value="cashier">Cashier</option>
            <option value="admin">Admin</option>
            <option value="owner">Owner</option>
          </select>
          <button className="btn" onClick={add}>Agregar</button>
        </div>
        <table className="w-full">
          <thead><tr><th className="p-2">ID</th><th className="p-2">Correo</th><th className="p-2">Rol</th></tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-t"><td className="p-2">{u.id}</td><td className="p-2">{u.email}</td><td className="p-2">{u.role}</td></tr>
            ))}
          </tbody>
        </table>
        {msg && <p className="text-sm text-green-700">{msg}</p>}
      </div>
    </Layout>
  )
}



