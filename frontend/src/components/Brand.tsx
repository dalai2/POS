import React from 'react'

export default function Brand() {
  return (
    <div className="flex items-center gap-2">
      <svg width="28" height="28" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2563eb"/>
            <stop offset="100%" stopColor="#06b6d4"/>
          </linearGradient>
        </defs>
        <rect x="4" y="8" width="56" height="40" rx="8" fill="url(#g)"/>
        <circle cx="20" cy="52" r="4" fill="#0ea5e9"/>
        <circle cx="46" cy="52" r="4" fill="#0ea5e9"/>
        <path d="M14 20h36" stroke="white" strokeWidth="4" strokeLinecap="round"/>
        <path d="M14 28h28" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      </svg>
      <div>
        <div className="text-xl font-extrabold tracking-tight">BlueCart POS</div>
        <div className="text-xs text-slate-500 -mt-1">ERP SaaS para puntos de venta</div>
      </div>
    </div>
  )
}





