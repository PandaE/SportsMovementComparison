"""
results_window.py
Results display window for comparison results.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, QListWidgetItem
from ui.video_player import VideoPlayer

class ResultsWindow(QWidget):
    def __init__(self, comparison_result, user_video_path, standard_video_path):
        super().__init__()
        self.setWindowTitle('Comparison Results')
        self.setGeometry(150, 150, 1000, 700)
        layout = QVBoxLayout()
        # Overall score
        score_label = QLabel(f"Overall Score: {comparison_result.get('score', 'N/A')}")
        score_label.setStyleSheet('font-size: 24px; font-weight: bold;')
        layout.addWidget(score_label)
        # Video players side by side
        video_layout = QHBoxLayout()
        self.user_video_player = VideoPlayer()
        self.user_video_player.set_video(user_video_path)
        self.standard_video_player = VideoPlayer()
        self.standard_video_player.set_video(standard_video_path)
        video_layout.addWidget(self.user_video_player)
        video_layout.addWidget(self.standard_video_player)
        layout.addLayout(video_layout)
        # Key movement comparisons
        layout.addWidget(QLabel('Key Movement Comparisons:'))
        self.movements_list = QListWidget()
        for movement in comparison_result.get('key_movements', []):
            item = QListWidgetItem()
            item.setText(f"{movement['name']}\nSummary: {movement['summary']}\nSuggestion: {movement['suggestion']}")
            self.movements_list.addItem(item)
        layout.addWidget(self.movements_list)
        self.setLayout(layout)
