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
import os
from ui.enhanced_video_player import EnhancedVideoPlayer
from ui.enhanced_dialogs import EnhancedDialogs
# from ui.enhanced_results_window import EnhancedResultsWindow  # deprecated in new flow
from ui.enhanced_settings_dialog import EnhancedSettingsDialog
from ui.i18n_mixin import I18nMixin
from core.comparison_engine import ComparisonEngine
from core.experimental_comparison_engine import ExperimentalComparisonEngine
from core.experimental.frame_analyzer.preset_key_frame_extractor import PresetKeyFrameExtractor
from core.experimental.frame_analyzer.key_frame_extractor import KeyFrameExtractor
from core.new_evaluation.data_models import ActionConfig as NEActionConfig, StageConfig as NEStageConfig, MetricConfig as NEMetricConfig, KeyframeSet, FrameRef
from core.new_evaluation.session import EvaluationSession
from core.new_evaluation.adapter import UIAdapter
from ui.new_results.results_window import ResultsWindow as NewResultsWindow
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
        # 设置/分组/标签/按钮文本（原实现遗漏导致界面控件空白）
        if hasattr(self, 'settings_btn'):
            self.settings_btn.setText(self.translate(TK.UI.MainWindow.SETTINGS))
        if hasattr(self, 'settings_group'):
            self.settings_group.setTitle(self.translate(TK.UI.MainWindow.ANALYSIS_GROUP))
        if hasattr(self, 'sport_label'):
            self.sport_label.setText(self.translate(TK.UI.MainWindow.SPORT_LABEL))
        if hasattr(self, 'action_label'):
            self.action_label.setText(self.translate(TK.UI.MainWindow.ACTION_LABEL))
        if hasattr(self, 'import_user_btn'):
            self.import_user_btn.setText(self.translate(TK.UI.MainWindow.IMPORT_USER))
        if hasattr(self, 'import_standard_btn'):
            self.import_standard_btn.setText(self.translate(TK.UI.MainWindow.IMPORT_STANDARD))
        # Sport combo
        current_index = self.sport_combo.currentIndex()
        self.sport_combo.blockSignals(True)
        self.sport_combo.clear()
        self.sport_combo.addItem(self.translate(TK.Analysis.Sports.BADMINTON))
        self.sport_combo.setCurrentIndex(current_index if current_index >= 0 else 0)
        self.sport_combo.blockSignals(False)
        # Action combo（此处只显示一个动作，仍然刷新以确保语言切换）
        self.update_action_combo()
        # Compare button 文本根据当前引擎（目前始终 experimental）
        if hasattr(self, 'compare_btn'):
            self.update_compare_button_text()

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
            sport_display = self.sport_combo.currentText()
            action_display = self.action_combo.currentText()
            sport = self.sport_mapping.get(sport_display, 'badminton')
            action = self.action_mapping.get(action_display, 'clear')

            if not (self.user_video_path and self.standard_video_path):
                print("缺少视频路径，无法开始对比")
                return

            preset_extractor = getattr(self, '_preset_extractor', None)
            if preset_extractor is None:
                preset_extractor = PresetKeyFrameExtractor()
                self._preset_extractor = preset_extractor
            key_extractor = getattr(self, '_key_extractor', None)
            if key_extractor is None:
                key_extractor = KeyFrameExtractor()
                self._key_extractor = key_extractor

            def obtain_stage_frames(video_path: str, is_standard: bool):
                base_name = os.path.basename(video_path) if video_path else None
                frames = None
                try:
                    if preset_extractor.has_preset(sport, action, video_name=base_name):
                        frames = preset_extractor.extract_stage_frames(video_path, sport, action, video_name=base_name)
                    elif preset_extractor.has_preset(sport, action):
                        frames = preset_extractor.extract_stage_frames(video_path, sport, action)
                except Exception:
                    frames = None
                if frames is None:
                    try:
                        frames = key_extractor.extract_stage_frames(video_path, sport, action)
                    except Exception as e:
                        print(f"自动提取关键帧失败: {e}")
                        frames = {}
                return frames or {}

            user_frame_positions = obtain_stage_frames(self.user_video_path, is_standard=False)
            std_frame_positions = obtain_stage_frames(self.standard_video_path, is_standard=True)
            if not user_frame_positions:
                print("未能提取到用户关键帧，终止")
                return

            stage_keys = sorted(set(list(user_frame_positions.keys()) + list(std_frame_positions.keys())))
            if not stage_keys:
                print("没有阶段关键帧，终止")
                return
            stages_cfg = []
            for sk in stage_keys:
                metric = NEMetricConfig(key=f"{sk}_presence", name=f"{sk}关键帧质量", unit=None, target=1.0)
                stages_cfg.append(NEStageConfig(key=sk, name=sk, metrics=[metric], weight=1.0/len(stage_keys)))
            action_cfg = NEActionConfig(sport=sport, action=action, stages=stages_cfg)

            user_refs = {k: FrameRef(video_path=self.user_video_path, frame_index=v) for k, v in user_frame_positions.items()}
            std_refs = {k: FrameRef(video_path=self.standard_video_path, frame_index=v) for k, v in std_frame_positions.items()}
            keyframes = KeyframeSet(user=user_refs, standard=std_refs)

            session = EvaluationSession(config=action_cfg, keyframes=keyframes, user_video=self.user_video_path, standard_video=self.standard_video_path)
            session.evaluate()
            state = session.get_state()
            vm = UIAdapter.to_vm(state, keyframes.user, keyframes.standard)
            self.results_window = NewResultsWindow(vm, session=session, keyframes=keyframes, adapter=UIAdapter)
            self.results_window.show()
        except Exception as e:
            print(f"新评估流程失败: {e}")
            import traceback; traceback.print_exc()
        finally:
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