import { useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { Bbox, Filters } from './types/transaction';
import { useTransactions } from './hooks/useTransactions';
import MapView from './components/Map/MapView';
import FiltersPanel from './components/Filters/FiltersPanel';
import StatsPanel from './components/Stats/StatsPanel';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const INITIAL_FILTERS: Filters = {};

function AppContent() {
  const [bbox, setBbox] = useState<Bbox | null>(null);
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);

  const { items, totalFetched, isLoading, isFetching, error } =
    useTransactions(bbox, filters);

  const handleBoundsChange = useCallback((newBbox: Bbox) => {
    setBbox(newBbox);
  }, []);

  const handleResetFilters = useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Warsaw Property Prices</h1>
        {isFetching && <span className="header-status">Fetching data...</span>}
        {error && (
          <span className="header-error">
            Error loading data. Check API connection.
          </span>
        )}
      </header>
      <div className="app-body">
        <div className="sidebar">
          <FiltersPanel
            filters={filters}
            onChange={setFilters}
            onReset={handleResetFilters}
          />
          <StatsPanel items={items} totalFetched={totalFetched} />
        </div>
        <MapView
          items={items}
          onBoundsChange={handleBoundsChange}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
