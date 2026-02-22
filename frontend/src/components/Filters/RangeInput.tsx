interface RangeInputProps {
  label: string;
  unit?: string;
  minValue?: number;
  maxValue?: number;
  minPlaceholder?: string;
  maxPlaceholder?: string;
  onMinChange: (value: number | undefined) => void;
  onMaxChange: (value: number | undefined) => void;
}

export default function RangeInput({
  label,
  unit,
  minValue,
  maxValue,
  minPlaceholder = 'min',
  maxPlaceholder = 'max',
  onMinChange,
  onMaxChange,
}: RangeInputProps) {
  return (
    <div className="filter-group">
      <label className="filter-label">
        {label} {unit && <span className="filter-unit">({unit})</span>}
      </label>
      <div className="range-inputs">
        <input
          type="number"
          className="filter-input"
          placeholder={minPlaceholder}
          value={minValue ?? ''}
          onChange={(e) =>
            onMinChange(e.target.value ? Number(e.target.value) : undefined)
          }
        />
        <span className="range-separator">—</span>
        <input
          type="number"
          className="filter-input"
          placeholder={maxPlaceholder}
          value={maxValue ?? ''}
          onChange={(e) =>
            onMaxChange(e.target.value ? Number(e.target.value) : undefined)
          }
        />
      </div>
    </div>
  );
}
