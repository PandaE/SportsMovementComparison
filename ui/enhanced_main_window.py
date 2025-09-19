"""
Enhanced MainWindow with full internationalization support.
增强的主窗口，完整支持国际化
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, 
    QCheckBox, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt
from ui.enhanced_video_player import EnhancedVideoPlayer
from ui.enhanced_dialogs import EnhancedDialogs
from ui.enhanced_results_window import EnhancedResultsWindow
from ui.enhanced_settings_dialog import EnhancedSettingsDialog
from ui.i18n_mixin import I18nMixin
from core.comparison_engine import ComparisonEngine
from core.experimental_comparison_engine import ExperimentalComparisonEngine
from localization.translation_keys import TK


class EnhancedMainWindow(QWidget, I18nMixin):
    """增强的主窗口，使用新的国际化系统"""
    
    def __init__(self):
        QWidget.__init__(self)
        I18nMixin.__init__(self)  # 初始化国际化混入
        
        # 运动和动作映射（保持向后兼容）
        self.sport_mapping = {
            '羽毛球': 'badminton',
            'badminton': 'badminton',
            'Badminton': 'badminton'
        }
        
        self.action_mapping = {
            '正手高远球': 'clear',
            'Clear Shot (High Long Shot)': 'clear',
            'clear': 'clear',
            'forehand_clear': 'clear'
        }
        
        # 初始化分析引擎
        self.experimental_engine = ExperimentalComparisonEngine(use_experimental_features=True)
        self.basic_engine = ComparisonEngine()
        self.current_engine = self.experimental_engine

        # 设置对话框
        self.settings_dialog = EnhancedSettingsDialog(self)
        self.settings_dialog.settings_changed.connect(self.apply_settings)

        self.init_ui()
        self.update_ui_texts()  # 初始化文本

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 菜单栏（简化版）
        menu_layout = QHBoxLayout()
        menu_layout.addStretch()
        
        self.settings_btn = QPushButton()
        self.settings_btn.clicked.connect(self.open_settings)
        menu_layout.addWidget(self.settings_btn)
        
        layout.addLayout(menu_layout)
        
        # 分析设置组
        self.settings_group = QGroupBox()
        settings_layout = QFormLayout()
        
    # (已移除实验功能开关，默认高级模式)
        
        # Sport and action selection
        selection_layout = QHBoxLayout()
        
        self.sport_label = QLabel()
        self.sport_combo = QComboBox()
        self.sport_combo.addItems(['Badminton'])
        
        self.action_label = QLabel()
        self.action_combo = QComboBox()
        self.update_action_combo()  # 动态更新可用动作
        self.sport_combo.currentTextChanged.connect(self.update_action_combo)
        
        selection_layout.addWidget(self.sport_label)
        selection_layout.addWidget(self.sport_combo)
        selection_layout.addWidget(self.action_label)
        selection_layout.addWidget(self.action_combo)
        
        settings_layout.addRow(selection_layout)
        self.settings_group.setLayout(settings_layout)
        layout.addWidget(self.settings_group)

        # Video players
        video_layout = QHBoxLayout()
        self.user_video_player = EnhancedVideoPlayer()
        self.standard_video_player = EnhancedVideoPlayer()
        video_layout.addWidget(self.user_video_player)
        video_layout.addWidget(self.standard_video_player)
        layout.addLayout(video_layout)

        # Import buttons
        button_layout = QHBoxLayout()
        self.import_user_btn = QPushButton()
        self.import_standard_btn = QPushButton()
        button_layout.addWidget(self.import_user_btn)
        button_layout.addWidget(self.import_standard_btn)
        layout.addLayout(button_layout)

        # Compare button
        self.compare_btn = QPushButton()
        self.compare_btn.setEnabled(False)
        layout.addWidget(self.compare_btn)

        self.setLayout(layout)

        # Connect buttons
        self.import_user_btn.clicked.connect(self.import_user_video)
        self.import_standard_btn.clicked.connect(self.import_standard_video)
        self.compare_btn.clicked.connect(self.compare_videos)

        self.user_video_path = None
        self.standard_video_path = None

    def update_ui_texts(self):
        """更新所有UI文本"""
        # 窗口标题
        self.setWindowTitle(self.translate(TK.UI.MainWindow.TITLE))
        
        # 按钮文本
        self.settings_btn.setText(self.translate(TK.UI.MainWindow.SETTINGS))
        self.import_user_btn.setText(self.translate(TK.UI.MainWindow.IMPORT_USER))
        self.import_standard_btn.setText(self.translate(TK.UI.MainWindow.IMPORT_STANDARD))
        
        # 分析设置组
        self.settings_group.setTitle(self.translate(TK.UI.MainWindow.ANALYSIS_GROUP))
    # 实验模式标签移除
        
        # 标签
        self.sport_label.setText(self.translate(TK.UI.MainWindow.SPORT_LABEL))
        self.action_label.setText(self.translate(TK.UI.MainWindow.ACTION_LABEL))
        
        # 更新运动下拉框
        self.update_sport_combo_texts()
        
        # 更新对比按钮文本
        self.update_compare_button_text()
        
        # 通知视频播放器更新语言
        if hasattr(self.user_video_player, 'update_language'):
            current_lang = 'zh' if self.get_current_language() == 'zh_CN' else 'en'
            self.user_video_player.update_language(current_lang)
            self.standard_video_player.update_language(current_lang)

    def update_sport_combo_texts(self):
        """更新运动下拉框文本"""
        current_index = self.sport_combo.currentIndex()
        self.sport_combo.clear()
        self.sport_combo.addItem(self.translate(TK.Analysis.Sports.BADMINTON))
        self.sport_combo.setCurrentIndex(current_index)

    def update_compare_button_text(self):
        """更新对比按钮文本"""
        self.compare_btn.setText(self.translate(TK.UI.MainWindow.COMPARE_ADVANCED))

    # toggle_experimental_mode 已废弃
    
    def update_action_combo(self):
        """更新动作下拉列表"""
        current_index = self.action_combo.currentIndex()
        self.action_combo.clear()
        
        if hasattr(self.current_engine, 'get_available_configs'):
            try:
                configs = self.current_engine.get_available_configs()
                for sport, action in configs:
                    # 使用翻译后的动作名称
                    translated_action = self.translate(TK.Analysis.Actions.CLEAR_SHOT)
                    self.action_combo.addItem(translated_action)
            except:
                self.action_combo.addItem(self.translate(TK.Analysis.Actions.CLEAR_SHOT))
        else:
            self.action_combo.addItem(self.translate(TK.Analysis.Actions.CLEAR_SHOT))
        
        # 保持之前的选择
        if current_index >= 0 and current_index < self.action_combo.count():
            self.action_combo.setCurrentIndex(current_index)

    def import_user_video(self):
        self.import_user_btn.setDisabled(True)
        """导入用户视频"""
        file_path = EnhancedDialogs.select_video(self, TK.UI.Dialogs.SELECT_VIDEO)
        print(f"用户选择的视频文件: {repr(file_path)}")
        if file_path:
            self.user_video_path = file_path
            self.user_video_player.set_video(file_path)
            print(f"用户视频路径设置为: {repr(self.user_video_path)}")
            self.check_compare_ready()
        else:
            print("用户取消了视频选择")
        self.import_user_btn.setDisabled(False)

    def import_standard_video(self):
        self.import_standard_btn.setDisabled(True)
        """Import standard video from Azure Blob Storage"""
        from ui.standard_video_dialog import StandardVideoDialog
        from core.azure_blob_reader import AzureBlobReader
        import os
        sport_display = self.sport_combo.currentText()
        action_display = self.action_combo.currentText()
        sport = self.sport_mapping.get(sport_display, 'badminton')
        action = self.action_mapping.get(action_display, 'clear')
        dialog = StandardVideoDialog(sport, action, self)
        result = dialog.exec_()
        if result == dialog.Accepted:
            blob_name = dialog.get_selected_blob()
            if blob_name:
                local_path = dialog.get_cache_path(blob_name)
                if not os.path.exists(local_path):
                    reader = AzureBlobReader()
                    from ui.download_progress_dialog import DownloadProgressDialog
                    from .download_worker import DownloadWorker
                    from PyQt5.QtCore import QThread
                    progress_dialog = DownloadProgressDialog(self)
                    thread = QThread()
                    worker = DownloadWorker(reader, blob_name, local_path)
                    worker.moveToThread(thread)
                    worker.progress.connect(progress_dialog.set_progress)
                    def finish_handler(path):
                        progress_dialog.close()
                        thread.quit()
                        thread.wait()
                        worker.deleteLater()
                        thread.deleteLater()
                    def error_handler(msg):
                        progress_dialog.close()
                        thread.quit()
                        thread.wait()
                        worker.deleteLater()
                        thread.deleteLater()
                        print(f"Download error: {msg}")
                    worker.finished.connect(finish_handler)
                    worker.error.connect(error_handler)
                    thread.started.connect(worker.run)
                    progress_dialog.show()
                    thread.start()
                self.standard_video_path = local_path
                self.standard_video_player.set_video(local_path)
                self.check_compare_ready()
        else:
            print("User cancelled standard video selection.")
        self.import_standard_btn.setDisabled(False)

    def check_compare_ready(self):
        """检查是否可以开始对比"""
        self.compare_btn.setEnabled(bool(self.user_video_path and self.standard_video_path))

    def compare_videos(self):
        """对比视频"""
        # 禁用按钮，防止重复点击
        self.compare_btn.setEnabled(False)
        
        try:
            # 根据当前引擎类型进行分析
            # 始终使用实验引擎；若失败会在异常中捕获
            sport_display = self.sport_combo.currentText()
            action_display = self.action_combo.currentText()
            sport = self.sport_mapping.get(sport_display, 'badminton')
            action = self.action_mapping.get(action_display, 'clear')
            try:
                result = self.experimental_engine.compare(
                    self.user_video_path,
                    self.standard_video_path,
                    sport=sport,
                    action=action
                )
                # 如果结果包含错误则尝试回退
                if isinstance(result, dict) and result.get('error'):
                    print("高级分析返回错误，回退基础模式: ", result.get('error'))
                    result = self.basic_engine.compare(self.user_video_path, self.standard_video_path)
            except Exception as exp_err:
                print(f"高级分析异常，回退基础模式: {exp_err}")
                result = self.basic_engine.compare(self.user_video_path, self.standard_video_path)

            self.results_window = EnhancedResultsWindow(
                result,
                self.user_video_path,
                self.standard_video_path
            )
            
            self.results_window.show()
            
        except Exception as e:
            print(f"分析过程中出现错误: {e}")
            # 这里可以显示错误对话框
        finally:
            # 分析结束后重新启用按钮
            self.compare_btn.setEnabled(True)
    
    def open_settings(self):
        """打开设置对话框"""
        self.settings_dialog.show()
    
    def apply_settings(self, settings):
        """应用设置变更"""
        # 更新实验模式状态
    # 实验模式相关设置忽略（已默认高级）

        # 语言切换由I18nManager自动处理，这里不需要手动设置
        # 因为设置对话框已经直接调用了i18n.set_language()

        # 可以在这里应用其他设置到引擎
        if hasattr(self.experimental_engine, 'apply_settings'):
            self.experimental_engine.apply_settings(settings)


def main():
    """
    Entry point for the enhanced Sports Movement Comparator application.
    增强版运动动作对比分析应用程序入口点
    """
    app = QApplication(sys.argv)
    window = EnhancedMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Application failed to start: {e}")
        import traceback
        traceback.print_exc()