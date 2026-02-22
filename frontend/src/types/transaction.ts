export interface GeoJSONPoint {
  type: 'Point';
  coordinates: [number, number]; // [longitude, latitude]
}

export interface TransactionItem {
  id: string;
  doc_date: string | null;
  doc_ref: string | null;
  notary: string | null;
  market: string | null;
  price_brutto: number | null;
  area_uzyt: number | null;
  function: string | null;
  rooms: number | null;
  floor: string | null;
  share: string | null;
  geometry: GeoJSONPoint | null;
  source: string;
  fetched_at: string;
}

export interface TransactionListResponse {
  page: number;
  page_size: number;
  next_page: number | null;
  items: TransactionItem[];
}

export interface FilterParams {
  bbox?: string;
  market?: 'pierwotny' | 'wtorny';
  function?: string;
  min_price?: number;
  max_price?: number;
  min_area?: number;
  max_area?: number;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
  include_geometry?: boolean;
  include_raw?: boolean;
}

export interface Bbox {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
}

export interface Filters {
  market?: 'pierwotny' | 'wtorny';
  minPrice?: number;
  maxPrice?: number;
  minArea?: number;
  maxArea?: number;
  dateFrom?: string;
  dateTo?: string;
  rooms?: number[];
  minPricePerSqm?: number;
  maxPricePerSqm?: number;
}
