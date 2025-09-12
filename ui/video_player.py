"""
video_player.py
Enhanced video player widget with frame-level navigation for PyQt5.
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, 
    QLabel, QFrame, QSizePolicy
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont
import os

class VideoPlayer(QWidget):
    """增强的视频播放器，支持帧级导航"""
    
    # 信号定义
    frame_changed = pyqtSignal(int)  # 当前帧变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 视频相关属性
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 30.0
        
        # 播放控制
        self.is_playing = False
        self.current_speed = 1.0
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.next_frame)
        
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # 视频显示区域
        self.create_video_display(layout)
        
        # 帧信息显示
        self.create_frame_info(layout)
        
        # 进度条
        self.create_progress_bar(layout)
        
        # 控制按钮
        self.create_controls(layout)
        
        self.setLayout(layout)
    
    def create_video_display(self, layout):
        """创建视频显示区域"""
        # 视频预览标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(320, 240)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        self.video_label.setText("点击导入视频文件")
        layout.addWidget(self.video_label)
    
    def create_frame_info(self, layout):
        """创建帧信息显示"""
        info_layout = QHBoxLayout()
        
        # 当前帧/总帧数
        self.frame_info_label = QLabel("0 / 0")
        self.frame_info_label.setAlignment(Qt.AlignCenter)
        frame_font = QFont()
        frame_font.setPointSize(10)
        frame_font.setBold(True)
        self.frame_info_label.setFont(frame_font)
        self.frame_info_label.setStyleSheet("color: #2c3e50;")
        
        # 时间信息
        self.time_info_label = QLabel("00:00 / 00:00")
        self.time_info_label.setAlignment(Qt.AlignCenter)
        self.time_info_label.setFont(frame_font)
        self.time_info_label.setStyleSheet("color: #34495e;")
        
        info_layout.addWidget(QLabel("帧数:"))
        info_layout.addWidget(self.frame_info_label)
        info_layout.addStretch()
        info_layout.addWidget(QLabel("时间:"))
        info_layout.addWidget(self.time_info_label)
        
        layout.addLayout(info_layout)
    
    def create_progress_bar(self, layout):
        """创建进度条"""
        # 进度条
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3498db, stop:1 #2980b9);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3498db, stop:1 #2980b9);
                border: 1px solid #777;
                height: 8px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
    
    def create_controls(self, layout):
        """创建控制按钮"""
        controls_layout = QHBoxLayout()
        
        # 帧控制按钮
        self.prev_frame_btn = QPushButton("⏮")
        self.prev_frame_btn.setFixedSize(35, 35)
        self.prev_frame_btn.setToolTip("上一帧")
        self.prev_frame_btn.setEnabled(False)
        
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setFixedSize(45, 45)
        self.play_pause_btn.setToolTip("播放/暂停")
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                border-radius: 22px;
                background-color: #3498db;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.next_frame_btn = QPushButton("⏭")
        self.next_frame_btn.setFixedSize(35, 35)
        self.next_frame_btn.setToolTip("下一帧")
        self.next_frame_btn.setEnabled(False)
        
        # 速度控制
        self.speed_btn = QPushButton("1X")
        self.speed_btn.setFixedSize(40, 35)
        self.speed_btn.setToolTip("播放速度")
        self.speed_btn.setEnabled(False)
        
        # 布局
        controls_layout.addStretch()
        controls_layout.addWidget(self.prev_frame_btn)
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.next_frame_btn)
        controls_layout.addWidget(self.speed_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
    
    def setup_connections(self):
        """设置信号连接"""
        self.progress_bar.sliderPressed.connect(self.on_slider_pressed)
        self.progress_bar.sliderReleased.connect(self.on_slider_released)
        self.progress_bar.valueChanged.connect(self.on_progress_changed)
        
        self.prev_frame_btn.clicked.connect(self.prev_frame)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        self.next_frame_btn.clicked.connect(self.next_frame)
        self.speed_btn.clicked.connect(self.toggle_speed)
    
    def set_video(self, file_path):
        """设置视频文件"""
        if not os.path.exists(file_path):
            self.video_label.setText("视频文件不存在")
            return
        
        # 释放之前的视频
        if self.cap:
            self.cap.release()
        
        # 打开新视频
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            self.video_label.setText("无法打开视频文件")
            return
        
        self.video_path = file_path
        
        # 获取视频信息
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        # 更新UI
        self.progress_bar.setRange(0, self.total_frames - 1)
        self.current_frame = 0
        self.progress_bar.setValue(0)
        
        # 启用控件
        self.enable_controls(True)
        
        # 显示第一帧
        self.show_current_frame()
        self.update_info_display()
    
    def enable_controls(self, enabled):
        """启用/禁用控件"""
        self.prev_frame_btn.setEnabled(enabled)
        self.play_pause_btn.setEnabled(enabled)
        self.next_frame_btn.setEnabled(enabled)
        self.speed_btn.setEnabled(enabled)
    
    def show_current_frame(self):
        """显示当前帧"""
        if not self.cap:
            return
        
        # 设置视频位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        
        if ret:
            # 转换为Qt格式并显示
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # 创建QPixmap
            from PyQt5.QtGui import QImage
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # 缩放以适应标签大小
            label_size = self.video_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size.width() - 10, 
                label_size.height() - 10, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
        else:
            self.video_label.setText(f"无法读取第 {self.current_frame} 帧")
    
    def update_info_display(self):
        """更新信息显示"""
        # 更新帧数信息
        self.frame_info_label.setText(f"{self.current_frame + 1} / {self.total_frames}")
        
        # 更新时间信息
        current_time = self.current_frame / self.fps if self.fps > 0 else 0
        total_time = self.total_frames / self.fps if self.fps > 0 else 0
        
        current_time_str = self.format_time(current_time)
        total_time_str = self.format_time(total_time)
        self.time_info_label.setText(f"{current_time_str} / {total_time_str}")
        
        # 发射帧变化信号
        self.frame_changed.emit(self.current_frame)
    
    def format_time(self, seconds):
        """格式化时间显示"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def on_slider_pressed(self):
        """进度条按下时停止播放"""
        if self.is_playing:
            self.play_timer.stop()
    
    def on_slider_released(self):
        """进度条释放时恢复播放"""
        if self.is_playing:
            self.start_playback()
    
    def on_progress_changed(self, value):
        """进度条值变化时更新当前帧"""
        if self.cap and value != self.current_frame:
            self.current_frame = value
            self.show_current_frame()
            self.update_info_display()
    
    def prev_frame(self):
        """上一帧"""
        if self.current_frame > 0:
            self.current_frame -= 1
            self.progress_bar.setValue(self.current_frame)
            self.show_current_frame()
            self.update_info_display()
    
    def next_frame(self):
        """下一帧"""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.progress_bar.setValue(self.current_frame)
            self.show_current_frame()
            self.update_info_display()
    
    def toggle_play_pause(self):
        """切换播放/暂停"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """开始播放"""
        if self.cap and self.current_frame < self.total_frames - 1:
            self.is_playing = True
            self.play_pause_btn.setText("⏸")
            self.play_pause_btn.setToolTip("暂停")
            self.start_playback()
    
    def pause(self):
        """暂停播放"""
        self.is_playing = False
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setToolTip("播放")
        self.play_timer.stop()
    
    def start_playback(self):
        """开始播放定时器"""
        interval = int(1000 / (self.fps * self.current_speed))
        self.play_timer.start(interval)
    
    def toggle_speed(self):
        """切换播放速度"""
        speed_options = [0.25, 0.5, 1.0, 1.5, 2.0]
        current_index = speed_options.index(self.current_speed) if self.current_speed in speed_options else 2
        next_index = (current_index + 1) % len(speed_options)
        self.current_speed = speed_options[next_index]
        self.speed_btn.setText(f"{self.current_speed}X")
        
        # 如果正在播放，重新启动定时器
        if self.is_playing:
            self.play_timer.stop()
            self.start_playback()
    
    def get_current_frame_number(self):
        """获取当前帧号"""
        return self.current_frame
    
    def get_total_frames(self):
        """获取总帧数"""
        return self.total_frames
    
    def set_frame(self, frame_number):
        """设置到指定帧"""
        if 0 <= frame_number < self.total_frames:
            self.current_frame = frame_number
            self.progress_bar.setValue(frame_number)
            self.show_current_frame()
            self.update_info_display()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.cap:
            self.cap.release()
        super().closeEvent(event)
