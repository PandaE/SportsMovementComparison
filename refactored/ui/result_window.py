"""
Simplified Result Window for displaying analysis results
简化的结果窗口，用于显示分析结果

Based on EnhancedResultsWindow and EnhancedAdvancedAnalysisWindow but simplified.
基于EnhancedResultsWindow和EnhancedAdvancedAnalysisWindow但进行了简化。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton,
    QSplitter, QGroupBox, QScrollArea, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QPainter, QPen, QColor
import json
import numpy as np
import cv2

from .video_player import VideoPlayer
from localization.i18n_manager import I18nManager
from localization.translation_keys import TK


class ResultWindow(QWidget):
    """简化的结果显示窗口"""
    
    def __init__(self, analysis_result, user_video_path, standard_video_path, parent=None):
        super().__init__(parent)
        
        # Store analysis data
        self.analysis_result = analysis_result
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        
        # Initialize localization
        self.i18n = I18nManager.instance()
        self.i18n.register_observer(self._on_language_changed)
        
        # UI state
        self.current_stage = 0
        
        self.init_ui()
        self.load_analysis_data()
        self.update_ui_texts()

    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout()
        
        # Title section
        title_layout = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.close_btn = QPushButton()
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)
        layout.addLayout(title_layout)
        
        # Main content area
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Analysis results
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Overall score section
        self.score_group = QGroupBox()
        score_layout = QVBoxLayout()
        
        self.overall_score_label = QLabel()
        self.overall_score_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.overall_score_label.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(self.overall_score_label)
        
        self.score_progress = QProgressBar()
        self.score_progress.setRange(0, 100)
        score_layout.addWidget(self.score_progress)
        
        self.score_group.setLayout(score_layout)
        left_layout.addWidget(self.score_group)
        
        # Stage analysis tabs
        self.stage_tabs = QTabWidget()
        left_layout.addWidget(self.stage_tabs)
        
        # Detailed measurements
        self.measurements_group = QGroupBox()
        measurements_layout = QVBoxLayout()
        
        self.measurements_table = QTableWidget()
        self.measurements_table.setColumnCount(4)
        measurements_layout.addWidget(self.measurements_table)
        
        self.measurements_group.setLayout(measurements_layout)
        left_layout.addWidget(self.measurements_group)
        
        left_panel.setLayout(left_layout)
        main_splitter.addWidget(left_panel)
        
        # Right panel: Video comparison
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        self.video_group = QGroupBox()
        video_layout = QVBoxLayout()
        
        # Video players
        video_players_layout = QHBoxLayout()
        
        user_video_layout = QVBoxLayout()
        self.user_video_label = QLabel()
        self.user_video_player = VideoPlayer()
        user_video_layout.addWidget(self.user_video_label)
        user_video_layout.addWidget(self.user_video_player)
        
        standard_video_layout = QVBoxLayout()
        self.standard_video_label = QLabel()
        self.standard_video_player = VideoPlayer()
        standard_video_layout.addWidget(self.standard_video_label)
        standard_video_layout.addWidget(self.standard_video_player)
        
        video_players_layout.addLayout(user_video_layout)
        video_players_layout.addLayout(standard_video_layout)
        video_layout.addLayout(video_players_layout)
        
        # Video controls
        control_layout = QHBoxLayout()
        self.sync_btn = QPushButton()
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(True)
        self.sync_btn.clicked.connect(self.toggle_sync)
        
        self.show_keyframes_btn = QPushButton()
        self.show_keyframes_btn.clicked.connect(self.show_key_frames)
        
        control_layout.addWidget(self.sync_btn)
        control_layout.addWidget(self.show_keyframes_btn)
        control_layout.addStretch()
        
        video_layout.addLayout(control_layout)
        self.video_group.setLayout(video_layout)
        right_layout.addWidget(self.video_group)
        
        # Suggestions section
        self.suggestions_group = QGroupBox()
        suggestions_layout = QVBoxLayout()
        
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setMaximumHeight(150)
        self.suggestions_text.setReadOnly(True)
        suggestions_layout.addWidget(self.suggestions_text)
        
        self.suggestions_group.setLayout(suggestions_layout)
        right_layout.addWidget(self.suggestions_group)
        
        right_panel.setLayout(right_layout)
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)
        layout.addWidget(main_splitter)
        
        self.setLayout(layout)
        
        # Set window properties
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Connect video player signals for synchronization
        self.user_video_player.position_changed.connect(self.on_user_position_changed)
        self.standard_video_player.position_changed.connect(self.on_standard_position_changed)

    def load_analysis_data(self):
        """加载分析数据到UI"""
        try:
            if not self.analysis_result:
                return
            
            # Load videos
            if self.user_video_path:
                self.user_video_player.set_video(self.user_video_path)
            if self.standard_video_path:
                self.standard_video_player.set_video(self.standard_video_path)
            
            # Extract overall score
            overall_score = 0
            if hasattr(self.analysis_result, 'overall_score'):
                overall_score = self.analysis_result.overall_score
            elif isinstance(self.analysis_result, dict):
                overall_score = self.analysis_result.get('overall_score', 0)
            
            self.score_progress.setValue(int(overall_score))
            
            # Load stage data
            self.load_stage_data()
            
            # Load measurements
            self.load_measurements_data()
            
            # Load suggestions
            self.load_suggestions()
            
        except Exception as e:
            print(f"Error loading analysis data: {e}")

    def load_stage_data(self):
        """加载阶段数据"""
        try:
            stages_data = []
            
            if hasattr(self.analysis_result, 'stage_results'):
                stages_data = self.analysis_result.stage_results
            elif isinstance(self.analysis_result, dict):
                stages_data = self.analysis_result.get('stage_results', [])
            
            # Clear existing tabs
            self.stage_tabs.clear()
            
            for i, stage_data in enumerate(stages_data):
                stage_widget = self.create_stage_widget(stage_data, i)
                stage_name = stage_data.get('stage_name', f'Stage {i+1}')
                self.stage_tabs.addTab(stage_widget, stage_name)
                
        except Exception as e:
            print(f"Error loading stage data: {e}")

    def create_stage_widget(self, stage_data, stage_index):
        """创建阶段分析组件"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Stage score
        score_label = QLabel(f"Stage Score: {stage_data.get('score', 0):.1f}%")
        score_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(score_label)
        
        # Stage analysis
        analysis_text = QTextEdit()
        analysis_text.setReadOnly(True)
        analysis_text.setMaximumHeight(100)
        
        analysis_content = stage_data.get('analysis', 'No analysis available')
        analysis_text.setPlainText(analysis_content)
        layout.addWidget(analysis_text)
        
        # Measurements for this stage
        measurements = stage_data.get('measurements', [])
        if measurements:
            measurements_label = QLabel("Measurements:")
            measurements_label.setFont(QFont("Arial", 10, QFont.Bold))
            layout.addWidget(measurements_label)
            
            for measurement in measurements:
                measurement_text = f"• {measurement.get('name', 'Unknown')}: {measurement.get('result', 'N/A')}"
                measurement_label = QLabel(measurement_text)
                layout.addWidget(measurement_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def load_measurements_data(self):
        """加载测量数据到表格"""
        try:
            measurements_data = []
            
            if hasattr(self.analysis_result, 'detailed_measurements'):
                measurements_data = self.analysis_result.detailed_measurements
            elif isinstance(self.analysis_result, dict):
                measurements_data = self.analysis_result.get('detailed_measurements', [])
            
            # Set up table
            self.measurements_table.setRowCount(len(measurements_data))
            headers = ["Measurement", "User Value", "Standard Value", "Status"]
            self.measurements_table.setHorizontalHeaderLabels(headers)
            
            # Populate table
            for i, measurement in enumerate(measurements_data):
                name_item = QTableWidgetItem(measurement.get('name', 'Unknown'))
                user_value_item = QTableWidgetItem(str(measurement.get('user_value', 'N/A')))
                standard_value_item = QTableWidgetItem(str(measurement.get('standard_value', 'N/A')))
                
                status = measurement.get('status', 'Unknown')
                status_item = QTableWidgetItem(status)
                
                # Set status color
                if 'pass' in status.lower() or '达标' in status:
                    status_item.setBackground(QColor(200, 255, 200))
                elif 'fail' in status.lower() or '偏' in status:
                    status_item.setBackground(QColor(255, 200, 200))
                
                self.measurements_table.setItem(i, 0, name_item)
                self.measurements_table.setItem(i, 1, user_value_item)
                self.measurements_table.setItem(i, 2, standard_value_item)
                self.measurements_table.setItem(i, 3, status_item)
            
            # Adjust column widths
            header = self.measurements_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            
        except Exception as e:
            print(f"Error loading measurements data: {e}")

    def load_suggestions(self):
        """加载改进建议"""
        try:
            suggestions = ""
            
            if hasattr(self.analysis_result, 'suggestions'):
                suggestions = self.analysis_result.suggestions
            elif isinstance(self.analysis_result, dict):
                suggestions_list = self.analysis_result.get('suggestions', [])
                if isinstance(suggestions_list, list):
                    suggestions = "\\n".join(suggestions_list)
                else:
                    suggestions = str(suggestions_list)
            
            self.suggestions_text.setPlainText(suggestions)
            
        except Exception as e:
            print(f"Error loading suggestions: {e}")

    def update_ui_texts(self):
        """更新所有UI文本"""
        # Window title
        self.setWindowTitle(self.translate(TK.UI.Results.TITLE))
        
        # Main labels
        self.title_label.setText(self.translate(TK.UI.Results.ANALYSIS_TITLE))
        self.close_btn.setText(self.translate(TK.UI.Common.CLOSE))
        
        # Groups
        self.score_group.setTitle(self.translate(TK.UI.Results.OVERALL_SCORE))
        self.video_group.setTitle(self.translate(TK.UI.Results.VIDEO_COMPARISON))
        self.measurements_group.setTitle(self.translate(TK.UI.Results.DETAILED_MEASUREMENTS))
        self.suggestions_group.setTitle(self.translate(TK.UI.Results.SUGGESTIONS))
        
        # Video labels
        self.user_video_label.setText(self.translate(TK.UI.Results.USER_VIDEO))
        self.standard_video_label.setText(self.translate(TK.UI.Results.STANDARD_VIDEO))
        
        # Buttons
        self.sync_btn.setText(self.translate(TK.UI.Results.SYNC_VIDEOS))
        self.show_keyframes_btn.setText(self.translate(TK.UI.Results.SHOW_KEY_FRAMES))
        
        # Update overall score label
        score_value = self.score_progress.value()
        self.overall_score_label.setText(f"{self.translate(TK.UI.Results.SCORE_LABEL)}: {score_value}%")

    def toggle_sync(self):
        """切换视频同步模式"""
        # Implementation for video synchronization
        pass

    def show_key_frames(self):
        """显示关键帧"""
        # Implementation for showing key frames
        pass

    def on_user_position_changed(self, position):
        """用户视频位置变化"""
        if self.sync_btn.isChecked():
            # Sync standard video to same position
            self.standard_video_player.seek_frame(position)

    def on_standard_position_changed(self, position):
        """标准视频位置变化"""
        if self.sync_btn.isChecked():
            # Sync user video to same position
            self.user_video_player.seek_frame(position)

    def translate(self, key: str, **kwargs) -> str:
        """翻译文本"""
        return self.i18n.t(key, **kwargs)

    def _on_language_changed(self):
        """语言变更回调"""
        self.update_ui_texts()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # Clean up video players
        self.user_video_player.close()
        self.standard_video_player.close()
        event.accept()


if __name__ == '__main__':
    """Test the result window"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Create test data
    test_result = {
        'overall_score': 75,
        'stage_results': [
            {
                'stage_name': 'Preparation',
                'score': 80,
                'analysis': 'Good preparation stance',
                'measurements': [
                    {'name': 'Arm Angle', 'result': 'Good'}
                ]
            }
        ],
        'detailed_measurements': [
            {
                'name': 'Elbow Angle',
                'user_value': '145°',
                'standard_value': '150°',
                'status': 'Pass'
            }
        ],
        'suggestions': ['Improve arm positioning', 'Focus on timing']
    }
    
    app = QApplication(sys.argv)
    window = ResultWindow(test_result, None, None)
    window.show()
    sys.exit(app.exec_())