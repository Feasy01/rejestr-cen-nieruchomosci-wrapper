interface MarketToggleProps {
  value?: 'pierwotny' | 'wtorny';
  onChange: (value: 'pierwotny' | 'wtorny' | undefined) => void;
}

const options: { label: string; value: 'pierwotny' | 'wtorny' | undefined }[] = [
  { label: 'All', value: undefined },
  { label: 'Primary', value: 'pierwotny' },
  { label: 'Secondary', value: 'wtorny' },
];

export default function MarketToggle({ value, onChange }: MarketToggleProps) {
  return (
    <div className="filter-group">
      <label className="filter-label">Market type</label>
      <div className="toggle-group">
        {options.map((opt) => (
          <button
            key={opt.label}
            type="button"
            className={`toggle-btn ${value === opt.value ? 'active' : ''}`}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
