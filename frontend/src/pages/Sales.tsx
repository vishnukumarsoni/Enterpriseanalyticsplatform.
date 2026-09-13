import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { useFilters } from '../hooks/useFilters';
import { api } from '../services/api';
import { PageHeader, Card, FilterBar, LoadingState, ErrorState, EmptyState, Badge, ExportButton, fmtCurrency, fmtPct, CHART_COLORS } from '../components/ui';

interface SalesResponse {
  monthly_trend: { month: string; revenue: number; orders: number }[];
  target_vs_actual: { employee_id: string; employee_name: string; region: string; target_amount: number; actual_revenue: number; achievement_pct: number }[];
  salesperson_ranking: { employee_id: string; employee_name: string; region: string; revenue: number; rank: number }[];
  region_ranking: { region: string; revenue: number; rank: number }[];
}

function tierFor(pct: number): { label: string; tone: 'positive' | 'warning' | 'negative' } {
  if (pct >= 100) return { label: 'Top Performer', tone: 'positive' };
  if (pct >= 80) return { label: 'Strong Performer', tone: 'positive' };
  if (pct >= 60) return { label: 'Average Performer', tone: 'warning' };
  return { label: 'Needs Improvement', tone: 'negative' };
}

export default function Sales() {
  const { filters } = useFilters();
  const { data, loading, error, reload } = useFetch<SalesResponse>(() => api.sales(filters) as Promise<SalesResponse>, [filters]);

  return (
    <div>
      <PageHeader title="Sales Performance" subtitle="Revenue trend, targets, and salesperson &amp; region rankings" />
      <FilterBar />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {!loading && !error && data && (
        <>
          <Card title="Monthly Revenue Trend">
            {data.monthly_trend.length === 0 ? <EmptyState /> : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data.monthly_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                  <Line type="monotone" dataKey="revenue" stroke={CHART_COLORS[0]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            <Card title="Region Ranking">
              {data.region_ranking.length === 0 ? <EmptyState /> : (
                <table className="w-full text-[12px]">
                  <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                    <th className="py-2">#</th><th>Region</th><th className="text-right">Revenue</th>
                  </tr></thead>
                  <tbody>
                    {data.region_ranking.map((r) => (
                      <tr key={r.region} className="border-b border-[var(--color-border)] last:border-0">
                        <td className="py-2">{r.rank}</td><td>{r.region}</td>
                        <td className="text-right tabular-nums">{fmtCurrency(r.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>

            <Card title="Top Salespeople" action={<ExportButton data={data.salesperson_ranking} filename="salesperson_ranking" />}>
              {data.salesperson_ranking.length === 0 ? <EmptyState /> : (
                <div className="max-h-[300px] overflow-y-auto">
                  <table className="w-full text-[12px]">
                    <thead className="sticky top-0 bg-[var(--color-surface)]"><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                      <th className="py-2">#</th><th>Name</th><th>Region</th><th className="text-right">Revenue</th>
                    </tr></thead>
                    <tbody>
                      {data.salesperson_ranking.slice(0, 15).map((s) => (
                        <tr key={s.employee_id} className="border-b border-[var(--color-border)] last:border-0">
                          <td className="py-2">{s.rank}</td><td>{s.employee_name}</td><td>{s.region}</td>
                          <td className="text-right tabular-nums">{fmtCurrency(s.revenue)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>

          <Card title="Target Achievement" action={<ExportButton data={data.target_vs_actual} filename="target_vs_actual" />}>
            {data.target_vs_actual.length === 0 ? <EmptyState /> : (
              <div className="max-h-[360px] overflow-y-auto mt-4">
                <table className="w-full text-[12px]">
                  <thead className="sticky top-0 bg-[var(--color-surface)]"><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                    <th className="py-2">Name</th><th>Region</th><th className="text-right">Target</th>
                    <th className="text-right">Actual</th><th className="text-right">Achievement</th><th>Tier</th>
                  </tr></thead>
                  <tbody>
                    {data.target_vs_actual.map((t) => {
                      const tier = tierFor(t.achievement_pct);
                      return (
                        <tr key={t.employee_id} className="border-b border-[var(--color-border)] last:border-0">
                          <td className="py-2">{t.employee_name}</td><td>{t.region}</td>
                          <td className="text-right tabular-nums">{fmtCurrency(t.target_amount)}</td>
                          <td className="text-right tabular-nums">{fmtCurrency(t.actual_revenue)}</td>
                          <td className="text-right tabular-nums">{fmtPct(t.achievement_pct)}</td>
                          <td><Badge tone={tier.tone}>{tier.label}</Badge></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
