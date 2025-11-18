import React from 'react';

interface PiecesByNameCardsProps {
  vendidas?: Record<string, number> | null;
  entregadas?: Record<string, number> | null;
}

const buildEntries = (data?: Record<string, number> | null) => {
  if (!data) {
    return [];
  }
  return Object.entries(data).sort((a, b) => b[1] - a[1]);
};

const CardSection: React.FC<{
  title: string;
  icon: string;
  entries: Array<[string, number]>;
}> = ({ title, icon, entries }) => (
  <div className="flex-1 rounded-2xl border border-[rgba(46,67,84,0.15)] bg-white shadow-sm">
    <div className="border-b border-[rgba(46,67,84,0.1)] px-5 py-4">
      <h4 className="text-base font-['Exo_2',sans-serif] font-bold" style={{ color: '#2e4354' }}>
        {icon} {title}
      </h4>
      <p className="text-xs" style={{ color: '#2e4354', opacity: 0.7 }}>
        Totales agrupados por nombre en el periodo seleccionado
      </p>
    </div>
    <div className="px-5 py-4">
      {entries.length === 0 ? (
        <p className="text-sm" style={{ color: '#2e4354', opacity: 0.7 }}>
          Sin datos disponibles para este periodo.
        </p>
      ) : (
        <ul className="space-y-2">
          {entries.map(([nombre, total]) => (
            <li
              key={nombre}
              className="flex items-center justify-between rounded-lg bg-[rgba(46,67,84,0.05)] px-3 py-2 text-sm font-medium"
              style={{ color: '#2e4354' }}
            >
              <span>{nombre}</span>
              <span className="text-base font-bold" style={{ color: '#0f172a' }}>
                {total}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  </div>
);

export const PiecesByNameCards: React.FC<PiecesByNameCardsProps> = ({ vendidas, entregadas }) => {
  const vendidasEntries = buildEntries(vendidas);
  const entregadasEntries = buildEntries(entregadas);

  if (vendidasEntries.length === 0 && entregadasEntries.length === 0) {
    return null;
  }

  return (
    <div className="mt-6 grid gap-4 md:grid-cols-2">
      <CardSection title="Piezas Vendidas" icon="🛒" entries={vendidasEntries} />
      <CardSection title="Piezas Entregadas" icon="📦" entries={entregadasEntries} />
    </div>
  );
};


