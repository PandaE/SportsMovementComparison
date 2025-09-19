import sys, os
from PyQt5.QtWidgets import QApplication

# Allow running this file directly: add project root to sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from ui.new_results.mock_data import build_mock_vm
    from ui.new_results.results_window import ResultsWindow
except ImportError:  # Fallback if package resolution changes
    from .mock_data import build_mock_vm  # type: ignore
    from .results_window import ResultsWindow  # type: ignore

if __name__ == '__main__':
    app = QApplication(sys.argv)
    vm = build_mock_vm()
    w = ResultsWindow(vm)
    w.show()
    sys.exit(app.exec_())
