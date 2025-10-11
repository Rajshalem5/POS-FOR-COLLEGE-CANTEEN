# src/views/resume_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt

class ResumeDialog(QDialog):
    def __init__(self, held_orders):
        super().__init__()
        self.setWindowTitle("Resume / Manage Held Orders")
        self.resize(600, 500)
        self.held_orders = held_orders
        self.selected_order = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        if not self.held_orders:
            layout.addWidget(QLabel("No held orders."))
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return

        # Top buttons: Resume, Delete Selected, Delete All
        top_btn_layout = QHBoxLayout()
        resume_btn = QPushButton("▶️ Resume Selected")
        resume_btn.clicked.connect(self.resume_selected)
        delete_selected_btn = QPushButton("🗑️ Delete Selected")
        delete_selected_btn.clicked.connect(self.delete_selected)
        delete_all_btn = QPushButton("🗑️ Delete All")
        delete_all_btn.clicked.connect(self.delete_all)

        top_btn_layout.addWidget(resume_btn)
        top_btn_layout.addWidget(delete_selected_btn)
        top_btn_layout.addWidget(delete_all_btn)

        # Manual cleanup button
        cleanup_btn = QPushButton("🧹 Clear Old Held Orders")
        cleanup_btn.clicked.connect(self.cleanup_old_orders)
        top_btn_layout.addWidget(cleanup_btn)

        layout.addLayout(top_btn_layout)

        # "Select All" checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        layout.addWidget(self.select_all_checkbox)

        # List of held orders with checkboxes
        self.list_widget = QListWidget()
        self.checkboxes = []
        for order in self.held_orders:
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            display_text = f"H{order['id']:03} • {order['time'][11:16]} • {order['summary']}"
            item.setText(display_text)
            self.list_widget.addItem(item)
            self.checkboxes.append(item)

        layout.addWidget(self.list_widget)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def toggle_select_all(self, state):
        """Toggle all checkboxes when 'Select All' is clicked."""
        check_state = Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        for item in self.checkboxes:
            item.setCheckState(check_state)

    def get_selected_indices(self):
        """Return list of indices of checked orders."""
        selected = []
        for i, item in enumerate(self.checkboxes):
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(i)
        return selected

    def resume_selected(self):
        """Resume the first selected order (if any)."""
        selected = self.get_selected_indices()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an order to resume.")
            return
        # Resume the first selected order
        self.selected_order = selected[0]
        self.accept()

    def delete_selected(self):
        """Delete selected held orders."""
        selected = self.get_selected_indices()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select orders to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected)} selected held order(s)?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from ..core.database import delete_held_order
            # Delete from DB (in reverse order to avoid index shift)
            for i in sorted(selected, reverse=True):
                order_id = self.held_orders[i]['id']
                delete_held_order(order_id)
                # Remove from local list
                del self.held_orders[i]
                # Remove from UI
                self.list_widget.takeItem(i)
                del self.checkboxes[i]
            # Reset select all
            self.select_all_checkbox.setChecked(False)
            if not self.held_orders:
                QMessageBox.information(self, "All Cleared", "No held orders remaining.")
                self.reject()

    def delete_all(self):
        """Delete all held orders."""
        if not self.held_orders:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete All",
            "Delete ALL held orders?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from ..core.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE status = 'held'")
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Deleted", "All held orders deleted.")
            self.held_orders.clear()
            self.list_widget.clear()
            self.checkboxes.clear()
            self.select_all_checkbox.setChecked(False)

    def cleanup_old_orders(self):
        """Manually delete held orders older than 2 hours."""
        from datetime import datetime, timedelta
        from ..core.database import get_db_connection
        
        cutoff_time = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE status = 'held' AND date_time < ?", (cutoff_time,))
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Cleanup Complete", 
                f"{deleted_count} old held order(s) deleted."
            )
            # Refresh the list
            from ..core.database import get_held_orders
            held_orders, _ = get_held_orders()
            self.held_orders = held_orders
            self.list_widget.clear()
            self.checkboxes.clear()
            for order in held_orders:
                item = QListWidgetItem()
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                display_text = f"H{order['id']:03} • {order['time'][11:16]} • {order['summary']}"
                item.setText(display_text)
                self.list_widget.addItem(item)
                self.checkboxes.append(item)
            self.select_all_checkbox.setChecked(False)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Old Orders", "No held orders older than 2 hours.")