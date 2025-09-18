from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt
from ui.enhanced_video_player import EnhancedVideoPlayer
from core.azure_blob_reader import AzureBlobReader
import os

class StandardVideoDialog(QDialog):
    def __init__(self, sport, action, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Standard Video")
        self.setFixedSize(700, 420)
        self.selected_blob = None
        self.reader = AzureBlobReader()
        self.folder_path = f"{sport}/{action}/"
        self.video_list = self.reader.list_files(self.folder_path)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        list_layout = QHBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.addItems([os.path.basename(v) for v in self.video_list])
        self.list_widget.setMinimumWidth(220)
        list_layout.addWidget(self.list_widget)
        self.video_player = EnhancedVideoPlayer()
        list_layout.addWidget(self.video_player)
        layout.addLayout(list_layout)
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.list_widget.currentRowChanged.connect(self.on_video_selected)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def on_video_selected(self, row):
        if row < 0 or row >= len(self.video_list):
            return
        blob_name = self.video_list[row]
        self.selected_blob = blob_name
        url = self.reader.get_blob_url(blob_name)
        self.video_player.set_video_from_blob(url, blob_name)  # Play network video

    def get_selected_blob(self):
        return self.selected_blob
