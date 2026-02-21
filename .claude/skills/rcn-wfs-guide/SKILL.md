---
name: rcn-wfs-guide
description: Reference guide for the RCN (Rejestr Cen Nieruchomosci) WFS upstream service — data model, query patterns, known quirks. Use when testing, debugging, or extending the wrapper API.
---

# RCN WFS Service — Upstream Reference

## What is RCN?

Rejestr Cen Nieruchomosci (Real Estate Price Register) is a public WFS service run by GUGiK (Poland's Main Office of Geodesy and Cartography). It exposes property transaction data (sales of apartments, buildings, land parcels) via OGC WFS 2.0.

**Base URL:** `https://mapy.geoportal.gov.pl/wss/service/rcn`

No authentication or API key is required.

---

## Available Layers (FeatureTypes)

| Layer          | Description                        | Typical use               |
|----------------|------------------------------------|---------------------------|
| `ms:lokale`    | Apartment/unit transactions        | Main layer for this API   |
| `ms:budynki`   | Building transactions              | Not wrapped yet           |
| `ms:dzialki`   | Land parcel transactions           | Not wrapped yet           |
| `ms:powiaty`   | County boundaries (helper layer)   | Administrative boundaries |

All layers live under the MapServer namespace: `xmlns:ms="http://mapserver.gis.umn.edu/mapserver"`

---

## ms:lokale — Field Reference

All fields are **string type** in the upstream schema (even numeric ones). All are optional (`minOccurs="0"`).

### Geometry
- `msGeometry` — `gml:Point` with `gml:pos` containing two floats: **northing easting** in EPSG:2180

### Transaction fields
| Field                    | Example value                  | Notes                            |
|--------------------------|--------------------------------|----------------------------------|
| `tran_oznaczenie_trans`  | `RCN_T_12029`                  | Internal transaction ID          |
| `tran_rodzaj_trans`      | `wolnyRynek`                   | Transaction type                 |
| `tran_rodzaj_rynku`      | `pierwotny` / `wtorny`         | Market type (primary/secondary)  |
| `tran_sprzedajacy`       | `osobaPrawna`                  | Seller type                      |
| `tran_kupujacy`          | `osobaFizyczna`                | Buyer type                       |
| `tran_cena_brutto`       | `528916`                       | Gross price in PLN (as string!)  |
| `tran_vat`               | *(often empty)*                | VAT amount                       |

### Document fields
| Field             | Example value                     | Notes                              |
|-------------------|-----------------------------------|------------------------------------|
| `dok_oznaczenie`  | `AN 7739/2024`                    | Notarial act reference             |
| `dok_data`        | `2024-10-02 00:00:00+02`          | Date — first 10 chars = YYYY-MM-DD|
| `dok_tworca`      | `KUNECKA AGNIESZKA`               | Notary name                        |

### Property/unit fields
| Field             | Example value                                 | Notes                        |
|-------------------|-----------------------------------------------|------------------------------|
| `lok_funkcja`     | `mieszkalna`                                  | Function (residential, etc.) |
| `lok_liczba_izb`  | `3`                                           | Number of rooms (as string)  |
| `lok_nr_kond`     | `6`                                           | Floor number (as string)     |
| `lok_pow_uzyt`    | `60.36`                                       | Usable area m² (as string)   |
| `lok_pow_przyn`   | *(often empty)*                               | Ancillary area               |
| `lok_id_lokalu`   | `061701_1.0001.2262_BUD.108_LOK`              | Internal unit ID             |
| `lok_nr_lokalu`   | `108_LOK`                                     | Unit number                  |
| `lok_adres`       | *(often empty)*                               | Address (rarely populated)   |
| `nier_udzial`     | `1/1`                                         | Ownership share              |
| `nier_pow_gruntu` | `0.4823`                                      | Land area (ha)               |
| `nier_rodzaj`     | `nieruchomoscLokalowa`                        | Property type                |
| `nier_prawo`      | `wlasnoscLokaluWrazZPrawemZwiazanym`          | Legal title type             |
| `teryt`           | `0617`                                        | TERYT code (county)          |

---

## WFS Query Patterns

### Supported operations
`GetCapabilities`, `DescribeFeatureType`, `GetFeature`, `GetPropertyValue`

### Basic GetFeature (no filters)
```
GET /wss/service/rcn?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&TYPENAMES=ms:lokale&COUNT=5
```

### BBOX query (EPSG:2180 only!)
```
GET ...&TYPENAMES=ms:lokale&COUNT=100&STARTINDEX=0
      &SRSNAME=urn:ogc:def:crs:EPSG::2180
      &BBOX=460000,630000,500000,670000,urn:ogc:def:crs:EPSG::2180
```

BBOX values are: `minNorthing,minEasting,maxNorthing,maxEasting,CRS`

### PropertyIsEqualTo (text filter)
Use the `FILTER` KVP param with OGC XML:
```
FILTER=<Filter xmlns="http://www.opengis.net/ogc">
  <PropertyIsEqualTo>
    <PropertyName>tran_rodzaj_rynku</PropertyName>
    <Literal>pierwotny</Literal>
  </PropertyIsEqualTo>
</Filter>
```

### Combined BBOX + property filter
**Critical:** BBOX and FILTER KVP params are **mutually exclusive**. To combine them, put BBOX inside the FILTER XML:
```xml
<Filter xmlns="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml">
  <And>
    <BBOX>
      <PropertyName>msGeometry</PropertyName>
      <gml:Envelope srsName="urn:ogc:def:crs:EPSG::2180">
        <gml:lowerCorner>460000 630000</gml:lowerCorner>
        <gml:upperCorner>500000 670000</gml:upperCorner>
      </gml:Envelope>
    </BBOX>
    <PropertyIsEqualTo>
      <PropertyName>lok_funkcja</PropertyName>
      <Literal>mieszkalna</Literal>
    </PropertyIsEqualTo>
  </And>
</Filter>
```

### Pagination
- Use `COUNT` (page size) and `STARTINDEX` (offset)
- Response attribute `numberMatched` is **always "unknown"**
- Response attribute `numberReturned` tells how many came back
- If `numberReturned == COUNT`, there are probably more pages

---

## Known Quirks and Gotchas

### 1. EPSG:4326 BBOX returns empty results
WFS 2.0 uses **lat,lon** axis order for EPSG:4326 (not the intuitive lon,lat). Sending `BBOX=20.85,52.05,21.30,52.37` with `SRSNAME=urn:ogc:def:crs:EPSG::4326` returns 0 results because the axis order is swapped.

**Our solution:** Always query in EPSG:2180 and convert coordinates with pyproj.

### 2. All fields are strings
Even `tran_cena_brutto` (price) and `lok_pow_uzyt` (area) are stored as XML strings. Upstream `PropertyIsGreaterThan` on these fields does **lexicographic** comparison ("9" > "50000"), not numeric.

**Our solution:** Only use `PropertyIsEqualTo` upstream; apply numeric filters locally.

### 3. EPSG:2180 axis order is (northing, easting)
`gml:pos` returns `378176.102614 758653.828868` which is `northing easting` (Y X), not X Y. This matters for pyproj conversion.

### 4. Empty fields come as `<ms:field></ms:field>` (not missing)
Elements are always present in the response but may have no text content. The parser treats these as empty strings.

### 5. `dok_data` has timezone offset
Format: `2024-10-02 00:00:00+02` — we extract just the first 10 characters for the date.

### 6. Many fields are commonly empty
`lok_adres`, `lok_pow_przyn`, `tran_vat`, `lok_cena_brutto`, `lok_vat` are frequently empty. The API must tolerate this gracefully.

---

## Wrapper API Quick Reference

### GET /v1/transactions/lokale
Main endpoint. Query params:
- `bbox=minLon,minLat,maxLon,maxLat` (EPSG:4326, converted internally)
- `market=pierwotny|wtorny`
- `function=mieszkalna`
- `date_from=YYYY-MM-DD`, `date_to=YYYY-MM-DD`
- `min_price`, `max_price` (PLN)
- `min_area`, `max_area` (m²)
- `page=1`, `page_size=100` (max 500)
- `include_geometry=true` (adds GeoJSON Point in EPSG:4326)
- `include_raw=true` (adds raw upstream fields for debugging)

### GET /v1/metadata/lokale/schema
Returns field names and types from DescribeFeatureType (cached 24h).

### GET /v1/health/upstream
Pings GetCapabilities, returns `{"status": "ok", "latency_ms": 234.5}`.

---

## Useful Test Queries

```bash
# Health check
curl http://localhost:8000/v1/health/upstream

# Fetch 5 transactions from Warsaw area
curl "http://localhost:8000/v1/transactions/lokale?bbox=20.85,52.05,21.30,52.37&page_size=5"

# Primary market apartments with geometry
curl "http://localhost:8000/v1/transactions/lokale?bbox=20.85,52.05,21.30,52.37&market=pierwotny&function=mieszkalna&include_geometry=true"

# Filter by price and area
curl "http://localhost:8000/v1/transactions/lokale?bbox=20.85,52.05,21.30,52.37&min_price=300000&max_price=600000&min_area=40&max_area=80"

# Page 2
curl "http://localhost:8000/v1/transactions/lokale?bbox=20.85,52.05,21.30,52.37&page=2&page_size=50"

# Debug with raw upstream fields
curl "http://localhost:8000/v1/transactions/lokale?bbox=20.85,52.05,21.30,52.37&page_size=1&include_raw=true"

# Schema introspection
curl http://localhost:8000/v1/metadata/lokale/schema
```

## Running the app

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload        # dev server on :8000
pytest tests/ -v                      # 44 tests
```
