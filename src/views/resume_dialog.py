# src/views/resume_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel
)

class ResumeDialog(QDialog):
    def __init__(self, held_orders):
        super().__init__()
        self.setWindowTitle("Resume Held Order")
        self.resize(500, 400)
        self.selected_order = None

        layout = QVBoxLayout(self)

        if not held_orders:
            layout.addWidget(QLabel("No held orders."))
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.reject)
            layout.addWidget(close_btn)
            return

        self.list_widget = QListWidget()
        for order in held_orders:
            display_text = f"H{order['id']:03} • {order['time'][11:16]} • {order['summary']}"
            item = self.list_widget.addItem(display_text)
        layout.addWidget(self.list_widget)

        btn_layout = QVBoxLayout()
        resume_btn = QPushButton("Resume Selected")
        resume_btn.clicked.connect(self.resume_selected)
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.reject)

        btn_layout.addWidget(resume_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def resume_selected(self):
        current = self.list_widget.currentRow()
        if current >= 0:
            self.selected_order = current
            self.accept()
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Selection", "Please select an order to resume.")