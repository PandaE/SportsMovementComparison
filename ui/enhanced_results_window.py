"""
Enhanced Results Window - 增强版结果显示窗口
Enhanced results display window for comparison results with full internationalization support
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QTabWidget, QGroupBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from localization.i18n_manager import I18nManager
from localization.translation_keys import TK
from ui.i18n_mixin import I18nMixin
from .enhanced_video_player import EnhancedVideoPlayer
# from .edit_frames_dialog import EditFramesDialog  # Dialog no longer used after inline editing
from core.experimental_comparison_engine import ExperimentalComparisonEngine


class EnhancedResultsWindow(QWidget, I18nMixin):
    """增强版结果窗口 - 支持国际化"""
    
    def __init__(self, comparison_result, user_video_path, standard_video_path):
        super().__init__()
        I18nMixin.__init__(self)
        
        self.comparison_result = comparison_result
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        # Always treat as advanced/experimental mode
        # Detect new evaluation presence
        self.new_evaluation = comparison_result.get('new_evaluation')
        self.manual_frames_override = None
        self.engine = ExperimentalComparisonEngine()
        
        self.setGeometry(150, 150, 1400, 900)
        self.init_ui()
        self.update_ui_texts()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        # 得分区域
        self.create_score_section(layout)
        # 标签页（视频 + 合并阶段）
        self.create_tab_widget(layout)
        self.setLayout(layout)

    def update_ui_texts(self):
        """更新UI文本"""
        self.setWindowTitle(self.translate(TK.UI.RESULTS.TITLE))
        
        # 更新得分标签
        if hasattr(self, 'score_label'):
            score = self.comparison_result.get('score', 0)
            self.score_label.setText(f"{self.translate(TK.UI.RESULTS.SCORE)}: {score}")
        
        if hasattr(self, 'detail_label'):
            if self.new_evaluation:
                new_score = self.new_evaluation.get('overall_score')
                if isinstance(new_score, (int, float)):
                    try:
                        self.detail_label.setText(f"Eval Score: {new_score:.2f}")
                    except Exception:
                        self.detail_label.setText(f"Eval Score: {new_score}")
                else:
                    self.detail_label.setText("Eval Score: N/A")
            else:
                detailed_score = self.comparison_result.get('detailed_score', 0)
                try:
                    self.detail_label.setText(f"{self.translate(TK.UI.RESULTS.DETAILED_SCORE)}: {detailed_score:.2%}")
                except Exception:
                    self.detail_label.setText(f"{self.translate(TK.UI.RESULTS.DETAILED_SCORE)}: {detailed_score}")
        
        # 更新标签页标题（合并后仅两个标签）
        if hasattr(self, 'tab_widget') and self.tab_widget.count() >= 2:
            self.tab_widget.setTabText(0, self.translate(TK.UI.RESULTS.VIDEO_TAB))
            combined_key = getattr(TK.UI.RESULTS, 'COMBINED_STAGE_TAB', TK.UI.RESULTS.ANALYSIS_TAB)
            self.tab_widget.setTabText(1, self.translate(combined_key))
        
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

        # 总是显示详细信息标签（用于详细得分或新评价得分）
        self.detail_label = QLabel()
        self.detail_label.setStyleSheet('font-size: 16px; color: #666;')
        score_layout.addWidget(self.detail_label)

    # （移除手动覆盖徽章，按需求不再显示）

        score_frame.setLayout(score_layout)
        layout.addWidget(score_frame)
    
    def create_tab_widget(self, layout):
        """创建标签页组件"""
        self.tab_widget = QTabWidget()
        self.create_video_tab(self.tab_widget)
        self.create_combined_stage_tab(self.tab_widget)
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

    def create_combined_stage_tab(self, tab_widget):
        """创建合并的阶段分析/详细测量/姿态可视化标签页"""
        combined_widget = QWidget()
        main_layout = QVBoxLayout()

        # 编辑关键帧按钮
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel
        top_row = QHBoxLayout()
        # Inline edit hint label
        self.inline_edit_hint = QLabel(self.translate(getattr(TK.UI.RESULTS, 'EDIT_FRAMES', TK.UI.RESULTS.ANALYSIS_TAB)))
        self.inline_edit_hint.setStyleSheet('font-size:13px; font-weight:bold;')
        top_row.addWidget(self.inline_edit_hint, 0, Qt.AlignLeft)
        # Rerun button to apply manual frame overrides
        self.rerun_btn = QPushButton(self.translate(getattr(TK.UI.RESULTS, 'RERUN_ANALYSIS', TK.UI.RESULTS.ANALYSIS_TAB)))
        self.rerun_btn.clicked.connect(self.collect_and_rerun_manual_frames)
        top_row.addWidget(self.rerun_btn, 0, Qt.AlignLeft)
        main_layout.addLayout(top_row)

        # 聚合阶段数据
        movements = []
        legacy_movements = self.comparison_result.get('key_movements', []) or []
        movements.extend(legacy_movements)

        if self.new_evaluation:
            refined = self.new_evaluation.get('refined_summary') or self.new_evaluation.get('summary')
            if refined:
                movements.insert(0, {
                    'name': self.translate(TK.UI.RESULTS.EVAL_SUMMARY),
                    'summary': refined,
                    'suggestion': refined,
                    'score': self.new_evaluation.get('overall_score', 0),
                    'evaluation_summary': True,
                    'is_refined': bool(self.new_evaluation.get('refined_summary'))
                })
            existing_names = {m.get('name') for m in legacy_movements}
            for st in self.new_evaluation.get('stages', []):
                stage_name = st.get('name')
                if stage_name in existing_names:
                    for mv in movements:
                        if mv.get('name') == stage_name:
                            mv.setdefault('evaluation_measurements', st.get('measurements', []))
                            mv.setdefault('score', st.get('score'))
                            break
                    continue
                measurements = st.get('measurements', [])
                fails = [m for m in measurements if m.get('passed') is False]
                if fails:
                    fail_feedback = [m.get('feedback') for m in fails if m.get('feedback')]
                    if not fail_feedback:
                        fail_feedback = [self.translate(TK.UI.RESULTS.EVAL_NEEDS_IMPROVEMENT)]
                    suggestion_text = ' | '.join(fail_feedback[:2])
                else:
                    suggestion_text = self.translate(TK.UI.RESULTS.EVAL_ALL_ACCEPTABLE)
                stage_score_val = st.get('score', 0)
                if not isinstance(stage_score_val, (int, float)):
                    summary_score_text = f"{self.translate(TK.UI.RESULTS.EVAL_STAGE_SCORE)}: N/A"
                else:
                    try:
                        summary_score_text = f"{self.translate(TK.UI.RESULTS.EVAL_STAGE_SCORE)}: {stage_score_val:.2f}"
                    except Exception:
                        summary_score_text = f"{self.translate(TK.UI.RESULTS.EVAL_STAGE_SCORE)}: {stage_score_val}"
                movements.append({
                    'name': stage_name,
                    'summary': summary_score_text,
                    'suggestion': suggestion_text,
                    'score': stage_score_val if isinstance(stage_score_val, (int, float)) else 0,
                    'evaluation_measurements': measurements
                })

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()

        # Keep references to spinboxes per stage
        self._frame_spinboxes = {}

        for movement in movements:
            box = QGroupBox(movement.get('name', 'Stage'))
            box_layout = QVBoxLayout()
            stage_name = movement.get('name', 'Stage')

            # 姿态图像
            user_img = movement.get('user_image')
            std_img = movement.get('standard_image')
            if user_img or std_img:
                img_row = QHBoxLayout()
                if user_img and os.path.exists(user_img):
                    lbl_u = QLabel()
                    pm = QPixmap(user_img)
                    if not pm.isNull():
                        lbl_u.setPixmap(pm.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    lbl_u.setAlignment(Qt.AlignCenter)
                    lbl_u.setToolTip(self.translate(TK.UI.RESULTS.USER_POSE))
                    img_row.addWidget(lbl_u)
                if std_img and os.path.exists(std_img):
                    lbl_s = QLabel()
                    pm2 = QPixmap(std_img)
                    if not pm2.isNull():
                        lbl_s.setPixmap(pm2.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    lbl_s.setAlignment(Qt.AlignCenter)
                    lbl_s.setToolTip(self.translate(TK.UI.RESULTS.STANDARD_POSE))
                    img_row.addWidget(lbl_s)
                box_layout.addLayout(img_row)

            # 文本详情
            text_lines = []
            if movement.get('evaluation_summary'):
                # Overall evaluation summary line
                ov = self.new_evaluation.get('overall_score') if self.new_evaluation else None
                if isinstance(ov, (int, float)):
                    try:
                        text_lines.append(f"{self.translate(TK.UI.RESULTS.EVAL_OVERALL_SCORE)}: {ov:.2f}")
                    except Exception:
                        text_lines.append(f"{self.translate(TK.UI.RESULTS.EVAL_OVERALL_SCORE)}: {ov}")
                if movement.get('is_refined'):
                    text_lines.append(f"{self.translate(getattr(TK.UI.RESULTS, 'LLM_REFINED_SUMMARY', TK.UI.RESULTS.EVAL_SUMMARY))}: \n{movement.get('summary','')}")
                else:
                    text_lines.append(movement.get('summary', ''))
            else:
                text_lines.append(f"{self.translate(TK.UI.RESULTS.ANALYSIS_RESULT)}: {movement.get('summary','')}")
                text_lines.append(f"{self.translate(TK.UI.RESULTS.SUGGESTION)}: {movement.get('suggestion','')}")

            if 'evaluation_measurements' in movement:
                text_lines.append(f"\n{self.translate(TK.UI.RESULTS.DETAILED_MEASUREMENTS)}:")
                for m in movement['evaluation_measurements']:
                    key = m.get('key')
                    val = m.get('value')
                    score = m.get('score')
                    passed = m.get('passed')
                    feedback = m.get('feedback')
                    icon = '✅' if passed else '❌'
                    if isinstance(val, (int, float)):
                        try:
                            val_txt = f"{val:.2f}"
                        except Exception:
                            val_txt = str(val)
                    else:
                        val_txt = str(val)
                    score_txt = f"{score:.0%}" if isinstance(score, (int, float)) else 'N/A'
                    feedback_txt = f" - {feedback}" if feedback else ''
                    text_lines.append(f"  {icon} {key}: {val_txt} ({score_txt}){feedback_txt}")

            if 'detailed_measurements' in movement and 'evaluation_measurements' not in movement:
                text_lines.append(f"\n{self.translate(TK.UI.RESULTS.DETAILED_MEASUREMENTS)}:")
                for dm in movement['detailed_measurements']:
                    text_lines.append(f"  {dm}")

            detail_label = QLabel("\n".join(text_lines))
            detail_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            detail_label.setWordWrap(True)
            box_layout.addWidget(detail_label)

            # 显示帧号信息（如果有 key_frame_info）
            kfi = self.comparison_result.get('key_frame_info', {})
            user_frames_map = kfi.get('user_frames', {})
            std_frames_map = kfi.get('standard_frames', {})
            # Inline editable spinboxes for frames
            if stage_name in user_frames_map or stage_name in std_frames_map:
                from PyQt5.QtWidgets import QSpinBox, QFormLayout
                form = QFormLayout()
                user_spin = QSpinBox()
                std_spin = QSpinBox()
                # Determine sensible range based on loaded videos if available
                max_user = getattr(self.user_video_player, 'total_frames', 0) or 100000
                max_std = getattr(self.standard_video_player, 'total_frames', 0) or 100000
                user_spin.setRange(0, max_user if max_user > 0 else 100000)
                std_spin.setRange(0, max_std if max_std > 0 else 100000)
                user_val = user_frames_map.get(stage_name, 0)
                std_val = std_frames_map.get(stage_name, 0)
                if isinstance(user_val, int):
                    user_spin.setValue(user_val)
                if isinstance(std_val, int):
                    std_spin.setValue(std_val)
                form.addRow(self.translate(TK.UI.RESULTS.USER_FRAME), user_spin)
                form.addRow(self.translate(TK.UI.RESULTS.STANDARD_FRAME), std_spin)
                box_layout.addLayout(form)
                self._frame_spinboxes[stage_name] = {'user': user_spin, 'standard': std_spin}

            if 'score' in movement and isinstance(movement['score'], (int, float)):
                sc = movement['score']
                if sc >= 0.8:
                    box.setStyleSheet("QGroupBox { border:1px solid #4caf50; margin-top:6px; } QGroupBox::title{ color:#2e7d32; }")
                elif sc >= 0.6:
                    box.setStyleSheet("QGroupBox { border:1px solid #ffb300; margin-top:6px; } QGroupBox::title{ color:#ff6f00; }")
                else:
                    box.setStyleSheet("QGroupBox { border:1px solid #d32f2f; margin-top:6px; } QGroupBox::title{ color:#b71c1c; }")

            box.setLayout(box_layout)
            content_layout.addWidget(box)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        combined_widget.setLayout(main_layout)
        tab_widget.addTab(combined_widget, "")

    def collect_and_rerun_manual_frames(self):
        # Build manual frames override from spinboxes
        if not hasattr(self, '_frame_spinboxes') or not self._frame_spinboxes:
            return
        manual = {}
        for stage_name, spins in self._frame_spinboxes.items():
            manual[stage_name] = {
                'user': spins['user'].value(),
                'standard': spins['standard'].value()
            }
        self.manual_frames_override = manual
        self.rerun_with_manual_frames()

    def rerun_with_manual_frames(self):
        if not self.manual_frames_override:
            return
        try:
            current_tab = self.tab_widget.currentIndex() if hasattr(self, 'tab_widget') else 0
            new_result = self.engine.compare(
                self.user_video_path,
                self.standard_video_path,
                sport=self.comparison_result.get('sport','badminton'),
                action=self.comparison_result.get('action','clear'),
                manual_frames=self.manual_frames_override
            )
            # 保留手动覆盖标记
            self.comparison_result = new_result
            self.new_evaluation = new_result.get('new_evaluation')
            # 重新构建 UI （仅重建合并 tab 内容）
            # 移除旧第二个 tab 并重建
            if self.tab_widget.count() > 1:
                self.tab_widget.removeTab(1)
            self.create_combined_stage_tab(self.tab_widget)
            self.update_ui_texts()
            # 恢复原 tab
            if 0 <= current_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(current_tab)
            # 手动徽章需求取消，不再处理
        except Exception as e:
            print(f"Manual re-run failed: {e}")
    
    
    def build_detailed_measurements_text(self):
        """构建详细测量信息文本"""
        info_lines = []
        info_lines.append(f"=== {self.translate(TK.UI.RESULTS.COMPARISON_REPORT)} ===\n")
        
        # 基本信息
        info_lines.append(f"{self.translate(TK.UI.RESULTS.SPORT_TYPE)}: {self.comparison_result.get('sport', self.translate(TK.UI.RESULTS.UNKNOWN))}")
        info_lines.append(f"{self.translate(TK.UI.RESULTS.ACTION_TYPE)}: {self.comparison_result.get('action', self.translate(TK.UI.RESULTS.UNKNOWN))}")
        analysis_type = self.translate(TK.UI.RESULTS.ADVANCED_ANALYSIS)
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
        info_lines.append(f"{self.translate(TK.UI.RESULTS.DETAILED_SCORE)}: {detailed_score:.2%}")
        info_lines.append("")
        
        # 各阶段分析
        for i, movement in enumerate(self.comparison_result.get('key_movements', []), 1):
            info_lines.append(f"=== {self.translate(TK.UI.RESULTS.STAGE)} {i}: {movement['name']} ===")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.ANALYSIS_RESULT)}: {movement['summary']}")
            info_lines.append(f"{self.translate(TK.UI.RESULTS.SUGGESTION)}: {movement['suggestion']}")
            
            if 'score' in movement:
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

        # 新评价模块输出
        if self.new_evaluation:
            info_lines.append("")
            info_lines.append("=== New Evaluation Summary ===")
            ov_score = self.new_evaluation.get('overall_score')
            if isinstance(ov_score, (int, float)):
                try:
                    info_lines.append(f"Overall Eval Score: {ov_score:.2f}")
                except Exception:
                    info_lines.append(f"Overall Eval Score: {ov_score}")
            info_lines.append(f"Summary: {self.new_evaluation.get('summary','')}")
            for i, st in enumerate(self.new_evaluation.get('stages', []), 1):
                stage_score_val = st.get('score', 0)
                if isinstance(stage_score_val, (int, float)):
                    try:
                        stage_score_fmt = f"{stage_score_val:.2f}"
                    except Exception:
                        stage_score_fmt = str(stage_score_val)
                else:
                    stage_score_fmt = 'N/A'
                info_lines.append(f"--- Eval Stage {i}: {st.get('name')} ({stage_score_fmt}) ---")
                for mv in st.get('measurements', []):
                    key = mv.get('key')
                    val = mv.get('value')
                    score = mv.get('score')
                    passed = mv.get('passed')
                    feedback = mv.get('feedback')
                    icon = 'OK' if passed else 'NG'
                    if isinstance(val, (int, float)):
                        try:
                            val_txt = f"{val:.2f}"
                        except Exception:
                            val_txt = str(val)
                    else:
                        val_txt = str(val)
                    score_txt = f"{score:.0%}" if isinstance(score, (int, float)) else 'N/A'
                    feedback_txt = f" | {feedback}" if feedback else ''
                    info_lines.append(f"  {icon} {key}: {val_txt} ({score_txt}){feedback_txt}")
        
        return "\n".join(info_lines)