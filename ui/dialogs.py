"""
dialogs.py
File selection and error dialogs for PyQt5.
"""
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

class Dialogs:
    @staticmethod
    def select_video(parent: QWidget, title: str) -> str:
        file_path, _ = QFileDialog.getOpenFileName(parent, title, '', 'Video Files (*.mp4 *.avi *.mov)')
        return file_path

    @staticmethod
    def show_error(parent: QWidget, message: str):
        QMessageBox.critical(parent, 'Error', message)
