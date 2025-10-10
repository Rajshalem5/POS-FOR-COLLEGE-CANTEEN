# src/core/database.py
import sqlite3
import json
import os
from .config import DB_PATH, DEFAULT_SETTINGS

def get_db_connection():
    """Get a new database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            available INTEGER DEFAULT 1
        )
    ''')

    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Orders table (for future)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT NOT NULL,
            total_amount REAL NOT NULL,
            items_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed'
        )
    ''')

    # Insert default settings if not present
    for key, value in DEFAULT_SETTINGS.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (name, value) VALUES (?, ?)",
            (key, value)
        )

    # Add sample items if no items exist
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        sample_items = [
            ("Tea", "Drinks", 10.0),
            ("Coffee", "Drinks", 15.0),
            ("Sandwich", "Snacks", 30.0),
            ("Biscuit", "Snacks", 5.0),
        ]
        cursor.executemany(
            "INSERT INTO items (name, category, price) VALUES (?, ?, ?)",
            sample_items
        )

    conn.commit()
    conn.close()

def save_held_order(cart_items):
    """Save current cart as a held order."""
    import json
    from datetime import datetime

    # Calculate total
    subtotal = sum(item['price'] * item['qty'] for item in cart_items.values())
    tax_percent = 5.0
    tax = subtotal * (tax_percent / 100)
    total = subtotal + tax

    # Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (date_time, total_amount, items_json, status)
        VALUES (?, ?, ?, 'held')
        """,
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, json.dumps(list(cart_items.values())))
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_held_orders():
    """Get all held orders."""
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, date_time, items_json FROM orders WHERE status = 'held' ORDER BY date_time")
    rows = cursor.fetchall()
    conn.close()

    held_orders = []
    for row in rows:
        items = json.loads(row[2])
        # Generate summary: "Sandwich x1, Tea x2"
        summary = ", ".join([f"{item['name']} x{item['qty']}" for item in items])
        held_orders.append({
            'id': row[0],
            'time': row[1],
            'summary': summary,
            'items': items
        })
    return held_orders

def delete_held_order(order_id):
    """Delete a held order (after resuming)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()