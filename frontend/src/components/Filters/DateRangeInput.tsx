interface DateRangeInputProps {
  fromValue?: string;
  toValue?: string;
  onFromChange: (value: string | undefined) => void;
  onToChange: (value: string | undefined) => void;
}

export default function DateRangeInput({
  fromValue,
  toValue,
  onFromChange,
  onToChange,
}: DateRangeInputProps) {
  return (
    <div className="filter-group">
      <label className="filter-label">Date range</label>
      <div className="range-inputs">
        <input
          type="date"
          className="filter-input"
          value={fromValue ?? ''}
          onChange={(e) =>
            onFromChange(e.target.value || undefined)
          }
        />
        <span className="range-separator">—</span>
        <input
          type="date"
          className="filter-input"
          value={toValue ?? ''}
          onChange={(e) =>
            onToChange(e.target.value || undefined)
          }
        />
      </div>
    </div>
  );
}
