from PyQt5.QtCore import QObject, pyqtSignal

class DownloadWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, reader, blob_name, cache_path):
        super().__init__()
        self.reader = reader
        self.blob_name = blob_name
        self.cache_path = cache_path

    def run(self):
        try:
            self.reader.download_blob_to_path(self.blob_name, self.cache_path, self.progress.emit)
            self.finished.emit(self.cache_path)
        except Exception as e:
            self.error.emit(str(e))
