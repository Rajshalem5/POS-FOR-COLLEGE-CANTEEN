# src/main.py
import sys
import traceback
from PyQt6.QtWidgets import QApplication

def main():
    try:
        # ✅ Relative import: .core = src.core
        from .core.database import init_db
        init_db()
        
        from .views.main_window import MainWindow
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print("❌ CRITICAL ERROR:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()