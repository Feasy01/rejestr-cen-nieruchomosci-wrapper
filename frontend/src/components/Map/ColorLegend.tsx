import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { PRICE_COLOR_STOPS } from '../../utils/colors';

export function ColorLegend() {
  const map = useMap();

  useEffect(() => {
    const legend = new L.Control({ position: 'bottomright' });

    legend.onAdd = () => {
      const div = L.DomUtil.create('div', 'price-legend');
      div.innerHTML = `
        <div style="
          background: white;
          padding: 8px 12px;
          border-radius: 6px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.2);
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          font-size: 11px;
          line-height: 1.6;
        ">
          <div style="font-weight: 600; margin-bottom: 4px;">PLN/m\u00B2</div>
          ${PRICE_COLOR_STOPS.map(
            (stop) => `
            <div style="display: flex; align-items: center; gap: 6px;">
              <span style="
                display: inline-block;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: ${stop.color};
                border: 1px solid #333;
              "></span>
              <span>${stop.label}</span>
            </div>
          `
          ).join('')}
        </div>
      `;
      return div;
    };

    legend.addTo(map);
    return () => {
      legend.remove();
    };
  }, [map]);

  return null;
}
