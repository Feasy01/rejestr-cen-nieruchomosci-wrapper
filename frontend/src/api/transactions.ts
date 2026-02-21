import apiClient from './client';
import type { FilterParams, TransactionListResponse } from '../types/transaction';

export async function fetchTransactions(
  params: FilterParams
): Promise<TransactionListResponse> {
  const query: Record<string, string> = {};

  if (params.bbox) query.bbox = params.bbox;
  if (params.market) query.market = params.market;
  if (params.function) query.function = params.function;
  if (params.min_price != null) query.min_price = String(params.min_price);
  if (params.max_price != null) query.max_price = String(params.max_price);
  if (params.min_area != null) query.min_area = String(params.min_area);
  if (params.max_area != null) query.max_area = String(params.max_area);
  if (params.date_from) query.date_from = params.date_from;
  if (params.date_to) query.date_to = params.date_to;
  if (params.page != null) query.page = String(params.page);
  if (params.page_size != null) query.page_size = String(params.page_size);
  if (params.include_geometry != null)
    query.include_geometry = String(params.include_geometry);
  if (params.include_raw != null)
    query.include_raw = String(params.include_raw);

  const { data } = await apiClient.get<TransactionListResponse>(
    '/transactions/lokale',
    { params: query }
  );
  return data;
}

export async function fetchAllPages(
  params: FilterParams,
  maxPages = 5
): Promise<TransactionListResponse> {
  const allItems: TransactionListResponse['items'] = [];
  let currentPage = 1;

  for (let i = 0; i < maxPages; i++) {
    const response = await fetchTransactions({
      ...params,
      page: currentPage,
      page_size: params.page_size ?? 500,
      include_geometry: true,
    });

    allItems.push(...response.items);

    if (!response.next_page) break;
    currentPage = response.next_page;
  }

  return {
    page: 1,
    page_size: allItems.length,
    next_page: null,
    items: allItems,
  };
}
