"""
Enhanced VideoPlayer with full internationalization support.
增强的视频播放器，完整支持国际化
"""
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, 
    QLabel, QFrame, QSizePolicy, QCheckBox
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage
import os
from ui.i18n_mixin import I18nMixin
from localization import TK

# 尝试导入姿态检测相关模块
try:
    from core.experimental.frame_analyzer.pose_extractor import PoseExtractor
    from core.utils.image_utils import ImageUtils
    POSE_AVAILABLE = True
except ImportError as e:
    print(f"姿态检测模块导入失败: {e}")
    POSE_AVAILABLE = False


class EnhancedVideoPlayer(QWidget, I18nMixin):
    """增强的视频播放器，支持国际化和帧级导航"""
    
    # 信号定义
    frame_changed = pyqtSignal(int)  # 当前帧变化信号
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        I18nMixin.__init__(self)  # 初始化国际化混入

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

        # 姿态检测相关
        self.pose_extractor = None
        self.show_pose = False
        self.pose_color = (0, 255, 0)  # 默认绿色
        if POSE_AVAILABLE:
            try:
                self.pose_extractor = PoseExtractor(backend="mediapipe")
                print("姿态检测器初始化成功")
            except Exception as e:
                print(f"姿态检测器初始化失败: {e}")

        self.init_ui()
        self.setup_connections()
        self.update_ui_texts()  # 初始化文本
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # 视频显示区域
        self.video_frame = QLabel()
        self.video_frame.setMinimumHeight(200)
        self.video_frame.setMaximumHeight(400)
        self.video_frame.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
                text-align: center;
                color: #666666;
                font-size: 14px;
            }
        """)
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.video_frame)
        
        # 进度条
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.progress_slider)
        
        # 控制信息行
        info_layout = QHBoxLayout()
        
        # 帧信息标签
        self.frame_label = QLabel()
        self.time_label = QLabel()
        
        info_layout.addWidget(self.frame_label)
        info_layout.addStretch()
        info_layout.addWidget(self.time_label)
        
        layout.addLayout(info_layout)
        
        # 播放控制区域
        controls_layout = QHBoxLayout()
        
        # 上一帧按钮
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(35, 35)
        self.prev_btn.clicked.connect(self.prev_frame)
        
        # 播放/暂停按钮
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(45, 35)
        self.play_btn.clicked.connect(self.toggle_play)
        
        # 下一帧按钮
        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(35, 35)
        self.next_btn.clicked.connect(self.next_frame)
        
        # 速度选择
        self.speed_label = QLabel("1x")
        self.speed_label.setMinimumWidth(30)
        
        # 姿态显示开关
        self.pose_checkbox = QCheckBox()
        self.pose_checkbox.setChecked(False)
        self.pose_checkbox.stateChanged.connect(self.toggle_pose_display)
        if not POSE_AVAILABLE:
            self.pose_checkbox.setEnabled(False)
        
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.speed_label)
        controls_layout.addStretch()
        controls_layout.addWidget(self.pose_checkbox)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        """设置信号连接"""
        # 鼠标点击视频区域导入文件
        self.video_frame.mousePressEvent = self.on_video_frame_clicked
    
    def update_ui_texts(self):
        """更新所有UI文本"""
        # 提示文本
        self.video_frame.setText(self.translate(TK.UI.VideoPlayer.IMPORT_TIP))
        
        # 按钮提示
        self.prev_btn.setToolTip(self.translate(TK.UI.VideoPlayer.PREV_TIP))
        self.next_btn.setToolTip(self.translate(TK.UI.VideoPlayer.NEXT_TIP))
        self.play_btn.setToolTip(self.translate(TK.UI.VideoPlayer.PLAY_TIP))
        self.pose_checkbox.setText(self.translate(TK.UI.VideoPlayer.SHOW_POSE))
        
        # 更新信息标签
        self.update_frame_info()
    
    def update_frame_info(self):
        """更新帧信息显示"""
        if self.video_path and self.total_frames > 0:
            frame_text = self.translate(TK.UI.VideoPlayer.FRAME_INFO, 
                                      current=self.current_frame + 1, 
                                      total=self.total_frames)
            self.frame_label.setText(frame_text)
            
            # 计算时间
            current_time = self.current_frame / self.fps if self.fps > 0 else 0
            total_time = self.total_frames / self.fps if self.fps > 0 else 0
            time_text = self.translate(TK.UI.VideoPlayer.TIME_INFO,
                                     current_min=int(current_time // 60),
                                     current_sec=int(current_time % 60),
                                     total_min=int(total_time // 60),
                                     total_sec=int(total_time % 60))
            self.time_label.setText(time_text)
        else:
            self.frame_label.setText(self.translate(TK.UI.VideoPlayer.FRAME_INFO, current=1, total=0))
            self.time_label.setText(self.translate(TK.UI.VideoPlayer.TIME_INFO, 
                                                 current_min=0, current_sec=0,
                                                 total_min=0, total_sec=0))
    
    def on_video_frame_clicked(self, event):
        """点击视频区域导入文件"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translate(TK.UI.VideoPlayer.SELECT_VIDEO),
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All Files (*)"
        )
        
        if file_path:
            self.set_video(file_path)
    
    def set_video(self, video_path):
        """设置视频文件"""
        if not os.path.exists(video_path):
            print(self.translate(TK.Messages.Errors.FILE_NOT_FOUND))
            return False
        
        # 释放之前的视频
        if self.cap:
            self.cap.release()
        
        # 打开新视频
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            print(self.translate(TK.Messages.Errors.INVALID_VIDEO))
            return False
        
        self.video_path = video_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.current_frame = 0
        
        # 更新进度条
        self.progress_slider.setMaximum(self.total_frames - 1)
        self.progress_slider.setValue(0)
        
        # 显示第一帧
        self.display_current_frame()
        self.update_frame_info()
        
        return True
    
    def display_current_frame(self):
        """显示当前帧"""
        if not self.cap or not self.cap.isOpened():
            return
        
        # 设置帧位置
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        
        if not ret:
            print(self.translate(TK.Messages.Errors.CANNOT_READ_FRAME, frame=self.current_frame))
            return
        
        # 姿态检测
        if self.show_pose and self.pose_extractor:
            try:
                pose = self.pose_extractor.extract_pose_from_image(frame)
                if pose:
                    frame = self.pose_extractor.visualize_pose(frame, pose, color=self.pose_color)
            except Exception as e:
                print(f"姿态检测失败: {e}")
        
        # 转换为QPixmap并显示
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # 缩放到合适大小
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_frame.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        self.video_frame.setPixmap(scaled_pixmap)
        
        # 发出信号
        self.frame_changed.emit(self.current_frame)
    
    def toggle_play(self):
        """切换播放/暂停"""
        if not self.cap or self.total_frames == 0:
            return
        
        if self.is_playing:
            self.pause()
        else:
            self.play()
    
    def play(self):
        """开始播放"""
        if self.total_frames == 0:
            return
        
        self.is_playing = True
        self.play_btn.setText(self.translate(TK.UI.VideoPlayer.PAUSE))
        self.play_btn.setToolTip(self.translate(TK.UI.VideoPlayer.PAUSE_TIP))
        
        # 设置定时器间隔（基于FPS和播放速度）
        interval = int(1000 / (self.fps * self.current_speed))
        self.play_timer.start(interval)
    
    def pause(self):
        """暂停播放"""
        self.is_playing = False
        self.play_btn.setText(self.translate(TK.UI.VideoPlayer.PLAY))
        self.play_btn.setToolTip(self.translate(TK.UI.VideoPlayer.PLAY_TIP))
        self.play_timer.stop()
    
    def prev_frame(self):
        """上一帧"""
        if self.current_frame > 0:
            self.current_frame -= 1
            self.progress_slider.setValue(self.current_frame)
            self.display_current_frame()
            self.update_frame_info()
    
    def next_frame(self):
        """下一帧"""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.progress_slider.setValue(self.current_frame)
            self.display_current_frame()
            self.update_frame_info()
        else:
            # 到达末尾，停止播放
            if self.is_playing:
                self.pause()
    
    def on_slider_changed(self, value):
        """进度条变化"""
        if value != self.current_frame:
            self.current_frame = value
            self.display_current_frame()
            self.update_frame_info()
    
    def toggle_pose_display(self, state):
        """切换姿态显示"""
        self.show_pose = state == Qt.Checked
        if self.cap:
            self.display_current_frame()
    
    def set_speed(self, speed):
        """设置播放速度"""
        self.current_speed = speed
        self.speed_label.setText(f"{speed}x")
        
        # 如果正在播放，重新设置定时器
        if self.is_playing:
            self.play_timer.stop()
            interval = int(1000 / (self.fps * self.current_speed))
            self.play_timer.start(interval)
    
    def get_current_frame_image(self):
        """获取当前帧图像"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, frame = self.cap.read()
        
        return frame if ret else None
    
    def jump_to_frame(self, frame_number):
        """跳转到指定帧"""
        if 0 <= frame_number < self.total_frames:
            self.current_frame = frame_number
            self.progress_slider.setValue(frame_number)
            self.display_current_frame()
            self.update_frame_info()
    
    def set_pose_color(self, color):
        """设置火柴人颜色 (RGB格式)"""
        self.pose_color = color
        if hasattr(self, 'show_pose') and self.show_pose:
            self.show_current_frame()
    
    def enable_pose_display(self, enabled=True):
        """启用/禁用姿态显示功能"""
        if hasattr(self, 'pose_checkbox'):
            self.pose_checkbox.setEnabled(enabled)
    
    def set_pose_display(self, enabled):
        """设置姿态显示状态"""
        if hasattr(self, 'pose_checkbox'):
            self.pose_checkbox.setChecked(enabled)
        self.show_pose = enabled
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.cap:
            self.cap.release()
        event.accept()


# 为了保持向后兼容，创建一个别名
VideoPlayer = EnhancedVideoPlayer