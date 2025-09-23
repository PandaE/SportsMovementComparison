import sys, os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame,
                             QProgressBar, QTextEdit, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QThread
from core.azure_blob_reader import AzureBlobReader
from ui.download_progress_dialog import DownloadProgressDialog
from ui.download_worker import DownloadWorker
from ui.new.simple_video_player import SimpleVideoPlayer
import cv2
from core.frame_extractors import PreconfiguredFrameExtractor, EvenlySpacedFrameExtractor
from core.new_evaluation.session import EvaluationSession
from core.new_evaluation.config_converter import convert
from core.new_evaluation.data_models import KeyframeSet, FrameRef
from core.new_evaluation.adapter import UIAdapter
from core.experimental.config.sport_configs import SportConfigs
from ui.new_results.results_window import ResultsWindow


# 兼容保留原 VideoLoadState / VideoMeta 以最小改动
class VideoLoadState:
    EMPTY = 'EMPTY'
    LOADING = 'LOADING'
    READY = 'READY'
    ERROR = 'ERROR'

class VideoMeta:
    def __init__(self, path: str, duration: float = None, fps: float = None, width: int = None, height: int = None, source: str = None):
        self.path = path
        self.duration = duration
        self.fps = fps
        self.width = width
        self.height = height
        self.source = source

# --- 简化状态枚举 ---
class PreparationState:
    IDLE = 'IDLE'
    DOWNLOADING_STD = 'DOWNLOADING_STD'
    PARSING_USER = 'PARSING_USER'
    PARSING_STD = 'PARSING_STD'
    EXTRACTING_KEYFRAMES = 'EXTRACTING_KEYFRAMES'
    READY = 'READY'
    BLOCKED = 'BLOCKED'

class MainWindowState:
    def __init__(self):
        self.sport = '羽毛球'
        self.action = '正手高远球'
        self.user_state = VideoLoadState.EMPTY
        self.std_state = VideoLoadState.EMPTY
        self.user_meta = None
        self.std_meta = None
        self.preparation = PreparationState.IDLE
        self.can_start = False

class RedesignedMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = MainWindowState()
        self.setWindowTitle('动作对比分析')
        self.resize(1280, 820)
        self._std_download_thread = None
        self._std_worker = None
        # 帧提取器实例
        self._std_extractor = PreconfiguredFrameExtractor()
        self._user_extractor = EvenlySpacedFrameExtractor()
        self._build_ui()
        self._wire_events()
        self._update_all()

    # --- UI 构建 ---
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(18)

        # 标题区
        head = QVBoxLayout(); head.setSpacing(4)
        title = QLabel('动作对比分析')
        title.setStyleSheet('font-size:28px; font-weight:600; color:#1A2736;')
        desc = QLabel('请选择运动、动作，并提供标准视频与个人视频进行分析')
        desc.setStyleSheet('font-size:14px; color:#485463;')
        head.addWidget(title)
        head.addWidget(desc)
        root.addLayout(head)

        # 选择行
        sel_row = QHBoxLayout(); sel_row.setSpacing(12)
        self.sport_combo = QComboBox(); self.sport_combo.addItems(['羽毛球'])
        self.action_combo = QComboBox(); self.action_combo.addItems(['正手高远球'])
        sel_row.addWidget(self._labeled('运动', self.sport_combo))
        sel_row.addWidget(self._labeled('动作', self.action_combo))
        sel_row.addStretch()
        root.addLayout(sel_row)

        # 视频选择控制区（标准视频来自 Blob 下拉，个人视频本地文件）
        ctrl_row = QHBoxLayout(); ctrl_row.setSpacing(16)
        # 标准视频下拉
        self.standard_combo = QComboBox(); self.standard_combo.setMinimumWidth(260)
        self.standard_combo.setEditable(False)
        self.standard_refresh_btn = QPushButton('刷新标准视频列表')
        self.load_standard_btn = QPushButton('加载选中标准视频')
        ctrl_row.addWidget(QLabel('标准视频:'))
        ctrl_row.addWidget(self.standard_combo)
        ctrl_row.addWidget(self.standard_refresh_btn)
        ctrl_row.addWidget(self.load_standard_btn)
        # 个人视频按钮
        self.user_select_btn = QPushButton('选择个人视频')
        ctrl_row.addStretch()
        ctrl_row.addWidget(self.user_select_btn)
        root.addLayout(ctrl_row)

        # 视频显示区域
        vids = QHBoxLayout(); vids.setSpacing(20)
        self.standard_player = SimpleVideoPlayer()
        self.user_player = SimpleVideoPlayer()
        vids.addWidget(self.standard_player, 1)
        vids.addWidget(self.user_player, 1)
        root.addLayout(vids)

    # （已移除校验条，留白可后续放提示或统计）

        # 准备状态卡片
        prep_card = QFrame(); prep_card.setStyleSheet('QFrame { background:white; border:1px solid #E2E6EB; border-radius:16px; }')
        pc_lay = QVBoxLayout(prep_card); pc_lay.setContentsMargins(16,14,16,14); pc_lay.setSpacing(8)
        self.step_label = QLabel('当前步骤：空闲')
        self.step_label.setStyleSheet('font-size:14px; color:#1A2736;')
        pc_lay.addWidget(self.step_label)
        self.prep_progress = QProgressBar(); self.prep_progress.setFixedHeight(10); self.prep_progress.setTextVisible(False)
        pc_lay.addWidget(self.prep_progress)
        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setFixedHeight(120)
        self.log.setStyleSheet('font-size:12px; background:#F8F9FB; border:1px solid #E2E6EB; border-radius:8px;')
        pc_lay.addWidget(self.log)
        root.addWidget(prep_card)

        # 底部操作区
        foot = QHBoxLayout(); foot.setSpacing(12)
        self.hint_label = QLabel('提示：请选择标准视频和个人视频')
        self.hint_label.setStyleSheet('font-size:13px; color:#5B6470;')
        foot.addWidget(self.hint_label)
        foot.addStretch()
    # 开始按钮移除自动流程（保留占位可后续添加其他操作）
        root.addLayout(foot)

    def _labeled(self, text, widget):
        box = QVBoxLayout(); box.setSpacing(4)
        lab = QLabel(text); lab.setStyleSheet('font-size:13px; font-weight:600; color:#1A2736;')
        wrap = QFrame(); wrap_l = QVBoxLayout(wrap); wrap_l.setContentsMargins(0,0,0,0); wrap_l.addWidget(widget)
        widget.setFixedHeight(34)
        widget.setStyleSheet('QComboBox { background:white; border:1px solid #CED4DA; border-radius:8px; padding:2px 8px; }')
        box.addWidget(lab)
        box.addWidget(wrap)
        cont = QFrame(); lay = QVBoxLayout(cont); lay.setContentsMargins(0,0,0,0); lay.addLayout(box)
        return cont

    # --- 事件绑定 ---
    def _wire_events(self):
        self.standard_refresh_btn.clicked.connect(self._load_standard_list)
        self.load_standard_btn.clicked.connect(self._on_load_standard_clicked)
        self.user_select_btn.clicked.connect(self._choose_user_local)
        self.standard_combo.currentIndexChanged.connect(self._on_standard_selection_changed)
    # 自动流程无需按钮
        # 初始化加载一次标准视频列表
        QTimer.singleShot(100, self._load_standard_list)

    # --- 状态更新 ---
    def _update_all(self):
        self._recalc_can_start()

    def _recalc_can_start(self):
        # 现在点击“开始分析”之前不进入 READY，只要两个视频都解析完成即可允许点击
        can = (self.state.user_state == VideoLoadState.READY and
               self.state.std_state == VideoLoadState.READY)
        self.state.can_start = can
    # 自动流程不控制按钮
        if not can:
            if self.state.user_state != VideoLoadState.READY:
                self.hint_label.setText('提示：请提供个人视频')
            elif self.state.std_state != VideoLoadState.READY:
                self.hint_label.setText('提示：请提供标准视频')
            else:
                self.hint_label.setText('提示：准备中...')
        else:
            self.hint_label.setText('可以开始分析')

    # --- 处理选择 ---
    def _on_standard_selected(self, path: str, source_label: str = '云端缓存'):
        self._log(f'选择标准视频: {path}')
        self.state.std_state = VideoLoadState.LOADING
        self.step_label.setText('当前步骤：解析标准视频')
        self.state.preparation = PreparationState.PARSING_STD
        self._parse_video(path, is_standard=True, source=source_label)
        self._recalc_can_start()

    def _on_user_selected(self, path: str):
        self._log(f'选择个人视频: {path}')
        self.state.user_state = VideoLoadState.LOADING
        self.step_label.setText('当前步骤：解析个人视频')
        self.state.preparation = PreparationState.PARSING_USER
        self._parse_video(path, is_standard=False, source='本地')
        self._recalc_can_start()

    def _choose_user_local(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择个人视频', '', 'Video Files (*.mp4 *.mov *.avi *.mkv)')
        if file_path:
            self._on_user_selected(file_path)

    def _load_standard_list(self):
        # 列出 blob 名称
        self.standard_combo.clear()
        sport_key = 'badminton'; action_key = 'clear'
        folder = f"{sport_key}/{action_key}/"
        try:
            reader = AzureBlobReader()
            blobs = reader.list_files(folder)
            # 仅保留视频扩展
            videos = [b for b in blobs if b.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
            base_names = [os.path.basename(v) for v in videos]
            self._standard_blob_map = {bn: v for bn, v in zip(base_names, videos)}
            self.standard_combo.addItems(base_names)
            self._log(f'加载标准视频列表，共 {len(base_names)} 个')
        except Exception as e:
            self._log(f'加载标准列表失败: {e}')

    def _on_standard_selection_changed(self, idx: int):
        # 选择变化暂不立即下载，等待用户点击“加载”按钮
        pass

    def _on_load_standard_clicked(self):
        name = self.standard_combo.currentText()
        if not name:
            return
        blob_path = self._standard_blob_map.get(name)
        if not blob_path:
            return
        cache_path = self._cache_path(blob_path)
        if os.path.exists(cache_path):
            self._on_standard_selected(cache_path)
            self.standard_player.set_video(cache_path)
            return
        # 下载
        reader = AzureBlobReader()
        progress_dialog = DownloadProgressDialog(self)
        thread = QThread()
        worker = DownloadWorker(reader, blob_path, cache_path)
        worker.moveToThread(thread)
        worker.progress.connect(progress_dialog.set_progress)
        def finished(cp):
            progress_dialog.close()
            thread.quit(); thread.wait(); worker.deleteLater(); thread.deleteLater()
            self.standard_player.set_video(cp)
            self._on_standard_selected(cp)
        def error(msg):
            progress_dialog.close()
            self._log(f'标准视频下载失败: {msg}')
            thread.quit(); thread.wait(); worker.deleteLater(); thread.deleteLater()
        worker.finished.connect(finished)
        worker.error.connect(error)
        thread.started.connect(worker.run)
        progress_dialog.show()
        thread.start()

    def _cache_path(self, blobname: str) -> str:
        cache_dir = os.path.join(os.getcwd(), 'standard_videos_cache')
        local_path = os.path.join(cache_dir, blobname)
        parent_dir = os.path.dirname(local_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)
        return local_path

    # --- 真实解析（OpenCV 获取元数据） + 模拟进度条 ---
    def _parse_video(self, path: str, is_standard: bool, source: str):
        # 解析放到单次回调即可（视频较短），这里仍做一个短进度动画
        steps = 15
        progress = {'v':0}
        def tick():
            progress['v'] += 1
            pct = int(progress['v']/steps*100)
            if progress['v'] >= steps:
                self._parse_timer.stop()
                meta = self._read_video_meta(path, source)
                if not meta:
                    self._log('视频元数据读取失败')
                    if is_standard:
                        self.state.std_state = VideoLoadState.ERROR
                    else:
                        self.state.user_state = VideoLoadState.ERROR
                    return
                # 设置播放
                if is_standard:
                    self.standard_player.set_video(path)
                else:
                    self.user_player.set_video(path)
                if is_standard:
                    self.state.std_state = VideoLoadState.READY
                    self.state.std_meta = meta
                else:
                    self.state.user_state = VideoLoadState.READY
                    self.state.user_meta = meta
                self._log(('标准' if is_standard else '个人') + '视频解析完成，等待开始分析')
                # 不设置 READY，等待用户点击开始分析来触发后续流程
                if (self.state.user_state == VideoLoadState.READY and
                        self.state.std_state == VideoLoadState.READY):
                    self.step_label.setText('当前步骤：可开始')
                else:
                    self.step_label.setText('当前步骤：等待另一个视频')
                self._recalc_can_start()
                self._auto_run_pipeline()
        self._parse_timer = QTimer(self)
        self._parse_timer.timeout.connect(tick)
        self._parse_timer.start(80)

    def _read_video_meta(self, path: str, source: str) -> VideoMeta:
        try:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                return None
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            duration = frame_count / fps if fps > 0 else None
            cap.release()
            return VideoMeta(path=path, duration=duration, fps=fps, width=width, height=height, source=source)
        except Exception as e:
            self._log(f'读取视频失败: {e}')
            return None

    # 去除校验/关键帧模拟：相关函数删除

    def _log(self, line: str):
        self.log.append(line)

    # --- 开始分析 ---
    @pyqtSlot()
    def _auto_run_pipeline(self):
        if self.state.preparation == PreparationState.READY:
            return
        if not (self.state.user_state == VideoLoadState.READY and self.state.std_state == VideoLoadState.READY):
            return
        self._log('开始自动关键帧提取...')
        self.step_label.setText('当前步骤：关键帧提取')
        self.prep_progress.setRange(0,0)
        timer = QTimer(self)
        def finish():
            timer.stop()
            try:
                sport = 'Badminton'
                action = 'Forehand Clear'
                std_path = self.state.std_meta.path if self.state.std_meta else None
                user_path = self.state.user_meta.path if self.state.user_meta else None
                std_frames = self._std_extractor.extract('badminton', 'clear', std_path) if std_path else []
                user_frames = self._user_extractor.extract('badminton', 'clear', user_path) if user_path else []
                self._log(f'标准关键帧({len(std_frames)}): ' + ', '.join(f"{f.label or f.frame_index}@{f.frame_index}" for f in std_frames))
                self._log(f'用户关键帧({len(user_frames)}): ' + ', '.join(f"{f.label or f.frame_index}@{f.frame_index}" for f in user_frames))
                # 构造 KeyframeSet
                # 映射策略：预配置帧按顺序映射到 experimental config stages (如果存在)
                old_cfg = SportConfigs.get_config(sport, action)
                new_cfg = convert(old_cfg)
                stage_keys = [s.key for s in new_cfg.stages]
                def map_frames(frames):
                    m = {}
                    for i, sk in enumerate(stage_keys):
                        if i < len(frames):
                            f = frames[i]
                            m[sk] = FrameRef(user_path if frames is user_frames else std_path, f.frame_index)
                    return m
                keyframes = KeyframeSet(user=map_frames(user_frames), standard=map_frames(std_frames))
                session = EvaluationSession(new_cfg, keyframes, user_video=user_path or '', standard_video=std_path or '')
                self._log('执行评估...')
                session.evaluate()
                state = session.get_state()
                vm = UIAdapter.to_vm(state, keyframes.user, keyframes.standard)
                self._log('评估完成，打开结果窗口')
                self._results_win = ResultsWindow(vm, session=session, keyframes=keyframes, adapter=UIAdapter)
                self._results_win.show()
                self.state.preparation = PreparationState.READY
                self.prep_progress.setRange(0,1); self.prep_progress.setValue(1)
                self.step_label.setText('当前步骤：完成')
            except Exception as e:
                self._log(f'自动流程失败: {e}')
                self.state.preparation = PreparationState.BLOCKED
                self.prep_progress.setRange(0,1); self.prep_progress.setValue(0)
        timer.setSingleShot(True)
        timer.timeout.connect(finish)
        timer.start(800)

# --- 入口 ---
def main():
    app = QApplication(sys.argv)
    w = RedesignedMainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
