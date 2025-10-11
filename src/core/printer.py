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

def print_receipt(cart_items, subtotal, tax, total, cash_received=0.0):
    """Print formatted receipt to console."""
    p = get_printer()
    
    try:
        # Get canteen name and tax percent from settings
        from .database import get_setting
        import os
        canteen_name = get_setting("canteen_name", "SVG FOOD COURT")
        tax_percent = float(get_setting("tax_percent", "5.0"))

        # Header
        p.set(align='center', bold=True)
        p.text(canteen_name + "\n")
        p.set(align='center', bold=False)
        p.text("-" * 32 + "\n")

        # Optional: Print logo (if file exists)
        logo_path = os.path.join(os.path.dirname(__file__), "..", "resources", "logo.png")
        if os.path.exists(logo_path):
            try:
                p.image(logo_path)
                p.text("\n")
            except Exception as e:
                print(f"⚠️ Logo print failed: {e}")

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
        p.text(f"Tax ({tax_percent:.0f}%):          ₹{tax:>6.2f}\n")
        p.text(f"Total:             ₹{total:>6.2f}\n")

        # Cash handling section
        if cash_received > 0:
            p.text("-" * 32 + "\n")
            p.text(f"Cash:              ₹{cash_received:>6.2f}\n")
            p.text(f"Change:            ₹{cash_received - total:>6.2f}\n")

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