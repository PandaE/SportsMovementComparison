"""
Enhanced Results Window - 增强版结果显示窗口
Enhanced results display window for comparison results with full internationalization support
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QGroupBox, QScrollArea, QFrame, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from localization.i18n_manager import I18nManager
from localization.translation_keys import TK
from ui.i18n_mixin import I18nMixin
from .enhanced_video_player import EnhancedVideoPlayer


class EnhancedResultsWindow(QWidget, I18nMixin):
    """增强版结果窗口 - 支持国际化"""
    
    def __init__(self, comparison_result, user_video_path, standard_video_path):
        super().__init__()
        I18nMixin.__init__(self)
        
        self.comparison_result = comparison_result
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        self.is_experimental = comparison_result.get('analysis_type') == 'experimental'
        # Detect new evaluation presence
        self.new_evaluation = comparison_result.get('new_evaluation')
        
        self.setGeometry(150, 150, 1400, 900)
        self.init_ui()
        self.update_ui_texts()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 整体得分显示
        self.create_score_section(layout)
        
        # 创建标签页
        self.create_tab_widget(layout)
        
        self.setLayout(layout)

    def update_ui_texts(self):
        """更新UI文本"""
        self.setWindowTitle(self.translate(TK.UI.RESULTS.TITLE))
        
        # 更新得分标签
        if hasattr(self, 'score_label'):
            score = self.comparison_result.get('score', 0)
            self.score_label.setText(f"{self.translate(TK.UI.RESULTS.SCORE)}: {score}")
        
        if hasattr(self, 'detail_label') and (self.is_experimental or self.new_evaluation):
            if self.new_evaluation:
                new_score = self.new_evaluation.get('overall_score')
                if new_score is not None:
                    self.detail_label.setText(f"Eval Score: {new_score:.2f}")
                else:
                    self.detail_label.setText("Eval Score: N/A")
            else:
                detailed_score = self.comparison_result.get('detailed_score', 0)
                self.detail_label.setText(f"{self.translate(TK.UI.RESULTS.DETAILED_SCORE)}: {detailed_score:.2%}")
        
        # 更新标签页标题
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setTabText(0, self.translate(TK.UI.RESULTS.VIDEO_TAB))
            self.tab_widget.setTabText(1, self.translate(TK.UI.RESULTS.ANALYSIS_TAB))
            if self.is_experimental:
                if self.tab_widget.count() > 2:
                    self.tab_widget.setTabText(2, self.translate(TK.UI.RESULTS.DETAILED_TAB))
                if self.tab_widget.count() > 3:
                    self.tab_widget.setTabText(3, self.translate(TK.UI.RESULTS.POSE_TAB))
        
        # 更新视频标题
        if hasattr(self, 'user_title'):
            self.user_title.setText(self.translate(TK.UI.RESULTS.USER_VIDEO))
        if hasattr(self, 'standard_title'):
            self.standard_title.setText(self.translate(TK.UI.RESULTS.STANDARD_VIDEO))
        
        # 更新分析标签
        if hasattr(self, 'analysis_label'):
            self.analysis_label.setText(self.translate(TK.UI.RESULTS.KEY_ANALYSIS))
        
        # 更新详细测量标签
        if hasattr(self, 'measurements_label'):
            self.measurements_label.setText(self.translate(TK.UI.RESULTS.DETAILED_MEASUREMENTS))
        
        # 更新姿态可视化标签
        if hasattr(self, 'pose_label'):
            self.pose_label.setText(self.translate(TK.UI.RESULTS.POSE_VISUALIZATION))
        
        # 更新无图像标签
        if hasattr(self, 'no_image_label'):
            self.no_image_label.setText(self.translate(TK.UI.RESULTS.NO_POSE_IMAGE))
        
        # 更新姿态标题
        if hasattr(self, 'user_pose_label'):
            self.user_pose_label.setText(self.translate(TK.UI.RESULTS.USER_POSE))
        if hasattr(self, 'standard_pose_label'):
            self.standard_pose_label.setText(self.translate(TK.UI.RESULTS.STANDARD_POSE))
        
        # 重新构建详细测量文本
        if hasattr(self, 'measurements_text'):
            detailed_info = self.build_detailed_measurements_text()
            self.measurements_text.setText(detailed_info)
    
    def create_score_section(self, layout):
        """创建得分区域"""
        score_frame = QFrame()
        score_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 2px solid #4169e1;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        score_layout = QHBoxLayout()

        # 主得分
        score = self.comparison_result.get('score', 0)
        self.score_label = QLabel()
        self.score_label.setStyleSheet('font-size: 28px; font-weight: bold; color: #4169e1;')
        score_layout.addWidget(self.score_label)

        # 如果是实验结果，显示更详细信息
        if self.is_experimental:
            self.detail_label = QLabel()
            self.detail_label.setStyleSheet('font-size: 16px; color: #666;')
            score_layout.addWidget(self.detail_label)

        score_frame.setLayout(score_layout)
        layout.addWidget(score_frame)
    
    def create_tab_widget(self, layout):
        """创建标签页组件"""
        self.tab_widget = QTabWidget()

        # 视频对比标签页
        self.create_video_tab(self.tab_widget)

        # 动作分析标签页
        self.create_analysis_tab(self.tab_widget)

        # 如果是实验结果，添加详细测量标签页
        if self.is_experimental:
            self.create_detailed_measurements_tab(self.tab_widget)
            self.create_pose_visualization_tab(self.tab_widget)

        layout.addWidget(self.tab_widget)
    
    def create_video_tab(self, tab_widget):
        """创建视频对比标签页"""
        video_widget = QWidget()
        video_layout = QVBoxLayout()

        # 视频标题
        title_layout = QHBoxLayout()
        self.user_title = QLabel()
        self.user_title.setStyleSheet('font-size: 16px; font-weight: bold;')
        self.user_title.setAlignment(Qt.AlignCenter)

        self.standard_title = QLabel()
        self.standard_title.setStyleSheet('font-size: 16px; font-weight: bold;')
        self.standard_title.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(self.user_title)
        title_layout.addWidget(self.standard_title)
        video_layout.addLayout(title_layout)

        # 视频播放器
        player_layout = QHBoxLayout()
        self.user_video_player = EnhancedVideoPlayer()
        self.user_video_player.set_video(self.user_video_path)
        self.standard_video_player = EnhancedVideoPlayer()
        self.standard_video_player.set_video(self.standard_video_path)

        player_layout.addWidget(self.user_video_player)
        player_layout.addWidget(self.standard_video_player)
        video_layout.addLayout(player_layout)

        video_widget.setLayout(video_layout)
        tab_widget.addTab(video_widget, "")  # 标题将在update_ui_texts中设置
    
    def create_analysis_tab(self, tab_widget):
        """创建动作分析标签页"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout()

        # 关键动作分析
        self.analysis_label = QLabel()
        analysis_layout.addWidget(self.analysis_label)

        self.movements_list = QListWidget()
        self.movements_list.setStyleSheet("""
            QListWidget::item {
                border-bottom: 1px solid #ddd;
                padding: 10px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
            }
        """)

        # Existing legacy movements (旧评估数据)
        legacy_movements = self.comparison_result.get('key_movements', [])
        for movement in legacy_movements:
            self.add_movement_item(movement)

        # New Evaluation summary (整体评价)
        if self.new_evaluation:
            overall_summary = self.new_evaluation.get('summary')
            if overall_summary:
                summary_item = {
                    'name': 'Evaluation Summary',
                    'summary': overall_summary,
                    'suggestion': overall_summary,
                    'score': self.new_evaluation.get('overall_score', 0),
                    'evaluation_summary': True
                }
                self.add_movement_item(summary_item)

            # Map new evaluation stages (新评价阶段)
            existing_names = {m.get('name') for m in legacy_movements}
            for st in self.new_evaluation.get('stages', []):
                stage_name = st.get('name')
                if stage_name in existing_names:
                    continue
                measurements = st.get('measurements', [])
                fails = [m for m in measurements if m.get('passed') is False]
                if fails:
                    # Use feedback from failed measurements; pick up to 2
                    fail_feedback = [m.get('feedback') for m in fails if m.get('feedback')]
                    if not fail_feedback:
                        fail_feedback = [f"{len(fails)} measurements need improvement"]
                    suggestion_text = ' | '.join(fail_feedback[:2])
                else:
                    suggestion_text = 'All measurements acceptable'

                pseudo = {
                    'name': stage_name,
                    'summary': f"Stage Score: {st.get('score', 0):.2f}",
                    'suggestion': suggestion_text,
                    'score': st.get('score', 0),
                    # Keep original raw evaluation measurements for richer formatting
                    'evaluation_measurements': measurements
                }
                self.add_movement_item(pseudo)

        analysis_layout.addWidget(self.movements_list)
        analysis_widget.setLayout(analysis_layout)
        tab_widget.addTab(analysis_widget, "")  # 标题将在update_ui_texts中设置
    
    def add_movement_item(self, movement):
        """添加动作项目"""
        item = QListWidgetItem()
        
        name = movement.get('name', 'Stage')
        display_text = f"【{name}】\n"

        # Evaluation Summary special case
        if movement.get('evaluation_summary'):
            display_text += movement.get('summary', '')
        else:
            display_text += f"{self.translate(TK.UI.RESULTS.ANALYSIS_RESULT)}: {movement.get('summary','')}\n"
            display_text += f"{self.translate(TK.UI.RESULTS.SUGGESTION)}: {movement.get('suggestion','')}"

        # New evaluation measurement rich formatting
        if 'evaluation_measurements' in movement:
            display_text += f"\n\n{self.translate(TK.UI.RESULTS.DETAILED_MEASUREMENTS)}:"
            eval_meas = movement['evaluation_measurements']
            for m in eval_meas:
                key = m.get('key')
                val = m.get('value')
                score = m.get('score')
                passed = m.get('passed')
                feedback = m.get('feedback')
                icon = '✅' if passed else '❌'
                val_txt = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
                score_txt = f"{score:.0%}" if isinstance(score, (int, float)) else 'N/A'
                feedback_txt = f" - {feedback}" if feedback else ''
                display_text += f"\n  {icon} {key}: {val_txt}  ({score_txt}){feedback_txt}"

        # 旧实验详细测量（保留原逻辑）
        if self.is_experimental and 'detailed_measurements' in movement and 'evaluation_measurements' not in movement:
            display_text += f"\n\n{self.translate(TK.UI.RESULTS.DETAILED_MEASUREMENTS)}:"
            for measurement in movement['detailed_measurements']:
                display_text += f"\n{measurement}"
        
        item.setText(display_text)
        
        # 根据得分设置颜色
        if (self.is_experimental or 'evaluation_measurements' in movement or movement.get('evaluation_summary')) and 'score' in movement:
            score = movement['score']
            if score >= 0.8:
                item.setBackground(Qt.green)
                item.setForeground(Qt.white)
            elif score >= 0.6:
                item.setBackground(Qt.yellow)
            else:
                item.setBackground(Qt.red)
                item.setForeground(Qt.white)
        
        self.movements_list.addItem(item)
    
    def create_detailed_measurements_tab(self, tab_widget):
        """创建详细测量标签页（仅实验模式）"""
        measurements_widget = QWidget()
        measurements_layout = QVBoxLayout()

        self.measurements_label = QLabel()
        measurements_layout.addWidget(self.measurements_label)

        self.measurements_text = QTextEdit()
        self.measurements_text.setReadOnly(True)
        self.measurements_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f8f8f8;
            }
        """)

        measurements_layout.addWidget(self.measurements_text)
        measurements_widget.setLayout(measurements_layout)
        tab_widget.addTab(measurements_widget, "")  # 标题将在update_ui_texts中设置
    
    def create_pose_visualization_tab(self, tab_widget):
        """创建姿态可视化标签页（仅实验模式）"""
        pose_widget = QWidget()
        pose_layout = QVBoxLayout()

        self.pose_label = QLabel()
        pose_layout.addWidget(self.pose_label)

        # 检查是否有姿态图像
        has_pose_images = False
        for movement in self.comparison_result.get('key_movements', []):
            if movement.get('user_image') or movement.get('standard_image'):
                has_pose_images = True
                break

        if has_pose_images:
            self.create_pose_image_display(pose_layout)
        else:
            self.no_image_label = QLabel()
            self.no_image_label.setAlignment(Qt.AlignCenter)
            self.no_image_label.setStyleSheet("color: #666; font-size: 14px;")
            pose_layout.addWidget(self.no_image_label)

        pose_widget.setLayout(pose_layout)
        tab_widget.addTab(pose_widget, "")  # 标题将在update_ui_texts中设置
    
    def create_pose_image_display(self, layout):
        """创建姿态图像显示"""
        image_layout = QHBoxLayout()

        # 获取第一个有效的图像路径
        user_image_path = None
        standard_image_path = None

        for movement in self.comparison_result.get('key_movements', []):
            if movement.get('user_image'):
                user_image_path = movement['user_image']
            if movement.get('standard_image'):
                standard_image_path = movement['standard_image']
            if user_image_path and standard_image_path:
                break

        # 用户姿态图像
        if user_image_path and os.path.exists(user_image_path):
            self.user_pose_label = QLabel()
            self.user_pose_label.setAlignment(Qt.AlignCenter)
            user_image_label = QLabel()
            pixmap = QPixmap(user_image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                user_image_label.setPixmap(scaled_pixmap)
            user_image_label.setAlignment(Qt.AlignCenter)

            user_frame = QFrame()
            user_frame_layout = QVBoxLayout()
            user_frame_layout.addWidget(self.user_pose_label)
            user_frame_layout.addWidget(user_image_label)
            user_frame.setLayout(user_frame_layout)
            image_layout.addWidget(user_frame)

        # 标准姿态图像
        if standard_image_path and os.path.exists(standard_image_path):
            self.standard_pose_label = QLabel()
            self.standard_pose_label.setAlignment(Qt.AlignCenter)
            standard_image_label = QLabel()
            pixmap = QPixmap(standard_image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                standard_image_label.setPixmap(scaled_pixmap)
            standard_image_label.setAlignment(Qt.AlignCenter)

            standard_frame = QFrame()
            standard_frame_layout = QVBoxLayout()
            standard_frame_layout.addWidget(self.standard_pose_label)
            standard_frame_layout.addWidget(standard_image_label)
            standard_frame.setLayout(standard_frame_layout)
            image_layout.addWidget(standard_frame)

        layout.addLayout(image_layout)
    
    def build_detailed_measurements_text(self):
        """构建详细测量信息文本"""
        info_lines = []
        info_lines.append(f"=== {self.translate(TK.UI.RESULTS.COMPARISON_REPORT)} ===\n")
        
        # 基本信息
        info_lines.append(f"{self.translate(TK.UI.RESULTS.SPORT_TYPE)}: {self.comparison_result.get('sport', self.translate(TK.UI.RESULTS.UNKNOWN))}")
        info_lines.append(f"{self.translate(TK.UI.RESULTS.ACTION_TYPE)}: {self.comparison_result.get('action', self.translate(TK.UI.RESULTS.UNKNOWN))}")
        analysis_type = self.translate(TK.UI.RESULTS.ADVANCED_ANALYSIS) if self.is_experimental else self.translate(TK.UI.RESULTS.BASIC_ANALYSIS)
        info_lines.append(f"{self.translate(TK.UI.RESULTS.ANALYSIS_TYPE)}: {analysis_type}")
        
        # 对比信息
        if 'comparison_info' in self.comparison_result:
            comp_info = self.comparison_result['comparison_info']
            info_lines.append("")
            info_lines.append(f"=== {self.translate(TK.UI.RESULTS.COMPARISON_DATA)} ===")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.USER_FRAME)}: {comp_info.get('user_frame', self.translate(TK.UI.RESULTS.UNKNOWN))}")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.STANDARD_FRAME)}: {comp_info.get('standard_frame', self.translate(TK.UI.RESULTS.UNKNOWN))}")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.RULES_APPLIED)}: {', '.join(comp_info.get('rules_applied', []))}")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.TOTAL_COMPARISONS)}: {comp_info.get('total_comparisons', 0)}")
        
        info_lines.append("")
        
        # 整体得分
        score = self.comparison_result.get('score', 0)
        detailed_score = self.comparison_result.get('detailed_score', 0)
        info_lines.append(f"{self.translate(TK.UI.RESULTS.OVERALL_SCORE)}: {score}/100")
        if self.is_experimental:
            info_lines.append(f"{self.translate(TK.UI.RESULTS.DETAILED_SCORE)}: {detailed_score:.2%}")
        info_lines.append("")
        
        # 各阶段分析
        for i, movement in enumerate(self.comparison_result.get('key_movements', []), 1):
            info_lines.append(f"=== {self.translate(TK.UI.RESULTS.STAGE)} {i}: {movement['name']} ===")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.ANALYSIS_RESULT)}: {movement['summary']}")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.SUGGESTION)}: {movement['suggestion']}")
            
            if self.is_experimental and 'score' in movement:
                info_lines.append(f"{self.translate(TK.UI.RESULTS.STAGE_SCORE)}: {movement['score']:.2%}")
            
            # 核心对比数据
            if 'detailed_measurements' in movement:
                info_lines.append(f"\n--- {self.translate(TK.UI.RESULTS.COMPARISON_DATA)} ---")
                for measurement in movement['detailed_measurements']:
                    info_lines.append(f"  {measurement}")
            
            info_lines.append("")
        
        # 错误信息
        if 'error' in self.comparison_result:
            info_lines.append(f"=== {self.translate(TK.UI.RESULTS.ERROR_INFO)} ===")
            info_lines.append(self.comparison_result['error'])
        
        return "\n".join(info_lines)