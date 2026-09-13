import type { ReactNode } from 'react';
import { useFilters } from '../hooks/useFilters';

// ---------- formatting helpers ----------
export function fmtCurrency(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);
}
export function fmtNumber(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return new Intl.NumberFormat('en-IN').format(v);
}
export function fmtPct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  return `${v.toFixed(digits)}%`;
}

// ---------- Page header ----------
export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-[20px] font-semibold text-[var(--color-ink)]">{title}</h1>
      {subtitle && <p className="text-[13px] text-[var(--color-ink-soft)] mt-1">{subtitle}</p>}
    </div>
  );
}

// ---------- KPI card ----------
export function KpiCard({
  label, value, delta, deltaLabel,
}: { label: string; value: string; delta?: number | null; deltaLabel?: string }) {
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-5 py-4">
      <div className="text-[12px] font-medium text-[var(--color-ink-soft)]">{label}</div>
      <div className="text-[22px] font-semibold text-[var(--color-ink)] mt-1.5 tabular-nums">{value}</div>
      {delta !== null && delta !== undefined && (
        <div className={`text-[12px] mt-1.5 font-medium ${positive ? 'text-[var(--color-positive)]' : 'text-[var(--color-negative)]'}`}>
          {positive ? '▲' : '▼'} {Math.abs(delta).toFixed(1)}% {deltaLabel ?? ''}
        </div>
      )}
    </div>
  );
}

// ---------- Card container ----------
export function Card({ title, action, children }: { title?: string; action?: ReactNode; children: ReactNode }) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="text-[13px] font-semibold text-[var(--color-ink)]">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

// ---------- Status states ----------
export function LoadingState({ label = 'Loading data…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-[13px] text-[var(--color-ink-soft)]">
      <div className="animate-pulse">{label}</div>
    </div>
  );
}
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
      <div className="text-[13px] text-[var(--color-negative)]">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="text-[12px] px-3 py-1.5 rounded-md bg-[var(--color-negative-soft)] text-[var(--color-negative)] font-medium">
          Retry
        </button>
      )}
    </div>
  );
}
export function EmptyState({ label = 'No data for this selection.' }: { label?: string }) {
  return <div className="py-16 text-center text-[13px] text-[var(--color-ink-faint)]">{label}</div>;
}

// ---------- Badge ----------
export function Badge({ tone, children }: { tone: 'positive' | 'negative' | 'warning' | 'neutral'; children: ReactNode }) {
  const map = {
    positive: 'bg-[var(--color-positive-soft)] text-[var(--color-positive)]',
    negative: 'bg-[var(--color-negative-soft)] text-[var(--color-negative)]',
    warning: 'bg-[var(--color-warning-soft)] text-[var(--color-warning)]',
    neutral: 'bg-[var(--color-canvas)] text-[var(--color-ink-soft)]',
  };
  return <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${map[tone]}`}>{children}</span>;
}

// ---------- Filter bar ----------
const REGIONS = ['North', 'South', 'East', 'West', 'Central'];
const CATEGORIES = ['Electronics', 'Office Supplies', 'Furniture', 'Apparel', 'Home & Kitchen', 'Sports & Outdoors'];
const SEGMENTS = ['Consumer', 'Small Business', 'Corporate', 'Enterprise'];

export function FilterBar({ show = ['region', 'category', 'customer_segment', 'date'] }: { show?: string[] }) {
  const { filters, updateFilter, clearFilters } = useFilters();
  const hasFilters = Object.keys(filters).length > 0;

  return (
    <div className="flex flex-wrap items-center gap-2 mb-5">
      {show.includes('date') && (
        <>
          <input
            type="date"
            value={filters.date_from ?? ''}
            onChange={(e) => updateFilter('date_from', e.target.value || undefined)}
            className="text-[12px] border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)]"
          />
          <span className="text-[12px] text-[var(--color-ink-faint)]">to</span>
          <input
            type="date"
            value={filters.date_to ?? ''}
            onChange={(e) => updateFilter('date_to', e.target.value || undefined)}
            className="text-[12px] border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)]"
          />
        </>
      )}
      {show.includes('region') && (
        <select
          value={filters.region ?? ''}
          onChange={(e) => updateFilter('region', e.target.value || undefined)}
          className="text-[12px] border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)]"
        >
          <option value="">All Regions</option>
          {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      )}
      {show.includes('category') && (
        <select
          value={filters.category ?? ''}
          onChange={(e) => updateFilter('category', e.target.value || undefined)}
          className="text-[12px] border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)]"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      )}
      {show.includes('customer_segment') && (
        <select
          value={filters.customer_segment ?? ''}
          onChange={(e) => updateFilter('customer_segment', e.target.value || undefined)}
          className="text-[12px] border border-[var(--color-border)] rounded-md px-2 py-1.5 bg-[var(--color-surface)]"
        >
          <option value="">All Segments</option>
          {SEGMENTS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      )}
      {hasFilters && (
        <button onClick={clearFilters} className="text-[12px] text-[var(--color-primary)] font-medium px-2 py-1.5">
          Clear filters
        </button>
      )}
    </div>
  );
}

// ---------- Export button ----------
export function ExportButton<T extends object>({ data, filename }: { data: T[]; filename: string }) {
  const exportCsv = () => {
    if (!data || data.length === 0) return;
    const headers = Object.keys(data[0]) as (keyof T)[];
    const rows = data.map((row) => headers.map((h) => JSON.stringify(row[h] ?? '')).join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <button onClick={exportCsv} className="text-[12px] px-3 py-1.5 rounded-md border border-[var(--color-border)] text-[var(--color-ink-soft)] font-medium hover:bg-[var(--color-canvas)]">
      Export CSV
    </button>
  );
}

export const CHART_COLORS = [
  'var(--color-chart-1)', 'var(--color-chart-2)', 'var(--color-chart-3)',
  'var(--color-chart-4)', 'var(--color-chart-5)', 'var(--color-chart-6)',
];
