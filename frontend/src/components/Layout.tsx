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
    <div className="min-h-screen flex" style={{ backgroundColor: '#f0f7f7', fontFamily: 'Poppins, sans-serif' }}>
      <Sidebar />
      <div className="flex-1">
        <header className="border-b sticky top-0 z-10" style={{ backgroundColor: 'white', borderColor: '#f0f7f7' }}>
          <div className="px-6 py-3 flex items-center justify-between">
            <Brand />
            <div className="flex items-center gap-4">
              <nav className="text-sm flex gap-4" style={{ color: '#2e4354' }}>
                <a className="hover:opacity-80 transition-opacity" href="/products">Productos</a>
                <a className="hover:opacity-80 transition-opacity" href="/sales">Ventas</a>
              </nav>
              <button
                onClick={handleLogout}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                style={{ backgroundColor: '#2e4354', color: 'white' }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#1e2d3a'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#2e4354'}
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


