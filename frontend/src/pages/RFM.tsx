import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { PageHeader, Card, LoadingState, ErrorState, EmptyState, ExportButton, fmtCurrency, fmtNumber, CHART_COLORS } from '../components/ui';

interface RfmResponse {
  segment_summary: { segment: string; count: number; avg_monetary: number; avg_frequency: number; avg_recency_days: number }[];
  customers: { customer_id: string; customer_name: string; recency: number; frequency: number; monetary: number; segment: string }[];
  pagination: { total_rows: number };
}

export default function RFM() {
  const { data, loading, error, reload } = useFetch<RfmResponse>(() => api.rfm() as Promise<RfmResponse>, []);

  return (
    <div>
      <PageHeader title="RFM Segmentation" subtitle="Recency, Frequency, Monetary scoring and customer segments" />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <Card title="Customers per Segment">
              {data.segment_summary.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.segment_summary} layout="vertical" margin={{ left: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="segment" tick={{ fontSize: 10 }} width={120} />
                    <Tooltip />
                    <Bar dataKey="count" fill={CHART_COLORS[0]} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
            <Card title="Average Monetary Value per Segment">
              {data.segment_summary.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.segment_summary} layout="vertical" margin={{ left: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="segment" tick={{ fontSize: 10 }} width={120} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Bar dataKey="avg_monetary" fill={CHART_COLORS[1]} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          <Card title="Segment Summary" action={<ExportButton data={data.segment_summary} filename="rfm_segments" />}>
            {data.segment_summary.length === 0 ? <EmptyState /> : (
              <table className="w-full text-[12px]">
                <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                  <th className="py-2">Segment</th><th className="text-right">Customers</th>
                  <th className="text-right">Avg Recency (days)</th><th className="text-right">Avg Frequency</th><th className="text-right">Avg Monetary</th>
                </tr></thead>
                <tbody>
                  {data.segment_summary.map((s) => (
                    <tr key={s.segment} className="border-b border-[var(--color-border)] last:border-0">
                      <td className="py-2 font-medium">{s.segment}</td>
                      <td className="text-right tabular-nums">{fmtNumber(s.count)}</td>
                      <td className="text-right tabular-nums">{s.avg_recency_days.toFixed(0)}</td>
                      <td className="text-right tabular-nums">{s.avg_frequency.toFixed(1)}</td>
                      <td className="text-right tabular-nums">{fmtCurrency(s.avg_monetary)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
