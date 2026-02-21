import type { Filters } from '../../types/transaction';
import MarketToggle from './MarketToggle';
import RangeInput from './RangeInput';
import RoomsSelect from './RoomsSelect';
import DateRangeInput from './DateRangeInput';
import './FiltersPanel.css';

interface FiltersPanelProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
  onReset: () => void;
}

export default function FiltersPanel({ filters, onChange, onReset }: FiltersPanelProps) {
  const update = (patch: Partial<Filters>) => {
    onChange({ ...filters, ...patch });
  };

  return (
    <div className="filters-panel">
      <div className="filters-header">
        <h3>Filters</h3>
        <button type="button" className="reset-btn" onClick={onReset}>
          Reset
        </button>
      </div>

      <MarketToggle
        value={filters.market}
        onChange={(market) => update({ market })}
      />

      <RangeInput
        label="Price"
        unit="PLN"
        minValue={filters.minPrice}
        maxValue={filters.maxPrice}
        minPlaceholder="e.g. 300000"
        maxPlaceholder="e.g. 800000"
        onMinChange={(v) => update({ minPrice: v })}
        onMaxChange={(v) => update({ maxPrice: v })}
      />

      <RangeInput
        label="Area"
        unit="m²"
        minValue={filters.minArea}
        maxValue={filters.maxArea}
        minPlaceholder="e.g. 30"
        maxPlaceholder="e.g. 100"
        onMinChange={(v) => update({ minArea: v })}
        onMaxChange={(v) => update({ maxArea: v })}
      />

      <RoomsSelect
        value={filters.rooms ?? []}
        onChange={(rooms) => update({ rooms })}
      />

      <DateRangeInput
        fromValue={filters.dateFrom}
        toValue={filters.dateTo}
        onFromChange={(v) => update({ dateFrom: v })}
        onToChange={(v) => update({ dateTo: v })}
      />

      <RangeInput
        label="Price per m²"
        unit="PLN/m²"
        minValue={filters.minPricePerSqm}
        maxValue={filters.maxPricePerSqm}
        minPlaceholder="e.g. 8000"
        maxPlaceholder="e.g. 20000"
        onMinChange={(v) => update({ minPricePerSqm: v })}
        onMaxChange={(v) => update({ maxPricePerSqm: v })}
      />
    </div>
  );
}
