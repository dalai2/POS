import React from 'react'
import Brand from './Brand'
import Sidebar from './Sidebar'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar />
      <div className="flex-1">
        <header className="border-b bg-white/80 backdrop-blur sticky top-0 z-10">
          <div className="px-6 py-3 flex items-center justify-between">
            <Brand />
            <nav className="text-sm text-slate-600 flex gap-4">
              <a className="hover:text-slate-900" href="/products">Productos</a>
              <a className="hover:text-slate-900" href="/sales">Ventas</a>
            </nav>
          </div>
        </header>
        <main className="px-6 py-6">
          {children}
        </main>
      </div>
    </div>
  )}


