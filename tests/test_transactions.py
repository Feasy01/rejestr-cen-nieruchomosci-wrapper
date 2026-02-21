"""Tests for the transactions API endpoint."""

from unittest.mock import AsyncMock

from tests.conftest import SAMPLE_EMPTY_XML, SAMPLE_FEATURE_XML


class TestGetLokale:
    def test_basic_request(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale")
        assert resp.status_code == 200

        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 100
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["id"] == "lokale.3751688"
        assert item["doc_date"] == "2024-10-02"
        assert item["price_brutto"] == "528916"
        assert item["area_uzyt"] == "60.36"
        assert item["source"] == "geoportal_rcn_wfs"

    def test_with_bbox(self, test_client, mock_rcn_client):
        resp = test_client.get(
            "/v1/transactions/lokale?bbox=20.85,52.05,21.30,52.37"
        )
        assert resp.status_code == 200
        mock_rcn_client.get_feature.assert_called_once()
        call_kwargs = mock_rcn_client.get_feature.call_args.kwargs
        assert call_kwargs["bbox_2180"] is not None

    def test_with_market_filter(self, test_client, mock_rcn_client):
        resp = test_client.get(
            "/v1/transactions/lokale?market=pierwotny"
        )
        assert resp.status_code == 200
        call_kwargs = mock_rcn_client.get_feature.call_args.kwargs
        assert call_kwargs["market"] == "pierwotny"

    def test_with_function_filter(self, test_client, mock_rcn_client):
        resp = test_client.get(
            "/v1/transactions/lokale?function=mieszkalna"
        )
        assert resp.status_code == 200
        call_kwargs = mock_rcn_client.get_feature.call_args.kwargs
        assert call_kwargs["function"] == "mieszkalna"

    def test_pagination_params(self, test_client, mock_rcn_client):
        resp = test_client.get(
            "/v1/transactions/lokale?page=3&page_size=50"
        )
        assert resp.status_code == 200
        call_kwargs = mock_rcn_client.get_feature.call_args.kwargs
        assert call_kwargs["count"] == 50
        assert call_kwargs["start_index"] == 100  # (3-1)*50

        data = resp.json()
        assert data["page"] == 3
        assert data["page_size"] == 50

    def test_next_page_when_full(self, test_client, mock_rcn_client):
        # numberReturned=1, page_size=1 -> next_page=2
        resp = test_client.get("/v1/transactions/lokale?page_size=1")
        data = resp.json()
        assert data["next_page"] == 2

    def test_no_next_page_when_partial(self, test_client, mock_rcn_client):
        # numberReturned=1, page_size=100 -> no next page
        resp = test_client.get("/v1/transactions/lokale?page_size=100")
        data = resp.json()
        assert data["next_page"] is None

    def test_empty_response(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_EMPTY_XML)
        resp = test_client.get("/v1/transactions/lokale")
        assert resp.status_code == 200

        data = resp.json()
        assert data["items"] == []
        assert data["next_page"] is None

    def test_include_geometry(self, test_client, mock_rcn_client):
        resp = test_client.get(
            "/v1/transactions/lokale?include_geometry=true"
        )
        assert resp.status_code == 200

        item = resp.json()["items"][0]
        assert item["geometry"] is not None
        assert item["geometry"]["type"] == "Point"
        assert len(item["geometry"]["coordinates"]) == 2

    def test_geometry_excluded_by_default(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale")
        item = resp.json()["items"][0]
        assert item["geometry"] is None

    def test_include_raw(self, test_client, mock_rcn_client):
        resp = test_client.get(
            "/v1/transactions/lokale?include_raw=true"
        )
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["raw"] is not None
        assert "tran_cena_brutto" in item["raw"]

    def test_invalid_bbox_format(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale?bbox=invalid")
        assert resp.status_code == 422

    def test_invalid_market_value(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale?market=invalid")
        assert resp.status_code == 422

    def test_page_size_too_large(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale?page_size=1000")
        assert resp.status_code == 422

    def test_page_zero_invalid(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale?page=0")
        assert resp.status_code == 422

    def test_upstream_error(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        resp = test_client.get("/v1/transactions/lokale")
        assert resp.status_code == 502

    def test_local_price_filter(self, test_client, mock_rcn_client):
        # Sample feature has price 528916
        resp = test_client.get(
            "/v1/transactions/lokale?min_price=600000"
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 0

    def test_local_area_filter(self, test_client, mock_rcn_client):
        # Sample feature has area 60.36
        resp = test_client.get(
            "/v1/transactions/lokale?min_area=50&max_area=70"
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    def test_request_id_header(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/transactions/lokale")
        assert "x-request-id" in resp.headers


class TestMetadataEndpoints:
    def test_schema_endpoint(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/metadata/lokale/schema")
        assert resp.status_code == 200

        data = resp.json()
        assert data["feature_type"] == "ms:lokale"
        assert len(data["fields"]) > 0
        field_names = [f["name"] for f in data["fields"]]
        assert "tran_cena_brutto" in field_names

    def test_health_upstream(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/health/upstream")
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "ok"
        assert "latency_ms" in data

    def test_health_upstream_error(self, test_client, mock_rcn_client):
        mock_rcn_client.get_capabilities = AsyncMock(
            side_effect=Exception("timeout")
        )
        resp = test_client.get("/v1/health/upstream")
        assert resp.status_code == 200
        assert "error" in resp.json()["status"]


class TestRootEndpoint:
    def test_root(self, test_client):
        resp = test_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "RCN Wrapper API"
