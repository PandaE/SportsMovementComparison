"""
settings_dialog.py
应用设置对话框
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, 
    QComboBox, QSpinBox, QLabel, QPushButton, QFormLayout,
    QSlider, QLineEdit, QTextEdit, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal


class SettingsDialog(QDialog):
    """设置对话框"""
    
    settings_changed = pyqtSignal(dict)  # 设置变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应用设置")
        self.setFixedSize(500, 400)

        # 默认设置
        self.settings = {
            'experimental_enabled': True,
            'pose_backend': 'mediapipe',
            'frame_extraction_method': 'uniform',
            'max_frames_per_video': 3,
            'quality_threshold': 0.6,
            'angle_tolerance': 10.0,
            'enable_frame_enhancement': True,
            'save_analysis_images': True,
            'auto_select_best_frames': True,
            'language': 'zh'  # 新增语言设置
        }

        # 文本映射（中英文）
        self.translations = {
            'zh': {
                'title': '应用设置',
                'basic_tab': '基本设置',
                'language_label': '显示语言:',
                'analysis_tab': '分析设置',
                'video_tab': '视频处理',
                'advanced_tab': '高级设置',
                'ok': '确定',
                'cancel': '取消',
                'reset': '重置为默认',
                'experimental': '启用高级姿态分析',
                'pose_backend': '姿态检测后端:',
                'angle_tolerance': '角度容差:',
                'frame_extraction': '提取方法:',
                'max_frames': '每视频最大帧数:',
                'auto_select': '自动选择最佳质量帧',
                'enhancement': '启用帧质量增强',
                'quality_threshold': '质量阈值:',
                'save_images': '保存分析图像',
                'output_settings': '输出设置',
                'system_info': '系统信息',
                'exp_group': '实验功能',
                'measure_group': '测量设置',
                'frame_group': '帧提取设置',
                'image_group': '图像处理',
            },
            'en': {
                'title': 'Settings',
                'basic_tab': 'Basic',
                'language_label': 'Language:',
                'analysis_tab': 'Analysis',
                'video_tab': 'Video',
                'advanced_tab': 'Advanced',
                'ok': 'OK',
                'cancel': 'Cancel',
                'reset': 'Reset to Default',
                'experimental': 'Enable Advanced Pose Analysis',
                'pose_backend': 'Pose Backend:',
                'angle_tolerance': 'Angle Tolerance:',
                'frame_extraction': 'Extraction Method:',
                'max_frames': 'Max Frames per Video:',
                'auto_select': 'Auto Select Best Frames',
                'enhancement': 'Enable Frame Enhancement',
                'quality_threshold': 'Quality Threshold:',
                'save_images': 'Save Analysis Images',
                'output_settings': 'Output Settings',
                'system_info': 'System Info',
                'exp_group': 'Experimental Features',
                'measure_group': 'Measurement Settings',
                'frame_group': 'Frame Extraction',
                'image_group': 'Image Processing',
            }
        }

        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 基本设置标签页
        self.create_basic_tab(self.tab_widget)
        # 分析设置标签页
        self.create_analysis_tab(self.tab_widget)
        # 视频处理标签页
        self.create_video_tab(self.tab_widget)
        # 高级设置标签页
        self.create_advanced_tab(self.tab_widget)

        layout.addWidget(self.tab_widget)

        # 按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton(self.tr_text('ok'))
        self.cancel_button = QPushButton(self.tr_text('cancel'))
        self.reset_button = QPushButton(self.tr_text('reset'))

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # 连接信号
        self.ok_button.clicked.connect(self.accept_settings)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset_to_defaults)

        self.setLayout(layout)

        self.update_language(self.settings['language'])

    def tr_text(self, key):
        lang = self.settings.get('language', 'zh')
        return self.translations.get(lang, self.translations['zh']).get(key, key)

    def create_basic_tab(self, tab_widget):
        """创建基本设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.language_combo = QComboBox()
        self.language_combo.addItems(['中文', 'English'])
        self.language_combo.setCurrentIndex(0 if self.settings['language'] == 'zh' else 1)
        form_layout.addRow(self.tr_text('language_label'), self.language_combo)

        layout.addLayout(form_layout)
        layout.addStretch()
        widget.setLayout(layout)
        tab_widget.addTab(widget, self.tr_text('basic_tab'))

        # 语言切换信号
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)

    def on_language_changed(self, idx):
        lang = 'zh' if idx == 0 else 'en'
        self.settings['language'] = lang
        self.update_language(lang)

    def update_language(self, lang):
        # 更新所有文本
        self.setWindowTitle(self.tr_text('title'))
        self.tab_widget.setTabText(0, self.tr_text('basic_tab'))
        self.tab_widget.setTabText(1, self.tr_text('analysis_tab'))
        self.tab_widget.setTabText(2, self.tr_text('video_tab'))
        self.tab_widget.setTabText(3, self.tr_text('advanced_tab'))
        self.ok_button.setText(self.tr_text('ok'))
        self.cancel_button.setText(self.tr_text('cancel'))
        self.reset_button.setText(self.tr_text('reset'))
        # 更新各tab内容（如label）
        self.update_tab_labels()

    def update_tab_labels(self):
        # 基本设置tab
        try:
            basic_tab = self.tab_widget.widget(0)
            form_layout = basic_tab.findChild(QFormLayout)
            if form_layout:
                form_layout.labelForField(self.language_combo).setText(self.tr_text('language_label'))
        except Exception:
            pass
        # 分析设置tab
        try:
            exp_group = self.tab_widget.widget(1).findChild(QGroupBox)
            if exp_group:
                exp_group.setTitle(self.tr_text('exp_group'))
            measure_group = self.tab_widget.widget(1).findChildren(QGroupBox)[1]
            if measure_group:
                measure_group.setTitle(self.tr_text('measure_group'))
            self.experimental_checkbox.setText(self.tr_text('experimental'))
            # 更新“姿态检测后端”标签
            exp_layout = exp_group.layout()
            if exp_layout:
                label = exp_layout.labelForField(self.pose_backend_combo)
                if label:
                    label.setText(self.tr_text('pose_backend'))
            # 更新“角度容差”标签
            measure_layout = measure_group.layout()
            if measure_layout:
                label = measure_layout.labelForField(self.angle_layout)
                if label:
                    label.setText(self.tr_text('angle_tolerance'))
            self.pose_backend_combo.setItemText(0, 'mediapipe')
            self.pose_backend_combo.setItemText(1, 'mock')
            self.angle_tolerance_label.setText(f"{self.angle_tolerance_slider.value():.1f}°")
        except Exception:
            pass
        # 视频处理tab
        try:
            frame_group = self.tab_widget.widget(2).findChild(QGroupBox)
            if frame_group:
                frame_group.setTitle(self.tr_text('frame_group'))
            image_group = self.tab_widget.widget(2).findChildren(QGroupBox)[1]
            if image_group:
                image_group.setTitle(self.tr_text('image_group'))
            # 更新“提取方法”标签
            frame_layout = frame_group.layout()
            if frame_layout:
                label = frame_layout.labelForField(self.extraction_method_combo)
                if label:
                    label.setText(self.tr_text('frame_extraction'))
                label2 = frame_layout.labelForField(self.max_frames_spinbox)
                if label2:
                    label2.setText(self.tr_text('max_frames'))
            image_layout = image_group.layout()
            if image_layout:
                label3 = image_layout.labelForField(self.quality_layout)
                if label3:
                    label3.setText(self.tr_text('quality_threshold'))
            self.extraction_method_combo.setItemText(0, 'uniform')
            self.extraction_method_combo.setItemText(1, 'middle')
            self.extraction_method_combo.setItemText(2, 'motion_based')
            self.auto_select_checkbox.setText(self.tr_text('auto_select'))
            self.enhancement_checkbox.setText(self.tr_text('enhancement'))
            self.quality_threshold_label.setText(f"{self.quality_threshold_slider.value()/100:.2f}")
        except Exception:
            pass
        # 高级设置tab
        try:
            output_group = self.tab_widget.widget(3).findChild(QGroupBox)
            if output_group:
                output_group.setTitle(self.tr_text('output_settings'))
            self.save_images_checkbox.setText(self.tr_text('save_images'))
            info_group = self.tab_widget.widget(3).findChildren(QGroupBox)[1]
            if info_group:
                info_group.setTitle(self.tr_text('system_info'))
                info_layout = info_group.layout()
                if info_layout:
                    info_text = info_group.findChild(QTextEdit)
                    if info_text:
                        try:
                            import cv2
                            opencv_version = cv2.__version__
                        except:
                            opencv_version = "未安装" if self.settings['language'] == 'zh' else "Not Installed"
                        try:
                            import mediapipe
                            mediapipe_version = mediapipe.__version__
                        except:
                            mediapipe_version = "未安装" if self.settings['language'] == 'zh' else "Not Installed"
                        if self.settings['language'] == 'zh':
                            info_content = f"""OpenCV 版本: {opencv_version}\nMediaPipe 版本: {mediapipe_version}\n实验模块状态: 可用\n支持的运动: 羽毛球\n支持的动作: 正手高远球"""
                        else:
                            info_content = f"""OpenCV Version: {opencv_version}\nMediaPipe Version: {mediapipe_version}\nExperimental Module: Available\nSupported Sports: Badminton\nSupported Actions: Forehand Clear"""
                        info_text.setText(info_content)
        except Exception:
            pass
    
    def create_analysis_tab(self, tab_widget):
        """创建分析设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 实验功能组
        exp_group = QGroupBox("实验功能")
        exp_layout = QFormLayout()
        
        self.experimental_checkbox = QCheckBox("启用高级姿态分析")
        self.experimental_checkbox.setChecked(self.settings['experimental_enabled'])
        exp_layout.addRow(self.experimental_checkbox)
        
        self.pose_backend_combo = QComboBox()
        self.pose_backend_combo.addItems(['mediapipe', 'mock'])
        self.pose_backend_combo.setCurrentText(self.settings['pose_backend'])
        exp_layout.addRow("姿态检测后端:", self.pose_backend_combo)
        
        exp_group.setLayout(exp_layout)
        layout.addWidget(exp_group)
        
        # 测量设置组
        measure_group = QGroupBox("测量设置")
        measure_layout = QFormLayout()
        
        self.angle_tolerance_slider = QSlider(Qt.Horizontal)
        self.angle_tolerance_slider.setMinimum(1)
        self.angle_tolerance_slider.setMaximum(30)
        self.angle_tolerance_slider.setValue(int(self.settings['angle_tolerance']))
        self.angle_tolerance_label = QLabel(f"{self.settings['angle_tolerance']:.1f}°")
        self.angle_tolerance_slider.valueChanged.connect(
            lambda v: self.angle_tolerance_label.setText(f"{v:.1f}°")
        )
        
        self.angle_layout = QHBoxLayout()
        self.angle_layout.addWidget(self.angle_tolerance_slider)
        self.angle_layout.addWidget(self.angle_tolerance_label)
        measure_layout.addRow("角度容差:", self.angle_layout)
        
        measure_group.setLayout(measure_layout)
        layout.addWidget(measure_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        tab_widget.addTab(widget, "分析设置")
    
    def create_video_tab(self, tab_widget):
        """创建视频处理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 帧提取设置组
        frame_group = QGroupBox("帧提取设置")
        frame_layout = QFormLayout()
        
        self.extraction_method_combo = QComboBox()
        self.extraction_method_combo.addItems(['uniform', 'middle', 'motion_based'])
        self.extraction_method_combo.setCurrentText(self.settings['frame_extraction_method'])
        frame_layout.addRow("提取方法:", self.extraction_method_combo)
        
        self.max_frames_spinbox = QSpinBox()
        self.max_frames_spinbox.setMinimum(1)
        self.max_frames_spinbox.setMaximum(10)
        self.max_frames_spinbox.setValue(self.settings['max_frames_per_video'])
        frame_layout.addRow("每视频最大帧数:", self.max_frames_spinbox)
        
        self.auto_select_checkbox = QCheckBox("自动选择最佳质量帧")
        self.auto_select_checkbox.setChecked(self.settings['auto_select_best_frames'])
        frame_layout.addRow(self.auto_select_checkbox)
        
        frame_group.setLayout(frame_layout)
        layout.addWidget(frame_group)
        
        # 图像处理设置组
        image_group = QGroupBox("图像处理")
        image_layout = QFormLayout()
        
        self.enhancement_checkbox = QCheckBox("启用帧质量增强")
        self.enhancement_checkbox.setChecked(self.settings['enable_frame_enhancement'])
        image_layout.addRow(self.enhancement_checkbox)
        
        self.quality_threshold_slider = QSlider(Qt.Horizontal)
        self.quality_threshold_slider.setMinimum(0)
        self.quality_threshold_slider.setMaximum(100)
        self.quality_threshold_slider.setValue(int(self.settings['quality_threshold'] * 100))
        self.quality_threshold_label = QLabel(f"{self.settings['quality_threshold']:.2f}")
        self.quality_threshold_slider.valueChanged.connect(
            lambda v: self.quality_threshold_label.setText(f"{v/100:.2f}")
        )
        
        self.quality_layout = QHBoxLayout()
        self.quality_layout.addWidget(self.quality_threshold_slider)
        self.quality_layout.addWidget(self.quality_threshold_label)
        image_layout.addRow("质量阈值:", self.quality_layout)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        tab_widget.addTab(widget, "视频处理")
    
    def create_advanced_tab(self, tab_widget):
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout()
        
        self.save_images_checkbox = QCheckBox("保存分析图像")
        self.save_images_checkbox.setChecked(self.settings['save_analysis_images'])
        output_layout.addRow(self.save_images_checkbox)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        
        try:
            import cv2
            opencv_version = cv2.__version__
        except:
            opencv_version = "未安装"
        
        try:
            import mediapipe
            mediapipe_version = mediapipe.__version__
        except:
            mediapipe_version = "未安装"
        
        info_content = f"""OpenCV 版本: {opencv_version}
MediaPipe 版本: {mediapipe_version}
实验模块状态: 可用
支持的运动: 羽毛球
支持的动作: 正手高远球"""
        
        info_text.setText(info_content)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        tab_widget.addTab(widget, "高级设置")
    
    def get_current_settings(self):
        """获取当前设置"""
        return {
            'experimental_enabled': self.experimental_checkbox.isChecked(),
            'pose_backend': self.pose_backend_combo.currentText(),
            'frame_extraction_method': self.extraction_method_combo.currentText(),
            'max_frames_per_video': self.max_frames_spinbox.value(),
            'quality_threshold': self.quality_threshold_slider.value() / 100.0,
            'angle_tolerance': float(self.angle_tolerance_slider.value()),
            'enable_frame_enhancement': self.enhancement_checkbox.isChecked(),
            'save_analysis_images': self.save_images_checkbox.isChecked(),
            'auto_select_best_frames': self.auto_select_checkbox.isChecked(),
            'language': 'zh' if self.language_combo.currentIndex() == 0 else 'en'
        }
    
    def apply_settings(self, settings_dict):
        """应用设置"""
        self.settings.update(settings_dict)

        # 更新界面控件
        self.experimental_checkbox.setChecked(self.settings['experimental_enabled'])
        self.pose_backend_combo.setCurrentText(self.settings['pose_backend'])
        self.max_frames_spinbox.setValue(self.settings['max_frames_per_video'])
        self.quality_threshold_slider.setValue(int(self.settings['quality_threshold'] * 100))
        self.angle_tolerance_slider.setValue(int(self.settings['angle_tolerance']))
        self.enhancement_checkbox.setChecked(self.settings['enable_frame_enhancement'])
        self.save_images_checkbox.setChecked(self.settings['save_analysis_images'])
        self.auto_select_checkbox.setChecked(self.settings['auto_select_best_frames'])
        self.language_combo.setCurrentIndex(0 if self.settings['language'] == 'zh' else 1)
        self.update_language(self.settings['language'])
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        default_settings = {
            'experimental_enabled': True,
            'pose_backend': 'mediapipe',
            'frame_extraction_method': 'uniform',
            'max_frames_per_video': 3,
            'quality_threshold': 0.6,
            'angle_tolerance': 10.0,
            'enable_frame_enhancement': True,
            'save_analysis_images': True,
            'auto_select_best_frames': True,
            'language': 'zh'
        }
        self.apply_settings(default_settings)
    
    def accept_settings(self):
        """接受设置并发出信号"""
        current_settings = self.get_current_settings()
        self.settings.update(current_settings)
        self.settings_changed.emit(self.settings)
        self.accept()


class QuickSettingsWidget(QWidget):
    """快速设置小部件（可嵌入主界面）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 实验模式开关
        self.experimental_checkbox = QCheckBox("高级分析")
        self.experimental_checkbox.setChecked(True)
        layout.addWidget(self.experimental_checkbox)
        
        # 设置按钮
        self.settings_button = QPushButton("设置...")
        self.settings_button.setMaximumWidth(60)
        layout.addWidget(self.settings_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_experimental_enabled(self, enabled):
        """设置实验模式状态"""
        self.experimental_checkbox.setChecked(enabled)
    
    def is_experimental_enabled(self):
        """获取实验模式状态"""
        return self.experimental_checkbox.isChecked()