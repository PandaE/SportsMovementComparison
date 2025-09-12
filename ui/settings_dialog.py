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
            'auto_select_best_frames': True
        }
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 分析设置标签页
        self.create_analysis_tab(tab_widget)
        
        # 视频处理标签页
        self.create_video_tab(tab_widget)
        
        # 高级设置标签页
        self.create_advanced_tab(tab_widget)
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        self.reset_button = QPushButton("重置为默认")
        
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
        
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(self.angle_tolerance_slider)
        angle_layout.addWidget(self.angle_tolerance_label)
        measure_layout.addRow("角度容差:", angle_layout)
        
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
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(self.quality_threshold_slider)
        quality_layout.addWidget(self.quality_threshold_label)
        image_layout.addRow("质量阈值:", quality_layout)
        
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
            'auto_select_best_frames': self.auto_select_checkbox.isChecked()
        }
    
    def apply_settings(self, settings_dict):
        """应用设置"""
        self.settings.update(settings_dict)
        
        # 更新界面控件
        self.experimental_checkbox.setChecked(self.settings['experimental_enabled'])
        self.pose_backend_combo.setCurrentText(self.settings['pose_backend'])
        self.extraction_method_combo.setCurrentText(self.settings['frame_extraction_method'])
        self.max_frames_spinbox.setValue(self.settings['max_frames_per_video'])
        self.quality_threshold_slider.setValue(int(self.settings['quality_threshold'] * 100))
        self.angle_tolerance_slider.setValue(int(self.settings['angle_tolerance']))
        self.enhancement_checkbox.setChecked(self.settings['enable_frame_enhancement'])
        self.save_images_checkbox.setChecked(self.settings['save_analysis_images'])
        self.auto_select_checkbox.setChecked(self.settings['auto_select_best_frames'])
    
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
            'auto_select_best_frames': True
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