import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
)
from ui.video_player import VideoPlayer
from ui.dialogs import Dialogs
from ui.results_window import ResultsWindow
from core.comparison_engine import ComparisonEngine

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sports Movement Comparator')
        self.setGeometry(100, 100, 1200, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Sport and action selection
        selection_layout = QHBoxLayout()
        self.sport_combo = QComboBox()
        self.sport_combo.addItems(['Badminton'])
        self.action_combo = QComboBox()
        self.action_combo.addItems(['Clear Shot (High Long Shot)'])
        selection_layout.addWidget(QLabel('Sport:'))
        selection_layout.addWidget(self.sport_combo)
        selection_layout.addWidget(QLabel('Action:'))
        selection_layout.addWidget(self.action_combo)
        layout.addLayout(selection_layout)

        # Video players
        video_layout = QHBoxLayout()
        self.user_video_player = VideoPlayer()
        self.standard_video_player = VideoPlayer()
        video_layout.addWidget(self.user_video_player)
        video_layout.addWidget(self.standard_video_player)
        layout.addLayout(video_layout)

        # Import buttons
        button_layout = QHBoxLayout()
        self.import_user_btn = QPushButton('Import User Video')
        self.import_standard_btn = QPushButton('Import Standard Video')
        button_layout.addWidget(self.import_user_btn)
        button_layout.addWidget(self.import_standard_btn)
        layout.addLayout(button_layout)

        # Compare button
        self.compare_btn = QPushButton('Compare')
        self.compare_btn.setEnabled(False)
        layout.addWidget(self.compare_btn)

        self.setLayout(layout)

        # Connect buttons
        self.import_user_btn.clicked.connect(self.import_user_video)
        self.import_standard_btn.clicked.connect(self.import_standard_video)
        self.compare_btn.clicked.connect(self.compare_videos)

        self.user_video_path = None
        self.standard_video_path = None

    def import_user_video(self):
        file_path = Dialogs.select_video(self, 'Import User Video')
        if file_path:
            self.user_video_path = file_path
            self.user_video_player.set_video(file_path)
            self.check_compare_ready()

    def import_standard_video(self):
        file_path = Dialogs.select_video(self, 'Import Standard Video')
        if file_path:
            self.standard_video_path = file_path
            self.standard_video_player.set_video(file_path)
            self.check_compare_ready()

    def check_compare_ready(self):
        if self.user_video_path and self.standard_video_path:
            self.compare_btn.setEnabled(True)
        else:
            self.compare_btn.setEnabled(False)

    def compare_videos(self):
        # Use ComparisonEngine to get dummy results
        engine = ComparisonEngine()
        result = engine.compare(self.user_video_path, self.standard_video_path)
        self.results_window = ResultsWindow(result, self.user_video_path, self.standard_video_path)
        self.results_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
