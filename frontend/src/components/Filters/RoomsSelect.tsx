interface RoomsSelectProps {
  value: number[];
  onChange: (rooms: number[]) => void;
}

const ROOM_OPTIONS = [1, 2, 3, 4, 5];

export default function RoomsSelect({ value, onChange }: RoomsSelectProps) {
  const toggle = (room: number) => {
    if (value.includes(room)) {
      onChange(value.filter((r) => r !== room));
    } else {
      onChange([...value, room]);
    }
  };

  return (
    <div className="filter-group">
      <label className="filter-label">Rooms</label>
      <div className="toggle-group">
        {ROOM_OPTIONS.map((room) => (
          <button
            key={room}
            type="button"
            className={`toggle-btn ${value.includes(room) ? 'active' : ''}`}
            onClick={() => toggle(room)}
          >
            {room === 5 ? '5+' : room}
          </button>
        ))}
      </div>
    </div>
  );
}
