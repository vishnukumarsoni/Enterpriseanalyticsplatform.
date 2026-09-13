import { useFetch } from '../hooks/useFetch';
import { useFilters } from '../hooks/useFilters';
import { api } from '../services/api';
import { PageHeader, Card, FilterBar, LoadingState, ErrorState, EmptyState, Badge, ExportButton, fmtCurrency, fmtNumber, fmtPct } from '../components/ui';

interface EmployeeRow {
  employee_id: string; employee_name: string; department: string; region: string;
  joining_date: string; annual_target: number; total_revenue: number; total_profit: number;
  total_orders: number; customer_count: number; target_achievement_pct: number; performance_tier: string;
}
interface EmployeesResponse {
  employees: EmployeeRow[];
  performance_tier_summary: { performance_tier: string; count: number }[];
}

const TIER_TONE: Record<string, 'positive' | 'warning' | 'negative' | 'neutral'> = {
  'Top Performer': 'positive',
  'Strong Performer': 'positive',
  'Average Performer': 'warning',
  'Needs Improvement': 'negative',
};

export default function Employees() {
  const { filters } = useFilters();
  const { data, loading, error, reload } = useFetch<EmployeesResponse>(() => api.employees(filters) as Promise<EmployeesResponse>, [filters]);

  return (
    <div>
      <PageHeader title="Salesperson Performance" subtitle="Individual revenue, profit, and target achievement" />
      <FilterBar show={['region', 'date']} />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="flex gap-3 mb-4">
            {data.performance_tier_summary.map((t) => (
              <div key={t.performance_tier} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3 flex-1">
                <Badge tone={TIER_TONE[t.performance_tier] ?? 'neutral'}>{t.performance_tier}</Badge>
                <div className="text-[18px] font-semibold mt-1.5">{fmtNumber(t.count)}</div>
              </div>
            ))}
          </div>

          <Card title="All Employees" action={<ExportButton data={data.employees} filename="employees" />}>
            {data.employees.length === 0 ? <EmptyState /> : (
              <div className="max-h-[500px] overflow-y-auto">
                <table className="w-full text-[12px]">
                  <thead className="sticky top-0 bg-[var(--color-surface)]"><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                    <th className="py-2">Name</th><th>Dept</th><th>Region</th>
                    <th className="text-right">Revenue</th><th className="text-right">Profit</th>
                    <th className="text-right">Orders</th><th className="text-right">Customers</th>
                    <th className="text-right">Achievement</th><th>Tier</th>
                  </tr></thead>
                  <tbody>
                    {data.employees.map((e) => (
                      <tr key={e.employee_id} className="border-b border-[var(--color-border)] last:border-0">
                        <td className="py-2">{e.employee_name}</td><td>{e.department}</td><td>{e.region}</td>
                        <td className="text-right tabular-nums">{fmtCurrency(e.total_revenue)}</td>
                        <td className="text-right tabular-nums">{fmtCurrency(e.total_profit)}</td>
                        <td className="text-right tabular-nums">{e.total_orders}</td>
                        <td className="text-right tabular-nums">{e.customer_count}</td>
                        <td className="text-right tabular-nums">{fmtPct(e.target_achievement_pct)}</td>
                        <td><Badge tone={TIER_TONE[e.performance_tier] ?? 'neutral'}>{e.performance_tier}</Badge></td>
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
