import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { useFilters } from '../hooks/useFilters';
import { api } from '../services/api';
import { PageHeader, Card, KpiCard, FilterBar, LoadingState, ErrorState, EmptyState, ExportButton, fmtCurrency, fmtNumber, CHART_COLORS } from '../components/ui';

interface CustomersResponse {
  summary: { total_customers: number; active_customers: number; purchasing_customers: number; new_customer_orders: number; returning_customer_orders: number };
  customer_growth: { month: string; new_customers: number }[];
  rfm_segments: { segment: string; customer_count: number }[];
  customers: { customer_id: string; customer_name: string; region: string; customer_segment: string; customer_status: string; total_revenue: number; total_orders: number; last_purchase_date: string | null }[];
  pagination: { page: number; page_size: number; total_rows: number };
}

export default function Customers() {
  const { filters } = useFilters();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, loading, error, reload } = useFetch<CustomersResponse>(
    () => api.customers(filters, page, pageSize, search || undefined) as Promise<CustomersResponse>,
    [filters, page, search]
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.pagination.total_rows / pageSize)) : 1;
  const retentionRate = data
    ? ((data.summary.returning_customer_orders / (data.summary.new_customer_orders + data.summary.returning_customer_orders)) * 100)
    : null;

  return (
    <div>
      <PageHeader title="Customer Analytics" subtitle="Retention, growth, RFM segments, and customer-level detail" />
      <FilterBar />

      {loading && !data && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <KpiCard label="Total Customers" value={fmtNumber(data.summary.total_customers)} />
            <KpiCard label="Active Customers" value={fmtNumber(data.summary.active_customers)} />
            <KpiCard label="Purchasing Customers" value={fmtNumber(data.summary.purchasing_customers)} />
            <KpiCard label="Repeat Order Share" value={retentionRate !== null ? `${retentionRate.toFixed(1)}%` : '—'} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <Card title="Customer Growth (New Customers by Month)">
              {data.customer_growth.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.customer_growth}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="new_customers" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
            <Card title="RFM Segment Distribution">
              {data.rfm_segments.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={data.rfm_segments} layout="vertical" margin={{ left: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="segment" tick={{ fontSize: 10 }} width={110} />
                    <Tooltip />
                    <Bar dataKey="customer_count" fill={CHART_COLORS[3]} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          <Card
            title="Customers"
            action={
              <div className="flex items-center gap-2">
                <input
                  placeholder="Search by name…"
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  className="text-[12px] border border-[var(--color-border)] rounded-md px-2 py-1.5"
                />
                <ExportButton data={data.customers} filename="customers" />
              </div>
            }
          >
            {data.customers.length === 0 ? <EmptyState /> : (
              <>
                <table className="w-full text-[12px]">
                  <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                    <th className="py-2">Customer</th><th>Region</th><th>Segment</th><th>Status</th>
                    <th className="text-right">Revenue</th><th className="text-right">Orders</th><th>Last Purchase</th>
                  </tr></thead>
                  <tbody>
                    {data.customers.map((c) => (
                      <tr key={c.customer_id} className="border-b border-[var(--color-border)] last:border-0">
                        <td className="py-2">{c.customer_name}</td><td>{c.region}</td><td>{c.customer_segment}</td>
                        <td>{c.customer_status}</td>
                        <td className="text-right tabular-nums">{fmtCurrency(c.total_revenue)}</td>
                        <td className="text-right tabular-nums">{c.total_orders}</td>
                        <td>{c.last_purchase_date ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="flex items-center justify-between mt-4 text-[12px] text-[var(--color-ink-soft)]">
                  <span>Page {data.pagination.page} of {totalPages} &middot; {fmtNumber(data.pagination.total_rows)} customers</span>
                  <div className="flex gap-2">
                    <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-2 py-1 border border-[var(--color-border)] rounded disabled:opacity-40">Prev</button>
                    <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="px-2 py-1 border border-[var(--color-border)] rounded disabled:opacity-40">Next</button>
                  </div>
                </div>
              </>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
