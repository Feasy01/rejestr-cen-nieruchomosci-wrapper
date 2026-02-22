export interface ColorStop {
  threshold: number;
  color: string;
  label: string;
}

export const PRICE_COLOR_STOPS: ColorStop[] = [
  { threshold: 0, color: '#2ecc71', label: '< 10k' },
  { threshold: 10000, color: '#a3d977', label: '10k–13k' },
  { threshold: 13000, color: '#f1c40f', label: '13k–16k' },
  { threshold: 16000, color: '#e67e22', label: '16k–20k' },
  { threshold: 20000, color: '#e74c3c', label: '> 20k' },
];

export function getPriceColor(pricePerSqm: number): string {
  for (let i = PRICE_COLOR_STOPS.length - 1; i >= 0; i--) {
    if (pricePerSqm >= PRICE_COLOR_STOPS[i].threshold) {
      return PRICE_COLOR_STOPS[i].color;
    }
  }
  return PRICE_COLOR_STOPS[0].color;
}
