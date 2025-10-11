# src/views/admin_window.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QTabWidget, QHeaderView, QWidget, QItemDelegate
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
import csv
import os
from ..core.database import get_db_connection, get_all_orders, get_daily_summary, get_most_sold_items, get_setting, set_setting

class StockEditor(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QIntValidator(0, 9999, editor))
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = int(editor.text())
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class AdminWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Panel")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Menu Management (existing)
        menu_tab = QWidget()
        self.setup_menu_tab(menu_tab)
        tabs.addTab(menu_tab, "Menu Management")

        # Tab 2: Reports
        report_tab = QWidget()
        self.setup_report_tab(report_tab)
        tabs.addTab(report_tab, "Reports")

        # Tab 3: Settings
        settings_tab = QWidget()
        self.setup_settings_tab(settings_tab)
        tabs.addTab(settings_tab, "Settings")

    def setup_menu_tab(self, parent):
        layout = QVBoxLayout(parent)

        # Form to add new item
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price (e.g., 25.0)")
        self.category_input = QComboBox()
        self.category_input.addItems(["Snacks", "Drinks", "Meals", "Other"])
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Stock (999=unlimited)")
        self.stock_input.setText("999")
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_item)

        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("Price:"))
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(QLabel("Category:"))
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(QLabel("Stock:"))
        form_layout.addWidget(self.stock_input)
        form_layout.addWidget(add_btn)

        # Table to show/edit items
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Price", "Stock"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        # Make stock column editable
        self.table.setItemDelegateForColumn(4, StockEditor())
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.cellChanged.connect(self.on_cell_changed)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_item)

        layout.addLayout(form_layout)
        layout.addWidget(self.table)
        layout.addWidget(delete_btn)
        self.load_items()

    def setup_report_tab(self, parent):
        layout = QVBoxLayout(parent)

        # Daily Summary
        count, total = get_daily_summary()
        summary_label = QLabel(f"📅 Today's Sales: {count} orders • ₹{total:.2f}")
        summary_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(summary_label)

        # Most Sold Items
        layout.addWidget(QLabel("🏆 Top 5 Most Sold Items:"))
        top_items = get_most_sold_items(5)
        top_list = ""
        for i, ((name, price), qty) in enumerate(top_items, 1):
            top_list += f"{i}. {name} — {qty} sold\n"
        if not top_list:
            top_list = "No sales yet."
        top_label = QLabel(top_list)
        layout.addWidget(top_label)

        # Export Button
        export_btn = QPushButton("📤 Export All Sales to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        layout.addWidget(export_btn)

        # Sales History Table
        layout.addWidget(QLabel("📋 Sales History (Completed Orders):"))
        self.history_table = QTableWidget(0, 4)
        self.history_table.setHorizontalHeaderLabels(["Order ID", "Date & Time", "Items", "Total"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.history_table)

        self.load_sales_history()

    def load_sales_history(self):
        orders = get_all_orders()
        self.history_table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(order['id'])))
            self.history_table.setItem(row, 1, QTableWidgetItem(order['datetime']))
            items_summary = ", ".join([f"{item['name']} x{item['qty']}" for item in order['items']])
            self.history_table.setItem(row, 2, QTableWidgetItem(items_summary))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"₹{order['total']:.2f}"))

    def export_to_csv(self):
        """Export all completed orders to CSV."""
        try:
            orders = get_all_orders()
            if not orders:
                QMessageBox.warning(self, "No Data", "No completed orders to export.")
                return

            # Save to project root as 'sales_report.csv'
            csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sales_report.csv"))
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Order ID", "Date & Time", "Item", "Qty", "Price", "Total"])
                for order in orders:
                    for item in order['items']:
                        writer.writerow([
                            order['id'],
                            order['datetime'],
                            item['name'],
                            item['qty'],
                            item['price'],
                            order['total']
                        ])

            QMessageBox.information(self, "Export Success", f"Sales report saved to:\n{csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    def add_item(self):
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip()
        category = self.category_input.currentText()

        if not name or not price_text:
            QMessageBox.warning(self, "Input Error", "Please fill all fields.")
            return

        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Price must be a number.")
            return

        try:
            stock = int(self.stock_input.text() or 999)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Stock must be a number.")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
            (name, category, price, stock)
        )
        conn.commit()
        conn.close()

        self.name_input.clear()
        self.price_input.clear()
        self.stock_input.setText("999")
        self.load_items()
        # Refresh main window menu (if exists)
        if hasattr(self.parent(), 'load_menu_items'):
            self.parent().load_menu_items()
        if hasattr(self.parent(), 'refresh_menu'):
            self.parent().refresh_menu()

    def load_items(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, price, stock_quantity FROM items ORDER BY name")
        items = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(items))
        for row, (id, name, category, price, stock) in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(category))
            self.table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(stock)))
        # (Optional) Connect cellChanged for advanced editing

    def delete_item(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selection Error", "Please select an item to delete.")
            return

        item_id = int(self.table.item(selected, 0).text())
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            self.load_items()
            if hasattr(self.parent(), 'load_menu_items'):
                self.parent().load_menu_items()
            if hasattr(self.parent(), 'refresh_menu'):
                self.parent().refresh_menu()

    def setup_settings_tab(self, parent):
        layout = QVBoxLayout(parent)

        # Canteen Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Canteen Name:"))
        self.canteen_name_input = QLineEdit()
        self.canteen_name_input.setText(get_setting("canteen_name", "College Canteen"))
        name_layout.addWidget(self.canteen_name_input)
        layout.addLayout(name_layout)

        # Tax Percentage
        tax_layout = QHBoxLayout()
        tax_layout.addWidget(QLabel("Tax Percentage (%):"))
        self.tax_input = QLineEdit()
        self.tax_input.setText(get_setting("tax_percent", "5.0"))
        tax_layout.addWidget(self.tax_input)
        layout.addLayout(tax_layout)

        # Paper Width
        paper_layout = QHBoxLayout()
        paper_layout.addWidget(QLabel("Paper Width:"))
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["58mm", "80mm"])
        current_paper = get_setting("paper_width", "58")
        self.paper_combo.setCurrentText(f"{current_paper}mm")
        paper_layout.addWidget(self.paper_combo)
        layout.addLayout(paper_layout)

        # Admin Password
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(QLabel("Admin Password:"))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setText(get_setting("admin_password", "1234"))
        pwd_layout.addWidget(self.pwd_input)
        layout.addLayout(pwd_layout)

        # Save Button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    def save_settings(self):
        """Save all settings to database."""
        try:
            # Validate tax
            tax = float(self.tax_input.text())
            if tax < 0:
                raise ValueError("Tax cannot be negative")

            # Save settings
            set_setting("canteen_name", self.canteen_name_input.text().strip() or "College Canteen")
            set_setting("tax_percent", str(tax))
            set_setting("paper_width", self.paper_combo.currentText().replace("mm", ""))
            set_setting("admin_password", self.pwd_input.text().strip() or "1234")

            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", f"Invalid tax value: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
