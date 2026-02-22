import type { TransactionItem } from '../../types/transaction';
import { computeStats } from '../../utils/stats';
import { formatPLN, formatArea, formatPricePerSqm } from '../../utils/formatters';
import './StatsPanel.css';

interface StatsPanelProps {
  items: TransactionItem[];
  totalFetched: number;
}

export default function StatsPanel({ items, totalFetched }: StatsPanelProps) {
  const stats = computeStats(items);

  return (
    <div className="stats-panel">
      <h4 className="stats-title">Statistics</h4>
      <div className="stats-grid">
        <StatRow label="Shown" value={`${stats.count} of ${totalFetched}`} />
        <StatRow
          label="Avg price"
          value={stats.avgPrice != null ? formatPLN(stats.avgPrice) : '—'}
        />
        <StatRow
          label="Avg PLN/m²"
          value={stats.avgPricePerSqm != null ? formatPricePerSqm(stats.avgPricePerSqm) : '—'}
        />
        <StatRow
          label="Median PLN/m²"
          value={stats.medianPricePerSqm != null ? formatPricePerSqm(stats.medianPricePerSqm) : '—'}
        />
        <StatRow
          label="Avg area"
          value={stats.avgArea != null ? formatArea(stats.avgArea) : '—'}
        />
        <StatRow
          label="Price range"
          value={
            stats.minPrice != null && stats.maxPrice != null
              ? `${formatPLN(stats.minPrice)} – ${formatPLN(stats.maxPrice)}`
              : '—'
          }
        />
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-row">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
