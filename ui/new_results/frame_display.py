from __future__ import annotations
import os, hashlib, tempfile
from typing import Optional, Callable, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None  # gracefully degrade

# Optional mediapipe pose
try:  # pragma: no cover - imported dynamically
    import mediapipe as mp  # type: ignore
    _MP_AVAILABLE = True
    mp_pose = mp.solutions.pose
except Exception:  # pragma: no cover
    mp_pose = None
    _MP_AVAILABLE = False


def _hash_video(path: str) -> str:
    return hashlib.md5(path.encode('utf-8')).hexdigest()[:10]


class FrameDisplayWidget(QWidget):
    """Display a single video frame given a video path and frame index.

    Features:
    - Optional frame extraction caching to speed repeated loads.
    - Optional slider to allow user selecting a different frame (if allow_adjust=True).
    - Graceful fallback when video / OpenCV is unavailable.
    """
    def __init__(self, video_path: Optional[str], frame_index: int = 0, *,
                 allow_adjust: bool = True, use_cache: bool = True,
                 label: str = '', on_frame_changed: Optional[Callable[[int], None]] = None,
                 enable_pose: bool = False):
        super().__init__()
        self.video_path = video_path
        self.current_index = frame_index
        self.allow_adjust = allow_adjust
        self.use_cache = use_cache
        self.on_frame_changed = on_frame_changed
        self.total_frames: Optional[int] = None
        self.enable_pose = enable_pose and _MP_AVAILABLE
        self._pose = None
        if self.enable_pose and mp_pose:
            try:
                self._pose = mp_pose.Pose(static_image_mode=True, model_complexity=1, enable_segmentation=False)
            except Exception:
                self._pose = None
                self.enable_pose = False
        self._build_ui(label)
        self._init_video_meta()
        self._load_and_show(self.current_index)

    # UI -----------------------------------------------------------------
    def _build_ui(self, label_text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4,4,4,4)
        layout.setSpacing(6)

        if label_text:
            lab = QLabel(label_text)
            lab.setAlignment(Qt.AlignCenter)
            lab.setStyleSheet('font-size:13px; font-weight:600; color:#1A2736;')
            layout.addWidget(lab)

        frame_box = QFrame()
        frame_box.setStyleSheet('QFrame { background:#0b152233; border:1px solid #CED3D9; border-radius:12px; }')
        vb = QVBoxLayout(frame_box)
        vb.setContentsMargins(6,6,6,6)
        self.image_label = QLabel('Loading...')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet('font-size:12px; color:#2F3B48;')
        self.image_label.setMinimumSize(200,140)
        vb.addWidget(self.image_label)
        layout.addWidget(frame_box)

        bottom_row = QHBoxLayout(); bottom_row.setContentsMargins(0,0,0,0)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setVisible(self.allow_adjust)
        self.slider.valueChanged.connect(self._on_slider)
        bottom_row.addWidget(self.slider, 1)
        self.frame_info_label = QLabel('--/--')
        self.frame_info_label.setStyleSheet('font-size:11px; color:#55606B; min-width:70px;')
        self.frame_info_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bottom_row.addWidget(self.frame_info_label)
        layout.addLayout(bottom_row)

    # Video meta ---------------------------------------------------------
    def _init_video_meta(self):
        if not self.video_path or not os.path.exists(self.video_path) or cv2 is None:
            self.total_frames = None
            self.slider.setEnabled(False)
            return
        cap = cv2.VideoCapture(self.video_path)
        if cap.isOpened():
            cnt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            self.total_frames = cnt if cnt > 0 else None
        cap.release()
        if self.total_frames:
            self.slider.setRange(0, self.total_frames - 1)
            self.slider.setValue(min(self.current_index, self.total_frames - 1))
            self._update_frame_info()
        else:
            self.slider.setEnabled(False)
            self._update_frame_info()

    # Loading ------------------------------------------------------------
    def _cache_path(self, idx: int) -> str:
        base = os.path.join(tempfile.gettempdir(), 'smc_frame_cache')
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, f"{_hash_video(self.video_path or 'none')}_{idx}.jpg")

    def _extract_frame(self, idx: int) -> Optional[str]:
        if not self.video_path or not os.path.exists(self.video_path) or cv2 is None:
            return None
        cache_file = self._cache_path(idx)
        if self.use_cache and os.path.exists(cache_file):
            return cache_file
        cap = cv2.VideoCapture(self.video_path)
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                return None
            # Save to cache
            if self.use_cache:
                cv2.imwrite(cache_file, frame)
                return cache_file
            # Non-cached: write temp unique path
            temp_path = self._cache_path(idx) + '.tmp.jpg'
            cv2.imwrite(temp_path, frame)
            return temp_path
        finally:
            cap.release()

    def _draw_pose(self, image_bgr):
        if not (self.enable_pose and self._pose and mp_pose):
            return image_bgr
        try:
            import numpy as np  # local import to avoid hard dep at top
        except Exception:
            return image_bgr
        h, w = image_bgr.shape[:2]
        # mediapipe expects RGB
        results = None
        try:
            results = self._pose.process(image_bgr[:,:,::-1])
        except Exception:
            return image_bgr
        if not results or not results.pose_landmarks:
            return image_bgr
        lm = results.pose_landmarks.landmark
        pts = []
        for p in lm:
            if 0 <= p.x <= 1 and 0 <= p.y <= 1:
                pts.append((int(p.x * w), int(p.y * h)))
            else:
                pts.append(None)
        # Define simple skeleton pairs (subset)
        pairs: List[Tuple[int,int]] = [
            (11,13),(13,15),(12,14),(14,16), # arms
            (11,12), (23,24), # shoulders-hips
            (23,25),(25,27),(24,26),(26,28), # legs
            (27,29),(29,31),(28,30),(30,32)  # lower legs
        ]
        for a,b in pairs:
            if a < len(pts) and b < len(pts) and pts[a] and pts[b]:
                cv2.line(image_bgr, pts[a], pts[b], (0,255,0), 2)
        for p in pts:
            if p:
                cv2.circle(image_bgr, p, 3, (0,140,255), -1)
        return image_bgr

    def _load_and_show(self, idx: int):
        path = self._extract_frame(idx)
        if path and os.path.exists(path):
            pix = QPixmap(path)
            if not pix.isNull():
                if self.enable_pose and cv2 is not None:
                    # Re-load original frame to draw landmarks (avoid double JPEG compression artifacts if possible)
                    frame = cv2.imread(path)
                    if frame is not None:
                        frame = self._draw_pose(frame)
                        # convert to QImage
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb.shape
                        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
                        pix = QPixmap.fromImage(qimg)
                scaled = pix.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled)
                self.image_label.setText('')
                self._update_frame_info()
                return
        # Fallback
        if not self.video_path:
            self.image_label.setText('No Video')
        elif cv2 is None:
            self.image_label.setText('Missing OpenCV')
        else:
            self.image_label.setText('Failed to Load Frame')
        self._update_frame_info()

    # Events --------------------------------------------------------------
    def _on_slider(self, value: int):
        if value == self.current_index:
            return
        self.current_index = value
        self._load_and_show(value)
        if self.on_frame_changed:
            self.on_frame_changed(value)

    # Public --------------------------------------------------------------
    def set_frame_index(self, idx: int):
        if self.total_frames and (idx < 0 or idx >= self.total_frames):
            return
        self.current_index = idx
        if self.allow_adjust:
            self.slider.blockSignals(True)
            self.slider.setValue(idx)
            self.slider.blockSignals(False)
        self._load_and_show(idx)

    def frame_index(self) -> int:
        return self.current_index

    def _update_frame_info(self):
        cur = self.current_index
        total = self.total_frames if self.total_frames is not None else 0
        if total <= 0:
            self.frame_info_label.setText(f"{cur}/--")
        else:
            self.frame_info_label.setText(f"{cur}/{total-1}")

    # Pose toggle --------------------------------------------------------
    def set_pose_enabled(self, enabled: bool):
        want = bool(enabled)
        if want and not _MP_AVAILABLE:
            self.enable_pose = False
            return
        if want and not self.enable_pose:
            # lazy init
            if mp_pose and self._pose is None:
                try:
                    self._pose = mp_pose.Pose(static_image_mode=True, model_complexity=1)
                except Exception:
                    self.enable_pose = False
                    return
            self.enable_pose = True
            self._load_and_show(self.current_index)
        elif not want and self.enable_pose:
            self.enable_pose = False
            self._load_and_show(self.current_index)

__all__ = ['FrameDisplayWidget']
