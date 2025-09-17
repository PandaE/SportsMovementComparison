"""
Simplified Video Player Component
简化的视频播放器组件

Based on EnhancedVideoPlayer but with simplified functionality focused on core features.
基于EnhancedVideoPlayer但简化功能，专注于核心特性。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QFont
import cv2
import numpy as np


class VideoPlayer(QWidget):
    """简化的视频播放器组件"""
    
    # Signals
    position_changed = pyqtSignal(int)  # Frame position changed
    frame_extracted = pyqtSignal(int, np.ndarray)  # Frame extracted with position and image
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Video properties
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 30
        self.current_frame = 0
        self.is_playing = False
        
        # UI state
        self.display_width = 400
        self.display_height = 300
        
        # Timer for playback
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # Video display area
        self.video_frame = QLabel()
        self.video_frame.setFixedSize(self.display_width, self.display_height)
        self.video_frame.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setText("No Video Loaded")
        layout.addWidget(self.video_frame)
        
        # Video info
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.info_label)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(0)
        self.progress_slider.valueChanged.connect(self.seek_frame)
        layout.addWidget(self.progress_slider)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setMaximumWidth(50)
        self.play_btn.clicked.connect(self.toggle_play)
        
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setMaximumWidth(50)
        self.stop_btn.clicked.connect(self.stop)
        
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setMaximumWidth(50)
        self.prev_btn.clicked.connect(self.previous_frame)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.setMaximumWidth(50)
        self.next_btn.clicked.connect(self.next_frame)
        
        self.extract_btn = QPushButton("Extract Frame")
        self.extract_btn.clicked.connect(self.extract_current_frame)
        
        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.next_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.extract_btn)
        
        layout.addLayout(control_layout)
        
        # Position info
        self.position_label = QLabel("Frame: 0 / 0")
        self.position_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.position_label)
        
        self.setLayout(layout)
        
        # Initially disable controls
        self.set_controls_enabled(False)

    def set_video(self, video_path: str) -> bool:
        """
        Set video file for playback
        设置视频文件进行播放
        
        Args:
            video_path: Path to video file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Release previous video
            if self.cap:
                self.cap.release()
            
            # Open new video
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                return False
            
            # Get video properties
            self.video_path = video_path
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.current_frame = 0
            
            # Update UI
            self.progress_slider.setMaximum(self.total_frames - 1)
            self.progress_slider.setValue(0)
            self.set_controls_enabled(True)
            self.update_info()
            
            # Display first frame
            self.seek_frame(0)
            
            return True
            
        except Exception as e:
            print(f"Error loading video: {e}")
            return False

    def set_controls_enabled(self, enabled: bool):
        """Enable/disable video controls"""
        self.play_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.prev_btn.setEnabled(enabled)
        self.next_btn.setEnabled(enabled)
        self.extract_btn.setEnabled(enabled)
        self.progress_slider.setEnabled(enabled)

    def toggle_play(self):
        """Toggle play/pause"""
        if not self.cap:
            return
        
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self):
        """Start playback"""
        if not self.cap or self.current_frame >= self.total_frames - 1:
            return
        
        self.is_playing = True
        self.play_btn.setText("⏸")
        
        # Calculate interval based on FPS
        interval = max(1, int(1000 / self.fps))
        self.timer.start(interval)

    def pause(self):
        """Pause playback"""
        self.is_playing = False
        self.play_btn.setText("▶")
        self.timer.stop()

    def stop(self):
        """Stop playback and return to beginning"""
        self.pause()
        self.seek_frame(0)

    def seek_frame(self, frame_number: int):
        """
        Seek to specific frame
        跳转到指定帧
        
        Args:
            frame_number: Target frame number
        """
        if not self.cap or frame_number < 0 or frame_number >= self.total_frames:
            return
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        if ret:
            self.current_frame = frame_number
            self.display_frame(frame)
            self.update_position()
            self.position_changed.emit(frame_number)

    def next_frame(self):
        """Move to next frame"""
        if self.current_frame < self.total_frames - 1:
            self.seek_frame(self.current_frame + 1)
        else:
            self.pause()  # End of video

    def previous_frame(self):
        """Move to previous frame"""
        if self.current_frame > 0:
            self.seek_frame(self.current_frame - 1)

    def display_frame(self, frame: np.ndarray):
        """
        Display frame in the video widget
        在视频组件中显示帧
        
        Args:
            frame: OpenCV frame (BGR format)
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Get dimensions
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            
            # Create QImage
            from PyQt5.QtGui import QImage
            q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Scale to fit display
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                self.display_width, self.display_height, 
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            self.video_frame.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error displaying frame: {e}")

    def extract_current_frame(self):
        """Extract current frame for analysis"""
        if not self.cap:
            return
        
        # Get current frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_extracted.emit(self.current_frame, frame)

    def get_current_frame_data(self) -> tuple:
        """
        Get current frame data
        获取当前帧数据
        
        Returns:
            tuple: (frame_number, frame_array) or (None, None) if no frame
        """
        if not self.cap:
            return None, None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        
        if ret:
            return self.current_frame, frame
        return None, None

    def update_info(self):
        """Update video information display"""
        if self.video_path:
            video_name = self.video_path.split('/')[-1].split('\\')[-1]
            duration = self.total_frames / self.fps if self.fps > 0 else 0
            info_text = f"{video_name} | {self.total_frames} frames | {duration:.1f}s | {self.fps:.1f} FPS"
            self.info_label.setText(info_text)
        else:
            self.info_label.setText("No video loaded")

    def update_position(self):
        """Update position display"""
        self.position_label.setText(f"Frame: {self.current_frame + 1} / {self.total_frames}")
        
        # Update slider without triggering signal
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(self.current_frame)
        self.progress_slider.blockSignals(False)

    def closeEvent(self, event):
        """Clean up when widget is closed"""
        if self.cap:
            self.cap.release()
        self.timer.stop()
        event.accept()

    def __del__(self):
        """Destructor"""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()


if __name__ == '__main__':
    """Test the video player"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())