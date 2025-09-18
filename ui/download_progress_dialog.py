from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QLabel

class DownloadProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading Video...")
        self.setFixedSize(320, 100)
        layout = QVBoxLayout()
        self.label = QLabel("Downloading, please wait...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

    def set_progress(self, value):
        self.progress_bar.setValue(value)
