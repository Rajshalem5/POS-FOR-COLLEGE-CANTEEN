# src/views/admin_window.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox
)
from core.database import get_db_connection

class AdminWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Panel - Menu Management")
        self.resize(600, 500)
        self.setup_ui()
        self.load_items()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Form to add new item
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name")
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Price (e.g., 25.0)")
        self.category_input = QComboBox()
        self.category_input.addItems(["Snacks", "Drinks", "Meals", "Other"])
        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.add_item)

        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("Price:"))
        form_layout.addWidget(self.price_input)
        form_layout.addWidget(QLabel("Category:"))
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(add_btn)

        # Table to show/edit items
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Price"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_item)

        layout.addLayout(form_layout)
        layout.addWidget(self.table)
        layout.addWidget(delete_btn)

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

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (name, category, price) VALUES (?, ?, ?)",
            (name, category, price)
        )
        conn.commit()
        conn.close()

        self.name_input.clear()
        self.price_input.clear()
        self.load_items()

    def load_items(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, price FROM items ORDER BY name")
        items = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(items))
        for row, (id, name, category, price) in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(id)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(category))
            self.table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))

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