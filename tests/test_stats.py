"""Tests for the stats API endpoint."""

from unittest.mock import AsyncMock

from tests.conftest import SAMPLE_EMPTY_XML, SAMPLE_FEATURE_XML, SAMPLE_MULTI_FEATURE_XML


class TestGetLokaleStats:
    def test_basic_stats(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_MULTI_FEATURE_XML)
        resp = test_client.get("/v1/stats/lokale")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] == 3
        assert data["avg_price"] is not None
        assert data["min_price"] is not None
        assert data["max_price"] is not None
        assert data["avg_price_per_sqm"] is not None
        assert data["median_price_per_sqm"] is not None

    def test_stats_values(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_MULTI_FEATURE_XML)
        resp = test_client.get("/v1/stats/lokale")
        data = resp.json()

        # Prices: 300000, 600000, 450000
        assert float(data["min_price"]) == 300000
        assert float(data["max_price"]) == 600000
        # avg = (300000 + 600000 + 450000) / 3 = 450000
        assert float(data["avg_price"]) == 450000.0

    def test_stats_empty(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_EMPTY_XML)
        resp = test_client.get("/v1/stats/lokale")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] == 0
        assert data["avg_price"] is None
        assert data["groups"] is None

    def test_stats_single_feature(self, test_client, mock_rcn_client):
        resp = test_client.get("/v1/stats/lokale")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] == 1
        assert float(data["min_price"]) == 528916
        assert float(data["max_price"]) == 528916

    def test_stats_group_by_teryt(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_MULTI_FEATURE_XML)
        resp = test_client.get("/v1/stats/lokale?group_by=teryt")
        assert resp.status_code == 200

        data = resp.json()
        assert data["groups"] is not None
        assert len(data["groups"]) == 2  # teryt 0617 and 0618

        groups_by_key = {g["group_key"]: g for g in data["groups"]}
        assert "0617" in groups_by_key
        assert "0618" in groups_by_key
        assert groups_by_key["0617"]["count"] == 2
        assert groups_by_key["0618"]["count"] == 1

    def test_stats_group_by_month(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_MULTI_FEATURE_XML)
        resp = test_client.get("/v1/stats/lokale?group_by=month")
        assert resp.status_code == 200

        data = resp.json()
        assert data["groups"] is not None
        # Dates: 2024-01 (x2), 2024-06 (x1)
        assert len(data["groups"]) == 2

        groups_by_key = {g["group_key"]: g for g in data["groups"]}
        assert "2024-01" in groups_by_key
        assert "2024-06" in groups_by_key
        assert groups_by_key["2024-01"]["count"] == 2
        assert groups_by_key["2024-06"]["count"] == 1

    def test_stats_no_groups_by_default(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_MULTI_FEATURE_XML)
        resp = test_client.get("/v1/stats/lokale")
        data = resp.json()
        assert data["groups"] is None

    def test_stats_with_price_filter(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(return_value=SAMPLE_MULTI_FEATURE_XML)
        resp = test_client.get("/v1/stats/lokale?min_price=400000")
        assert resp.status_code == 200

        data = resp.json()
        # Only prices 600000 and 450000 pass
        assert data["total_count"] == 2

    def test_stats_upstream_error(self, test_client, mock_rcn_client):
        mock_rcn_client.get_feature = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        resp = test_client.get("/v1/stats/lokale")
        assert resp.status_code == 502
