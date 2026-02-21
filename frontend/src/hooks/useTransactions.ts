import { useQuery } from '@tanstack/react-query';
import { fetchAllPages } from '../api/transactions';
import type { Bbox, Filters, FilterParams, TransactionItem } from '../types/transaction';
import { getPricePerSqm } from '../utils/formatters';

function buildApiParams(bbox: Bbox | null, filters: Filters): FilterParams {
  const params: FilterParams = {
    include_geometry: true,
    page_size: 500,
  };

  if (bbox) {
    params.bbox = `${bbox.minLon},${bbox.minLat},${bbox.maxLon},${bbox.maxLat}`;
  }
  if (filters.market) params.market = filters.market;
  if (filters.minPrice != null) params.min_price = filters.minPrice;
  if (filters.maxPrice != null) params.max_price = filters.maxPrice;
  if (filters.minArea != null) params.min_area = filters.minArea;
  if (filters.maxArea != null) params.max_area = filters.maxArea;
  if (filters.dateFrom) params.date_from = filters.dateFrom;
  if (filters.dateTo) params.date_to = filters.dateTo;

  return params;
}

function applyClientFilters(
  items: TransactionItem[],
  filters: Filters
): TransactionItem[] {
  return items.filter((item) => {
    // Rooms filter
    if (filters.rooms && filters.rooms.length > 0) {
      if (item.rooms == null) return false;
      const matchesRoom = filters.rooms.some((r) =>
        r === 5 ? item.rooms! >= 5 : item.rooms === r
      );
      if (!matchesRoom) return false;
    }

    // Price per m² filter
    const ppsm = getPricePerSqm(item.price_brutto, item.area_uzyt);
    if (filters.minPricePerSqm != null) {
      if (ppsm == null || ppsm < filters.minPricePerSqm) return false;
    }
    if (filters.maxPricePerSqm != null) {
      if (ppsm == null || ppsm > filters.maxPricePerSqm) return false;
    }

    return true;
  });
}

export function useTransactions(bbox: Bbox | null, filters: Filters) {
  const apiParams = buildApiParams(bbox, filters);

  const query = useQuery({
    queryKey: ['transactions', apiParams],
    queryFn: () => fetchAllPages(apiParams, 5),
    enabled: bbox != null,
    staleTime: 60_000,
    placeholderData: (prev) => prev,
  });

  const allItems = query.data?.items ?? [];
  const filteredItems = applyClientFilters(allItems, filters);

  return {
    items: filteredItems,
    totalFetched: allItems.length,
    isLoading: query.isLoading,
    isFetching: query.isFetching,
    error: query.error,
  };
}
