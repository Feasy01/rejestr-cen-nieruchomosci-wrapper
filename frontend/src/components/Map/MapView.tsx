import { useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from 'react-leaflet';
import type { Map as LeafletMap } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { TransactionItem, Bbox } from '../../types/transaction';
import { getPriceColor } from '../../utils/colors';
import { formatPLN, formatArea, formatPricePerSqm, getPricePerSqm } from '../../utils/formatters';
import { ColorLegend } from './ColorLegend';
import './MapView.css';

const WARSAW_CENTER: [number, number] = [52.23, 21.01];
const DEFAULT_ZOOM = 12;

interface MapViewProps {
  items: TransactionItem[];
  onBoundsChange: (bbox: Bbox) => void;
  isLoading: boolean;
}

function BoundsWatcher({ onBoundsChange }: { onBoundsChange: (bbox: Bbox) => void }) {
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const reportBounds = useCallback(
    (map: LeafletMap) => {
      const bounds = map.getBounds();
      onBoundsChange({
        minLon: bounds.getWest(),
        minLat: bounds.getSouth(),
        maxLon: bounds.getEast(),
        maxLat: bounds.getNorth(),
      });
    },
    [onBoundsChange]
  );

  const map = useMapEvents({
    moveend: () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => reportBounds(map), 500);
    },
    load: () => reportBounds(map),
  });

  useEffect(() => {
    // Report initial bounds
    reportBounds(map);
  }, [map, reportBounds]);

  return null;
}

function TransactionPopup({ item }: { item: TransactionItem }) {
  const ppsm = getPricePerSqm(item.price_brutto, item.area_uzyt);
  return (
    <div className="transaction-popup">
      <div className="popup-row popup-price">
        {item.price_brutto != null ? formatPLN(item.price_brutto) : '—'}
        {item.area_uzyt != null && (
          <span className="popup-separator"> | {formatArea(item.area_uzyt)}</span>
        )}
      </div>
      {ppsm != null && (
        <div className="popup-row popup-ppsm">{formatPricePerSqm(ppsm)}</div>
      )}
      <div className="popup-row popup-details">
        {item.rooms != null && <span>{item.rooms} rooms</span>}
        {item.floor != null && <span> | Floor {item.floor}</span>}
      </div>
      <div className="popup-row popup-meta">
        {item.market && (
          <span>{item.market === 'pierwotny' ? 'Primary' : 'Secondary'} market</span>
        )}
        {item.doc_date && <span> | {item.doc_date}</span>}
      </div>
      {item.doc_ref && (
        <div className="popup-row popup-ref">Ref: {item.doc_ref}</div>
      )}
    </div>
  );
}

export default function MapView({ items, onBoundsChange, isLoading }: MapViewProps) {
  return (
    <div className="map-container">
      {isLoading && <div className="map-loading">Loading...</div>}
      <MapContainer
        center={WARSAW_CENTER}
        zoom={DEFAULT_ZOOM}
        className="leaflet-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <BoundsWatcher onBoundsChange={onBoundsChange} />
        <ColorLegend />
        {items.map((item) => {
          if (!item.geometry) return null;
          const ppsm = getPricePerSqm(item.price_brutto, item.area_uzyt);
          const color = ppsm != null ? getPriceColor(ppsm) : '#999';
          const [lng, lat] = item.geometry.coordinates;
          return (
            <CircleMarker
              key={item.id}
              center={[lat, lng]}
              radius={7}
              pathOptions={{
                fillColor: color,
                fillOpacity: 0.8,
                color: '#333',
                weight: 1,
              }}
            >
              <Popup>
                <TransactionPopup item={item} />
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
