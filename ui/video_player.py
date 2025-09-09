"""
video_player.py
Reusable video player widget for PyQt5.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon
import os

class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)
        # Progress bar
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)
        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.addStretch(1)
        # Circular play/pause button (centered)
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.setIcon(QIcon('assets/icons/play.png'))
        self.play_pause_btn.setStyleSheet('border-radius: 20px;')
        self.play_pause_btn.setEnabled(False)
        controls_layout.addWidget(self.play_pause_btn)
        # Speed toggle button (right of play, slightly shorter)
        self.speed_btn = QPushButton('1X')
        self.speed_btn.setFixedSize(32, 32)
        controls_layout.addWidget(self.speed_btn)
        controls_layout.addStretch(1)
        self.layout.addLayout(controls_layout)
        self.setLayout(self.layout)

        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.video_widget)
        self.is_playing = False
        self.current_speed = 1.0

        # Connect signals
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.speed_btn.clicked.connect(self.toggle_speed)
        self.player.positionChanged.connect(self.update_progress)
        self.player.durationChanged.connect(self.set_duration)
        self.progress_bar.sliderMoved.connect(self.seek)
        self.player.stateChanged.connect(self.on_state_changed)

    def set_video(self, file_path):
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
        self.play_pause_btn.setIcon(QIcon('assets/icons/play.png'))
        self.is_playing = False
        self.progress_bar.setValue(0)
        self.player.stop()
        self.play_pause_btn.setEnabled(True)

    def toggle_play_pause(self):
        if self.is_playing:
            self.player.pause()
        else:
            self.player.play()
        self.is_playing = not self.is_playing
        self.update_play_pause_icon()

    def update_play_pause_icon(self):
        icon_path = 'assets/icons/pause.png' if self.is_playing else 'assets/icons/play.png'
        self.play_pause_btn.setIcon(QIcon(icon_path))

    def toggle_speed(self):
        if self.current_speed == 1.0:
            self.current_speed = 0.5
            self.speed_btn.setText('0.5X')
        else:
            self.current_speed = 1.0
            self.speed_btn.setText('1X')
        self.player.setPlaybackRate(self.current_speed)

    def update_progress(self, position):
        duration = self.player.duration()
        if duration > 0:
            self.progress_bar.setValue(int(position * 100 / duration))
        else:
            self.progress_bar.setValue(0)

    def set_duration(self, duration):
        self.progress_bar.setRange(0, 100)

    def seek(self, value):
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(value * duration / 100))

    def on_state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.is_playing = False
            self.update_play_pause_icon()
