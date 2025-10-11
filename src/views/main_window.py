# src/views/main_window.py
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QTableWidget,
    QTableWidgetItem, QSpinBox, QMessageBox,
    QAbstractItemView, QLineEdit  # 👈 Add QLineEdit if not present
)
from PyQt6.QtGui import QShortcut, QFont,QKeySequence  # 👈 QShortcut is here!
from PyQt6.QtCore import Qt
from .resume_dialog import ResumeDialog
from ..core.database import get_db_connection, save_held_order, get_held_orders, delete_held_order

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("College Canteen POS")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left: Menu buttons
        self.menu_area = QScrollArea()
        self.menu_area.setWidgetResizable(True)
        self.menu_widget = QWidget()
        self.menu_layout = QVBoxLayout(self.menu_widget)
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.menu_area.setWidget(self.menu_widget)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search items...")
        self.search_bar.textChanged.connect(self.filter_menu_items)
        self.menu_layout.insertWidget(0, self.search_bar)

        # Right: Cart panel
        self.cart_panel = QWidget()
        self.cart_layout = QVBoxLayout(self.cart_panel)
        self.cart_layout.addWidget(QLabel("🛒 Cart"))

        # Cart table
        self.cart_table = QTableWidget(0, 5)
        self.cart_table.setHorizontalHeaderLabels(["Item", "Qty", "Price", "Total", "Action"])
        self.cart_table.setColumnWidth(4, 60)  # Make Delete column narrow
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cart_layout.addWidget(self.cart_table)

        # Summary labels
        self.subtotal_label = QLabel("Subtotal: ₹0.00")
        self.tax_label = QLabel("Tax (5%): ₹0.00")
        self.total_label = QLabel("Total: ₹0.00")
        for label in [self.subtotal_label, self.tax_label, self.total_label]:
            label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.cart_layout.addWidget(self.subtotal_label)
        self.cart_layout.addWidget(self.tax_label)
        self.cart_layout.addWidget(self.total_label)

        # Cash handling fields
        self.cash_label = QLabel("💰 Cash Received:")
        self.cash_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.cash_input = QLineEdit()
        self.cash_input.setPlaceholderText("Enter cash amount (e.g., 100)")
        self.cash_input.setFixedHeight(40)
        self.cash_input.setStyleSheet("font-size: 16px; padding: 5px;")
        self.cash_input.textChanged.connect(self.update_change_due)

        self.change_label = QLabel("🔄 Change Due: ₹0.00")
        self.change_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #4CAF50;")

        # Add to cart layout (before action buttons)
        self.cart_layout.addWidget(self.cash_label)
        self.cart_layout.addWidget(self.cash_input)
        self.cart_layout.addWidget(self.change_label)

        # Action buttons
        btn_layout = QHBoxLayout()
        hold_btn = QPushButton("⏸️ Hold Order")
        resume_btn = QPushButton("▶️ Resume Order")
        cancel_btn = QPushButton("❌ Cancel Order")
        print_btn = QPushButton("🖨️ Print Bill")
        clear_btn = QPushButton("🧹 Clear Cart")

        btn_layout.addWidget(hold_btn)
        btn_layout.addWidget(resume_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(clear_btn)

        self.cart_layout.addLayout(btn_layout)

        main_layout.addWidget(self.menu_area, 70)
        main_layout.addWidget(self.cart_panel, 30)

        self.cart_items = {}  # {item_id: {name, price, qty}}
        self.current_held_id = None  # Tracks if current cart came from a held order
        self.load_menu_items()

        # Connect buttons
        hold_btn.clicked.connect(self.hold_order)
        resume_btn.clicked.connect(self.resume_order)
        cancel_btn.clicked.connect(self.clear_cart)  # Cancel = clear cart
        print_btn.clicked.connect(self.print_bill)
        clear_btn.clicked.connect(self.clear_cart)

        # Keyboard shortcuts
        self.hold_shortcut = QShortcut(QKeySequence("F1"), self)
        self.hold_shortcut.activated.connect(self.hold_order)

        self.resume_shortcut = QShortcut(QKeySequence("F2"), self)
        self.resume_shortcut.activated.connect(self.resume_order)

        self.print_shortcut = QShortcut(QKeySequence("F3"), self)
        self.print_shortcut.activated.connect(self.print_bill)

    def load_menu_items(self):
        """Load items from DB and create buttons."""
        while self.menu_layout.count():
            child = self.menu_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price FROM items WHERE available = 1 ORDER BY name")
        items = cursor.fetchall()
        conn.close()

        if not items:
            self.menu_layout.addWidget(QLabel("No items available"))
            return

        row_widget = None
        for i, (item_id, name, price) in enumerate(items):
            if i % 2 == 0:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                self.menu_layout.addWidget(row_widget)
            btn = QPushButton(f"{name}\n₹{price:.2f}")
            btn.setFixedSize(200, 80)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            btn.clicked.connect(lambda iid=item_id, n=name, p=price: self.add_to_cart(iid, n, p))
            row_layout.addWidget(btn)

        # Add Admin button at bottom
        admin_btn = QPushButton("⚙️ Admin Panel")
        admin_btn.setFixedSize(200, 50)
        admin_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
            }
        """)
        admin_btn.clicked.connect(self.open_admin_panel)
        self.menu_layout.addWidget(admin_btn)

    def add_to_cart(self, item_id, name, price):
        """Add item to cart or increase quantity."""
        key = (name, price)  # Use (name, price) as unique key
        if key in self.cart_items:
            self.cart_items[key]['qty'] += 1
        else:
            self.cart_items[key] = {'name': name, 'price': price, 'qty': 1}
        self.update_cart_display()

    def update_cart_display(self):
        """Refresh cart table and totals."""
        self.cart_table.setRowCount(0)

        subtotal = 0.0
        for key, data in self.cart_items.items():
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)

            # Item name
            name_item = QTableWidgetItem(data['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 0, name_item)

            # Qty (with spin box)
            qty_spin = QSpinBox()
            qty_spin.setRange(1, 99)  # Keep min=1 since we have delete button
            qty_spin.setValue(data['qty'])
            qty_spin.valueChanged.connect(lambda q, k=key: self.update_qty(k, q))
            self.cart_table.setCellWidget(row, 1, qty_spin)

            # Price
            price_item = QTableWidgetItem(f"₹{data['price']:.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 2, price_item)

            # Total
            total = data['price'] * data['qty']
            total_item = QTableWidgetItem(f"₹{total:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.cart_table.setItem(row, 3, total_item)

            # Delete button
            del_btn = QPushButton("🗑️")
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 2px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            del_btn.clicked.connect(lambda _, k=key: self.delete_item_from_cart(k))
            self.cart_table.setCellWidget(row, 4, del_btn)

            subtotal += total

        # Update totals
        tax_percent = 5.0
        tax = subtotal * (tax_percent / 100)
        total = subtotal + tax

        self.subtotal_label.setText(f"Subtotal: ₹{subtotal:.2f}")
        self.tax_label.setText(f"Tax ({tax_percent}%): ₹{tax:.2f}")
        self.total_label.setText(f"Total: ₹{total:.2f}")

    def update_qty(self, key, new_qty):
        """Update or remove item from cart based on quantity."""
        if new_qty <= 0:
            # Remove item if qty is 0 or less
            if key in self.cart_items:
                del self.cart_items[key]
        else:
            # Update quantity
            self.cart_items[key]['qty'] = new_qty
        self.update_cart_display()

    def clear_cart(self):
        """Empty the cart. If it's a resumed held order, ask whether to delete it."""
        if self.current_held_id is not None:
            from PyQt6.QtWidgets import QMessageBox, QDialogButtonBox

            # Create custom dialog with "Delete" and "Keep" buttons
            msg = QMessageBox(self)
            msg.setWindowTitle("Clear Resumed Order")
            msg.setText(f"This cart came from held order H{self.current_held_id:03}.")
            msg.setInformativeText("Do you want to delete this held order from history?")

            delete_btn = msg.addButton("Delete", QMessageBox.ButtonRole.YesRole)
            keep_btn = msg.addButton("Keep", QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(keep_btn)

            msg.exec()

            clicked_btn = msg.clickedButton()
            if clicked_btn == delete_btn:
                # Delete the held order
                from ..core.database import delete_held_order
                delete_held_order(self.current_held_id)

            # Always clear cart and reset
            self.cart_items.clear()
            self.current_held_id = None
            self.update_cart_display()
        else:
            # Normal clear (not a resumed order)
            self.cart_items.clear()
            self.update_cart_display()

    def update_change_due(self):
        """Calculate and display change due."""
        try:
            # Get cash input
            cash_text = self.cash_input.text().strip()
            if not cash_text:
                self.change_label.setText("🔄 Change Due: ₹0.00")
                self.change_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #4CAF50;")
                return

            cash = float(cash_text)
            
            # Get total from label (parse "Total: ₹78.75")
            total_text = self.total_label.text()
            total = float(total_text.split("₹")[-1])
            
            # Calculate change
            change = cash - total
            
            # Update label
            self.change_label.setText(f"🔄 Change Due: ₹{change:.2f}")
            
            # Color code: green (ok) / red (insufficient)
            if change >= 0:
                self.change_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #4CAF50;")
            else:
                self.change_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #f44336;")
                
        except ValueError:
            self.change_label.setText("🔄 Change Due: ₹0.00")
            self.change_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #4CAF50;")

    def print_bill(self):
        """Print receipt with cash handling."""
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "Cart is empty. Add items first.")
            return

        # Validate cash input
        try:
            cash_text = self.cash_input.text().strip()
            if not cash_text:
                QMessageBox.warning(self, "Cash Required", "Please enter cash received amount.")
                return
                
            cash = float(cash_text)
            total_text = self.total_label.text()
            total = float(total_text.split("₹")[-1])
            
            if cash < total:
                QMessageBox.warning(
                    self, 
                    "Insufficient Cash", 
                    f"Cash received (₹{cash:.2f}) is less than total (₹{total:.2f})!\n"
                    f"Need at least ₹{total:.2f}."
                )
                return
                
        except ValueError:
            QMessageBox.warning(self, "Invalid Cash", "Please enter a valid cash amount (e.g., 100).")
            return

        # Calculate totals
        subtotal = sum(data['price'] * data['qty'] for data in self.cart_items.values())
        from ..core.database import get_setting
        tax_percent = float(get_setting("tax_percent", "5.0"))
        tax = subtotal * (tax_percent / 100)
        total = subtotal + tax

        # Print receipt (pass cash amount)
        from ..core.printer import print_receipt
        print_receipt(self.cart_items, subtotal, tax, total, cash_received=cash)

        # Save order
        self.save_order()

        # Reset cash fields
        self.cash_input.clear()
        self.change_label.setText("🔄 Change Due: ₹0.00")

        # Delete held order if this was a resumed one
        if self.current_held_id is not None:
            from ..core.database import delete_held_order
            delete_held_order(self.current_held_id)
            self.current_held_id = None

    def save_order(self):
        """Save completed order to database."""
        import json
        from datetime import datetime

        conn = get_db_connection()
        cursor = conn.cursor()

        items_list = []
        for item_id, data in self.cart_items.items():
            items_list.append({
                'id': item_id,
                'name': data['name'],
                'price': data['price'],
                'qty': data['qty'],
                'total': data['price'] * data['qty']
            })

        subtotal = sum(item['total'] for item in items_list)
        tax_percent = 5.0
        tax = subtotal * (tax_percent / 100)
        total = subtotal + tax

        cursor.execute(
            """
            INSERT INTO orders (date_time, total_amount, items_json, status)
            VALUES (?, ?, ?, ?)
            """,
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, json.dumps(items_list), "completed")
        )
        conn.commit()
        conn.close()

        # Clear cart after saving
        self.clear_cart()

    def open_admin_panel(self):
        from .admin_window import AdminWindow
        self.admin_window = AdminWindow()
        self.admin_window.exec()

    def delete_item_from_cart(self, key):
        """Remove item from cart by key."""
        if key in self.cart_items:
            del self.cart_items[key]
            self.update_cart_display()

    def hold_order(self):
        """Save current cart as held order (create new or update existing)."""
        if not self.cart_items:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Empty Cart", "Cart is empty. Add items first.")
            return

        try:
            import json
            from datetime import datetime
            from ..core.database import get_db_connection

            subtotal = sum(item['price'] * item['qty'] for item in self.cart_items.values())
            tax_percent = 5.0
            tax = subtotal * (tax_percent / 100)
            total = subtotal + tax

            conn = get_db_connection()
            cursor = conn.cursor()

            if self.current_held_id is not None:
                # Update existing held order
                cursor.execute(
                    """
                    UPDATE orders 
                    SET date_time = ?, total_amount = ?, items_json = ?
                    WHERE order_id = ? AND status = 'held'
                    """,
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, json.dumps(list(self.cart_items.values())), self.current_held_id)
                )
                order_id = self.current_held_id
            else:
                # Create new held order
                cursor.execute(
                    """
                    INSERT INTO orders (date_time, total_amount, items_json, status)
                    VALUES (?, ?, ?, 'held')
                    """,
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, json.dumps(list(self.cart_items.values())))
                )
                order_id = cursor.lastrowid

            conn.commit()
            conn.close()

            self.clear_cart()
            self.current_held_id = None  # Reset after holding
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Order Held", f"Order H{order_id:03} has been held.\nCart cleared for new customer.")
        except Exception as e:
            print(f"❌ Hold error: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hold Failed", "Failed to hold order.")

    def resume_order(self):
        """Show dialog to resume a held order."""
        from PyQt6.QtWidgets import QMessageBox
        held_orders, deleted_count = get_held_orders()  # ← Now returns count
        
        # Show notification if old orders were cleaned
        if deleted_count > 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Held Orders Cleaned", 
                f"{deleted_count} old held order(s) (>2 hours) automatically deleted."
            )
        
        if not held_orders:
            QMessageBox.information(self, "No Held Orders", "No orders are currently held.")
            return

        dialog = ResumeDialog(held_orders)
        if dialog.exec():
            selected_order = held_orders[dialog.selected_order]
            self.current_held_id = selected_order['id']
            # Rebuild cart
            self.cart_items = {}
            for item in selected_order['items']:
                key = (item['name'], item['price'])
                self.cart_items[key] = {
                    'name': item['name'],
                    'price': item['price'],
                    'qty': item['qty']
                }
            self.update_cart_display()

    def filter_menu_items(self, text):
        """Filter menu buttons by search text."""
        text = text.lower()
        for i in range(self.menu_widget.layout().count()):
            widget = self.menu_widget.layout().itemAt(i).widget()
            if widget and isinstance(widget, QWidget):
                # Check if it's a row widget
                for child in widget.findChildren(QPushButton):
                    visible = text in child.text().lower()
                    widget.setVisible(visible)
                    break