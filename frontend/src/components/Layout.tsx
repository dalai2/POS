import React from 'react'
import Brand from './Brand'
import Sidebar from './Sidebar'

export default function Layout({ children }: { children: React.ReactNode }) {
  const handleLogout = () => {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('tenant')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar />
      <div className="flex-1">
        <header className="border-b bg-white/80 backdrop-blur sticky top-0 z-10">
          <div className="px-6 py-3 flex items-center justify-between">
            <Brand />
            <div className="flex items-center gap-4">
              <nav className="text-sm text-slate-600 flex gap-4">
                <a className="hover:text-slate-900" href="/products">Productos</a>
                <a className="hover:text-slate-900" href="/sales">Ventas</a>
              </nav>
              <button
                onClick={handleLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm font-medium"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </header>
        <main className="px-6 py-6">
          {children}
        </main>
      </div>
    </div>
  )}


