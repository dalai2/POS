import React from 'react';

interface SaleDetail {
  id: number;
  fecha: string;
  cliente: string;
  piezas: number;
  total: number;
  efectivo: number;
  tarjeta: number;
  estado: string;
  tipo: string;
  vendedor: string;
}

interface SalesDetailsTableProps {
  salesDetails: SaleDetail[];
}

export const SalesDetailsTable: React.FC<SalesDetailsTableProps> = ({ salesDetails }) => {
  if (!salesDetails || salesDetails.length === 0) {
    return null;
  }

  return (
    <div className="p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Detalle de Ventas</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Fecha</th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Cliente</th>
              <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Piezas</th>
              <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Total</th>
              <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Efectivo</th>
              <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">Tarjeta</th>
              <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Estado</th>
              <th className="px-2 py-2 text-center text-xs font-medium text-gray-500">Tipo</th>
              <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">Vendedor</th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {salesDetails.map((sale) => (
              <tr key={sale.id} className="border-t">
                <td className="px-2 py-2 text-xs">{new Date(sale.fecha).toLocaleString()}</td>
                <td className="px-2 py-2 text-xs">{sale.cliente}</td>
                <td className="px-2 py-2 text-center text-xs">{sale.piezas}</td>
                <td className="px-2 py-2 text-right text-xs font-bold">${sale.total.toFixed(2)}</td>
                <td className="px-2 py-2 text-right text-xs">${sale.efectivo.toFixed(2)}</td>
                <td className="px-2 py-2 text-right text-xs">${sale.tarjeta.toFixed(2)}</td>
                <td className="px-2 py-2 text-center text-xs">{sale.estado}</td>
                <td className="px-2 py-2 text-center text-xs">{sale.tipo}</td>
                <td className="px-2 py-2 text-xs">{sale.vendedor}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

