# src/core/printer.py
import os
import sys
from datetime import datetime
from escpos.printer import Dummy  # ← Always use Dummy for now
from .config import DB_PATH
from .database import get_db_connection

def get_printer():
    """Always return Dummy printer for testing (no USB required)."""
    print("✅ Using Dummy printer (printing to console only)")
    return Dummy()

def print_receipt(cart_items, subtotal, tax, total):
    """Print formatted receipt to console."""
    p = get_printer()
    
    try:
        # Get canteen name
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE name = 'canteen_name'")
        result = cursor.fetchone()
        canteen_name = result[0] if result else "COLLEGE CANTEEN"
        conn.close()

        # Header
        p.set(align='center', bold=True)
        p.text(canteen_name + "\n")
        p.set(align='center', bold=False)
        p.text("-" * 32 + "\n")

        # Items
        p.set(align='left')
        for key, data in cart_items.items():
            name = data['name'][:16]
            qty = data['qty']
            amt = data['price'] * qty
            line = f"{name:<16}{qty:>4}  ₹{amt:>6.2f}\n"
            p.text(line)

        p.text("-" * 32 + "\n")

        # Totals
        p.text(f"Subtotal:          ₹{subtotal:>6.2f}\n")
        p.text(f"Tax (5%):          ₹{tax:>6.2f}\n")
        p.text(f"Total:             ₹{total:>6.2f}\n")

        # Footer
        p.text("-" * 32 + "\n")
        p.set(align='center')
        p.text(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        p.text("\nThank you! Visit again\n")
        p.text("\n")

        p.cut()

        # Also print to console for visibility
        print("\n" + "="*50)
        print("🖨️  RECEIPT OUTPUT (Simulated)")
        print("="*50)
        print(p.output.decode('utf-8'))
        print("="*50)

    except Exception as e:
        print(f"❌ Print error: {e}")
        pass