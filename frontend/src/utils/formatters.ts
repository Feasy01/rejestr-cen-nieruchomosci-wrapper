export function formatPLN(value: number): string {
  return value.toLocaleString('pl-PL', {
    maximumFractionDigits: 0,
  }) + ' PLN';
}

export function formatArea(value: number): string {
  return value.toLocaleString('pl-PL', {
    maximumFractionDigits: 1,
  }) + ' m\u00B2';
}

export function formatPricePerSqm(value: number): string {
  return value.toLocaleString('pl-PL', {
    maximumFractionDigits: 0,
  }) + ' PLN/m\u00B2';
}

export function getPricePerSqm(
  price: number | null,
  area: number | null
): number | null {
  if (price == null || area == null || area === 0) return null;
  return price / area;
}
