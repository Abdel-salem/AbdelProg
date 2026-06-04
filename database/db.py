"""
Database initialization and all query functions for BizManager.
All raw SQL lives here — UI files must not contain any SQL.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bizmanager.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE,
            category TEXT,
            cost_price REAL NOT NULL DEFAULT 0,
            sell_price REAL NOT NULL DEFAULT 0,
            stock_qty REAL NOT NULL DEFAULT 0,
            low_stock_alert REAL DEFAULT 5,
            unit TEXT DEFAULT 'pcs',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            loyalty_points INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id),
            total_amount REAL NOT NULL,
            discount REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER REFERENCES sales(id),
            product_id INTEGER REFERENCES products(id),
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            cost_price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier TEXT,
            total_cost REAL NOT NULL,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER REFERENCES purchase_orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity REAL NOT NULL,
            unit_cost REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────────────────────

def get_all_products():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM products ORDER BY name"
        ).fetchall()]


def get_product_by_id(product_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        return dict(row) if row else None


def search_products(query):
    q = f"%{query}%"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? ORDER BY name",
            (q, q)
        ).fetchall()]


def add_product(name, sku, category, cost_price, sell_price, stock_qty, low_stock_alert, unit):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO products (name, sku, category, cost_price, sell_price,
               stock_qty, low_stock_alert, unit) VALUES (?,?,?,?,?,?,?,?)""",
            (name, sku, category, cost_price, sell_price, stock_qty, low_stock_alert, unit)
        )
        conn.commit()


def update_product(product_id, name, sku, category, cost_price, sell_price,
                   stock_qty, low_stock_alert, unit):
    with get_connection() as conn:
        conn.execute(
            """UPDATE products SET name=?, sku=?, category=?, cost_price=?,
               sell_price=?, stock_qty=?, low_stock_alert=?, unit=?
               WHERE id=?""",
            (name, sku, category, cost_price, sell_price, stock_qty,
             low_stock_alert, unit, product_id)
        )
        conn.commit()


def delete_product(product_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()


def deduct_stock(product_id, quantity):
    with get_connection() as conn:
        conn.execute(
            "UPDATE products SET stock_qty = stock_qty - ? WHERE id=?",
            (quantity, product_id)
        )
        conn.commit()


def add_stock(product_id, quantity, new_cost=None):
    with get_connection() as conn:
        if new_cost is not None:
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty + ?, cost_price=? WHERE id=?",
                (quantity, new_cost, product_id)
            )
        else:
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty + ? WHERE id=?",
                (quantity, product_id)
            )
        conn.commit()


# ─────────────────────────────────────────────────────────────
# CUSTOMERS
# ─────────────────────────────────────────────────────────────

def get_all_customers():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM customers ORDER BY name"
        ).fetchall()]


def get_customer_by_id(customer_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
        return dict(row) if row else None


def add_customer(name, phone, email):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO customers (name, phone, email) VALUES (?,?,?)",
            (name, phone, email)
        )
        conn.commit()


def update_customer(customer_id, name, phone, email):
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET name=?, phone=?, email=? WHERE id=?",
            (name, phone, email, customer_id)
        )
        conn.commit()


def delete_customer(customer_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()


def add_loyalty_points(customer_id, points):
    with get_connection() as conn:
        conn.execute(
            "UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id=?",
            (points, customer_id)
        )
        conn.commit()


def get_customer_sales(customer_id):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT s.id, s.total_amount, s.discount, s.payment_method, s.created_at,
               COUNT(si.id) as item_count
               FROM sales s LEFT JOIN sale_items si ON si.sale_id=s.id
               WHERE s.customer_id=? GROUP BY s.id ORDER BY s.created_at DESC""",
            (customer_id,)
        ).fetchall()]


# ─────────────────────────────────────────────────────────────
# SALES
# ─────────────────────────────────────────────────────────────

def create_sale(customer_id, total_amount, discount, payment_method, items):
    """
    items: list of dicts with keys: product_id, quantity, unit_price, cost_price
    Returns the new sale id.
    """
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO sales (customer_id, total_amount, discount, payment_method)
               VALUES (?,?,?,?)""",
            (customer_id, total_amount, discount, payment_method)
        )
        sale_id = cur.lastrowid

        for item in items:
            conn.execute(
                """INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, cost_price)
                   VALUES (?,?,?,?,?)""",
                (sale_id, item["product_id"], item["quantity"],
                 item["unit_price"], item["cost_price"])
            )
            # Deduct stock within same transaction
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty - ? WHERE id=?",
                (item["quantity"], item["product_id"])
            )

        conn.commit()
        return sale_id


def get_sale_with_items(sale_id):
    with get_connection() as conn:
        sale = dict(conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone())
        items = [dict(r) for r in conn.execute(
            """SELECT si.*, p.name as product_name, p.unit
               FROM sale_items si JOIN products p ON p.id=si.product_id
               WHERE si.sale_id=?""",
            (sale_id,)
        ).fetchall()]
        return sale, items


# ─────────────────────────────────────────────────────────────
# PURCHASE ORDERS
# ─────────────────────────────────────────────────────────────

def create_purchase_order(supplier, notes, items):
    """
    items: list of dicts: product_id, quantity, unit_cost
    Returns order id.
    """
    total_cost = sum(i["quantity"] * i["unit_cost"] for i in items)
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO purchase_orders (supplier, total_cost, notes) VALUES (?,?,?)",
            (supplier, total_cost, notes)
        )
        order_id = cur.lastrowid

        for item in items:
            conn.execute(
                """INSERT INTO purchase_order_items (order_id, product_id, quantity, unit_cost)
                   VALUES (?,?,?,?)""",
                (order_id, item["product_id"], item["quantity"], item["unit_cost"])
            )
            conn.execute(
                "UPDATE products SET stock_qty = stock_qty + ?, cost_price=? WHERE id=?",
                (item["quantity"], item["unit_cost"], item["product_id"])
            )

        conn.commit()
        return order_id


def get_all_purchase_orders():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM purchase_orders ORDER BY created_at DESC"
        ).fetchall()]


def get_purchase_order_items(order_id):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            """SELECT poi.*, p.name as product_name, p.unit
               FROM purchase_order_items poi JOIN products p ON p.id=poi.product_id
               WHERE poi.order_id=?""",
            (order_id,)
        ).fetchall()]


# ─────────────────────────────────────────────────────────────
# EXPENSES
# ─────────────────────────────────────────────────────────────

def get_all_expenses():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC"
        ).fetchall()]


def add_expense(category, description, amount, date):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO expenses (category, description, amount, date) VALUES (?,?,?,?)",
            (category, description, amount, date)
        )
        conn.commit()


def update_expense(expense_id, category, description, amount, date):
    with get_connection() as conn:
        conn.execute(
            "UPDATE expenses SET category=?, description=?, amount=?, date=? WHERE id=?",
            (category, description, amount, date, expense_id)
        )
        conn.commit()


def delete_expense(expense_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        conn.commit()


# ─────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────

def get_pnl_summary(date_from, date_to):
    """Returns dict with revenue, cogs, gross_profit, expenses, net_profit."""
    with get_connection() as conn:
        rev_row = conn.execute(
            """SELECT COALESCE(SUM(total_amount),0) as revenue
               FROM sales WHERE date(created_at) BETWEEN ? AND ?""",
            (date_from, date_to)
        ).fetchone()
        revenue = rev_row["revenue"]

        cogs_row = conn.execute(
            """SELECT COALESCE(SUM(si.quantity * si.cost_price),0) as cogs
               FROM sale_items si JOIN sales s ON s.id=si.sale_id
               WHERE date(s.created_at) BETWEEN ? AND ?""",
            (date_from, date_to)
        ).fetchone()
        cogs = cogs_row["cogs"]

        exp_row = conn.execute(
            """SELECT COALESCE(SUM(amount),0) as total
               FROM expenses WHERE date BETWEEN ? AND ?""",
            (date_from, date_to)
        ).fetchone()
        expenses = exp_row["total"]

        gross_profit = revenue - cogs
        net_profit = gross_profit - expenses

        return {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "expenses": expenses,
            "net_profit": net_profit,
        }


def get_daily_revenue_cost(date_from, date_to):
    """Returns list of dicts: date, revenue, cogs."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT date(s.created_at) as day,
                      SUM(s.total_amount) as revenue,
                      SUM(si.quantity * si.cost_price) as cogs
               FROM sales s JOIN sale_items si ON si.sale_id=s.id
               WHERE date(s.created_at) BETWEEN ? AND ?
               GROUP BY day ORDER BY day""",
            (date_from, date_to)
        ).fetchall()
        return [dict(r) for r in rows]


def get_sales_by_payment_method(date_from, date_to):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT payment_method, SUM(total_amount) as total
               FROM sales WHERE date(created_at) BETWEEN ? AND ?
               GROUP BY payment_method""",
            (date_from, date_to)
        ).fetchall()
        return [dict(r) for r in rows]


def get_top_products(date_from, date_to, limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.name, p.sku,
                      SUM(si.quantity) as qty_sold,
                      SUM(si.quantity * si.unit_price) as revenue,
                      SUM(si.quantity * si.cost_price) as cogs
               FROM sale_items si
               JOIN sales s ON s.id=si.sale_id
               JOIN products p ON p.id=si.product_id
               WHERE date(s.created_at) BETWEEN ? AND ?
               GROUP BY si.product_id
               ORDER BY revenue DESC LIMIT ?""",
            (date_from, date_to, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_expenses_for_period(date_from, date_to):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date",
            (date_from, date_to)
        ).fetchall()]


def get_monthly_revenue(months: int = 12):
    """Returns list of dicts: month (YYYY-MM), revenue for line chart."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT strftime('%Y-%m', created_at) as month,
                      SUM(total_amount) as revenue
               FROM sales
               GROUP BY month
               ORDER BY month DESC
               LIMIT ?""",
            (months,)
        ).fetchall()
        return list(reversed([dict(r) for r in rows]))


# ─────────────────────────────────────────────────────────────
# RECEIPTS HISTORY
# ─────────────────────────────────────────────────────────────

def get_all_sales_with_details():
    """Returns list of dicts: id, created_at, customer_name, total_amount, discount, payment_method."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT s.id, s.created_at, s.total_amount, s.discount, s.payment_method,
                      COALESCE(c.name, 'بدون عميل') as customer_name
               FROM sales s
               LEFT JOIN customers c ON c.id = s.customer_id
               ORDER BY s.created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_sale_items(sale_id):
    """Returns list: product_name, quantity, unit_price, cost_price, line_total."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.name as product_name, si.quantity, si.unit_price, si.cost_price,
                      (si.quantity * si.unit_price) as line_total
               FROM sale_items si
               JOIN products p ON p.id = si.product_id
               WHERE si.sale_id = ?""",
            (sale_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_recent_sales(limit: int = 5):
    """Returns last N sales with customer name for POS recent sales panel."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT s.id, s.created_at, s.total_amount, s.payment_method,
                      COALESCE(c.name, 'بدون عميل') as customer_name
               FROM sales s
               LEFT JOIN customers c ON c.id = s.customer_id
               ORDER BY s.created_at DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
