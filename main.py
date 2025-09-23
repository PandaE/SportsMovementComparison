import sys
from PyQt5.QtWidgets import QApplication
try:
    # Prefer new redesigned window
    from ui.new.redesigned_main_window import RedesignedMainWindow as AppMainWindow
except Exception:
    # Fallback to legacy enhanced window if new one fails to import
    from ui.enhanced_main_window import EnhancedMainWindow as AppMainWindow

def main():
    """
    Entry point for the Sports Movement Comparator application.
    Initializes the QApplication and shows the main window.
    """
    app = QApplication(sys.argv)
    window = AppMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Application failed to start: {e}")