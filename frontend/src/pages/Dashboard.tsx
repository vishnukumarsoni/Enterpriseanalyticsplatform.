import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { useFilters } from '../hooks/useFilters';
import { api } from '../services/api';
import { PageHeader, KpiCard, Card, FilterBar, LoadingState, ErrorState, EmptyState, fmtCurrency, fmtNumber, fmtPct, CHART_COLORS } from '../components/ui';
import type { DashboardResponse } from '../types';

export default function Dashboard() {
  const { filters } = useFilters();
  const { data, loading, error, reload } = useFetch<DashboardResponse>(() => api.dashboard(filters) as Promise<DashboardResponse>, [filters]);

  return (
    <div>
      <PageHeader title="Executive Dashboard" subtitle="Company-wide performance at a glance" />
      <FilterBar />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
            <KpiCard label="Total Revenue" value={fmtCurrency(data.kpis.total_revenue)} />
            <KpiCard label="Total Profit" value={fmtCurrency(data.kpis.total_profit)} />
            <KpiCard label="Profit Margin" value={fmtPct(data.kpis.profit_margin_pct)} />
            <KpiCard label="Total Orders" value={fmtNumber(data.kpis.total_orders)} />
            <KpiCard label="Active Customers" value={fmtNumber(data.kpis.active_customers)} />
            <KpiCard label="YoY Growth" value={fmtPct(data.kpis.yoy_growth_pct)} delta={data.kpis.yoy_growth_pct} deltaLabel="vs prior year" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <Card title="Revenue &amp; Profit Trend">
              {data.revenue_trend.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={data.revenue_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Line type="monotone" dataKey="revenue" name="Revenue" stroke={CHART_COLORS[0]} strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="profit" name="Profit" stroke={CHART_COLORS[1]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </Card>

            <Card title="Revenue by Region">
              {data.revenue_by_region.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.revenue_by_region}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="region" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Bar dataKey="revenue" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card title="Revenue by Category">
              {data.revenue_by_category.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.revenue_by_category} layout="vertical" margin={{ left: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="category" tick={{ fontSize: 10 }} width={110} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Bar dataKey="revenue" fill={CHART_COLORS[2]} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>

            <Card title="Top 10 Products">
              {data.top_products.length === 0 ? <EmptyState /> : (
                <div className="space-y-2 max-h-[240px] overflow-y-auto">
                  {data.top_products.map((p, i) => (
                    <div key={p.product_name} className="flex justify-between text-[12px] py-1 border-b border-[var(--color-border)] last:border-0">
                      <span className="text-[var(--color-ink-soft)]">{i + 1}. {p.product_name}</span>
                      <span className="font-medium tabular-nums">{fmtCurrency(p.revenue)}</span>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card title="Customer Segment Distribution">
              {data.customer_segment_distribution.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={data.customer_segment_distribution} dataKey="customer_count" nameKey="customer_segment" outerRadius={80} // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    label={(entry: any) => entry.customer_segment ?? ''}>
                      {data.customer_segment_distribution.map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
