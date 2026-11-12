"""
Tests for task endpoints and purchase-order endpoints.
"""
from datetime import date, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Tasks and purchase orders are module-level lists; restore them around each test."""
    original_pos = list(main.purchase_orders)
    main.tasks.clear()
    yield
    main.tasks.clear()
    main.purchase_orders[:] = original_pos


TOMORROW = (date.today() + timedelta(days=1)).isoformat()


class TestTaskEndpoints:
    """Test suite for /api/tasks."""

    def test_get_tasks_empty(self, client):
        """Test the task list starts empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it with server-assigned fields."""
        response = client.post("/api/tasks", json={"title": "  Count bin A-12  ", "priority": "high", "dueDate": TOMORROW})
        assert response.status_code == 201

        task = response.json()
        assert task["id"].startswith("task-")
        assert task["title"] == "Count bin A-12"
        assert task["priority"] == "high"
        assert task["dueDate"] == TOMORROW
        assert task["status"] == "pending"

    def test_task_ids_never_collide_with_demo_task_ids(self, client):
        """Test ids are prefixed strings, never the numeric ids the client's demo tasks use."""
        task = client.post("/api/tasks", json={"title": "x", "dueDate": TOMORROW}).json()
        assert not task["id"].isdigit()

    def test_create_task_default_priority(self, client):
        """Test priority defaults to medium."""
        task = client.post("/api/tasks", json={"title": "Review", "dueDate": TOMORROW}).json()
        assert task["priority"] == "medium"

    def test_tasks_listed_newest_first(self, client):
        """Test created tasks are listed newest first."""
        for title in ("first", "second"):
            client.post("/api/tasks", json={"title": title, "dueDate": TOMORROW})
        assert [t["title"] for t in client.get("/api/tasks").json()] == ["second", "first"]

    def test_toggle_task(self, client):
        """Test PATCH toggles a task between pending and completed."""
        task_id = client.post("/api/tasks", json={"title": "x", "dueDate": TOMORROW}).json()["id"]

        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it."""
        task_id = client.post("/api/tasks", json={"title": "x", "dueDate": TOMORROW}).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204
        assert client.get("/api/tasks").json() == []

    @pytest.mark.parametrize("method", ["patch", "delete"])
    def test_nonexistent_task(self, client, method):
        """Test toggling or deleting an unknown task returns 404."""
        response = getattr(client, method)("/api/tasks/task-missing")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_task_blank_title(self, client):
        """Test a whitespace-only title is rejected and nothing is stored."""
        response = client.post("/api/tasks", json={"title": "   ", "dueDate": TOMORROW})
        assert response.status_code == 400
        assert client.get("/api/tasks").json() == []

    @pytest.mark.parametrize("payload", [
        {"dueDate": TOMORROW},
        {"title": "", "dueDate": TOMORROW},
        {"title": "x"},
        {"title": "x", "dueDate": "next tuesday"},
        {"title": "x", "dueDate": TOMORROW, "priority": "urgent"},
    ])
    def test_create_task_invalid_payload(self, client, payload):
        """Test malformed task payloads fail validation."""
        assert client.post("/api/tasks", json=payload).status_code == 422


class TestPurchaseOrderEndpoints:
    """Test suite for /api/purchase-orders."""

    @pytest.fixture
    def backlog_id(self, client):
        """A backlog item that has no purchase order yet."""
        item = next(i for i in client.get("/api/backlog").json() if not i["has_purchase_order"])
        return item["id"]

    def po_payload(self, backlog_id, **overrides):
        payload = {
            "backlog_item_id": backlog_id,
            "supplier_name": "Apex Industrial Supply",
            "quantity": 350,
            "unit_cost": 12.4,
            "expected_delivery_date": TOMORROW,
            "notes": "Expedite",
        }
        payload.update(overrides)
        return payload

    def test_create_purchase_order(self, client, backlog_id):
        """Test creating a purchase order returns it with server-assigned fields."""
        response = client.post("/api/purchase-orders", json=self.po_payload(backlog_id))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_id
        assert po["status"] == "Pending"
        assert po["created_date"] == date.today().isoformat()
        assert po["expected_delivery_date"] == TOMORROW

    def test_create_purchase_order_flags_backlog_item(self, client, backlog_id):
        """Test the backlog item reports has_purchase_order after a PO is created."""
        client.post("/api/purchase-orders", json=self.po_payload(backlog_id))

        item = next(i for i in client.get("/api/backlog").json() if i["id"] == backlog_id)
        assert item["has_purchase_order"] is True

    def test_get_purchase_order_by_backlog_item(self, client, backlog_id):
        """Test fetching the PO for a backlog item."""
        created = client.post("/api/purchase-orders", json=self.po_payload(backlog_id)).json()

        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_nonexistent_purchase_order(self, client, backlog_id):
        """Test fetching a PO for an item without one returns 404."""
        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_create_duplicate_purchase_order(self, client, backlog_id):
        """Test a second PO for the same backlog item is rejected."""
        client.post("/api/purchase-orders", json=self.po_payload(backlog_id))
        response = client.post("/api/purchase-orders", json=self.po_payload(backlog_id))
        assert response.status_code == 409

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test a PO for an unknown backlog item returns 404."""
        response = client.post("/api/purchase-orders", json=self.po_payload("nonexistent-999"))
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_past_delivery_date(self, client, backlog_id):
        """Test a delivery date in the past is rejected."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        response = client.post("/api/purchase-orders", json=self.po_payload(backlog_id, expected_delivery_date=yesterday))
        assert response.status_code == 400

    def test_create_purchase_order_blank_supplier(self, client, backlog_id):
        """Test a whitespace-only supplier is rejected."""
        response = client.post("/api/purchase-orders", json=self.po_payload(backlog_id, supplier_name="   "))
        assert response.status_code == 400

    @pytest.mark.parametrize("overrides", [
        {"quantity": 0},
        {"quantity": -5},
        {"unit_cost": 0},
        {"supplier_name": ""},
        {"expected_delivery_date": "soon"},
    ])
    def test_create_purchase_order_invalid_payload(self, client, backlog_id, overrides):
        """Test malformed purchase orders fail validation."""
        response = client.post("/api/purchase-orders", json=self.po_payload(backlog_id, **overrides))
        assert response.status_code == 422
