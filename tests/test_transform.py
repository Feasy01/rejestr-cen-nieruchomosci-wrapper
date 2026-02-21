"""Tests for type conversion, CRS transform, and local filtering."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.services.parser_gml import ParsedFeature, parse_feature_collection
from app.services.transform import (
    apply_local_filters,
    bbox_4326_to_2180,
    feature_to_transaction,
)
from tests.conftest import SAMPLE_FEATURE_XML


def _make_feature(
    gml_id: str = "lokale.1",
    price: str = "500000",
    area: str = "60.0",
    date: str = "2024-06-15 00:00:00+02",
    market: str = "pierwotny",
    function: str = "mieszkalna",
    rooms: str = "3",
    floor: str = "5",
) -> ParsedFeature:
    return ParsedFeature(
        gml_id=gml_id,
        geometry_pos=(400000.0, 600000.0),
        properties={
            "dok_data": date,
            "dok_oznaczenie": "AN 1/2024",
            "dok_tworca": "TEST NOTARY",
            "tran_rodzaj_rynku": market,
            "tran_cena_brutto": price,
            "lok_pow_uzyt": area,
            "lok_funkcja": function,
            "lok_liczba_izb": rooms,
            "lok_nr_kond": floor,
            "nier_udzial": "1/1",
        },
    )


class TestFeatureToTransaction:
    def test_basic_conversion(self):
        parsed = parse_feature_collection(SAMPLE_FEATURE_XML)
        f = parsed.features[0]
        now = datetime(2026, 2, 21, 19, 0, 0, tzinfo=timezone.utc)

        item = feature_to_transaction(f, fetched_at=now)

        assert item.id == "lokale.3751688"
        assert item.doc_date == "2024-10-02"
        assert item.doc_ref == "AN 7739/2024"
        assert item.notary == "KUNECKA AGNIESZKA"
        assert item.market == "pierwotny"
        assert item.price_brutto == Decimal("528916")
        assert item.area_uzyt == Decimal("60.36")
        assert item.function == "mieszkalna"
        assert item.rooms == 3
        assert item.floor == "6"
        assert item.share == "1/1"
        assert item.geometry is None
        assert item.raw is None
        assert item.source == "geoportal_rcn_wfs"
        assert item.fetched_at == now

    def test_include_geometry(self):
        parsed = parse_feature_collection(SAMPLE_FEATURE_XML)
        f = parsed.features[0]
        now = datetime.now(timezone.utc)

        item = feature_to_transaction(f, include_geometry=True, fetched_at=now)

        assert item.geometry is not None
        assert item.geometry.type == "Point"
        lon, lat = item.geometry.coordinates
        # Should be roughly in Poland (~20-21 lon, ~51-53 lat)
        assert 14.0 < lon < 24.0, f"Longitude {lon} out of range for Poland"
        assert 49.0 < lat < 55.0, f"Latitude {lat} out of range for Poland"

    def test_include_raw(self):
        parsed = parse_feature_collection(SAMPLE_FEATURE_XML)
        f = parsed.features[0]
        now = datetime.now(timezone.utc)

        item = feature_to_transaction(f, include_raw=True, fetched_at=now)

        assert item.raw is not None
        assert item.raw["tran_cena_brutto"] == "528916"

    def test_empty_fields_become_none(self):
        f = ParsedFeature(
            gml_id="lokale.999",
            geometry_pos=None,
            properties={
                "dok_data": "",
                "dok_oznaczenie": "",
                "dok_tworca": "",
                "tran_rodzaj_rynku": "",
                "tran_cena_brutto": "",
                "lok_pow_uzyt": "",
                "lok_funkcja": "",
                "lok_liczba_izb": "",
                "lok_nr_kond": "",
                "nier_udzial": "",
            },
        )
        now = datetime.now(timezone.utc)
        item = feature_to_transaction(f, fetched_at=now)

        assert item.doc_date is None
        assert item.doc_ref is None
        assert item.price_brutto is None
        assert item.area_uzyt is None
        assert item.rooms is None
        assert item.geometry is None

    def test_invalid_number_returns_none(self):
        f = ParsedFeature(
            gml_id="lokale.bad",
            geometry_pos=None,
            properties={
                "tran_cena_brutto": "not-a-number",
                "lok_pow_uzyt": "abc",
                "lok_liczba_izb": "xyz",
            },
        )
        now = datetime.now(timezone.utc)
        item = feature_to_transaction(f, fetched_at=now)

        assert item.price_brutto is None
        assert item.area_uzyt is None
        assert item.rooms is None


class TestBboxConversion:
    def test_warsaw_bbox(self):
        # Warsaw area in EPSG:4326
        min_lon, min_lat, max_lon, max_lat = 20.85, 52.05, 21.30, 52.37
        result = bbox_4326_to_2180(min_lon, min_lat, max_lon, max_lat)

        min_n, min_e, max_n, max_e = result
        # EPSG:2180 coords for Warsaw should be roughly:
        # Northing: ~470000-500000, Easting: ~630000-660000
        assert 450000 < min_n < 520000, f"min northing {min_n} out of range"
        assert 600000 < min_e < 680000, f"min easting {min_e} out of range"
        assert min_n < max_n
        assert min_e < max_e


class TestLocalFilters:
    def test_no_filters_returns_all(self):
        features = [_make_feature(gml_id="a"), _make_feature(gml_id="b")]
        result = apply_local_filters(features)
        assert len(result) == 2

    def test_filter_by_date_from(self):
        features = [
            _make_feature(gml_id="early", date="2024-01-01 00:00:00+01"),
            _make_feature(gml_id="late", date="2024-12-01 00:00:00+01"),
        ]
        result = apply_local_filters(features, date_from=date(2024, 6, 1))
        assert len(result) == 1
        assert result[0].gml_id == "late"

    def test_filter_by_date_to(self):
        features = [
            _make_feature(gml_id="early", date="2024-01-01 00:00:00+01"),
            _make_feature(gml_id="late", date="2024-12-01 00:00:00+01"),
        ]
        result = apply_local_filters(features, date_to=date(2024, 6, 1))
        assert len(result) == 1
        assert result[0].gml_id == "early"

    def test_filter_by_min_price(self):
        features = [
            _make_feature(gml_id="cheap", price="100000"),
            _make_feature(gml_id="expensive", price="500000"),
        ]
        result = apply_local_filters(features, min_price=Decimal("200000"))
        assert len(result) == 1
        assert result[0].gml_id == "expensive"

    def test_filter_by_max_price(self):
        features = [
            _make_feature(gml_id="cheap", price="100000"),
            _make_feature(gml_id="expensive", price="500000"),
        ]
        result = apply_local_filters(features, max_price=Decimal("200000"))
        assert len(result) == 1
        assert result[0].gml_id == "cheap"

    def test_filter_by_area_range(self):
        features = [
            _make_feature(gml_id="small", area="30.0"),
            _make_feature(gml_id="medium", area="60.0"),
            _make_feature(gml_id="large", area="100.0"),
        ]
        result = apply_local_filters(
            features, min_area=Decimal("40"), max_area=Decimal("80")
        )
        assert len(result) == 1
        assert result[0].gml_id == "medium"

    def test_combined_filters(self):
        features = [
            _make_feature(gml_id="a", price="100000", area="30.0", date="2024-01-01 00:00:00+01"),
            _make_feature(gml_id="b", price="300000", area="60.0", date="2024-06-15 00:00:00+02"),
            _make_feature(gml_id="c", price="500000", area="90.0", date="2024-12-01 00:00:00+01"),
        ]
        result = apply_local_filters(
            features,
            min_price=Decimal("200000"),
            max_area=Decimal("80"),
            date_from=date(2024, 3, 1),
        )
        assert len(result) == 1
        assert result[0].gml_id == "b"

    def test_empty_price_excluded_by_price_filter(self):
        features = [_make_feature(gml_id="no_price", price="")]
        result = apply_local_filters(features, min_price=Decimal("1"))
        assert len(result) == 0
