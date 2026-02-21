"""Parse WFS GML FeatureCollection responses for ms:lokale."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from lxml import etree

logger = logging.getLogger(__name__)

NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "ms": "http://mapserver.gis.umn.edu/mapserver",
    "xsd": "http://www.w3.org/2001/XMLSchema",
}

# Fields to extract from ms:lokale (without namespace prefix)
_LOKALE_FIELDS = [
    "serwis_rcn",
    "teryt",
    "tran_przestrzen_nazw",
    "tran_lokalny_id_iip",
    "tran_wersja_id",
    "tran_oznaczenie_trans",
    "tran_rodzaj_trans",
    "tran_rodzaj_rynku",
    "tran_sprzedajacy",
    "tran_kupujacy",
    "tran_cena_brutto",
    "tran_vat",
    "dok_oznaczenie",
    "dok_data",
    "dok_tworca",
    "nier_rodzaj",
    "nier_prawo",
    "nier_udzial",
    "nier_pow_gruntu",
    "nier_cena_brutto",
    "nier_vat",
    "lok_id_lokalu",
    "lok_nr_lokalu",
    "lok_funkcja",
    "lok_liczba_izb",
    "lok_nr_kond",
    "lok_pow_uzyt",
    "lok_pow_przyn",
    "lok_cena_brutto",
    "lok_vat",
    "lok_adres",
]


@dataclass
class ParsedFeature:
    gml_id: str
    geometry_pos: tuple[float, float] | None  # (northing, easting) EPSG:2180
    properties: dict[str, str]


@dataclass
class ParsedResponse:
    number_returned: int
    features: list[ParsedFeature] = field(default_factory=list)


def parse_feature_collection(xml_bytes: bytes) -> ParsedResponse:
    """Parse a WFS FeatureCollection GML response into structured data."""
    root = etree.fromstring(xml_bytes)

    number_returned = int(root.attrib.get("numberReturned", "0"))

    features: list[ParsedFeature] = []

    for member in root.iterfind("wfs:member", NS):
        lokale_el = member.find("ms:lokale", NS)
        if lokale_el is None:
            continue

        gml_id = lokale_el.attrib.get(f"{{{NS['gml']}}}id", "")

        # Extract geometry
        geometry_pos: tuple[float, float] | None = None
        point_el = lokale_el.find("ms:msGeometry/gml:Point/gml:pos", NS)
        if point_el is not None and point_el.text:
            parts = point_el.text.strip().split()
            if len(parts) == 2:
                try:
                    geometry_pos = (float(parts[0]), float(parts[1]))
                except ValueError:
                    logger.warning(
                        "Invalid geometry coords for %s: %s",
                        gml_id,
                        point_el.text,
                    )

        # Extract properties
        props: dict[str, str] = {}
        for field_name in _LOKALE_FIELDS:
            el = lokale_el.find(f"ms:{field_name}", NS)
            if el is not None and el.text:
                props[field_name] = el.text
            else:
                props[field_name] = ""

        features.append(
            ParsedFeature(
                gml_id=gml_id,
                geometry_pos=geometry_pos,
                properties=props,
            )
        )

    return ParsedResponse(number_returned=number_returned, features=features)


@dataclass
class SchemaFieldInfo:
    name: str
    type: str
    min_occurs: int


def parse_describe_feature_type(xml_bytes: bytes) -> list[SchemaFieldInfo]:
    """Parse DescribeFeatureType response into a list of field definitions."""
    root = etree.fromstring(xml_bytes)

    fields: list[SchemaFieldInfo] = []

    for element in root.iter(f"{{{NS['xsd']}}}element"):
        name = element.attrib.get("name", "")
        if not name or name == "lokaleType":
            continue
        xsd_type = element.attrib.get("type", "")
        min_occurs = int(element.attrib.get("minOccurs", "0"))
        fields.append(SchemaFieldInfo(name=name, type=xsd_type, min_occurs=min_occurs))

    return fields
