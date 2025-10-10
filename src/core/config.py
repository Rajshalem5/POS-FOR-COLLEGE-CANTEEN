# src/core/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "canteen.db")

DEFAULT_SETTINGS = {
    "canteen_name": "College Canteen",
    "tax_percent": "5.0",
    "paper_width": "58",
    "admin_password": "1234"  # Default PIN
}