"""
Tests for report endpoints (quarterly performance and monthly trends).
"""
import pytest

import main


def quarter_key(q):
    """('2025', '1') for 'Q1-2025' -> chronological sort key."""
    return (q[3:], q[1])


class TestQuarterlyReports:
    """Test suite for GET /api/reports/quarterly."""

    def test_get_quarterly_reports(self, client):
        """Test quarterly reports return the expected structure."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for q in data:
            for field in ["quarter", "total_orders", "total_revenue", "delivered_orders",
                          "avg_order_value", "fulfillment_rate"]:
                assert field in q
            assert q["quarter"].startswith("Q")

    def test_quarterly_totals_match_orders(self, client):
        """Test that quarterly order counts and revenue add up to all orders."""
        orders = client.get("/api/orders").json()
        data = client.get("/api/reports/quarterly").json()

        assert sum(q["total_orders"] for q in data) == len(orders)
        assert abs(sum(q["total_revenue"] for q in data) - sum(o["total_value"] for o in orders)) < 0.05

    def test_quarterly_derived_values_calculation(self, client):
        """Test average order value and fulfillment rate are derived correctly."""
        for q in client.get("/api/reports/quarterly").json():
            assert abs(q["avg_order_value"] - q["total_revenue"] / q["total_orders"]) < 0.01
            assert abs(q["fulfillment_rate"] - q["delivered_orders"] / q["total_orders"] * 100) < 0.1

    def test_get_quarterly_reports_by_warehouse(self, client):
        """Test the warehouse filter applies to quarterly reports."""
        expected = len(client.get("/api/orders?warehouse=Tokyo").json())
        data = client.get("/api/reports/quarterly?warehouse=Tokyo").json()

        assert sum(q["total_orders"] for q in data) == expected
        assert expected < len(client.get("/api/orders").json())

    def test_get_quarterly_reports_multiple_filters(self, client):
        """Test warehouse, category and status filters combine."""
        query = "warehouse=London&category=Sensors&status=Delivered"
        expected = client.get(f"/api/orders?{query}").json()
        data = client.get(f"/api/reports/quarterly?{query}").json()

        assert sum(q["total_orders"] for q in data) == len(expected)
        # Status=Delivered means every order counted is delivered
        for q in data:
            assert q["delivered_orders"] == q["total_orders"]
            assert q["fulfillment_rate"] == 100.0

    def test_get_quarterly_reports_by_month(self, client):
        """Test a month filter narrows the report to that month's quarter."""
        data = client.get("/api/reports/quarterly?month=2025-05").json()

        assert [q["quarter"] for q in data] == ["Q2-2025"]
        assert data[0]["total_orders"] == len(client.get("/api/orders?month=2025-05").json())

    def test_get_quarterly_reports_by_quarter(self, client):
        """Test a quarter filter returns only that quarter."""
        data = client.get("/api/reports/quarterly?month=Q3-2025").json()
        assert [q["quarter"] for q in data] == ["Q3-2025"]

    def test_get_quarterly_reports_all_filter_ignored(self, client):
        """Test that 'all' filter values behave like no filter."""
        unfiltered = client.get("/api/reports/quarterly").json()
        all_filters = client.get(
            "/api/reports/quarterly?warehouse=all&category=all&status=all&month=all"
        ).json()
        assert all_filters == unfiltered

    def test_get_quarterly_reports_no_matches(self, client):
        """Test a filter with no matching orders returns an empty list."""
        response = client.get("/api/reports/quarterly?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrends:
    """Test suite for GET /api/reports/monthly-trends."""

    def test_get_monthly_trends(self, client):
        """Test monthly trends return the expected structure, sorted by month."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for m in data:
            for field in ["month", "order_count", "revenue", "delivered_count"]:
                assert field in m
            assert len(m["month"]) == 7 and m["month"][4] == "-"
        months = [m["month"] for m in data]
        assert months == sorted(months)

    def test_get_monthly_trends_by_warehouse(self, client):
        """Test the warehouse filter applies to monthly trends."""
        expected = client.get("/api/orders?warehouse=San Francisco").json()
        data = client.get("/api/reports/monthly-trends?warehouse=San Francisco").json()

        assert sum(m["order_count"] for m in data) == len(expected)

    def test_get_monthly_trends_by_month(self, client):
        """Test a month filter returns just that month."""
        data = client.get("/api/reports/monthly-trends?month=2025-07").json()
        assert [m["month"] for m in data] == ["2025-07"]

    def test_monthly_revenue_rounded(self, client):
        """Test revenue values are rounded to cents (no float noise)."""
        for m in client.get("/api/reports/monthly-trends").json():
            assert round(m["revenue"], 2) == m["revenue"]


class TestQuarterHandling:
    """Quarter logic must work for any year, not just 2025."""

    @pytest.mark.parametrize("order_date,expected", [
        ("2025-01-15T10:00:00", "Q1-2025"),
        ("2025-03-31", "Q1-2025"),
        ("2025-04-01", "Q2-2025"),
        ("2026-09-30", "Q3-2026"),
        ("2024-12-01", "Q4-2024"),
        ("", None),
        ("not-a-date", None),
        ("2025-13-01", None),
    ])
    def test_quarter_of(self, order_date, expected):
        """Test quarters are derived from the date itself."""
        assert main.quarter_of(order_date) == expected

    def test_filter_by_month_quarter_other_year(self):
        """Test quarter filtering works outside 2025 (it used to be a 2025-only lookup)."""
        items = [{"order_date": "2026-02-10"}, {"order_date": "2025-02-10"}, {"order_date": "2026-05-01"}]
        assert main.filter_by_month(items, "Q1-2026") == [{"order_date": "2026-02-10"}]

    def test_reports_include_other_years_in_chronological_order(self, client, monkeypatch):
        """Test orders from another year are reported and quarters sort chronologically."""
        extra = [
            {"order_date": "2026-01-05", "total_value": 100.0, "status": "Delivered"},
            {"order_date": "2024-11-20", "total_value": 50.0, "status": "Processing"},
        ]
        monkeypatch.setattr(main, "orders", main.orders + extra)

        quarters = [q["quarter"] for q in client.get("/api/reports/quarterly").json()]
        assert "Q1-2026" in quarters and "Q4-2024" in quarters
        assert quarters == sorted(quarters, key=quarter_key)
        assert quarters[0] == "Q4-2024" and quarters[-1] == "Q1-2026"

        months = [m["month"] for m in client.get("/api/reports/monthly-trends").json()]
        assert months[0] == "2024-11" and months[-1] == "2026-01"
