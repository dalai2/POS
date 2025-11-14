import React from 'react';
import {
  DashboardBreakdown,
  DashboardMetrics,
  DashboardMetodoDetalle,
  DashboardValue,
  DashboardTarjetaValue,
} from '../../types/reports';

interface SummaryCardProps {
  title: string;
  amount: number;
  count: number;
  background?: string;
  foreground?: string;
  highlightColor?: string;
  children?: React.ReactNode;
}

const formatCurrency = (value: number) =>
  (value ?? 0).toLocaleString('es-MX', { style: 'currency', currency: 'MXN' });

const formatNumber = (value: number) => (value ?? 0).toLocaleString('es-MX');

const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  amount,
  count,
  background = '#ffffff',
  foreground = '#2e4354',
  highlightColor,
  children,
}) => (
  <div
    className="rounded-2xl shadow-lg p-5 flex flex-col gap-4 transition-transform duration-200 hover:-translate-y-1"
    style={{ backgroundColor: background, color: foreground }}
  >
    <div className="flex items-center justify-between gap-2">
      <h5 className="text-sm font-semibold tracking-wide uppercase opacity-90">
        {title}
      </h5>
      {highlightColor && (
        <span
          className="inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded-full"
          style={{ backgroundColor: highlightColor, color: '#ffffff' }}
        >
          Cantidad: {formatNumber(count)}
        </span>
      )}
    </div>
    <div
      className="text-3xl font-extrabold tracking-tight"
      style={{ color: highlightColor ? highlightColor : foreground }}
    >
      {formatCurrency(amount)}
    </div>
    {!highlightColor && (
      <div className="text-sm font-medium opacity-80">
        Cantidad: {formatNumber(count)}
      </div>
    )}
    {children && <div className="text-sm leading-relaxed">{children}</div>}
  </div>
);

const MethodBreakdown: React.FC<{
  label: string;
  data: DashboardMetodoDetalle;
}> = ({ label, data }) => {
  const tarjeta = data.tarjeta as DashboardTarjetaValue | undefined;
  const efectivo = data.efectivo as DashboardValue | undefined;
  const total = data.total as DashboardValue | undefined;
  return (
    <div className="rounded-2xl bg-white shadow-md p-5 flex flex-col gap-3 border border-[rgba(46,67,84,0.08)]">
      <div className="text-sm font-semibold uppercase tracking-wide text-[#2e4354]">
        {label}
      </div>
      <div className="grid gap-2 text-sm">
        {efectivo && (
          <div className="flex items-center justify-between">
            <span className="font-medium text-[#2e4354]">Efectivo</span>
            <span>
              {formatCurrency(efectivo.monto)}{' '}
              <span className="opacity-70">
                ({formatNumber(efectivo.count)} operaciones)
              </span>
            </span>
          </div>
        )}
        {tarjeta && (
          <div className="flex items-center justify-between">
            <span className="font-medium text-[#2e4354]">Tarjeta</span>
            <span className="flex flex-col items-end leading-tight">
              <span>
                Subtotal: {formatCurrency(tarjeta.bruto)}{' '}
                <span className="opacity-70">
                  ({formatNumber(tarjeta.count)} operaciones)
                </span>
              </span>
              <span className="text-sm font-semibold text-[#2e4354]">
                Neto (-3%): {formatCurrency(tarjeta.neto)}
              </span>
            </span>
          </div>
        )}
        {total && (
          <div className="flex items-center justify-between pt-2 border-t border-[rgba(46,67,84,0.08)] mt-1">
            <span className="font-semibold text-[#2e4354]">Total neto</span>
            <span>
              {formatCurrency(total.monto)}{' '}
              <span className="opacity-70">
                ({formatNumber(total.count)} operaciones)
              </span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

const BreakdownBody: React.FC<{ data: DashboardBreakdown }> = ({ data }) => (
  <div className="grid gap-2">
    {data.efectivo && (
      <div className="flex items-center justify-between">
        <span className="font-medium text-[#2e4354]">Efectivo</span>
        <span>
          {formatCurrency(data.efectivo.monto)}{' '}
          <span className="opacity-70">
            ({formatNumber(data.efectivo.count)} operaciones)
          </span>
        </span>
      </div>
    )}
    {data.tarjeta && (
      <div className="flex items-center justify-between">
        <span className="font-medium text-[#2e4354]">Tarjeta</span>
        <span className="flex flex-col items-end leading-tight">
          <span>
            Subtotal: {formatCurrency(data.tarjeta.bruto)}{' '}
            <span className="opacity-70">
              ({formatNumber(data.tarjeta.count)} operaciones)
            </span>
          </span>
          <span className="text-sm font-semibold text-[#2e4354]">
            Neto (-3%): {formatCurrency(data.tarjeta.neto)}
          </span>
        </span>
      </div>
    )}
  </div>
);

interface AnalyticsDashboardProps {
  dashboard?: DashboardMetrics;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  dashboard,
}) => {
  if (!dashboard || !dashboard.ventas) {
    return null;
  }

  return (
    <div className="space-y-10">
      {/* Ventas */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Ventas
          </h4>
          <span className="text-sm text-[#2e4354] opacity-70">
            Montos netos y cantidades de operaciones
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <SummaryCard
            title="Ventas de contado"
            amount={dashboard.ventas.contado.monto}
            count={dashboard.ventas.contado.count}
            background="#f0f7f7"
          />
          <SummaryCard
            title="Ventas de pedidos de contado"
            amount={dashboard.ventas.pedidos_contado.monto}
            count={dashboard.ventas.pedidos_contado.count}
            background="#e0fdff"
          />
          <SummaryCard
            title="Ventas totales"
            amount={dashboard.ventas.total.monto}
            count={dashboard.ventas.total.count}
            background="#2e4354"
            foreground="#ffffff"
          />
        </div>
      </div>

      {/* Anticipos */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Anticipos
          </h4>
          <span className="text-sm text-[#2e4354] opacity-70">
            Desglose por método de pago
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <SummaryCard
            title="Anticipos de apartados"
            amount={dashboard.anticipos.apartados.monto}
            count={dashboard.anticipos.apartados.count}
            background="#ffffff"
          />
          <SummaryCard
            title="Anticipos de pedidos apartados"
            amount={dashboard.anticipos.pedidos_apartados.monto}
            count={dashboard.anticipos.pedidos_apartados.count}
            background="#f0f7f7"
          />
          <SummaryCard
            title="Anticipos totales"
            amount={dashboard.anticipos.total.monto}
            count={dashboard.anticipos.total.count}
            background="#2e4354"
            foreground="#ffffff"
          />
        </div>
      </div>

      {/* Abonos */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Abonos
          </h4>
          <span className="text-sm text-[#2e4354] opacity-70">
            Seguimiento de pagos recurrentes
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <SummaryCard
            title="Abonos a apartados"
            amount={dashboard.abonos.apartados.monto}
            count={dashboard.abonos.apartados.count}
            background="#ffffff"
          />
          <SummaryCard
            title="Abonos a pedidos apartados"
            amount={dashboard.abonos.pedidos_apartados.monto}
            count={dashboard.abonos.pedidos_apartados.count}
            background="#f0f7f7"
          />
          <SummaryCard
            title="Abonos totales"
            amount={dashboard.abonos.total.monto}
            count={dashboard.abonos.total.count}
            background="#2e4354"
            foreground="#ffffff"
          />
        </div>
      </div>

      {/* Liquidaciones */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Liquidaciones
          </h4>
          <span className="text-sm text-[#2e4354] opacity-70">
            Saldo liquidado por tipo de operación
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <SummaryCard
            title="Apartados liquidados"
            amount={dashboard.liquidaciones.apartados.monto}
            count={dashboard.liquidaciones.apartados.count}
            background="#f0f7f7"
          />
          <SummaryCard
            title="Pedidos apartados liquidados"
            amount={dashboard.liquidaciones.pedidos_apartados.monto}
            count={dashboard.liquidaciones.pedidos_apartados.count}
            background="#e0fdff"
          />
          <SummaryCard
            title="Liquidaciones totales"
            amount={dashboard.liquidaciones.total.monto}
            count={dashboard.liquidaciones.total.count}
            background="#2e4354"
            foreground="#ffffff"
          />
        </div>
      </div>

      {/* Vencimientos */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Vencimientos
          </h4>
          <span className="text-sm text-[#d97706] font-medium">
            Monitoreo de saldos en riesgo
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <SummaryCard
            title="Vencimientos de apartados"
            amount={dashboard.vencimientos.apartados.monto}
            count={dashboard.vencimientos.apartados.count}
            background="#fff7ed"
            foreground="#b45309"
          />
          <SummaryCard
            title="Vencimientos de pedidos apartados"
            amount={dashboard.vencimientos.pedidos_apartados.monto}
            count={dashboard.vencimientos.pedidos_apartados.count}
            background="#fff7ed"
            foreground="#b45309"
          />
          <SummaryCard
            title="Vencimientos totales"
            amount={dashboard.vencimientos.total.monto}
            count={dashboard.vencimientos.total.count}
            background="#d97706"
            foreground="#ffffff"
          />
        </div>
      </div>

      {/* Cancelaciones */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Cancelaciones
          </h4>
          <span className="text-sm text-[#b91c1c] font-medium">
            Incluye reembolsos y devoluciones por tipo
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-4">
          <SummaryCard
            title="Ventas de contado"
            amount={dashboard.cancelaciones.ventas_contado.monto}
            count={dashboard.cancelaciones.ventas_contado.count}
            background="#fee2e2"
            foreground="#7f1d1d"
          />
          <SummaryCard
            title="Pedidos de contado"
            amount={dashboard.cancelaciones.pedidos_contado.monto}
            count={dashboard.cancelaciones.pedidos_contado.count}
            background="#ffe4e6"
            foreground="#7f1d1d"
          />
          <SummaryCard
            title="Pedidos apartados"
            amount={dashboard.cancelaciones.pedidos_apartados.monto}
            count={dashboard.cancelaciones.pedidos_apartados.count}
            background="#fee2e2"
            foreground="#7f1d1d"
          />
          <SummaryCard
            title="Apartados cancelados"
            amount={dashboard.cancelaciones.apartados.monto}
            count={dashboard.cancelaciones.apartados.count}
            background="#ffe4e6"
            foreground="#7f1d1d"
          />
        </div>
        <SummaryCard
          title="Cancelaciones totales"
          amount={dashboard.cancelaciones.total.monto}
          count={dashboard.cancelaciones.total.count}
          background="#b91c1c"
          foreground="#ffffff"
        />
      </div>

      {/* Métodos de pago */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Métodos de pago
          </h4>
          <span className="text-sm text-[#2e4354] opacity-70">
            Subtotales, netos (-3% tarjeta) y cantidades
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-2">
          <MethodBreakdown
            label="Ventas de contado"
            data={dashboard.metodos_pago.ventas_contado}
          />
          <MethodBreakdown
            label="Pedidos de contado"
            data={dashboard.metodos_pago.pedidos_contado}
          />
          <MethodBreakdown
            label="Anticipos de apartados"
            data={dashboard.metodos_pago.anticipos_apartados}
          />
          <MethodBreakdown
            label="Anticipos de pedidos apartados"
            data={dashboard.metodos_pago.anticipos_pedidos_apartados}
          />
          <MethodBreakdown
            label="Abonos de apartados"
            data={dashboard.metodos_pago.abonos_apartados}
          />
          <MethodBreakdown
            label="Abonos de pedidos apartados"
            data={dashboard.metodos_pago.abonos_pedidos_apartados}
          />
        </div>
      </div>

      {/* Cantidades */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h4 className="text-xl font-semibold text-[#2e4354] tracking-tight">
            Cantidades de piezas
          </h4>
          <span className="text-sm text-[#2e4354] opacity-70">
            Piezas vendidas, entregadas, vencidas y canceladas
          </span>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {Object.entries(dashboard.contadores).map(([key, value]) => (
            <div
              key={key}
              className="rounded-2xl bg-white shadow-md p-5 border border-[rgba(46,67,84,0.08)]"
            >
              <div className="text-xs font-semibold uppercase tracking-wide text-[#2e4354] opacity-70">
                {key.replace(/_/g, ' ')}
              </div>
              <div className="text-2xl font-bold text-[#2e4354] mt-2">
                {formatNumber(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

