from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from .database import init_db, get_connection
from .seed import seed
from .forecasting import build_forecast
import secrets
import string

app = FastAPI(title="EVENTFUEL API", version="1.0.0", description="Campus event food infrastructure prototype")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    seed()

def rows(query, params=()):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]

def row(query, params=()):
    with get_connection() as conn:
        result = conn.execute(query, params).fetchone()
        return dict(result) if result else None

class EventCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    college: str = Field(min_length=2, max_length=100)
    event_type: str
    event_date: str
    start_time: str
    duration_hours: float = Field(gt=0, le=48)
    expected_attendees: int = Field(gt=0, le=100000)
    meal_period: str

class OrderCreate(BaseModel):
    event_id: int
    menu_item_id: int
    student_name: str = Field(min_length=2, max_length=60)
    quantity: int = Field(ge=1, le=10)

class StatusUpdate(BaseModel):
    status: Literal["Placed", "Preparing", "Ready", "Redeemed", "Cancelled"]

@app.get("/")
def root():
    return {"app": "EVENTFUEL", "status": "running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.get("/api/events")
def get_events():
    return rows("SELECT * FROM events ORDER BY event_date, start_time")

@app.post("/api/events", status_code=201)
def create_event(payload: EventCreate):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO events
            (name,college,event_type,event_date,start_time,duration_hours,expected_attendees,meal_period,status)
            VALUES (?,?,?,?,?,?,?,?, 'Planning')""",
            (payload.name, payload.college, payload.event_type, payload.event_date,
             payload.start_time, payload.duration_hours, payload.expected_attendees, payload.meal_period),
        )
        event_id = cur.lastrowid
    return row("SELECT * FROM events WHERE id=?", (event_id,))

@app.get("/api/vendors")
def get_vendors():
    return rows("SELECT * FROM vendors WHERE active=1 ORDER BY rating DESC")

@app.get("/api/menu")
def get_menu():
    return rows("""SELECT m.*, v.name AS vendor_name, v.cuisine, v.location
                   FROM menu_items m JOIN vendors v ON v.id=m.vendor_id
                   WHERE v.active=1 ORDER BY m.category, m.price""")

@app.get("/api/forecast/{event_id}")
def forecast(event_id: int):
    event = row("SELECT * FROM events WHERE id=?", (event_id,))
    if not event:
        raise HTTPException(404, "Event not found")
    return build_forecast(event, rows("SELECT * FROM vendors WHERE active=1"), get_menu())

@app.get("/api/orders")
def get_orders(event_id: int | None = None):
    sql = """SELECT o.*, e.name AS event_name, m.name AS item_name, v.name AS vendor_name
             FROM orders o JOIN events e ON e.id=o.event_id
             JOIN menu_items m ON m.id=o.menu_item_id JOIN vendors v ON v.id=m.vendor_id"""
    if event_id:
        return rows(sql + " WHERE o.event_id=? ORDER BY o.id DESC", (event_id,))
    return rows(sql + " ORDER BY o.id DESC")

def make_token():
    alphabet = string.ascii_uppercase + string.digits
    return "EF-" + "".join(secrets.choice(alphabet) for _ in range(6))

@app.post("/api/orders", status_code=201)
def create_order(payload: OrderCreate):
    event = row("SELECT * FROM events WHERE id=?", (payload.event_id,))
    item = row("SELECT * FROM menu_items WHERE id=?", (payload.menu_item_id,))
    if not event or not item:
        raise HTTPException(404, "Event or menu item not found")
    if item["available_qty"] < payload.quantity:
        raise HTTPException(400, "Not enough quantity available")
    total = round(item["price"] * payload.quantity, 2)
    token = make_token()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO orders (event_id,menu_item_id,student_name,quantity,total,pickup_token)
               VALUES (?,?,?,?,?,?)""",
            (payload.event_id, payload.menu_item_id, payload.student_name, payload.quantity, total, token),
        )
        conn.execute("UPDATE menu_items SET available_qty=available_qty-? WHERE id=?",
                     (payload.quantity, payload.menu_item_id))
        order_id = cur.lastrowid
    return row("""SELECT o.*, e.name AS event_name, m.name AS item_name, v.name AS vendor_name
                  FROM orders o JOIN events e ON e.id=o.event_id
                  JOIN menu_items m ON m.id=o.menu_item_id JOIN vendors v ON v.id=m.vendor_id
                  WHERE o.id=?""", (order_id,))

@app.patch("/api/orders/{order_id}/status")
def update_order_status(order_id: int, payload: StatusUpdate):
    existing = row("SELECT * FROM orders WHERE id=?", (order_id,))
    if not existing:
        raise HTTPException(404, "Order not found")
    allowed = {
        "Placed": ["Preparing", "Cancelled"],
        "Preparing": ["Ready", "Cancelled"],
        "Ready": ["Redeemed"],
        "Redeemed": [],
        "Cancelled": [],
    }
    if payload.status not in allowed.get(existing["status"], []):
        raise HTTPException(400, f"Cannot change {existing['status']} to {payload.status}")
    with get_connection() as conn:
        conn.execute("UPDATE orders SET status=? WHERE id=?", (payload.status, order_id))
        if payload.status == "Cancelled":
            conn.execute("UPDATE menu_items SET available_qty=available_qty+? WHERE id=?",
                         (existing["quantity"], existing["menu_item_id"]))
    return row("SELECT * FROM orders WHERE id=?", (order_id,))

@app.get("/api/metrics")
def metrics():
    with get_connection() as conn:
        orders = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(total),0) revenue FROM orders WHERE status!='Cancelled'").fetchone()
        redeemed = conn.execute("SELECT COUNT(*) n FROM orders WHERE status='Redeemed'").fetchone()["n"]
        placed = conn.execute("SELECT COUNT(*) n FROM orders WHERE status!='Cancelled'").fetchone()["n"]
        events = conn.execute("SELECT COUNT(*) n FROM events").fetchone()["n"]
        attendees = conn.execute("SELECT COALESCE(SUM(expected_attendees),0) n FROM events").fetchone()["n"]
        inventory = conn.execute("SELECT COALESCE(SUM(available_qty),0) n FROM menu_items").fetchone()["n"]
    return {
        "total_orders": orders["n"],
        "revenue": round(orders["revenue"], 2),
        "redeemed_orders": redeemed,
        "redemption_rate": round((redeemed / placed * 100) if placed else 0, 1),
        "total_events": events,
        "expected_attendees": attendees,
        "available_menu_units": inventory,
    }
