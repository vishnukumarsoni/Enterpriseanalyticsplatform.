import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ScatterChart, Scatter, ZAxis } from 'recharts';
import { useFetch } from '../hooks/useFetch';
import { useFilters } from '../hooks/useFilters';
import { api } from '../services/api';
import { PageHeader, Card, FilterBar, LoadingState, ErrorState, EmptyState, ExportButton, fmtCurrency, fmtPct, CHART_COLORS } from '../components/ui';

interface ProductRow { product_id: string; product_name: string; category: string; sub_category: string; revenue: number; profit: number; margin_pct: number; units_sold: number; }
interface ProductsResponse {
  top_10_products: ProductRow[];
  bottom_10_products: ProductRow[];
  highest_margin_products: ProductRow[];
  lowest_margin_products: ProductRow[];
  category_performance: { category: string; revenue: number; profit: number }[];
  most_returned_products: { product_id: string; product_name: string; return_count: number; total_orders: number; return_rate_pct: number }[];
  all_products: ProductRow[];
}

function ProductTable({ rows }: { rows: ProductRow[] }) {
  return (
    <table className="w-full text-[12px]">
      <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
        <th className="py-2">Product</th><th className="text-right">Revenue</th><th className="text-right">Margin</th>
      </tr></thead>
      <tbody>
        {rows.map((p) => (
          <tr key={p.product_id} className="border-b border-[var(--color-border)] last:border-0">
            <td className="py-2">{p.product_name}</td>
            <td className="text-right tabular-nums">{fmtCurrency(p.revenue)}</td>
            <td className="text-right tabular-nums">{fmtPct(p.margin_pct)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Products() {
  const { filters } = useFilters();
  const { data, loading, error, reload } = useFetch<ProductsResponse>(() => api.products(filters) as Promise<ProductsResponse>, [filters]);

  return (
    <div>
      <PageHeader title="Product Analytics" subtitle="Revenue, margin, and profitability across the catalog" />
      <FilterBar />

      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <Card title="Top 10 Products by Revenue">
              {data.top_10_products.length === 0 ? <EmptyState /> : <ProductTable rows={data.top_10_products} />}
            </Card>
            <Card title="Bottom 10 Products by Revenue">
              {data.bottom_10_products.length === 0 ? <EmptyState /> : <ProductTable rows={data.bottom_10_products} />}
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <Card title="Category Performance">
              {data.category_performance.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.category_performance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="category" tick={{ fontSize: 9 }} interval={0} angle={-15} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => fmtCurrency(Number(v))} />
                    <Bar dataKey="revenue" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
            <Card title="Profitability Matrix (Revenue vs Margin)">
              {data.all_products.length === 0 ? <EmptyState /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" dataKey="revenue" name="Revenue" tick={{ fontSize: 10 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="number" dataKey="margin_pct" name="Margin %" tick={{ fontSize: 10 }} />
                    <ZAxis type="number" dataKey="units_sold" range={[20, 200]} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(v, name) => name === 'Revenue' ? fmtCurrency(Number(v)) : `${Number(v).toFixed(1)}%`} />
                    <Scatter data={data.all_products.slice(0, 200)} fill={CHART_COLORS[4]} fillOpacity={0.6} />
                  </ScatterChart>
                </ResponsiveContainer>
              )}
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card title="Highest Margin Products">
              {data.highest_margin_products.length === 0 ? <EmptyState /> : <ProductTable rows={data.highest_margin_products} />}
            </Card>
            <Card title="Most Returned Products" action={<ExportButton data={data.most_returned_products} filename="most_returned_products" />}>
              {data.most_returned_products.length === 0 ? <EmptyState /> : (
                <table className="w-full text-[12px]">
                  <thead><tr className="text-left text-[var(--color-ink-faint)] border-b border-[var(--color-border)]">
                    <th className="py-2">Product</th><th className="text-right">Returns</th><th className="text-right">Return Rate</th>
                  </tr></thead>
                  <tbody>
                    {data.most_returned_products.map((p) => (
                      <tr key={p.product_id} className="border-b border-[var(--color-border)] last:border-0">
                        <td className="py-2">{p.product_name}</td>
                        <td className="text-right tabular-nums">{p.return_count}</td>
                        <td className="text-right tabular-nums">{fmtPct(p.return_rate_pct)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
