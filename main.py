import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """
    Entry point for the Sports Movement Comparator application.
    Initializes the QApplication and shows the main window.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Application failed to start: {e}")