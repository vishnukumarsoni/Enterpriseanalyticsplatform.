import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { PageHeader, Card, Badge, LoadingState, ErrorState } from '../components/ui';

export default function Settings() {
  const { data, loading, error, reload } = useFetch(() => api.health(), []);

  return (
    <div>
      <PageHeader title="Settings" subtitle="System status and configuration" />

      <Card title="API Connection">
        {loading && <LoadingState />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && (
          <div className="flex items-center gap-3 text-[13px]">
            <Badge tone={data.database_connected ? 'positive' : 'negative'}>
              {data.status === 'ok' ? 'Connected' : 'Degraded'}
            </Badge>
            <span className="text-[var(--color-ink-soft)]">
              Database: {data.database_connected ? 'connected' : 'unreachable'}
            </span>
          </div>
        )}
      </Card>

      <Card title="About">
        <p className="text-[13px] text-[var(--color-ink-soft)] leading-relaxed">
          Enterprise Sales, Customer &amp; Revenue Analytics Platform — a full-stack analytics
          system built on PostgreSQL, a Python ETL pipeline, scikit-learn ML models
          (churn prediction, RFM segmentation, revenue forecasting), a FastAPI backend,
          and this React + TypeScript dashboard. All figures on every page are computed
          live from the database — nothing here is hard-coded.
        </p>
      </Card>
    </div>
  );
}
