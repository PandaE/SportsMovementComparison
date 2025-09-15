import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QCheckBox, QGroupBox, QFormLayout, QMenuBar, QAction
)
from PyQt5.QtCore import Qt
from ui.video_player import VideoPlayer
from ui.dialogs import Dialogs
from ui.results_window import ResultsWindow
from ui.advanced_analysis_window import AdvancedAnalysisWindow
from ui.settings_dialog import SettingsDialog
from core.comparison_engine import ComparisonEngine
from core.experimental_comparison_engine import ExperimentalComparisonEngine

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.language = 'zh'  # 默认中文
        self.translations = {
            'zh': {
                'title': '运动动作对比分析',
                'settings': '设置',
                'analysis_group': '分析设置',
                'experimental': '启用高级姿态分析 (实验功能)',
                'sport_label': '运动类型:',
                'action_label': '动作类型:',
                'import_user': '导入用户视频',
                'import_standard': '导入标准视频',
                'compare': '开始分析对比',
                'compare_advanced': '开始高级分析对比',
                'compare_basic': '开始基础对比',
            },
            'en': {
                'title': 'Sports Movement Comparator',
                'settings': 'Settings',
                'analysis_group': 'Analysis Settings',
                'experimental': 'Enable Advanced Pose Analysis (Experimental)',
                'sport_label': 'Sport:',
                'action_label': 'Action:',
                'import_user': 'Import User Video',
                'import_standard': 'Import Standard Video',
                'compare': 'Start Comparison',
                'compare_advanced': 'Start Advanced Comparison',
                'compare_basic': 'Start Basic Comparison',
            }
        }

        # 初始化分析引擎
        self.experimental_engine = ExperimentalComparisonEngine(use_experimental_features=True)
        self.basic_engine = ComparisonEngine()
        self.current_engine = self.experimental_engine

        # 设置对话框
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.settings_changed.connect(self.apply_settings)

        self.init_ui()
        self.update_language(self.language)

    def tr_text(self, key):
        return self.translations.get(self.language, self.translations['zh']).get(key, key)

    def update_language(self, lang):
        self.language = lang
        self.setWindowTitle(self.tr_text('title'))
        self.settings_btn.setText(self.tr_text('settings'))
        self.experimental_checkbox.setText(self.tr_text('experimental'))
        self.sport_combo.setItemText(0, '羽毛球' if lang == 'zh' else 'Badminton')
        self.action_combo.setItemText(0, '正手高远球' if lang == 'zh' else 'Clear Shot (High Long Shot)')
        self.import_user_btn.setText(self.tr_text('import_user'))
        self.import_standard_btn.setText(self.tr_text('import_standard'))
        self.compare_btn.setText(self.tr_text('compare'))
        # 分析设置组
        self.findChild(QGroupBox).setTitle(self.tr_text('analysis_group'))
        # 标签
        labels = self.findChildren(QLabel)
        for label in labels:
            if label.text() in ['运动类型:', 'Sport:']:
                label.setText(self.tr_text('sport_label'))
            elif label.text() in ['动作类型:', 'Action:']:
                label.setText(self.tr_text('action_label'))
        # 其他窗口语言刷新（如 results_window、advanced_analysis_window）可在此扩展
        self.user_video_player.update_language(lang)
        self.standard_video_player.update_language(lang)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 菜单栏（简化版）
        menu_layout = QHBoxLayout()
        menu_layout.addStretch()
        
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings)
        menu_layout.addWidget(self.settings_btn)
        
        layout.addLayout(menu_layout)
        
        # 分析设置组
        settings_group = QGroupBox("分析设置")
        settings_layout = QFormLayout()
        
        # 实验功能开关
        self.experimental_checkbox = QCheckBox("启用高级姿态分析 (实验功能)")
        self.experimental_checkbox.setChecked(True)
        self.experimental_checkbox.stateChanged.connect(self.toggle_experimental_mode)
        settings_layout.addRow(self.experimental_checkbox)
        
        # Sport and action selection
        selection_layout = QHBoxLayout()
        self.sport_combo = QComboBox()
        self.sport_combo.addItems(['Badminton'])
        self.action_combo = QComboBox()
        self.update_action_combo()  # 动态更新可用动作
        self.sport_combo.currentTextChanged.connect(self.update_action_combo)
        
        selection_layout.addWidget(QLabel('运动类型:'))
        selection_layout.addWidget(self.sport_combo)
        selection_layout.addWidget(QLabel('动作类型:'))
        selection_layout.addWidget(self.action_combo)
        
        settings_layout.addRow(selection_layout)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Video players
        video_layout = QHBoxLayout()
        self.user_video_player = VideoPlayer()
        self.standard_video_player = VideoPlayer()
        video_layout.addWidget(self.user_video_player)
        video_layout.addWidget(self.standard_video_player)
        layout.addLayout(video_layout)

        # Import buttons
        button_layout = QHBoxLayout()
        self.import_user_btn = QPushButton('导入用户视频')
        self.import_standard_btn = QPushButton('导入标准视频')
        button_layout.addWidget(self.import_user_btn)
        button_layout.addWidget(self.import_standard_btn)
        layout.addLayout(button_layout)

        # Compare button
        self.compare_btn = QPushButton('开始分析对比')
        self.compare_btn.setEnabled(False)
        layout.addWidget(self.compare_btn)

        self.setLayout(layout)

        # Connect buttons
        self.import_user_btn.clicked.connect(self.import_user_video)
        self.import_standard_btn.clicked.connect(self.import_standard_video)
        self.compare_btn.clicked.connect(self.compare_videos)

        self.user_video_path = None
        self.standard_video_path = None

    def toggle_experimental_mode(self, state):
        """切换实验模式"""
        use_experimental = state == 2  # Qt.Checked
        if hasattr(self.experimental_engine, 'set_experimental_mode'):
            self.experimental_engine.set_experimental_mode(use_experimental)
        
        self.current_engine = self.experimental_engine if use_experimental else self.basic_engine
        self.update_action_combo()  # 更新可用动作列表
        
        # 更新按钮文本
        if use_experimental:
            self.compare_btn.setText('开始高级分析对比')
        else:
            self.compare_btn.setText('开始基础对比')
    
    def update_action_combo(self):
        """更新动作下拉列表"""
        self.action_combo.clear()
        
        if hasattr(self.current_engine, 'get_available_configs'):
            try:
                configs = self.current_engine.get_available_configs()
                for sport, action in configs:
                    self.action_combo.addItem(f"{action}")
            except:
                self.action_combo.addItem('Clear Shot (High Long Shot)')
        else:
            self.action_combo.addItem('Clear Shot (High Long Shot)')

    def import_user_video(self):
        file_path = Dialogs.select_video(self, '导入用户视频')
        if file_path:
            self.user_video_path = file_path
            self.user_video_player.set_video(file_path)
            self.check_compare_ready()

    def import_standard_video(self):
        file_path = Dialogs.select_video(self, '导入标准视频')
        if file_path:
            self.standard_video_path = file_path
            self.standard_video_player.set_video(file_path)
            self.check_compare_ready()

    def check_compare_ready(self):
        if self.user_video_path and self.standard_video_path:
            self.compare_btn.setEnabled(True)
        else:
            self.compare_btn.setEnabled(False)

    def compare_videos(self):
        # 根据当前引擎类型进行分析
        if self.current_engine == self.experimental_engine and hasattr(self.current_engine, 'compare'):
            # 使用实验引擎，传递运动和动作类型
            sport = self.sport_combo.currentText().lower()
            action = self.action_combo.currentText().lower()
            result = self.current_engine.compare(
                self.user_video_path, 
                self.standard_video_path, 
                sport=sport, 
                action=action
            )
            
            # 如果启用了高级分析，使用高级分析窗口
            if self.experimental_checkbox.isChecked():
                self.results_window = AdvancedAnalysisWindow(
                    result, 
                    self.user_video_path, 
                    self.standard_video_path,
                    self.language
                )
            else:
                self.results_window = ResultsWindow(
                    result, 
                    self.user_video_path, 
                    self.standard_video_path
                )
        else:
            # 使用基础引擎
            result = self.current_engine.compare(self.user_video_path, self.standard_video_path)
            self.results_window = ResultsWindow(result, self.user_video_path, self.standard_video_path)
        
        self.results_window.show()
    
    def open_settings(self):
        """打开设置对话框"""
        self.settings_dialog.show()
    
    def apply_settings(self, settings):
        """应用设置变更"""
        # 更新实验模式状态
        self.experimental_checkbox.setChecked(settings.get('experimental_enabled', True))
        self.toggle_experimental_mode(2 if settings.get('experimental_enabled', True) else 0)

        # 语言切换
        if 'language' in settings:
            self.update_language(settings['language'])

        # 可以在这里应用其他设置到引擎
        if hasattr(self.experimental_engine, 'apply_settings'):
            self.experimental_engine.apply_settings(settings)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
