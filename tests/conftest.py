from __future__ import annotations

import pytest
import httpx
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.rcn_client import RCNClient


SAMPLE_FEATURE_XML = b"""\
<?xml version='1.0' encoding="UTF-8" ?>
<wfs:FeatureCollection
   xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   timeStamp="2026-02-21T21:18:15" numberMatched="unknown" numberReturned="1">
    <wfs:member>
      <ms:lokale gml:id="lokale.3751688">
        <gml:boundedBy>
            <gml:Envelope srsName="urn:ogc:def:crs:EPSG::2180">
                <gml:lowerCorner>378176.102614 758653.828868</gml:lowerCorner>
                <gml:upperCorner>378176.102614 758653.828868</gml:upperCorner>
            </gml:Envelope>
        </gml:boundedBy>
        <ms:msGeometry>
          <gml:Point gml:id="lokale.3751688.1" srsName="urn:ogc:def:crs:EPSG::2180">
            <gml:pos>378176.102614 758653.828868</gml:pos>
          </gml:Point>
        </ms:msGeometry>
        <ms:serwis_rcn></ms:serwis_rcn>
        <ms:teryt>0617</ms:teryt>
        <ms:tran_przestrzen_nazw></ms:tran_przestrzen_nazw>
        <ms:tran_lokalny_id_iip>CEC7513F-95AF-430F-B597-84963C442F2A</ms:tran_lokalny_id_iip>
        <ms:tran_wersja_id></ms:tran_wersja_id>
        <ms:tran_oznaczenie_trans>RCN_T_12029</ms:tran_oznaczenie_trans>
        <ms:tran_rodzaj_trans>wolnyRynek</ms:tran_rodzaj_trans>
        <ms:tran_rodzaj_rynku>pierwotny</ms:tran_rodzaj_rynku>
        <ms:tran_sprzedajacy>osobaPrawna</ms:tran_sprzedajacy>
        <ms:tran_kupujacy>osobaFizyczna</ms:tran_kupujacy>
        <ms:tran_cena_brutto>528916</ms:tran_cena_brutto>
        <ms:tran_vat></ms:tran_vat>
        <ms:dok_oznaczenie>AN 7739/2024</ms:dok_oznaczenie>
        <ms:dok_data>2024-10-02 00:00:00+02</ms:dok_data>
        <ms:dok_tworca>KUNECKA AGNIESZKA</ms:dok_tworca>
        <ms:nier_rodzaj>nieruchomoscLokalowa</ms:nier_rodzaj>
        <ms:nier_prawo>wlasnoscLokaluWrazZPrawemZwiazanym</ms:nier_prawo>
        <ms:nier_udzial>1/1</ms:nier_udzial>
        <ms:nier_pow_gruntu>0.4823</ms:nier_pow_gruntu>
        <ms:nier_cena_brutto>488916</ms:nier_cena_brutto>
        <ms:nier_vat></ms:nier_vat>
        <ms:lok_id_lokalu>061701_1.0001.2262_BUD.108_LOK</ms:lok_id_lokalu>
        <ms:lok_nr_lokalu>108_LOK</ms:lok_nr_lokalu>
        <ms:lok_funkcja>mieszkalna</ms:lok_funkcja>
        <ms:lok_liczba_izb>3</ms:lok_liczba_izb>
        <ms:lok_nr_kond>6</ms:lok_nr_kond>
        <ms:lok_pow_uzyt>60.36</ms:lok_pow_uzyt>
        <ms:lok_pow_przyn></ms:lok_pow_przyn>
        <ms:lok_cena_brutto></ms:lok_cena_brutto>
        <ms:lok_vat></ms:lok_vat>
        <ms:lok_adres></ms:lok_adres>
      </ms:lokale>
    </wfs:member>
</wfs:FeatureCollection>
"""

SAMPLE_EMPTY_XML = b"""\
<?xml version='1.0' encoding="UTF-8" ?>
<wfs:FeatureCollection
   xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   timeStamp="2026-02-21T21:16:23" numberMatched="unknown" numberReturned="0">
</wfs:FeatureCollection>
"""

SAMPLE_DESCRIBE_XML = b"""\
<?xml version='1.0' encoding="UTF-8" ?>
<schema
   xmlns="http://www.w3.org/2001/XMLSchema"
   xmlns:ms="http://mapserver.gis.umn.edu/mapserver"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   targetNamespace="http://mapserver.gis.umn.edu/mapserver">
  <import namespace="http://www.opengis.net/gml/3.2"
          schemaLocation="http://schemas.opengis.net/gml/3.2.1/gml.xsd"/>
  <complexType name="lokaleType">
    <complexContent>
      <extension base="gml:AbstractFeatureType">
        <sequence>
          <element name="msGeometry" type="gml:GeometryPropertyType" minOccurs="0"/>
          <element name="tran_cena_brutto" minOccurs="0" type="string"/>
          <element name="lok_pow_uzyt" minOccurs="0" type="string"/>
          <element name="dok_data" minOccurs="0" type="string"/>
        </sequence>
      </extension>
    </complexContent>
  </complexType>
  <element name="lokale" type="ms:lokaleType" substitutionGroup="gml:AbstractFeature"/>
</schema>
"""

SAMPLE_CAPABILITIES_XML = b"""\
<?xml version='1.0' encoding="UTF-8" ?>
<wfs:WFS_Capabilities xmlns:wfs="http://www.opengis.net/wfs/2.0" version="2.0.0">
  <ows:ServiceIdentification xmlns:ows="http://www.opengis.net/ows/1.1">
    <ows:Title>Rejestr Cen Nieruchomosci</ows:Title>
  </ows:ServiceIdentification>
</wfs:WFS_Capabilities>
"""


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear all caches between tests."""
    from app.core.cache import features_cache, metadata_cache
    features_cache.clear()
    metadata_cache.clear()


@pytest.fixture
def mock_rcn_client():
    """Create a mock RCNClient."""
    client = AsyncMock(spec=RCNClient)
    client.get_feature = AsyncMock(return_value=SAMPLE_FEATURE_XML)
    client.get_capabilities = AsyncMock(return_value=SAMPLE_CAPABILITIES_XML)
    client.describe_feature_type = AsyncMock(return_value=SAMPLE_DESCRIBE_XML)
    return client


@pytest.fixture
def test_client(mock_rcn_client):
    """Create a TestClient with a mocked RCN client."""
    app.state.rcn_client = mock_rcn_client
    return TestClient(app, raise_server_exceptions=False)
