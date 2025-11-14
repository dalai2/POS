import React from 'react';

interface Vendedor {
  vendedor_id: number;
  vendedor_name: string;
  total_efectivo_contado: number;
  total_tarjeta_neto: number;
  anticipos_apartados: number;
  anticipos_pedidos: number;
  abonos_apartados: number;
  abonos_pedidos: number;
  cuentas_por_cobrar: number;
  productos_liquidados?: number;
}

interface VendorsTableProps {
  vendedores: Vendedor[];
}

export const VendorsTable: React.FC<VendorsTableProps> = ({ vendedores }) => {
  if (!vendedores || vendedores.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 pt-6" style={{ borderTop: '2px solid rgba(46, 67, 84, 0.1)' }}>
      <h5 className="text-lg font-['Exo_2',sans-serif] font-bold mb-4" style={{ color: '#2e4354' }}>👥 Resumen por Vendedores</h5>
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse rounded-lg overflow-hidden shadow-sm" style={{ border: '1px solid rgba(46, 67, 84, 0.2)' }}>
          <thead style={{ backgroundColor: '#2e4354' }}>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Vendedor</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Efectivo</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Tarjeta (-3%)</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Antic. Apart.</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Antic. Ped.</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Abono Apart.</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Abono Ped.</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', borderRight: '1px solid rgba(255, 255, 255, 0.1)' }}>Cuentas x Cobrar</th>
              <th className="px-4 py-3 text-right text-xs font-bold uppercase tracking-wider" style={{ color: '#ffffff', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>Prod. Liquidados</th>
            </tr>
          </thead>
          <tbody>
            {vendedores.map((vendedor, idx) => (
              <tr key={`${vendedor.vendedor_id}-${idx}`} style={{ backgroundColor: idx % 2 === 0 ? '#ffffff' : '#f0f7f7', borderBottom: '1px solid rgba(46, 67, 84, 0.08)' }}>
                <td className="px-4 py-3 text-sm font-semibold" style={{ color: '#000000', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>{vendedor.vendedor_name}</td>
                <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.total_efectivo_contado.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.total_tarjeta_neto.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.anticipos_apartados.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.anticipos_pedidos.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.abonos_apartados.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.abonos_pedidos.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right font-bold" style={{ color: '#2e4354', borderRight: '1px solid rgba(46, 67, 84, 0.05)' }}>${vendedor.cuentas_por_cobrar.toFixed(2)}</td>
                <td className="px-4 py-3 text-sm text-right font-bold" style={{ color: '#2e4354', backgroundColor: 'rgba(46, 67, 84, 0.1)' }}>${(vendedor.productos_liquidados ?? 0).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

