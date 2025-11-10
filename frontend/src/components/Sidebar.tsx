import React from 'react'
import Brand from './Brand'

export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 min-h-screen border-r" style={{ backgroundColor: 'white', borderColor: '#f0f7f7', fontFamily: 'Poppins, sans-serif' }}>
      <div className="p-4 border-b" style={{ borderColor: '#f0f7f7' }}>
        <Brand />
      </div>
      <nav className="p-3 text-sm space-y-1" style={{ color: '#2e4354' }}>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/sales" style={{ backgroundColor: 'transparent' }}>🛒 Punto de Venta</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/pedidos" style={{ backgroundColor: 'transparent' }}>📋 Pedidos</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/gestion-pedidos" style={{ backgroundColor: 'transparent' }}>📊 Gestión de Pedidos</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/products" style={{ backgroundColor: 'transparent' }}>💍 Productos/Joyería</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/credits" style={{ backgroundColor: 'transparent' }}>💳 Gestión de apartados</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/clients" style={{ backgroundColor: 'transparent' }}>👥 Clientes</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/reports" style={{ backgroundColor: 'transparent' }}>📊 Corte de Caja</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/metal-rates" style={{ backgroundColor: 'transparent' }}>⚖️ Tasas de Metal</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/tasas-pedido" style={{ backgroundColor: 'transparent' }}>💎 Tasas Metal Pedidos</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/sales/history" style={{ backgroundColor: 'transparent' }}>📋 Historial</a>
        <a className="block px-3 py-2 rounded transition-colors hover:opacity-80" href="/users" style={{ backgroundColor: 'transparent' }}>👤 Usuarios</a>
      </nav>
    </aside>
  )
}


