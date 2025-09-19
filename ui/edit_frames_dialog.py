from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFormLayout
from PyQt5.QtCore import Qt
from localization.translation_keys import TK
from localization.i18n_manager import I18nManager

class EditFramesDialog(QDialog):
    def __init__(self, parent, stage_frames, video_total_frames_user=None, video_total_frames_standard=None):
        super().__init__(parent)
        self.i18n = I18nManager.instance()
        self.stage_frames = stage_frames  # { stage: { 'user': idx, 'standard': idx } }
        self.video_total_frames_user = video_total_frames_user
        self.video_total_frames_standard = video_total_frames_standard
        self.setWindowTitle(self._t(TK.UI.RESULTS.EDIT_FRAMES))
        self.inputs = {}
        self._build_ui()

    def _t(self, key):
        return self.i18n.t(key)

    def _build_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        for stage, frames in self.stage_frames.items():
            user_idx = frames.get('user', 0)
            std_idx = frames.get('standard', 0)
            row_widget = QHBoxLayout()
            user_edit = QLineEdit(str(user_idx))
            std_edit = QLineEdit(str(std_idx))
            user_edit.setFixedWidth(80)
            std_edit.setFixedWidth(80)
            row_widget.addWidget(QLabel(self._t(TK.UI.RESULTS.USER_FRAME_IDX)))
            row_widget.addWidget(user_edit)
            row_widget.addWidget(QLabel(self._t(TK.UI.RESULTS.STANDARD_FRAME_IDX)))
            row_widget.addWidget(std_edit)
            container = QVBoxLayout()
            container.addLayout(row_widget)
            w = QLabel(stage)
            form.addRow(w, self._wrap(row_widget))
            self.inputs[stage] = (user_edit, std_edit)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton(self._t(TK.UI.RESULTS.APPLY_CHANGES))
        # 使用通用的取消翻译（common.cancel），如果不存在则退回英文
        cancel_text = self.i18n.t('ui.common.cancel') or 'Cancel'
        cancel_btn = QPushButton(cancel_text)
        apply_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def _wrap(self, layout_obj):
        from PyQt5.QtWidgets import QWidget
        w = QWidget()
        w.setLayout(layout_obj)
        return w

    def get_result(self):
        result = {}
        for stage, (u_edit, s_edit) in self.inputs.items():
            try:
                u_val = int(u_edit.text())
                s_val = int(s_edit.text())
            except ValueError:
                QMessageBox.warning(self, 'Error', f'Invalid number for stage {stage}')
                return None
            result[stage] = {'user': u_val, 'standard': s_val}
        return result
