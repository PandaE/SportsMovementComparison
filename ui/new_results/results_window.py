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
    def __init__(self, vm: ActionEvaluationVM, session=None, keyframes=None, adapter=None):
        super().__init__()
        self.vm = vm
        self._session = session  # optional EvaluationSession for dynamic recompute
        self._keyframes = keyframes  # KeyframeSet for updating indices
        self._adapter = adapter  # UIAdapter to rebuild VM
        self._pending_indices = {}  # stage_key -> pending user frame index (not yet applied)
        self._user_frame_widgets = []  # store user frame FrameDisplayWidget for global operations
        self._pose_enabled = False
        self._root_layout = None
        self._stages_container_layout = None
        self._stages_scroll = None
        self._training_widget = None
        self.setWindowTitle('Action Analysis Results (Simplified Model)')
        self.resize(1180, 860)
        self.build_ui()

    # --- Build root ------------------------------------------------------
    def build_ui(self):
        if self._root_layout is not None:
            # Already built; rebuild dynamic parts only
            self._rebuild_stages()
            self._rebuild_training()
            return
        root = QVBoxLayout(self)
        self._root_layout = root
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(18)
        root.addLayout(self.build_header())
        scroll, layout = self.build_stages_scroll()
        self._stages_scroll = scroll
        self._stages_container_layout = layout
        root.addWidget(scroll, 1)
        # Button row between stage comparison and training guidance
        root.addLayout(self.build_controls_row())
        if self.vm.training:
            self._training_widget = self.build_training()
            root.addWidget(self._training_widget)

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
        return scroll, layout

    # --- Controls (pose toggle etc.) -----------------------------------
    def build_controls_row(self):
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0); row.setSpacing(12)
        pose_btn = self.small_button('Show Pose Skeleton')
        pose_btn.setCheckable(True)
        pose_btn.toggled.connect(lambda st: self._on_toggle_pose(st, pose_btn))
        row.addWidget(pose_btn)
        row.addStretch()
        return row

    def _on_toggle_pose(self, state: bool, btn: QPushButton):
        self._pose_enabled = state
        btn.setText('Hide Pose Skeleton' if state else 'Show Pose Skeleton')
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
        title = QLabel(f"{stage.name} | {stage.score} pts")
        title.setStyleSheet(f"font-size:20px; font-weight:600; color:{score_color(stage.score)};")
        header.addWidget(title)
        header.addStretch()
        adj_btn = self.small_button('Adjust Frame')
        adj_btn.clicked.connect(lambda _, sk=stage.key: self._confirm_recompute(sk))
        header.addWidget(adj_btn)
        lay.addLayout(header)

        # Frames (actual display widget w/ caching & optional slider)
        frame_row = QHBoxLayout(); frame_row.setSpacing(16)
        frame_row.addWidget(self.frame_widget(stage.user_frame, allow_adjust=True, label_text='User Key Frame', collect_user=True, stage_key=stage.key), 1)
        frame_row.addWidget(self.frame_widget(stage.standard_frame, allow_adjust=False, label_text='Standard Key Frame'), 1)
        lay.addLayout(frame_row)

        # Metrics table
        lay.addWidget(self.metrics_table(stage.metrics))

        # Suggestion
        if stage.suggestion:
            sug = QLabel(f"Improvement Suggestion: {stage.suggestion}")
            sug.setWordWrap(True)
            sug.setStyleSheet('font-size:14px; color:#2F3B48; background:#F6F8FA; border-radius:8px; padding:8px 10px;')
            lay.addWidget(sug)
        return card

    # --- Metrics table ----------------------------------------------------
    def metrics_table(self, metrics):
        table = QTableWidget(len(metrics), 5)
        table.setHorizontalHeaderLabels(['Metric', 'User', 'Standard', 'Deviation', 'Status'])
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
        title = QLabel('Training Guidance'); title.setStyleSheet('font-size:20px; font-weight:600; color:#1A2736;')
        lay.addWidget(title)
        tri = self.vm.training
        if tri:
            lay.addLayout(self._training_row('Key Issues', tri.key_issues))
            lay.addLayout(self._training_row('Improvement Drills', tri.improvement_drills))
            lay.addLayout(self._training_row('Next Steps', tri.next_steps))
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

    def frame_widget(self, frame_ref, allow_adjust: bool, label_text: str, collect_user: bool = False, stage_key: str = ''):
        if frame_ref:
            cb = None
            if allow_adjust and stage_key:
                def _on_changed(idx: int, sk=stage_key):
                    # Just record; no engine calls
                    self._pending_indices[sk] = idx
                cb = _on_changed
            w = FrameDisplayWidget(frame_ref.video_path, frame_ref.frame_index,
                                   allow_adjust=allow_adjust, use_cache=True, label=label_text,
                                   on_frame_changed=cb, enable_pose=self._pose_enabled)
            if collect_user:
                self._user_frame_widgets.append(w)
            return w
        # fallback placeholder
        box = QFrame(); box.setMinimumSize(220,160)
        box.setStyleSheet('background:#0b152233; border:1px dashed #9AA4B1; border-radius:12px;')
        v = QVBoxLayout(box); v.setContentsMargins(4,4,4,4)
        lab = QLabel(label_text + '\n(No Data)'); lab.setAlignment(Qt.AlignCenter)
        lab.setStyleSheet('font-size:13px; color:#35404C;')
        v.addStretch(); v.addWidget(lab); v.addStretch()
        return box

    # --- Refresh logic -------------------------------------------------
    def _refresh_stage(self, stage_key: str, new_vm: ActionEvaluationVM):
        # Replace vm and only rebuild stages (simplified: full stages rebuild)
        self.vm = new_vm
        self._user_frame_widgets = []
        self._rebuild_stages()
        self._rebuild_training()

    def _rebuild_stages(self):
        if not self._stages_container_layout:
            return
        lay = self._stages_container_layout
        # remove all widgets except stretch at end
        # First remove stretch if present (will add back later)
        # Clear items
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        for s in self.vm.stages:
            lay.addWidget(self.build_stage_card(s))
        lay.addStretch()

    def _rebuild_training(self):
        # Remove existing training widget and rebuild based on vm.training
        if self._training_widget is not None:
            self._training_widget.setParent(None)
            self._training_widget = None
        if self.vm.training and self._root_layout is not None:
            self._training_widget = self.build_training()
            self._root_layout.addWidget(self._training_widget)

    def _confirm_recompute(self, stage_key: str):
        if not (self._session and self._adapter and self._keyframes):
            return
        try:
            # Apply pending index if any
            if stage_key in self._pending_indices:
                idx = self._pending_indices.pop(stage_key)
                # commit to session / keyframe set
                self._session.update_user_keyframe(stage_key, idx)
            # Now evaluate only that stage
            self._session.evaluate(stage_key=stage_key)
            state = self._session.get_state()
            new_vm = self._adapter.to_vm(state, self._keyframes.user, self._keyframes.standard)
            self._refresh_stage(stage_key, new_vm)
        except Exception:
            pass

__all__ = ['ResultsWindow']
