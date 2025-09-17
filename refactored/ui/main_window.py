"""
Simplified Main Window for Sports Movement Comparison
简化的体育动作对比主窗口

Based on enhanced_main_window.py but with simplified structure and improved modularity.
基于enhanced_main_window.py但采用简化结构和改进的模块化设计。
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QCheckBox, QGroupBox, QFormLayout, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

# Import core analysis modules
from core.analyzer import MovementAnalyzer
from core.video_processor import VideoProcessor
from config.settings import AppSettings, SportSettings

# Import UI components
from .video_player import VideoPlayer
from .result_window import ResultWindow

# Import localization
from localization.i18n_manager import I18nManager
from localization.translation_keys import TK


class MainWindow(QWidget):
    """简化的主窗口，支持核心功能"""
    
    # Signals
    language_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.analyzer = MovementAnalyzer()
        self.video_processor = VideoProcessor()
        self.settings = AppSettings()
        
        # Initialize localization
        self.i18n = I18nManager.instance()
        self.i18n.register_observer(self._on_language_changed)
        
        # Video paths
        self.user_video_path = None
        self.standard_video_path = None
        
        # UI state
        self.is_comparing = False
        
        self.init_ui()
        self.connect_signals()
        self.update_ui_texts()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # Top menu bar
        menu_layout = QHBoxLayout()
        menu_layout.addStretch()
        
        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItems(['中文', 'English'])
        self.language_combo.setCurrentText('中文')
        menu_layout.addWidget(QLabel('语言/Language:'))
        menu_layout.addWidget(self.language_combo)
        
        layout.addLayout(menu_layout)
        
        # Analysis settings group
        self.settings_group = QGroupBox()
        settings_layout = QFormLayout()
        
        # Sport selection
        sport_layout = QHBoxLayout()
        self.sport_label = QLabel()
        self.sport_combo = QComboBox()
        self.sport_combo.addItems(SportSettings.get_supported_sports())
        
        self.action_label = QLabel()
        self.action_combo = QComboBox()
        self.update_action_combo()
        
        sport_layout.addWidget(self.sport_label)
        sport_layout.addWidget(self.sport_combo)
        sport_layout.addWidget(self.action_label)
        sport_layout.addWidget(self.action_combo)
        
        settings_layout.addRow(sport_layout)
        
        # Advanced analysis option
        self.advanced_checkbox = QCheckBox()
        self.advanced_checkbox.setChecked(True)
        settings_layout.addRow(self.advanced_checkbox)
        
        self.settings_group.setLayout(settings_layout)
        layout.addWidget(self.settings_group)

        # Video players section
        video_layout = QHBoxLayout()
        
        # User video section
        user_section = QVBoxLayout()
        self.user_video_label = QLabel()
        self.user_video_player = VideoPlayer()
        self.import_user_btn = QPushButton()
        user_section.addWidget(self.user_video_label)
        user_section.addWidget(self.user_video_player)
        user_section.addWidget(self.import_user_btn)
        
        # Standard video section
        standard_section = QVBoxLayout()
        self.standard_video_label = QLabel()
        self.standard_video_player = VideoPlayer()
        self.import_standard_btn = QPushButton()
        standard_section.addWidget(self.standard_video_label)
        standard_section.addWidget(self.standard_video_player)
        standard_section.addWidget(self.import_standard_btn)
        
        video_layout.addLayout(user_section)
        video_layout.addLayout(standard_section)
        layout.addLayout(video_layout)

        # Compare button
        self.compare_btn = QPushButton()
        self.compare_btn.setEnabled(False)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        layout.addWidget(self.compare_btn)

        self.setLayout(layout)
        
        # Set window properties
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

    def connect_signals(self):
        """连接信号和槽"""
        # Language change
        self.language_combo.currentTextChanged.connect(self.change_language)
        
        # Sport/action selection
        self.sport_combo.currentTextChanged.connect(self.update_action_combo)
        
        # Video import
        self.import_user_btn.clicked.connect(self.import_user_video)
        self.import_standard_btn.clicked.connect(self.import_standard_video)
        
        # Analysis
        self.compare_btn.clicked.connect(self.compare_videos)

    def update_ui_texts(self):
        """更新所有UI文本"""
        # Window title
        self.setWindowTitle(self.translate(TK.UI.MainWindow.TITLE))
        
        # Settings group
        self.settings_group.setTitle(self.translate(TK.UI.MainWindow.ANALYSIS_GROUP))
        self.sport_label.setText(self.translate(TK.UI.MainWindow.SPORT_LABEL))
        self.action_label.setText(self.translate(TK.UI.MainWindow.ACTION_LABEL))
        self.advanced_checkbox.setText(self.translate(TK.UI.MainWindow.EXPERIMENTAL_MODE))
        
        # Video labels
        self.user_video_label.setText(self.translate(TK.UI.MainWindow.USER_VIDEO_LABEL))
        self.standard_video_label.setText(self.translate(TK.UI.MainWindow.STANDARD_VIDEO_LABEL))
        
        # Buttons
        self.import_user_btn.setText(self.translate(TK.UI.MainWindow.IMPORT_USER))
        self.import_standard_btn.setText(self.translate(TK.UI.MainWindow.IMPORT_STANDARD))
        self.update_compare_button_text()

    def update_compare_button_text(self):
        """更新对比按钮文本"""
        if self.is_comparing:
            self.compare_btn.setText(self.translate("ui.main_window.comparing"))
        elif self.advanced_checkbox.isChecked():
            self.compare_btn.setText(self.translate(TK.UI.MainWindow.COMPARE_ADVANCED))
        else:
            self.compare_btn.setText(self.translate(TK.UI.MainWindow.COMPARE_BASIC))

    def change_language(self, language_text):
        """切换语言"""
        lang_code = 'zh_CN' if language_text == '中文' else 'en_US'
        self.i18n.set_language(lang_code)

    def update_action_combo(self):
        """更新动作下拉列表"""
        current_sport = self.sport_combo.currentText()
        if not current_sport:
            return
            
        current_index = self.action_combo.currentIndex()
        self.action_combo.clear()
        
        # Get actions for current sport
        actions = SportSettings.get_sport_actions(current_sport)
        for action in actions:
            display_name = SportSettings.get_action_name(current_sport, action, 
                                                       self.i18n.get_current_language())
            self.action_combo.addItem(display_name)
        
        # Restore selection if possible
        if current_index >= 0 and current_index < self.action_combo.count():
            self.action_combo.setCurrentIndex(current_index)

    def import_user_video(self):
        """导入用户视频"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translate("ui.dialogs.select_user_video"),
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
        )
        
        if file_path:
            # Validate video
            if self.video_processor.validate_video(file_path):
                self.user_video_path = file_path
                self.user_video_player.set_video(file_path)
                self.check_compare_ready()
            else:
                QMessageBox.warning(
                    self,
                    self.translate("ui.dialogs.error"),
                    self.translate("ui.dialogs.invalid_video")
                )

    def import_standard_video(self):
        """导入标准视频"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translate("ui.dialogs.select_standard_video"),
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
        )
        
        if file_path:
            # Validate video
            if self.video_processor.validate_video(file_path):
                self.standard_video_path = file_path
                self.standard_video_player.set_video(file_path)
                self.check_compare_ready()
            else:
                QMessageBox.warning(
                    self,
                    self.translate("ui.dialogs.error"),
                    self.translate("ui.dialogs.invalid_video")
                )

    def check_compare_ready(self):
        """检查是否可以开始对比"""
        ready = (self.user_video_path and 
                self.standard_video_path and 
                not self.is_comparing)
        self.compare_btn.setEnabled(ready)

    def compare_videos(self):
        """对比视频"""
        if not self.user_video_path or not self.standard_video_path:
            return
        
        # Update UI state
        self.is_comparing = True
        self.compare_btn.setEnabled(False)
        self.update_compare_button_text()
        
        try:
            # Get current selections
            sport = self.sport_combo.currentText()
            action_display = self.action_combo.currentText()
            
            # Convert to internal format
            sport_code = sport.lower()
            action_code = 'clear'  # For now, only support clear shot
            
            # Perform analysis
            result = self.analyzer.analyze_movement(
                user_video_path=self.user_video_path,
                standard_video_path=self.standard_video_path,
                sport=sport_code,
                action=action_code,
                use_advanced=self.advanced_checkbox.isChecked()
            )
            
            # Show results
            self.show_results(result)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                self.translate("ui.dialogs.error"),
                self.translate("ui.dialogs.analysis_error") + f"\n\n{str(e)}"
            )
        finally:
            # Reset UI state
            self.is_comparing = False
            self.check_compare_ready()
            self.update_compare_button_text()

    def show_results(self, analysis_result):
        """显示分析结果"""
        self.result_window = ResultWindow(
            analysis_result,
            self.user_video_path,
            self.standard_video_path,
            parent=self
        )
        self.result_window.show()

    def translate(self, key: str, **kwargs) -> str:
        """翻译文本"""
        return self.i18n.t(key, **kwargs)

    def _on_language_changed(self):
        """语言变更回调"""
        self.update_ui_texts()
        
        # Update language combo without triggering signal
        current_lang = self.i18n.get_current_language()
        lang_text = '中文' if current_lang == 'zh_CN' else 'English'
        
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentText(lang_text)
        self.language_combo.blockSignals(False)

    def closeEvent(self, event):
        """窗口关闭事件"""
        # Clean up resources
        if hasattr(self, 'result_window'):
            self.result_window.close()
        
        # Save settings
        self.settings.save_user_preferences({
            'language': self.i18n.get_current_language(),
            'advanced_mode': self.advanced_checkbox.isChecked(),
            'sport': self.sport_combo.currentText(),
            'action': self.action_combo.currentText()
        })
        
        event.accept()


def main():
    """主函数，用于测试"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())