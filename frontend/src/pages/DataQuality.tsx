import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { PageHeader, Card, KpiCard, LoadingState, ErrorState, EmptyState, Badge } from '../components/ui';

interface DataQualityResponse {
  summary: { total_rules: number; passed: number; warnings: number; failed: number };
  rules: { Rule: string; ['Total Records']: number; ['Failed Records']: number; ['Failure Percentage']: number; Status: string }[];
}

const STATUS_TONE: Record<string, 'positive' | 'warning' | 'negative'> = { PASS: 'positive', WARN: 'warning', FAIL: 'negative' };

export default function DataQuality() {
  const { data, loading, error, reload } = useFetch<DataQualityResponse>(() => api.dataQuality() as Promise<DataQualityResponse>, []);

  return (
    <div>
      <PageHeader title="Data Quality" subtitle="Automated validation rules run by the ETL pipeline" />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <KpiCard label="Total Rules" value={String(data.summary.total_rules)} />
            <KpiCard label="Passed" value={String(data.summary.passed)} />
            <KpiCard label="Warnings" value={String(data.summary.warnings)} />
            <KpiCard label="Failed" value={String(data.summary.failed)} />
          </div>

          <Card title="Validation Rules">
            {data.rules.length === 0 ? <EmptyState /> : (
              <table className="w-full text-[12px]">
                <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                  <th className="py-2">Rule</th><th className="text-right">Total Records</th>
                  <th className="text-right">Failed Records</th><th className="text-right">Failure %</th><th>Status</th>
                </tr></thead>
                <tbody>
                  {data.rules.map((r) => (
                    <tr key={r.Rule} className="border-b border-[var(--color-border)] last:border-0">
                      <td className="py-2">{r.Rule}</td>
                      <td className="text-right tabular-nums">{r['Total Records'].toLocaleString()}</td>
                      <td className="text-right tabular-nums">{r['Failed Records'].toLocaleString()}</td>
                      <td className="text-right tabular-nums">{r['Failure Percentage'].toFixed(2)}%</td>
                      <td><Badge tone={STATUS_TONE[r.Status] ?? 'neutral'}>{r.Status}</Badge></td>
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
