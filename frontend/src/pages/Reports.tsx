import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { PageHeader, Card, LoadingState, ErrorState, EmptyState } from '../components/ui';

interface InsightsResponse {
  insights: { category: string; text: string }[];
  generated_from: string;
}

const REPORT_LINKS = [
  { label: 'Sales (Salesperson Ranking)', fetcher: () => api.sales(), key: 'salesperson_ranking' },
  { label: 'Customers', fetcher: () => api.customers(undefined, 1, 5000), key: 'customers' },
  { label: 'Products (All)', fetcher: () => api.products(), key: 'all_products' },
  { label: 'Churn Predictions', fetcher: () => api.churn(), key: 'at_risk_customers' },
  { label: 'RFM Segments', fetcher: () => api.rfm(), key: 'customers' },
];

export default function Reports() {
  const { data, loading, error, reload } = useFetch<InsightsResponse>(() => api.insights() as Promise<InsightsResponse>, []);

  return (
    <div>
      <PageHeader title="Reports &amp; Business Insights" subtitle="Auto-generated insights and downloadable exports" />

      <Card title="Automated Business Insights">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && (
          data.insights.length === 0 ? <EmptyState /> : (
            <ul className="space-y-3">
              {data.insights.map((ins, i) => (
                <li key={i} className="flex gap-3 text-[13px]">
                  <span className="shrink-0 text-[11px] font-medium px-2 py-0.5 rounded bg-[var(--color-primary-soft)] text-[var(--color-primary)] h-fit">{ins.category}</span>
                  <span className="text-[var(--color-ink)]">{ins.text}</span>
                </li>
              ))}
            </ul>
          )
        )}
        <p className="text-[11px] text-[var(--color-ink-faint)] mt-4">{data?.generated_from}</p>
      </Card>

      <Card title="Downloadable Reports">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {REPORT_LINKS.map((r) => (
            <ReportRow key={r.label} label={r.label} fetcher={r.fetcher} dataKey={r.key} />
          ))}
        </div>
      </Card>
    </div>
  );
}

function ReportRow({ label, fetcher, dataKey }: { label: string; fetcher: () => Promise<unknown>; dataKey: string }) {
  const download = async () => {
    const res = (await fetcher()) as Record<string, unknown>;
    const rows = (res[dataKey] as Record<string, unknown>[]) ?? [];
    if (rows.length === 0) return;
    const headers = Object.keys(rows[0]);
    const csv = [headers.join(','), ...rows.map((row) => headers.map((h) => JSON.stringify(row[h] ?? '')).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${label.toLowerCase().replace(/\s+/g, '_')}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="flex items-center justify-between border border-[var(--color-border)] rounded-md px-4 py-3">
      <span className="text-[13px]">{label}</span>
      <button onClick={download} className="text-[12px] px-3 py-1.5 rounded-md bg-[var(--color-primary)] text-white font-medium">Download CSV</button>
    </div>
  );
}
