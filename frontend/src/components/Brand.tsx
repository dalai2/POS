import React from 'react'

export default function Brand() {
  return (
    <div>
      <div className="flex items-center gap-3">
        <div className="text-xl font-bold tracking-tight" style={{ color: '#2e4354', fontFamily: 'Poppins, sans-serif' }}>
          POS Joyero by
        </div>
        <img 
          src="/logo-velant.jpg" 
          alt="Velant Logo" 
          className="w-16 h-16 object-contain"
          onError={(e) => {
            // Fallback si no existe el logo
            e.currentTarget.style.display = 'none'
          }}
        />
      </div>
      <div className="text-xs -mt-1" style={{ color: '#2e4354', opacity: 0.7, fontFamily: 'Poppins, sans-serif' }}>
        Sistema de punto de venta especializado
      </div>
    </div>
  )
}





