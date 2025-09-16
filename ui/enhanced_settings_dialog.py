"""
Enhanced settings dialog with internationalization support.
增强的设置对话框，支持国际化
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, 
    QComboBox, QSpinBox, QLabel, QPushButton, QFormLayout,
    QSlider, QTabWidget, QWidget, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from localization import I18nManager, TK


class EnhancedSettingsDialog(QDialog):
    """增强的设置对话框，使用新的国际化系统"""
    
    settings_changed = pyqtSignal(dict)  # 设置变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化国际化管理器
        self.i18n = I18nManager.instance()
        self.i18n.register_observer(self._on_language_changed)
        
        self.setFixedSize(500, 400)
        self.setModal(True)

        # 默认设置
        self.settings = {
            'experimental_enabled': True,
            'language': self.i18n.get_current_language(),
            'pose_backend': 'mediapipe',
            'angle_tolerance': 10.0,
            'max_frames_per_video': 3,
            'quality_threshold': 0.6,
            'enable_frame_enhancement': True,
            'save_analysis_images': True,
        }

        self._init_ui()
        self._update_texts()

    def tr(self, key: str, **kwargs) -> str:
        """翻译函数 - 使用备用名称避免冲突"""
        return self.i18n.t(key, **kwargs)
    
    def translate(self, key: str, **kwargs) -> str:
        """翻译函数的备用名称"""
        return self.i18n.t(key, **kwargs)
    
    def _on_language_changed(self):
        """语言变更回调"""
        self._update_texts()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 基本设置标签页
        self._create_basic_tab()
        # 分析设置标签页
        self._create_analysis_tab()
        # 高级设置标签页
        self._create_advanced_tab()

        layout.addWidget(self.tab_widget)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.reset_button = QPushButton()
        self.cancel_button = QPushButton()
        self.ok_button = QPushButton()

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # 连接信号
        self.ok_button.clicked.connect(self._accept_settings)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self._reset_to_defaults)

        self.setLayout(layout)

    def _create_basic_tab(self):
        """创建基本设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 语言设置组
        language_group = QGroupBox()
        form_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        # 使用I18nManager的支持语言列表
        supported_langs = self.i18n.get_supported_languages()
        for lang_code, lang_name in supported_langs.items():
            self.language_combo.addItem(lang_name, lang_code)
        
        # 设置当前语言
        current_lang = self.i18n.get_current_language()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
        
        self.language_label = QLabel()
        form_layout.addRow(self.language_label, self.language_combo)
        
        language_group.setLayout(form_layout)
        layout.addWidget(language_group)

        layout.addStretch()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "")  # 标题将在_update_texts中设置

        # 语言切换信号
        self.language_combo.currentIndexChanged.connect(self._on_language_combo_changed)

    def _create_analysis_tab(self):
        """创建分析设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 实验功能组
        self.exp_group = QGroupBox()
        exp_layout = QFormLayout()
        
        self.experimental_checkbox = QCheckBox()
        self.experimental_checkbox.setChecked(self.settings['experimental_enabled'])
        exp_layout.addRow(self.experimental_checkbox)
        
        self.pose_backend_combo = QComboBox()
        self.pose_backend_combo.addItems(['mediapipe', 'mock'])
        self.pose_backend_combo.setCurrentText(self.settings['pose_backend'])
        self.pose_backend_label = QLabel()
        exp_layout.addRow(self.pose_backend_label, self.pose_backend_combo)
        
        self.exp_group.setLayout(exp_layout)
        layout.addWidget(self.exp_group)
        
        # 测量设置组
        self.measure_group = QGroupBox()
        measure_layout = QFormLayout()
        
        # 角度容差设置
        angle_widget = QWidget()
        angle_layout = QHBoxLayout()
        angle_layout.setContentsMargins(0, 0, 0, 0)
        
        self.angle_tolerance_slider = QSlider(Qt.Horizontal)
        self.angle_tolerance_slider.setMinimum(1)
        self.angle_tolerance_slider.setMaximum(30)
        self.angle_tolerance_slider.setValue(int(self.settings['angle_tolerance']))
        
        self.angle_tolerance_label = QLabel(f"{self.settings['angle_tolerance']:.1f}°")
        self.angle_tolerance_slider.valueChanged.connect(
            lambda v: self.angle_tolerance_label.setText(f"{v:.1f}°")
        )
        
        angle_layout.addWidget(self.angle_tolerance_slider)
        angle_layout.addWidget(self.angle_tolerance_label)
        angle_widget.setLayout(angle_layout)
        
        self.angle_label = QLabel()
        measure_layout.addRow(self.angle_label, angle_widget)
        
        self.measure_group.setLayout(measure_layout)
        layout.addWidget(self.measure_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "")  # 标题将在_update_texts中设置

    def _create_advanced_tab(self):
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 输出设置组
        self.output_group = QGroupBox()
        output_layout = QFormLayout()
        
        self.save_images_checkbox = QCheckBox()
        self.save_images_checkbox.setChecked(self.settings['save_analysis_images'])
        output_layout.addRow(self.save_images_checkbox)
        
        self.output_group.setLayout(output_layout)
        layout.addWidget(self.output_group)
        
        # 系统信息
        self.info_group = QGroupBox()
        info_layout = QVBoxLayout()
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        
        info_layout.addWidget(self.info_text)
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "")  # 标题将在_update_texts中设置

    def _update_texts(self):
        """更新所有文本"""
        # 窗口标题
        self.setWindowTitle(self.translate(TK.UI.Settings.TITLE))
        
        # 标签页标题
        self.tab_widget.setTabText(0, self.translate('ui.settings.basic_tab'))
        self.tab_widget.setTabText(1, self.translate('ui.settings.analysis_tab'))
        self.tab_widget.setTabText(2, self.translate('ui.settings.advanced_tab'))
        
        # 按钮文本
        self.ok_button.setText(self.translate(TK.UI.Settings.OK))
        self.cancel_button.setText(self.translate(TK.UI.Settings.CANCEL))
        self.reset_button.setText(self.translate('ui.settings.reset'))
        
        # 基本设置标签页
        self.language_label.setText(self.translate(TK.UI.Settings.LANGUAGE))
        
        # 分析设置标签页
        self.exp_group.setTitle(self.translate('ui.settings.exp_group'))
        self.experimental_checkbox.setText(self.translate('ui.settings.experimental'))
        self.pose_backend_label.setText(self.translate('ui.settings.pose_backend'))
        
        self.measure_group.setTitle(self.translate('ui.settings.measure_group'))
        self.angle_label.setText(self.translate('ui.settings.angle_tolerance'))
        
        # 高级设置标签页
        self.output_group.setTitle(self.translate('ui.settings.output_settings'))
        self.save_images_checkbox.setText(self.translate('ui.settings.save_images'))
        self.info_group.setTitle(self.translate('ui.settings.system_info'))
        
        # 更新系统信息
        self._update_system_info()

    def _update_system_info(self):
        """更新系统信息"""
        try:
            import cv2
            opencv_version = cv2.__version__
        except ImportError:
            opencv_version = self.translate("messages.errors.not_installed")
        
        try:
            import mediapipe
            mediapipe_version = mediapipe.__version__
        except ImportError:
            mediapipe_version = self.translate("messages.errors.not_installed")
        
        info_content = f"""OpenCV: {opencv_version}
MediaPipe: {mediapipe_version}
{self.translate('ui.settings.exp_status')}: {self.translate('ui.common.available')}
{self.translate('analysis.sports.supported')}: {self.translate('analysis.sports.badminton')}
{self.translate('analysis.actions.supported')}: {self.translate('analysis.actions.clear_shot')}"""
        
        self.info_text.setText(info_content)

    def _on_language_combo_changed(self, index):
        """语言下拉框变更处理"""
        lang_code = self.language_combo.itemData(index)
        if lang_code and lang_code != self.i18n.get_current_language():
            self.i18n.set_language(lang_code)
            self.settings['language'] = lang_code

    def get_current_settings(self):
        """获取当前设置"""
        return {
            'experimental_enabled': self.experimental_checkbox.isChecked(),
            'language': self.language_combo.itemData(self.language_combo.currentIndex()),
            'pose_backend': self.pose_backend_combo.currentText(),
            'angle_tolerance': float(self.angle_tolerance_slider.value()),
            'save_analysis_images': self.save_images_checkbox.isChecked(),
        }

    def apply_settings(self, settings_dict):
        """应用设置"""
        self.settings.update(settings_dict)

        # 更新界面控件
        self.experimental_checkbox.setChecked(self.settings['experimental_enabled'])
        self.pose_backend_combo.setCurrentText(self.settings['pose_backend'])
        self.angle_tolerance_slider.setValue(int(self.settings['angle_tolerance']))
        self.save_images_checkbox.setChecked(self.settings['save_analysis_images'])
        
        # 更新语言设置
        lang_code = self.settings['language']
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == lang_code:
                self.language_combo.setCurrentIndex(i)
                break
        
        if lang_code != self.i18n.get_current_language():
            self.i18n.set_language(lang_code)

    def _reset_to_defaults(self):
        """重置为默认设置"""
        default_settings = {
            'experimental_enabled': True,
            'language': 'zh_CN',
            'pose_backend': 'mediapipe',
            'angle_tolerance': 10.0,
            'save_analysis_images': True,
        }
        self.apply_settings(default_settings)

    def _accept_settings(self):
        """接受设置并发出信号"""
        current_settings = self.get_current_settings()
        self.settings.update(current_settings)
        self.settings_changed.emit(self.settings)
        self.accept()