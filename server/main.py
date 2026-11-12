import math
import re
import threading
import uuid
from typing import Literal
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

QUARTER_PATTERN = re.compile(r'^Q([1-4])-(\d{4})$')

def quarter_of(order_date: str) -> Optional[str]:
    """Return 'Qn-YYYY' for an ISO date string, or None if it can't be parsed.

    Derived from the date itself so any year works (this used to be a lookup
    table hard-coded to 2025, which silently dropped orders from other years).
    """
    match = re.match(r'^(\d{4})-(\d{2})', order_date or '')
    if not match:
        return None
    year, month = match.group(1), int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return f"Q{(month - 1) // 3 + 1}-{year}"

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month ('YYYY-MM') or quarter ('Qn-YYYY') using order_date."""
    if not month or month == 'all':
        return items

    if QUARTER_PATTERN.match(month):
        return [item for item in items if quarter_of(item.get('order_date', '')) == month]

    # Direct month match on the date prefix (startswith, not substring, so
    # '2025-01' can't match a day component elsewhere in the string)
    return [item for item in items if item.get('order_date', '').startswith(month)]

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Same 422 shape as FastAPI's default, but safe for non-finite input.

    The default handler echoes the rejected input back, and JSON cannot encode inf/nan,
    so a body like {"budget": Infinity} would turn a 422 into a 500. Stringify those.
    """
    errors = jsonable_encoder(
        exc.errors(),
        custom_encoder={float: lambda f: f if math.isfinite(f) else str(f)},
    )
    return JSONResponse(status_code=422, content={"detail": errors})

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int
    supplier: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class RecommendationItem(BaseModel):
    sku: str
    item_name: str
    trend: str
    forecasted_demand: int
    recommended_quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    supplier: str
    is_partial: bool

class RestockingRecommendation(BaseModel):
    budget: float
    items: List[RecommendationItem]
    total_cost: float
    remaining_budget: float
    full_cost: float

class RestockingOrderItem(BaseModel):
    sku: str
    item_name: str
    quantity: int
    unit_cost: float
    line_total: float
    lead_time_days: int
    supplier: str

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderItem]
    total_cost: float
    budget: float
    status: str
    submitted_date: str
    lead_time_days: int
    expected_delivery: str

class RestockingOrderLine(BaseModel):
    sku: str
    quantity: int = Field(gt=0)

class CreateRestockingOrderRequest(BaseModel):
    # allow_inf_nan=False: JSON "Infinity" would otherwise pass ge=0 and be stored as null
    budget: float = Field(ge=0, allow_inf_nan=False)
    items: List[RestockingOrderLine] = Field(min_length=1)

# Submitted restocking orders live in memory only (newest first) and reset on server restart
restocking_orders: List[dict] = []
restocking_order_counter = 0
restocking_lock = threading.Lock()

# Lower rank = restock first. Growing demand is the most urgent to cover.
TREND_PRIORITY = {'increasing': 0, 'stable': 1, 'decreasing': 2}

def recommend_restock(forecasts: list, budget: float) -> dict:
    """Pick forecast items to restock within a budget, highest priority first."""
    # Rank by trend (increasing before stable before decreasing), then by percentage
    # growth so the fastest-growing items within a trend are funded first.
    def priority(f):
        growth = (f['forecasted_demand'] - f['current_demand']) / f['current_demand'] if f['current_demand'] else 0
        return (TREND_PRIORITY.get(f['trend'].lower(), len(TREND_PRIORITY)), -growth)

    remaining = budget
    items = []
    for f in sorted(forecasts, key=priority):
        full_qty = f['forecasted_demand']
        unit_cost = f['unit_cost']
        # Fund the whole forecast if it fits. Otherwise buy as many units as the remaining
        # budget allows, then keep scanning so cheaper, lower-ranked items can still use
        # whatever is left over.
        # Compare rounded cents and nudge the division so float error (e.g. 950 * 12.40 ->
        # 11780.000000000002) can't drop a unit when the budget is exactly enough.
        if round(full_qty * unit_cost, 2) <= remaining:
            qty = full_qty
        else:
            qty = math.floor(remaining / unit_cost + 1e-9)
        if qty <= 0:
            continue
        line_total = round(qty * unit_cost, 2)
        remaining = round(remaining - line_total, 2)
        items.append({
            'sku': f['item_sku'],
            'item_name': f['item_name'],
            'trend': f['trend'],
            'forecasted_demand': full_qty,
            'recommended_quantity': qty,
            'unit_cost': unit_cost,
            'line_total': line_total,
            'lead_time_days': f['lead_time_days'],
            'supplier': f['supplier'],
            'is_partial': qty < full_qty,
        })

    return {
        'budget': round(budget, 2),
        'items': items,
        'total_cost': round(sum(i['line_total'] for i in items), 2),
        'remaining_budget': round(remaining, 2),
        'full_cost': round(sum(f['forecasted_demand'] * f['unit_cost'] for f in forecasts), 2),
    }

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/restocking/recommendations", response_model=RestockingRecommendation)
def get_restocking_recommendations(budget: float = Query(0, ge=0, allow_inf_nan=False)):
    """Recommend forecast items to restock within the given budget"""
    return recommend_restock(demand_forecasts, budget)

@app.get("/api/restocking/orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get submitted restocking orders, newest first"""
    return restocking_orders

@app.post("/api/restocking/orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a restocking order. Prices and lead times come from server data, not the client."""
    global restocking_order_counter

    skus = [line.sku for line in request.items]
    duplicates = sorted({s for s in skus if skus.count(s) > 1})
    if duplicates:
        raise HTTPException(status_code=400, detail=f"Duplicate SKU(s): {', '.join(duplicates)}")

    forecasts_by_sku = {f['item_sku']: f for f in demand_forecasts}
    items = []
    for line in request.items:
        forecast = forecasts_by_sku.get(line.sku)
        if not forecast:
            raise HTTPException(status_code=400, detail=f"Unknown SKU: {line.sku}")
        items.append({
            'sku': line.sku,
            'item_name': forecast['item_name'],
            'quantity': line.quantity,
            'unit_cost': forecast['unit_cost'],
            'line_total': round(line.quantity * forecast['unit_cost'], 2),
            'lead_time_days': forecast['lead_time_days'],
            'supplier': forecast['supplier'],
        })

    total_cost = round(sum(i['line_total'] for i in items), 2)
    if total_cost > request.budget:
        raise HTTPException(status_code=400, detail=f"Order total {total_cost} exceeds budget {request.budget}")

    # Items ship together, so the order arrives when its slowest item does
    lead_time_days = max(i['lead_time_days'] for i in items)
    submitted = date.today()
    # Sync endpoints run in FastAPI's threadpool, so serialise the counter bump and insert
    # to stop concurrent submissions from receiving the same order number.
    with restocking_lock:
        restocking_order_counter += 1
        order = {
            'id': str(restocking_order_counter),
            'order_number': f"RST-{restocking_order_counter:04d}",
            'items': items,
            'total_cost': total_cost,
            'budget': round(request.budget, 2),
            'status': 'Submitted',
            'submitted_date': submitted.isoformat(),
            'lead_time_days': lead_time_days,
            'expected_delivery': (submitted + timedelta(days=lead_time_days)).isoformat(),
        }
        restocking_orders.insert(0, order)
    return order

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

class QuarterlyReport(BaseModel):
    quarter: str
    total_orders: int
    total_revenue: float
    delivered_orders: int
    avg_order_value: float
    fulfillment_rate: float

class MonthlyTrend(BaseModel):
    month: str
    order_count: int
    revenue: float
    delivered_count: int

def filtered_orders(warehouse, category, status, month) -> list:
    """Orders after the global filter bar's filters, shared by the report endpoints."""
    return filter_by_month(apply_filters(orders, warehouse, category, status), month)

@app.get("/api/reports/quarterly", response_model=List[QuarterlyReport])
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports, honouring the global filters"""
    quarters = {}

    for order in filtered_orders(warehouse, category, status, month):
        quarter = quarter_of(order.get('order_date', ''))
        if quarter is None:
            continue

        data = quarters.setdefault(quarter, {
            'quarter': quarter,
            'total_orders': 0,
            'total_revenue': 0.0,
            'delivered_orders': 0,
        })
        data['total_orders'] += 1
        data['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            data['delivered_orders'] += 1

    result = []
    for data in quarters.values():
        # Every quarter in the dict has at least one order, so no divide-by-zero
        data['total_revenue'] = round(data['total_revenue'], 2)
        data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
        data['fulfillment_rate'] = round(data['delivered_orders'] / data['total_orders'] * 100, 1)
        result.append(data)

    # Chronological, not alphabetical: as strings 'Q1-2026' would sort before 'Q2-2025'
    result.sort(key=lambda q: (q['quarter'][3:], q['quarter'][1]))
    return result

@app.get("/api/reports/monthly-trends", response_model=List[MonthlyTrend])
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends, honouring the global filters"""
    months = {}

    for order in filtered_orders(warehouse, category, status, month):
        order_date = order.get('order_date', '')
        if not re.match(r'^\d{4}-\d{2}', order_date):
            continue

        key = order_date[:7]  # YYYY-MM; ISO strings sort chronologically
        data = months.setdefault(key, {'month': key, 'order_count': 0, 'revenue': 0.0, 'delivered_count': 0})
        data['order_count'] += 1
        data['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            data['delivered_count'] += 1

    result = sorted(months.values(), key=lambda m: m['month'])
    for data in result:
        data['revenue'] = round(data['revenue'], 2)
    return result

# ---- Tasks ------------------------------------------------------------------
# The client's task list (TasksModal) merges built-in demo tasks with these.
# Field names are camelCase (dueDate) because that's the client's existing shape.

class Task(BaseModel):
    id: str
    title: str
    priority: Literal['high', 'medium', 'low']
    dueDate: str
    status: Literal['pending', 'completed']

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: Literal['high', 'medium', 'low'] = 'medium'
    dueDate: date

# In memory only, reset on restart (like restocking orders)
tasks: List[dict] = []
tasks_lock = threading.Lock()

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get user-created tasks, newest first"""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task"""
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title cannot be blank")
    # String ids with a prefix so they can never collide with the client's numeric
    # demo-task ids, which App.vue uses to decide whether a task lives on the server
    task = {
        'id': f"task-{uuid.uuid4().hex[:12]}",
        'title': title,
        'priority': request.priority,
        'dueDate': request.dueDate.isoformat(),
        'status': 'pending',
    }
    with tasks_lock:
        tasks.insert(0, task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    with tasks_lock:
        task = next((t for t in tasks if t['id'] == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        task['status'] = 'completed' if task['status'] == 'pending' else 'pending'
        return task

@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    """Delete a task"""
    with tasks_lock:
        index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
        if index is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        tasks.pop(index)

# ---- Purchase orders (for backlog shortages) ---------------------------------
purchase_orders_lock = threading.Lock()

class PurchaseOrderInput(BaseModel):
    """Request body for creating a purchase order."""
    backlog_item_id: str
    supplier_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0)
    unit_cost: float = Field(gt=0, allow_inf_nan=False)
    expected_delivery_date: date
    notes: Optional[str] = Field(default=None, max_length=1000)

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: PurchaseOrderInput):
    """Create a purchase order for a backlog item (one per item)"""
    if not any(item['id'] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    supplier = request.supplier_name.strip()
    if not supplier:
        raise HTTPException(status_code=400, detail="Supplier name cannot be blank")
    if request.expected_delivery_date < date.today():
        raise HTTPException(status_code=400, detail="Expected delivery date cannot be in the past")

    with purchase_orders_lock:
        # The dashboard shows one PO per shortage ("Create PO" becomes "View PO")
        if any(po['backlog_item_id'] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail=f"Backlog item {request.backlog_item_id} already has a purchase order")
        po = {
            'id': f"PO-{uuid.uuid4().hex[:8].upper()}",
            'backlog_item_id': request.backlog_item_id,
            'supplier_name': supplier,
            'quantity': request.quantity,
            'unit_cost': round(request.unit_cost, 2),
            'expected_delivery_date': request.expected_delivery_date.isoformat(),
            'status': 'Pending',
            'created_date': date.today().isoformat(),
            'notes': (request.notes or '').strip() or None,
        }
        # Appends to the list loaded from purchase_orders.json (in memory only), so
        # /api/backlog's has_purchase_order flag picks it up immediately
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    po = next((po for po in purchase_orders if po['backlog_item_id'] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
