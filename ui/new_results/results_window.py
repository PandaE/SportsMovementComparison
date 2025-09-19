from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QSlider
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from .view_models import ActionEvaluationVM, StageVM, MetricVM
from .frame_display import FrameDisplayWidget

# --- Styling helpers -------------------------------------------------------

def score_color(score: int) -> str:
    if score >= 85:
        return '#1B8D4B'
    if score >= 70:
        return '#E6A500'
    return '#C0392B'

STATUS_BG = {'ok': '#F2FFF7', 'warn': '#FFF9EC', 'bad': '#FFEDEB', 'na': '#F1F3F5'}
STATUS_FG = {'ok': '#1B8D4B', 'warn': '#C87F00', 'bad': '#B82E24', 'na': '#5B6470'}
STATUS_SYMBOL = {'ok': '✔', 'warn': '△', 'bad': '✖', 'na': '-'}

class ResultsWindow(QWidget):
    def __init__(self, vm: ActionEvaluationVM):
        super().__init__()
        self.vm = vm
        self._user_frame_widgets = []  # store user frame FrameDisplayWidget for global operations
        self._pose_enabled = False
        self.setWindowTitle('动作分析结果 (简化模型)')
        self.resize(1180, 860)
        self.build_ui()

    # --- Build root ------------------------------------------------------
    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(18)
        root.addLayout(self.build_header())
        root.addWidget(self.build_stages_scroll(), 1)
        # Button row between stage comparison and training guidance
        root.addLayout(self.build_controls_row())
        if self.vm.training:
            root.addWidget(self.build_training())

    # --- Header -----------------------------------------------------------
    def build_header(self):
        lay = QVBoxLayout()
        title = QLabel(f"{self.vm.sport} - {self.vm.action_name}")
        title.setStyleSheet('font-size:28px; font-weight:600; color:#1A2736;')
        lay.addWidget(title)

        line = QHBoxLayout()
        score_label = QLabel(str(self.vm.score))
        score_label.setStyleSheet(f"font-size:56px; font-weight:700; color:{score_color(self.vm.score)};")
        score_label.setFixedWidth(120)
        line.addWidget(score_label)

        summary_box = QVBoxLayout()
        refined = QLabel(self.vm.summary_refined or (self.vm.summary_raw or ''))
        refined.setStyleSheet('font-size:16px; color:#1A2736;')
        summary_box.addWidget(refined)
        summary_box.addWidget(self.build_progress_bar())
        line.addLayout(summary_box, 1)
        line.addStretch()
        lay.addLayout(line)
        return lay

    def build_progress_bar(self):
        bar_wrap = QFrame()
        bar_wrap.setStyleSheet('background:#E4E8EE; border-radius:8px; padding:4px;')
        inner = QHBoxLayout(bar_wrap)
        inner.setContentsMargins(4,2,4,2)
        for st in self.vm.stages:
            seg = QFrame()
            seg.setStyleSheet(f"background:{score_color(st.score)}; border-radius:5px;")
            seg.setFixedHeight(6)
            flex = max(1, int(st.score / 10))
            inner.addWidget(seg, flex)
        return bar_wrap

    # --- Stages -----------------------------------------------------------
    def build_stages_scroll(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        container = QFrame(); layout = QVBoxLayout(container)
        layout.setSpacing(24); layout.setContentsMargins(4,4,4,4)
        for s in self.vm.stages:
            layout.addWidget(self.build_stage_card(s))
        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    # --- Controls (pose toggle etc.) -----------------------------------
    def build_controls_row(self):
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0); row.setSpacing(12)
        pose_btn = self.small_button('显示姿态骨架')
        pose_btn.setCheckable(True)
        pose_btn.toggled.connect(lambda st: self._on_toggle_pose(st, pose_btn))
        row.addWidget(pose_btn)
        row.addStretch()
        return row

    def _on_toggle_pose(self, state: bool, btn: QPushButton):
        self._pose_enabled = state
        btn.setText('隐藏姿态骨架' if state else '显示姿态骨架')
        # Apply to all user frame widgets
        for w in self._user_frame_widgets:
            try:
                w.set_pose_enabled(state)
            except Exception:
                pass

    def build_stage_card(self, stage: StageVM):
        card = QFrame(); card.setStyleSheet('QFrame { background:white; border:1px solid #E2E6EB; border-radius:16px; }')
        lay = QVBoxLayout(card); lay.setContentsMargins(20,16,20,16); lay.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel(f"{stage.name} | {stage.score} 分")
        title.setStyleSheet(f"font-size:20px; font-weight:600; color:{score_color(stage.score)};")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.small_button('调整帧'))
        lay.addLayout(header)

        # Frames (actual display widget w/ caching & optional slider)
        frame_row = QHBoxLayout(); frame_row.setSpacing(16)
        frame_row.addWidget(self.frame_widget(stage.user_frame, allow_adjust=True, label_text='用户关键帧', collect_user=True), 1)
        frame_row.addWidget(self.frame_widget(stage.standard_frame, allow_adjust=False, label_text='标准关键帧'), 1)
        lay.addLayout(frame_row)

        # Metrics table
        lay.addWidget(self.metrics_table(stage.metrics))

        # Suggestion
        if stage.suggestion:
            sug = QLabel(f"改进建议：{stage.suggestion}")
            sug.setWordWrap(True)
            sug.setStyleSheet('font-size:14px; color:#2F3B48; background:#F6F8FA; border-radius:8px; padding:8px 10px;')
            lay.addWidget(sug)
        return card

    # --- Metrics table ----------------------------------------------------
    def metrics_table(self, metrics):
        table = QTableWidget(len(metrics), 5)
        table.setHorizontalHeaderLabels(['指标', '用户', '标准', '偏差', '状态'])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(table.NoEditTriggers)
        table.setSelectionMode(table.NoSelection)
        table.setFixedHeight(42 + len(metrics)*34)
        for row, m in enumerate(metrics):
            diff = m.deviation
            # Format deviation with sign
            if diff is not None:
                if isinstance(diff, float):
                    diff_txt = f"{diff:+.2f}{m.unit or ''}"
                else:
                    diff_txt = f"{diff:+}{m.unit or ''}"
            else:
                diff_txt = '--'
            items = [
                QTableWidgetItem(m.name),
                QTableWidgetItem(self._fmt_val(m.user_value, m.unit)),
                QTableWidgetItem(self._fmt_val(m.std_value, m.unit)),
                QTableWidgetItem(diff_txt),
                QTableWidgetItem(STATUS_SYMBOL.get(m.status, '-'))
            ]
            for col, it in enumerate(items):
                it.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, it)
            bg = QColor(STATUS_BG.get(m.status, 'white'))
            fg = QColor(STATUS_FG.get(m.status, '#222'))
            for col in range(5):
                table.item(row, col).setBackground(bg)
                table.item(row, col).setForeground(fg)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setHighlightSections(False)
        table.setStyleSheet('QTableWidget { font-size:13px; }')
        return table

    def _fmt_val(self, v, unit):
        if v is None:
            return '--'
        if isinstance(v, float):
            return f"{v:.2f}{unit or ''}"
        return f"{v}{unit or ''}"

    # --- Training ----------------------------------------------------------
    def build_training(self):
        blk = QFrame(); blk.setStyleSheet('QFrame { background:white; border:1px solid #E2E6EB; border-radius:16px; }')
        lay = QVBoxLayout(blk); lay.setContentsMargins(20,16,20,16); lay.setSpacing(12)
        title = QLabel('训练指导'); title.setStyleSheet('font-size:20px; font-weight:600; color:#1A2736;')
        lay.addWidget(title)
        tri = self.vm.training
        if tri:
            lay.addLayout(self._training_row('关键问题', tri.key_issues))
            lay.addLayout(self._training_row('改进练习', tri.improvement_drills))
            lay.addLayout(self._training_row('下一步建议', tri.next_steps))
        return blk

    def _training_row(self, label, lines):
        row = QHBoxLayout(); row.setSpacing(6)
        tag = QLabel(label); tag.setStyleSheet('font-size:14px; font-weight:600; color:#1A2736; min-width:80px;')
        row.addWidget(tag)
        text = '\n'.join(f'• {l}' for l in lines)
        body = QLabel(text); body.setStyleSheet('font-size:13px; color:#2F3B48;')
        body.setWordWrap(True)
        row.addWidget(body, 1)
        return row

    # --- Helpers -----------------------------------------------------------
    def small_button(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(30)
        btn.setStyleSheet('QPushButton { background:#EEF2F6; border:none; border-radius:8px; padding:4px 12px; font-size:13px; }'
                          'QPushButton:hover { background:#E1E7ED; }')
        return btn

    def frame_widget(self, frame_ref, allow_adjust: bool, label_text: str, collect_user: bool = False):
        if frame_ref:
            w = FrameDisplayWidget(frame_ref.video_path, frame_ref.frame_index,
                                   allow_adjust=allow_adjust, use_cache=True, label=label_text,
                                   enable_pose=self._pose_enabled)
            if collect_user:
                self._user_frame_widgets.append(w)
            return w
        # fallback placeholder
        box = QFrame(); box.setMinimumSize(220,160)
        box.setStyleSheet('background:#0b152233; border:1px dashed #9AA4B1; border-radius:12px;')
        v = QVBoxLayout(box); v.setContentsMargins(4,4,4,4)
        lab = QLabel(label_text + '\n(无数据)'); lab.setAlignment(Qt.AlignCenter)
        lab.setStyleSheet('font-size:13px; color:#35404C;')
        v.addStretch(); v.addWidget(lab); v.addStretch()
        return box

__all__ = ['ResultsWindow']
