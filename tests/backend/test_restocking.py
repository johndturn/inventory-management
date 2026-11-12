"""
Tests for restocking API endpoints (budget-based recommendations and restocking orders).
"""
from datetime import date, timedelta

import pytest

import main

TREND_RANK = {"increasing": 0, "stable": 1, "decreasing": 2}


@pytest.fixture(autouse=True)
def reset_restocking_orders():
    """Restocking orders are stored in module-level memory, so clear them around each test."""
    main.restocking_orders.clear()
    main.restocking_order_counter = 0
    yield
    main.restocking_orders.clear()
    main.restocking_order_counter = 0


@pytest.fixture
def forecasts(client):
    """Demand forecasts keyed by SKU."""
    return {f["item_sku"]: f for f in client.get("/api/demand").json()}


@pytest.fixture
def full_cost(forecasts):
    """Cost of funding every forecast in full."""
    return round(sum(f["forecasted_demand"] * f["unit_cost"] for f in forecasts.values()), 2)


def growth(forecast):
    return (forecast["forecasted_demand"] - forecast["current_demand"]) / forecast["current_demand"]


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_structure(self, client):
        """Test the recommendation response contains all expected fields."""
        response = client.get("/api/restocking/recommendations?budget=20000")
        assert response.status_code == 200

        data = response.json()
        for field in ["budget", "items", "total_cost", "remaining_budget", "full_cost"]:
            assert field in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        for item in data["items"]:
            for field in [
                "sku", "item_name", "trend", "forecasted_demand", "recommended_quantity",
                "unit_cost", "line_total", "lead_time_days", "supplier", "is_partial",
            ]:
                assert field in item
            assert isinstance(item["recommended_quantity"], int)
            assert item["recommended_quantity"] > 0
            assert abs(item["line_total"] - item["recommended_quantity"] * item["unit_cost"]) < 0.01

    @pytest.mark.parametrize("budget", [1, 500, 5000, 20000, 50000, 99999.99])
    def test_recommendations_never_exceed_budget(self, client, budget):
        """Test that recommended spend stays within the budget."""
        data = client.get(f"/api/restocking/recommendations?budget={budget}").json()

        assert data["total_cost"] <= budget
        assert abs(data["total_cost"] + data["remaining_budget"] - budget) < 0.01
        assert abs(sum(i["line_total"] for i in data["items"]) - data["total_cost"]) < 0.01

    def test_recommendations_zero_budget(self, client):
        """Test that a zero budget recommends nothing."""
        data = client.get("/api/restocking/recommendations?budget=0").json()

        assert data["items"] == []
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0

    def test_recommendations_default_budget_is_zero(self, client):
        """Test that omitting the budget behaves like a zero budget."""
        data = client.get("/api/restocking/recommendations").json()

        assert data["budget"] == 0
        assert data["items"] == []

    def test_recommendations_full_cost_calculation(self, client, full_cost):
        """Test that full_cost equals the cost of funding every forecast."""
        data = client.get("/api/restocking/recommendations?budget=0").json()
        assert abs(data["full_cost"] - full_cost) < 0.01

    def test_recommendations_exact_full_budget_funds_everything(self, client, forecasts, full_cost):
        """Test that a budget exactly equal to full_cost funds every forecast completely."""
        data = client.get(f"/api/restocking/recommendations?budget={full_cost}").json()

        assert len(data["items"]) == len(forecasts)
        assert abs(data["total_cost"] - full_cost) < 0.01
        for item in data["items"]:
            assert item["recommended_quantity"] == item["forecasted_demand"]
            assert item["is_partial"] is False

    def test_recommendations_ranked_by_trend_then_growth(self, client, forecasts, full_cost):
        """Test that increasing items come first, then stable, then decreasing, by growth within a trend."""
        items = client.get(f"/api/restocking/recommendations?budget={full_cost}").json()["items"]

        keys = [
            (TREND_RANK[i["trend"].lower()], -growth(forecasts[i["sku"]]))
            for i in items
        ]
        assert keys == sorted(keys)
        assert items[0]["trend"].lower() == "increasing"

    def test_recommendations_partial_fill(self, client, full_cost):
        """Test that the first item that doesn't fit is partially filled."""
        ranked = client.get(f"/api/restocking/recommendations?budget={full_cost}").json()["items"]
        first, second = ranked[0], ranked[1]

        # Enough for the whole first item plus half of the second
        budget = round(first["line_total"] + second["line_total"] / 2, 2)
        items = client.get(f"/api/restocking/recommendations?budget={budget}").json()["items"]

        assert items[0]["sku"] == first["sku"]
        assert items[0]["is_partial"] is False
        assert items[1]["sku"] == second["sku"]
        assert items[1]["is_partial"] is True
        assert 0 < items[1]["recommended_quantity"] < second["forecasted_demand"]

    def test_recommendations_negative_budget(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=-100")
        assert response.status_code == 422

    @pytest.mark.parametrize("budget", ["inf", "nan"])
    def test_recommendations_non_finite_budget(self, client, budget):
        """Test that infinite or NaN budgets are rejected rather than serialised as null."""
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        assert response.status_code == 422


class TestRestockingOrders:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_get_restocking_orders_empty(self, client):
        """Test that no orders exist before any are submitted."""
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_restocking_order(self, client, forecasts):
        """Test submitting an order computes totals, lead time and delivery date server-side."""
        payload = {
            "budget": 20000,
            "items": [
                {"sku": "WDG-001", "quantity": 100},
                {"sku": "GSK-203", "quantity": 200},
            ],
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 201

        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["budget"] == 20000
        assert len(order["items"]) == 2

        expected_total = 0
        for item in order["items"]:
            forecast = forecasts[item["sku"]]
            assert item["item_name"] == forecast["item_name"]
            assert item["unit_cost"] == forecast["unit_cost"]
            assert item["lead_time_days"] == forecast["lead_time_days"]
            assert item["supplier"] == forecast["supplier"]
            expected_total += item["quantity"] * forecast["unit_cost"]
        assert abs(order["total_cost"] - expected_total) < 0.01

    def test_create_restocking_order_lead_time_calculation(self, client, forecasts):
        """Test that order lead time is the slowest item's and delivery = submitted + lead time."""
        skus = ["WDG-001", "MTR-304", "FLT-405"]
        payload = {"budget": 100000, "items": [{"sku": s, "quantity": 1} for s in skus]}
        order = client.post("/api/restocking/orders", json=payload).json()

        assert order["lead_time_days"] == max(forecasts[s]["lead_time_days"] for s in skus)
        submitted = date.fromisoformat(order["submitted_date"])
        assert submitted == date.today()
        assert date.fromisoformat(order["expected_delivery"]) == submitted + timedelta(days=order["lead_time_days"])

    def test_create_restocking_order_ignores_client_prices(self, client, forecasts):
        """Test that prices sent by the client are ignored in favour of server data."""
        payload = {"budget": 5000, "items": [{"sku": "WDG-001", "quantity": 10, "unit_cost": 0.01}]}
        order = client.post("/api/restocking/orders", json=payload).json()

        assert order["items"][0]["unit_cost"] == forecasts["WDG-001"]["unit_cost"]

    def test_recommendations_can_be_ordered(self, client):
        """Test that the recommended items for a budget can be submitted as an order."""
        rec = client.get("/api/restocking/recommendations?budget=35000").json()
        payload = {
            "budget": rec["budget"],
            "items": [{"sku": i["sku"], "quantity": i["recommended_quantity"]} for i in rec["items"]],
        }
        response = client.post("/api/restocking/orders", json=payload)

        assert response.status_code == 201
        assert abs(response.json()["total_cost"] - rec["total_cost"]) < 0.01

    def test_restocking_orders_listed_newest_first(self, client):
        """Test that submitted orders appear in the list, newest first."""
        for qty in (1, 2):
            client.post("/api/restocking/orders", json={"budget": 1000, "items": [{"sku": "GSK-203", "quantity": qty}]})

        data = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in data] == ["RST-0002", "RST-0001"]

    def test_create_restocking_order_unknown_sku(self, client):
        """Test that an unknown SKU is rejected and nothing is stored."""
        payload = {"budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}]}
        response = client.post("/api/restocking/orders", json=payload)

        assert response.status_code == 400
        assert "NOPE-999" in response.json()["detail"]
        assert client.get("/api/restocking/orders").json() == []

    def test_create_restocking_order_over_budget(self, client):
        """Test that an order costing more than the budget is rejected and nothing is stored."""
        payload = {"budget": 100, "items": [{"sku": "MTR-304", "quantity": 10}]}
        response = client.post("/api/restocking/orders", json=payload)

        assert response.status_code == 400
        assert "exceeds budget" in response.json()["detail"]
        assert client.get("/api/restocking/orders").json() == []

    def test_create_restocking_order_duplicate_sku(self, client):
        """Test that repeating a SKU within one order is rejected and nothing is stored."""
        payload = {"budget": 1000, "items": [
            {"sku": "GSK-203", "quantity": 1},
            {"sku": "GSK-203", "quantity": 2},
        ]}
        response = client.post("/api/restocking/orders", json=payload)

        assert response.status_code == 400
        assert "GSK-203" in response.json()["detail"]
        assert client.get("/api/restocking/orders").json() == []

    def test_create_restocking_order_infinite_budget(self, client):
        """Test that a non-finite budget is rejected rather than stored as null."""
        # Raw body because the test client refuses to JSON-encode inf; Python's json parser
        # on the server accepts the non-standard "Infinity" literal.
        response = client.post(
            "/api/restocking/orders",
            content='{"budget": Infinity, "items": [{"sku": "GSK-203", "quantity": 1}]}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422
        assert client.get("/api/restocking/orders").json() == []

    @pytest.mark.parametrize("payload", [
        {"budget": 1000, "items": []},
        {"budget": 1000, "items": [{"sku": "GSK-203", "quantity": 0}]},
        {"budget": 1000, "items": [{"sku": "GSK-203", "quantity": -5}]},
        {"budget": -1, "items": [{"sku": "GSK-203", "quantity": 1}]},
        {"items": [{"sku": "GSK-203", "quantity": 1}]},
    ])
    def test_create_restocking_order_invalid_payload(self, client, payload):
        """Test that malformed orders fail validation."""
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422
