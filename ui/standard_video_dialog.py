from PyQt5.QtCore import Qt, QThread
from ui.download_progress_dialog import DownloadProgressDialog
from .download_worker import DownloadWorker
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
        self.progress_dialog = None
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
        cache_path = self.get_cache_path(blob_name)
        if not os.path.exists(cache_path):
            self.progress_dialog = DownloadProgressDialog(self)
            self.thread = QThread()
            self.worker = DownloadWorker(self.reader, blob_name, cache_path)
            self.worker.moveToThread(self.thread)
            self.worker.progress.connect(self.progress_dialog.set_progress)
            self.worker.finished.connect(self.on_download_finished)
            self.worker.error.connect(self.on_download_error)
            self.thread.started.connect(self.worker.run)
            self.progress_dialog.show()
            self.thread.start()
        else:
            self.video_player.set_video(cache_path)

    def on_download_finished(self, cache_path):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.video_player.set_video(cache_path)
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()

    def on_download_error(self, error_msg):
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()
        print(f"Download error: {error_msg}")

    def get_cache_path(self, blobname):
        cache_dir = os.path.join(os.getcwd(), "standard_videos_cache")
        local_path = os.path.join(cache_dir, blobname)
        parent_dir = os.path.dirname(local_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        return local_path
    def get_selected_blob(self):
        return self.selected_blob
