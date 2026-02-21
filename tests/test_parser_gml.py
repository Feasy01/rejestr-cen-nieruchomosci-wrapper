"""Tests for GML XML parsing."""

from app.services.parser_gml import (
    parse_describe_feature_type,
    parse_feature_collection,
)
from tests.conftest import (
    SAMPLE_DESCRIBE_XML,
    SAMPLE_EMPTY_XML,
    SAMPLE_FEATURE_XML,
)


class TestParseFeatureCollection:
    def test_parses_single_feature(self):
        result = parse_feature_collection(SAMPLE_FEATURE_XML)
        assert result.number_returned == 1
        assert len(result.features) == 1

        f = result.features[0]
        assert f.gml_id == "lokale.3751688"
        assert f.geometry_pos is not None
        assert f.geometry_pos == (378176.102614, 758653.828868)

    def test_extracts_properties(self):
        result = parse_feature_collection(SAMPLE_FEATURE_XML)
        p = result.features[0].properties

        assert p["tran_cena_brutto"] == "528916"
        assert p["lok_pow_uzyt"] == "60.36"
        assert p["dok_data"] == "2024-10-02 00:00:00+02"
        assert p["dok_oznaczenie"] == "AN 7739/2024"
        assert p["dok_tworca"] == "KUNECKA AGNIESZKA"
        assert p["tran_rodzaj_rynku"] == "pierwotny"
        assert p["lok_funkcja"] == "mieszkalna"
        assert p["lok_liczba_izb"] == "3"
        assert p["lok_nr_kond"] == "6"
        assert p["nier_udzial"] == "1/1"

    def test_empty_fields_are_empty_string(self):
        result = parse_feature_collection(SAMPLE_FEATURE_XML)
        p = result.features[0].properties

        assert p["tran_vat"] == ""
        assert p["lok_pow_przyn"] == ""
        assert p["lok_adres"] == ""

    def test_empty_collection(self):
        result = parse_feature_collection(SAMPLE_EMPTY_XML)
        assert result.number_returned == 0
        assert len(result.features) == 0

    def test_multiple_features(self):
        xml = b"""\
<?xml version='1.0' encoding="UTF-8" ?>
<wfs:FeatureCollection
   xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   numberMatched="unknown" numberReturned="2">
    <wfs:member>
      <ms:lokale gml:id="lokale.1">
        <ms:msGeometry>
          <gml:Point gml:id="lokale.1.1" srsName="urn:ogc:def:crs:EPSG::2180">
            <gml:pos>400000.0 600000.0</gml:pos>
          </gml:Point>
        </ms:msGeometry>
        <ms:tran_cena_brutto>100000</ms:tran_cena_brutto>
        <ms:lok_pow_uzyt>50.0</ms:lok_pow_uzyt>
        <ms:dok_data>2024-01-01 00:00:00+01</ms:dok_data>
        <ms:dok_oznaczenie>AN 1/2024</ms:dok_oznaczenie>
        <ms:dok_tworca>TEST NOTARY</ms:dok_tworca>
        <ms:tran_rodzaj_rynku>wtorny</ms:tran_rodzaj_rynku>
        <ms:lok_funkcja>mieszkalna</ms:lok_funkcja>
        <ms:lok_liczba_izb>2</ms:lok_liczba_izb>
        <ms:lok_nr_kond>3</ms:lok_nr_kond>
        <ms:nier_udzial>1/1</ms:nier_udzial>
      </ms:lokale>
    </wfs:member>
    <wfs:member>
      <ms:lokale gml:id="lokale.2">
        <ms:msGeometry>
          <gml:Point gml:id="lokale.2.1" srsName="urn:ogc:def:crs:EPSG::2180">
            <gml:pos>410000.0 610000.0</gml:pos>
          </gml:Point>
        </ms:msGeometry>
        <ms:tran_cena_brutto>200000</ms:tran_cena_brutto>
        <ms:lok_pow_uzyt>70.0</ms:lok_pow_uzyt>
        <ms:dok_data>2024-06-15 00:00:00+02</ms:dok_data>
        <ms:dok_oznaczenie>AN 2/2024</ms:dok_oznaczenie>
        <ms:dok_tworca>OTHER NOTARY</ms:dok_tworca>
        <ms:tran_rodzaj_rynku>pierwotny</ms:tran_rodzaj_rynku>
        <ms:lok_funkcja>mieszkalna</ms:lok_funkcja>
        <ms:lok_liczba_izb>4</ms:lok_liczba_izb>
        <ms:lok_nr_kond>1</ms:lok_nr_kond>
        <ms:nier_udzial>1/2</ms:nier_udzial>
      </ms:lokale>
    </wfs:member>
</wfs:FeatureCollection>
"""
        result = parse_feature_collection(xml)
        assert result.number_returned == 2
        assert len(result.features) == 2
        assert result.features[0].gml_id == "lokale.1"
        assert result.features[1].gml_id == "lokale.2"


class TestParseDescribeFeatureType:
    def test_parses_schema(self):
        fields = parse_describe_feature_type(SAMPLE_DESCRIBE_XML)
        names = [f.name for f in fields]
        assert "msGeometry" in names
        assert "tran_cena_brutto" in names
        assert "lok_pow_uzyt" in names
        assert "dok_data" in names

    def test_field_types(self):
        fields = parse_describe_feature_type(SAMPLE_DESCRIBE_XML)
        by_name = {f.name: f for f in fields}
        assert by_name["msGeometry"].type == "gml:GeometryPropertyType"
        assert by_name["tran_cena_brutto"].type == "string"
