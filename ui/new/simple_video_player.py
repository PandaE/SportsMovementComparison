import os
import cv2
from time import perf_counter
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSlider, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class SimpleVideoPlayer(QWidget):
    """极简视频播放器：显示视频、播放/暂停、进度拖动。
    改进：
    1. 不裁剪视频，按比例完整显示（letterbox/pillarbox 填充）
    2. 根据视频宽高比动态调整高度（上限可配置）
    3. 允许可选 unlock_auto_width() 使播放器随父布局拉伸
    """
    def __init__(self, parent=None, fixed_width: int = 480, min_height: int = 180, max_height: int = 520):
        super().__init__(parent)
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 30.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)
        self._playing = False
        self._fixed_width = fixed_width
        self._min_height = min_height
        self._max_height = max_height
        self._auto_width = False
        self._video_w = None
        self._video_h = None
        self._play_start_time = None
        self._play_start_frame = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(6)
        self.video_label = QLabel('无视频'); self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(self._fixed_width, self._min_height)
        self.video_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.video_label.setStyleSheet('background:#10161a; color:#7f8b95; border:1px solid #2c3a46; border-radius:6px;')
        layout.addWidget(self.video_label)

        self.slider = QSlider(Qt.Horizontal); self.slider.setRange(0,0)
        self.slider.valueChanged.connect(self._on_slider)
        layout.addWidget(self.slider)

        bar = QHBoxLayout(); bar.setSpacing(8)
        self.play_btn = QPushButton('播放'); self.play_btn.setFixedHeight(34)
        self.play_btn.clicked.connect(self.toggle_play)
        self.info_label = QLabel('-- / --'); self.info_label.setStyleSheet('color:#394956; font-size:12px;')
        bar.addWidget(self.play_btn)
        bar.addStretch(); bar.addWidget(self.info_label)
        layout.addLayout(bar)

    # --- Public API ---
    def set_video(self, path: str):
        if not os.path.exists(path):
            return False
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            return False
        self.video_path = path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._video_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        self._video_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        self._recalc_target_height()
        self.current_frame = 0
        self.slider.setRange(0, max(0, self.total_frames-1))
        self._update_frame()
        self._update_info()
        return True

    def toggle_play(self):
        if not self.cap:
            return
        if self._playing:
            self._playing = False
            self.timer.stop()
            self.play_btn.setText('播放')
        else:
            self._playing = True
            if self.fps <= 0:
                self.fps = 30.0
            # 记录起点，用基于时间的调度避免单帧耗时导致整体变慢
            self._play_start_time = perf_counter()
            self._play_start_frame = self.current_frame
            # 使用较小间隔（10ms）高频检查，内部按时间计算应到达的帧索引
            self.timer.start(10)
            self.play_btn.setText('暂停')

    # --- Internal ---
    def _advance(self):
        if not (self.cap and self._playing and self.fps > 0):
            return
        # 计算理论应该显示的帧号
        elapsed = perf_counter() - (self._play_start_time or perf_counter())
        expected = int(self._play_start_frame + elapsed * self.fps)
        if expected >= self.total_frames:
            # 播放结束
            self.current_frame = self.total_frames - 1
            self.slider.blockSignals(True)
            self.slider.setValue(self.current_frame)
            self.slider.blockSignals(False)
            self._update_frame()
            self.toggle_play()
            return
        if expected != self.current_frame:
            # 跳过（catch-up）或前进到 expected
            self.current_frame = expected
            self.slider.blockSignals(True)
            self.slider.setValue(self.current_frame)
            self.slider.blockSignals(False)
            self._update_frame()
        self._update_info()

    def _on_slider(self, val: int):
        if not self.cap:
            return
        self.current_frame = val
        self._update_frame()
        self._update_info()
        if self._playing and self.fps > 0:
            # 重新基准时间，避免拖动后出现漂移
            self._play_start_time = perf_counter()
            self._play_start_frame = self.current_frame

    def _update_frame(self):
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ok, frame = self.cap.read()
        if not ok:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        # 计算容器目标尺寸
        if self._auto_width:
            target_w = max(120, self.video_label.width())
        else:
            target_w = self._fixed_width
        target_h = self.video_label.height()
        if target_h <= 0:
            target_h = self._min_height
        scaled = pix.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        canvas = QPixmap(target_w, target_h)
        canvas.fill(Qt.black)
        from PyQt5.QtGui import QPainter
        p = QPainter(canvas)
        x_off = (target_w - scaled.width())//2
        y_off = (target_h - scaled.height())//2
        p.drawPixmap(x_off, y_off, scaled)
        p.end()
        self.video_label.setPixmap(canvas)

    # --- Layout helpers ---
    def _recalc_target_height(self):
        if not (self._video_w and self._video_h):
            return
        if self._auto_width:
            base_w = max(120, self.video_label.width() or self._fixed_width)
        else:
            base_w = self._fixed_width
        aspect_h = int(base_w * (self._video_h / self._video_w))
        target_h = min(max(aspect_h, self._min_height), self._max_height)
        self.video_label.setMinimumHeight(target_h)
        self.video_label.setMaximumHeight(target_h)
        if not self._auto_width:
            self.video_label.setMinimumWidth(self._fixed_width)
            self.video_label.setMaximumWidth(self._fixed_width)

    def unlock_auto_width(self):
        self._auto_width = True
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.video_label.setMinimumWidth(160)
        self.video_label.setMaximumWidth(16777215)
        self._recalc_target_height()
        self._update_frame()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._auto_width:
            self._recalc_target_height()
            self._update_frame()

    def _update_info(self):
        if not self.cap:
            self.info_label.setText('-- / --')
            return
        cur_t = self.current_frame / self.fps if self.fps > 0 else 0
        total_t = self.total_frames / self.fps if self.fps > 0 else 0
        def fmt(t):
            m = int(t//60); s = int(t%60)
            return f"{m:02d}:{s:02d}"
        self.info_label.setText(f"{fmt(cur_t)} / {fmt(total_t)}  {self.current_frame+1}/{self.total_frames}")

    def closeEvent(self, e):
        if self.cap:
            self.cap.release()
        e.accept()

__all__ = ['SimpleVideoPlayer']
