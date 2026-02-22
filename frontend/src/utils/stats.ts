import type { TransactionItem } from '../types/transaction';
import { getPricePerSqm } from './formatters';

export interface Stats {
  count: number;
  avgPrice: number | null;
  avgPricePerSqm: number | null;
  medianPricePerSqm: number | null;
  avgArea: number | null;
  minPrice: number | null;
  maxPrice: number | null;
}

export function computeStats(items: TransactionItem[]): Stats {
  if (items.length === 0) {
    return {
      count: 0,
      avgPrice: null,
      avgPricePerSqm: null,
      medianPricePerSqm: null,
      avgArea: null,
      minPrice: null,
      maxPrice: null,
    };
  }

  const prices = items
    .map((i) => i.price_brutto)
    .filter((p): p is number => p != null);

  const areas = items
    .map((i) => i.area_uzyt)
    .filter((a): a is number => a != null);

  const pricesPerSqm = items
    .map((i) => getPricePerSqm(i.price_brutto, i.area_uzyt))
    .filter((p): p is number => p != null);

  const avg = (arr: number[]) =>
    arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : null;

  const median = (arr: number[]): number | null => {
    if (arr.length === 0) return null;
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0
      ? sorted[mid]
      : (sorted[mid - 1] + sorted[mid]) / 2;
  };

  return {
    count: items.length,
    avgPrice: avg(prices),
    avgPricePerSqm: avg(pricesPerSqm),
    medianPricePerSqm: median(pricesPerSqm),
    avgArea: avg(areas),
    minPrice: prices.length > 0 ? Math.min(...prices) : null,
    maxPrice: prices.length > 0 ? Math.max(...prices) : null,
  };
}
