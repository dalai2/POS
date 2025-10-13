import React from 'react'
import Brand from './Brand'

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 min-h-screen border-r bg-white">
      <div className="p-4 border-b">
        <Brand />
      </div>
      <nav className="p-3 text-sm text-slate-700 space-y-1">
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/sales">🛒 Punto de Venta</a>
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/products">💍 Productos/Joyería</a>
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/credits">💳 Créditos</a>
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/reports">📊 Corte de Caja</a>
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/metal-rates">⚖️ Tasas de Metal</a>
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/sales/history">📋 Historial</a>
        <a className="block px-3 py-2 rounded hover:bg-slate-100" href="/users">👥 Usuarios</a>
      </nav>
    </aside>
  )
}


