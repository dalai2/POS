import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { api } from '../utils/api'

type User = { 
  id: number
  email: string
  role: string 
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [msg, setMsg] = useState('')
  const [userRole, setUserRole] = useState<string>('')
  
  // Form states
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [formEmail, setFormEmail] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formRole, setFormRole] = useState('cashier')

  const load = async () => {
    try {
      const r = await api.get('/admin/users')
      setUsers(r.data)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error loading users')
    }
  }

  useEffect(() => {
    const role = localStorage.getItem('role') || ''
    setUserRole(role)
    
    if (role !== 'owner') {
      return
    }
    
    load()
  }, [])

  // Verificar permisos
  if (userRole !== 'owner') {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">⛔ Acceso Denegado</h2>
            <p className="text-gray-600">Solo el dueño puede gestionar usuarios.</p>
          </div>
        </div>
      </Layout>
    )
  }

  const openAddModal = () => {
    setEditingUser(null)
    setFormEmail('')
    setFormPassword('')
    setFormRole('cashier')
    setShowAddModal(true)
  }

  const openEditModal = (user: User) => {
    setEditingUser(user)
    setFormEmail(user.email)
    setFormPassword('')
    setFormRole(user.role)
    setShowAddModal(true)
  }

  const closeModal = () => {
    setShowAddModal(false)
    setEditingUser(null)
    setFormEmail('')
    setFormPassword('')
    setFormRole('cashier')
  }

  const saveUser = async () => {
    if (!formEmail) {
      setMsg('⚠️ El correo es requerido')
      return
    }
    
    if (!editingUser && !formPassword) {
      setMsg('⚠️ La contraseña es requerida para nuevos usuarios')
      return
    }

    try {
      if (editingUser) {
        // Update existing user
        const updateData: any = { role: formRole }
        if (formEmail !== editingUser.email) {
          updateData.email = formEmail
        }
        if (formPassword) {
          updateData.password = formPassword
        }
        
        await api.put(`/admin/users/${editingUser.id}`, updateData)
        setMsg('✅ Usuario actualizado correctamente')
      } else {
        // Create new user
        await api.post('/admin/users', {
          email: formEmail,
          password: formPassword,
          role: formRole
        })
        setMsg('✅ Usuario creado correctamente')
      }
      
      closeModal()
      await load()
      setTimeout(() => setMsg(''), 3000)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error guardando usuario')
    }
  }

  const deleteUser = async (userId: number, userEmail: string) => {
    if (!confirm(`¿Estás seguro de eliminar al usuario ${userEmail}?`)) {
      return
    }

    try {
      await api.delete(`/admin/users/${userId}`)
      setMsg('✅ Usuario eliminado correctamente')
      await load()
      setTimeout(() => setMsg(''), 3000)
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'Error eliminando usuario')
    }
  }

  const getRoleBadge = (role: string) => {
    const badges = {
      owner: 'bg-purple-100 text-purple-800',
      admin: 'bg-blue-100 text-blue-800',
      cashier: 'bg-gray-100 text-gray-800'
    }
    const labels = {
      owner: 'Dueño',
      admin: 'Administrador',
      cashier: 'Cajero'
    }
    return { color: badges[role as keyof typeof badges] || badges.cashier, label: labels[role as keyof typeof labels] || role }
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-800">👥 Gestión de Usuarios</h1>
          <button
            onClick={openAddModal}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center gap-2"
          >
            ➕ Nuevo Usuario
          </button>
        </div>

        {/* Messages */}
        {msg && (
          <div className={`p-3 rounded-lg ${msg.includes('✅') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {msg}
          </div>
        )}

        {/* Users Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No hay usuarios registrados
                  </td>
                </tr>
              ) : (
                users.map(u => {
                  const badge = getRoleBadge(u.role)
                  return (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{u.id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {u.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${badge.color}`}>
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => openEditModal(u)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          ✏️ Editar
                        </button>
                        <button
                          onClick={() => deleteUser(u.id, u.email)}
                          className="text-red-600 hover:text-red-900 ml-4"
                        >
                          🗑️ Eliminar
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
          </tbody>
        </table>
        </div>

        {/* Add/Edit Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-semibold mb-4">
                {editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Correo electrónico
                  </label>
                  <input
                    type="email"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder="usuario@ejemplo.com"
                    value={formEmail}
                    onChange={e => setFormEmail(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña {editingUser && <span className="text-xs text-gray-500">(dejar vacío para no cambiar)</span>}
                  </label>
                  <input
                    type="password"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    placeholder={editingUser ? "••••••••" : "Contraseña"}
                    value={formPassword}
                    onChange={e => setFormPassword(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Rol
                  </label>
                  <select
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    value={formRole}
                    onChange={e => setFormRole(e.target.value)}
                  >
                    <option value="cashier">Cajero</option>
                    <option value="admin">Administrador</option>
                    <option value="owner">Dueño</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    <strong>Cajero:</strong> Solo punto de venta | 
                    <strong> Admin:</strong> Gestión completa | 
                    <strong> Dueño:</strong> Control total
                  </p>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={closeModal}
                  className="flex-1 bg-gray-500 text-white py-2 px-4 rounded-lg hover:bg-gray-600"
                >
                  Cancelar
                </button>
                <button
                  onClick={saveUser}
                  className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700"
                >
                  {editingUser ? 'Actualizar' : 'Crear'} Usuario
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
