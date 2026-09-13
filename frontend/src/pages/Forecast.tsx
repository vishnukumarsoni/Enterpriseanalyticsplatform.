import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, Area, ComposedChart } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { PageHeader, Card, KpiCard, LoadingState, ErrorState, EmptyState, fmtCurrency } from '../components/ui';

interface ForecastResponse {
  actual_monthly_revenue: { month: string; actual_revenue: number }[];
  forecast_next_30_days: { date: string; forecast_revenue: number; lower_bound: number; upper_bound: number }[];
  forecast_next_3_months: { month: string; forecast_revenue: number; lower_bound: number; upper_bound: number }[];
  forecast_next_6_months: { month: string; forecast_revenue: number; lower_bound: number; upper_bound: number }[];
  backtest_error_metrics: { MAE: number; RMSE: number; MAPE_pct: number };
}

type Horizon = '30d' | '3m' | '6m';

export default function Forecast() {
  const { data, loading, error, reload } = useFetch<ForecastResponse>(() => api.forecast() as Promise<ForecastResponse>, []);
  const [horizon, setHorizon] = useState<Horizon>('3m');

  const combined = data
    ? [
        ...data.actual_monthly_revenue.map((r) => ({ label: r.month, actual: r.actual_revenue })),
        ...(horizon === '3m' ? data.forecast_next_3_months : data.forecast_next_6_months).map((f) => ({
          label: f.month, forecast: f.forecast_revenue, lower: f.lower_bound, upper: f.upper_bound,
        })),
      ]
    : [];

  return (
    <div>
      <PageHeader title="Revenue Forecast" subtitle="Holt-Winters exponential smoothing, backtested on held-out history" />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <KpiCard label="Backtest MAE" value={fmtCurrency(data.backtest_error_metrics.MAE)} />
            <KpiCard label="Backtest RMSE" value={fmtCurrency(data.backtest_error_metrics.RMSE)} />
            <KpiCard label="Backtest MAPE" value={`${data.backtest_error_metrics.MAPE_pct.toFixed(1)}%`} />
          </div>

          <Card
            title="Actual vs Forecast Revenue"
            action={
              <div className="flex gap-1">
                {(['3m', '6m'] as Horizon[]).map((h) => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    className={`text-[11px] px-2 py-1 rounded ${horizon === h ? 'bg-[var(--color-primary)] text-white' : 'bg-[var(--color-canvas)] text-[var(--color-ink-soft)]'}`}
                  >
                    {h === '3m' ? '3 Months' : '6 Months'}
                  </button>
                ))}
              </div>
            }
          >
            {combined.length === 0 ? <EmptyState /> : (
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={combined}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Area type="monotone" dataKey="upper" stroke="none" fill="var(--color-primary-soft)" fillOpacity={0.6} name="Upper bound" />
                  <Area type="monotone" dataKey="lower" stroke="none" fill="var(--color-surface)" fillOpacity={1} name="Lower bound" />
                  <Line type="monotone" dataKey="actual" stroke="var(--color-chart-2)" strokeWidth={2} dot={false} name="Actual" />
                  <Line type="monotone" dataKey="forecast" stroke="var(--color-chart-1)" strokeWidth={2} strokeDasharray="5 3" dot={false} name="Forecast" />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </Card>

          <Card title="Next 30 Days (Daily Forecast)" action={undefined}>
            {data.forecast_next_30_days.length === 0 ? <EmptyState /> : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data.forecast_next_30_days}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 9 }} interval={4} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                  <Line type="monotone" dataKey="forecast_revenue" stroke="var(--color-chart-1)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
