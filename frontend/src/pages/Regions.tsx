import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, Legend } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { useFilters } from '../hooks/useFilters';
import { api } from '../services/api';
import { PageHeader, Card, FilterBar, LoadingState, ErrorState, EmptyState, fmtCurrency, fmtNumber, fmtPct, CHART_COLORS } from '../components/ui';

interface RegionsResponse {
  region_summary: { region: string; customer_count: number; total_orders: number; total_revenue: number; total_profit: number; profit_margin_pct: number }[];
  region_trend: { month: string; region: string; revenue: number }[];
}

export default function Regions() {
  const { filters } = useFilters();
  const { data, loading, error, reload } = useFetch<RegionsResponse>(() => api.regions(filters) as Promise<RegionsResponse>, [filters]);

  // pivot region_trend into a wide format for a multi-line chart
  const trendByMonth: Record<string, Record<string, number | string>> = {};
  const regionsSeen = new Set<string>();
  data?.region_trend.forEach((row) => {
    trendByMonth[row.month] = trendByMonth[row.month] || { month: row.month };
    trendByMonth[row.month][row.region] = row.revenue;
    regionsSeen.add(row.region);
  });
  const trendData = Object.values(trendByMonth).sort((a, b) => String(a.month).localeCompare(String(b.month)));

  return (
    <div>
      <PageHeader title="Regional Analytics" subtitle="Compare performance across North, South, East, West, and Central" />
      <FilterBar show={['category', 'customer_segment', 'date']} />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <Card title="Region Comparison">
            {data.region_summary.length === 0 ? <EmptyState /> : (
              <table className="w-full text-[12px]">
                <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                  <th className="py-2">Region</th><th className="text-right">Customers</th><th className="text-right">Orders</th>
                  <th className="text-right">Revenue</th><th className="text-right">Profit</th><th className="text-right">Margin</th>
                </tr></thead>
                <tbody>
                  {data.region_summary.map((r) => (
                    <tr key={r.region} className="border-b border-[var(--color-border)] last:border-0">
                      <td className="py-2 font-medium">{r.region}</td>
                      <td className="text-right tabular-nums">{fmtNumber(r.customer_count)}</td>
                      <td className="text-right tabular-nums">{fmtNumber(r.total_orders)}</td>
                      <td className="text-right tabular-nums">{fmtCurrency(r.total_revenue)}</td>
                      <td className="text-right tabular-nums">{fmtCurrency(r.total_profit)}</td>
                      <td className="text-right tabular-nums">{fmtPct(r.profit_margin_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            <Card title="Revenue by Region">
              {data.region_summary.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.region_summary}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="region" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Bar dataKey="total_revenue" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
            <Card title="Regional Revenue Trend (Monthly)">
              {trendData.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(Number(v) / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    {[...regionsSeen].map((region, i) => (
                      <Line key={region} type="monotone" dataKey={region} stroke={CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
