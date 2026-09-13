import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { PageHeader, Card, KpiCard, LoadingState, ErrorState, EmptyState, Badge, ExportButton, fmtCurrency, fmtNumber, fmtPct } from '../components/ui';

interface ChurnResponse {
  risk_summary: { risk_level: 'Low' | 'Medium' | 'High'; count: number; avg_probability: number }[];
  overall: { avg_churn_probability: number };
  at_risk_customers: { customer_id: string; customer_name: string; region: string; revenue: number; orders: number; last_purchase: string; rfm_segment: string; churn_probability: number; risk_level: string }[];
  pagination: { total_rows: number };
}

const RISK_COLOR: Record<string, string> = { High: 'var(--color-negative)', Medium: 'var(--color-warning)', Low: 'var(--color-positive)' };
const RISK_TONE: Record<string, 'positive' | 'warning' | 'negative'> = { High: 'negative', Medium: 'warning', Low: 'positive' };

export default function Churn() {
  const { data, loading, error, reload } = useFetch<ChurnResponse>(() => api.churn() as Promise<ChurnResponse>, []);
  const total = data ? data.risk_summary.reduce((s, r) => s + r.count, 0) : 0;
  const high = data?.risk_summary.find((r) => r.risk_level === 'High');
  const medium = data?.risk_summary.find((r) => r.risk_level === 'Medium');
  const low = data?.risk_summary.find((r) => r.risk_level === 'Low');

  return (
    <div>
      <PageHeader title="Churn Analysis" subtitle="ML-predicted churn risk (Random Forest, time-split validated)" />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <KpiCard label="High Risk Customers" value={fmtNumber(high?.count)} />
            <KpiCard label="Medium Risk Customers" value={fmtNumber(medium?.count)} />
            <KpiCard label="Low Risk Customers" value={fmtNumber(low?.count)} />
            <KpiCard label="Avg Churn Probability" value={fmtPct(data.overall.avg_churn_probability * 100)} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
            <Card title="Risk Distribution">
              {total === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={data.risk_summary} dataKey="count" nameKey="risk_level" outerRadius={80} label={(entry: any) => entry.risk_level}>
                      {data.risk_summary.map((r) => <Cell key={r.risk_level} fill={RISK_COLOR[r.risk_level]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>
            <div className="lg:col-span-2">
              <Card title="Churn Probability by Risk Tier">
                {data.risk_summary.length === 0 ? <EmptyState /> : (
                  <div className="space-y-3 mt-2">
                    {data.risk_summary.map((r) => (
                      <div key={r.risk_level}>
                        <div className="flex justify-between text-[12px] mb-1">
                          <Badge tone={RISK_TONE[r.risk_level]}>{r.risk_level} Risk</Badge>
                          <span className="tabular-nums text-[var(--color-ink-soft)]">{(r.avg_probability * 100).toFixed(1)}% avg probability &middot; {fmtNumber(r.count)} customers</span>
                        </div>
                        <div className="h-2 bg-[var(--color-canvas)] rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${r.avg_probability * 100}%`, background: RISK_COLOR[r.risk_level] }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>

          <Card title="At-Risk Customers" action={<ExportButton data={data.at_risk_customers} filename="at_risk_customers" />}>
            {data.at_risk_customers.length === 0 ? <EmptyState /> : (
              <div className="max-h-[420px] overflow-y-auto">
                <table className="w-full text-[12px]">
                  <thead className="sticky top-0 bg-[var(--color-surface)]"><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                    <th className="py-2">Customer</th><th>Region</th><th className="text-right">Revenue</th>
                    <th className="text-right">Orders</th><th>Last Purchase</th><th>RFM Segment</th>
                    <th className="text-right">Churn Prob.</th><th>Risk</th>
                  </tr></thead>
                  <tbody>
                    {data.at_risk_customers.map((c) => (
                      <tr key={c.customer_id} className="border-b border-[var(--color-border)] last:border-0">
                        <td className="py-2">{c.customer_name}</td><td>{c.region}</td>
                        <td className="text-right tabular-nums">{fmtCurrency(c.revenue)}</td>
                        <td className="text-right tabular-nums">{c.orders}</td>
                        <td>{c.last_purchase}</td><td>{c.rfm_segment}</td>
                        <td className="text-right tabular-nums">{(c.churn_probability * 100).toFixed(1)}%</td>
                        <td><Badge tone={RISK_TONE[c.risk_level] ?? 'neutral'}>{c.risk_level}</Badge></td>
                      </tr>
                    ))}
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
