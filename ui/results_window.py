"""
results_window.py
Enhanced results display window for comparison results with experimental features support.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QGroupBox, QScrollArea, QFrame, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from ui.video_player import VideoPlayer

class ResultsWindow(QWidget):
    def __init__(self, comparison_result, user_video_path, standard_video_path):
        super().__init__()
        self.comparison_result = comparison_result
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        
        self.setWindowTitle('动作分析结果')
        self.setGeometry(150, 150, 1400, 900)
        
        # 检查是否是实验结果
        self.is_experimental = comparison_result.get('analysis_type') == 'experimental'
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 整体得分显示
        self.create_score_section(layout)
        
        # 创建标签页
        self.create_tab_widget(layout)
        
        self.setLayout(layout)
    
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
        score_label = QLabel(f"综合得分: {score}")
        score_label.setStyleSheet('font-size: 28px; font-weight: bold; color: #4169e1;')
        score_layout.addWidget(score_label)
        
        # 如果是实验结果，显示更详细信息
        if self.is_experimental:
            detailed_score = self.comparison_result.get('detailed_score', 0)
            detail_label = QLabel(f"详细得分: {detailed_score:.2%}")
            detail_label.setStyleSheet('font-size: 16px; color: #666;')
            score_layout.addWidget(detail_label)
        
        score_frame.setLayout(score_layout)
        layout.addWidget(score_frame)
    
    def create_tab_widget(self, layout):
        """创建标签页组件"""
        tab_widget = QTabWidget()
        
        # 视频对比标签页
        self.create_video_tab(tab_widget)
        
        # 动作分析标签页
        self.create_analysis_tab(tab_widget)
        
        # 如果是实验结果，添加详细测量标签页
        if self.is_experimental:
            self.create_detailed_measurements_tab(tab_widget)
            self.create_pose_visualization_tab(tab_widget)
        
        layout.addWidget(tab_widget)
    
    def create_video_tab(self, tab_widget):
        """创建视频对比标签页"""
        video_widget = QWidget()
        video_layout = QVBoxLayout()
        
        # 视频标题
        title_layout = QHBoxLayout()
        user_title = QLabel("用户视频")
        user_title.setStyleSheet('font-size: 16px; font-weight: bold;')
        user_title.setAlignment(Qt.AlignCenter)
        
        standard_title = QLabel("标准视频")
        standard_title.setStyleSheet('font-size: 16px; font-weight: bold;')
        standard_title.setAlignment(Qt.AlignCenter)
        
        title_layout.addWidget(user_title)
        title_layout.addWidget(standard_title)
        video_layout.addLayout(title_layout)
        
        # 视频播放器
        player_layout = QHBoxLayout()
        self.user_video_player = VideoPlayer()
        self.user_video_player.set_video(self.user_video_path)
        self.standard_video_player = VideoPlayer()
        self.standard_video_player.set_video(self.standard_video_path)
        
        player_layout.addWidget(self.user_video_player)
        player_layout.addWidget(self.standard_video_player)
        video_layout.addLayout(player_layout)
        
        video_widget.setLayout(video_layout)
        tab_widget.addTab(video_widget, "视频对比")
    
    def create_analysis_tab(self, tab_widget):
        """创建动作分析标签页"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout()
        
        # 关键动作分析
        analysis_layout.addWidget(QLabel('关键动作分析:'))
        
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
        
        for movement in self.comparison_result.get('key_movements', []):
            self.add_movement_item(movement)
        
        analysis_layout.addWidget(self.movements_list)
        analysis_widget.setLayout(analysis_layout)
        tab_widget.addTab(analysis_widget, "动作分析")
    
    def add_movement_item(self, movement):
        """添加动作项目"""
        item = QListWidgetItem()
        
        # 构建显示文本
        display_text = f"【{movement['name']}】\n"
        display_text += f"分析结果: {movement['summary']}\n"
        display_text += f"改进建议: {movement['suggestion']}"
        
        # 如果是实验结果，添加更多详细信息
        if self.is_experimental and 'detailed_measurements' in movement:
            display_text += "\n\n详细测量:"
            for measurement in movement['detailed_measurements']:
                display_text += f"\n{measurement}"
        
        item.setText(display_text)
        
        # 根据得分设置颜色
        if self.is_experimental and 'score' in movement:
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
        
        measurements_layout.addWidget(QLabel('详细测量数据:'))
        
        measurements_text = QTextEdit()
        measurements_text.setReadOnly(True)
        measurements_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background-color: #f8f8f8;
            }
        """)
        
        # 构建详细测量信息
        detailed_info = self.build_detailed_measurements_text()
        measurements_text.setText(detailed_info)
        
        measurements_layout.addWidget(measurements_text)
        measurements_widget.setLayout(measurements_layout)
        tab_widget.addTab(measurements_widget, "详细测量")
    
    def create_pose_visualization_tab(self, tab_widget):
        """创建姿态可视化标签页（仅实验模式）"""
        pose_widget = QWidget()
        pose_layout = QVBoxLayout()
        
        pose_layout.addWidget(QLabel('姿态对比可视化:'))
        
        # 检查是否有姿态图像
        has_pose_images = False
        for movement in self.comparison_result.get('key_movements', []):
            if movement.get('user_image') or movement.get('standard_image'):
                has_pose_images = True
                break
        
        if has_pose_images:
            self.create_pose_image_display(pose_layout)
        else:
            no_image_label = QLabel("暂无姿态可视化图像")
            no_image_label.setAlignment(Qt.AlignCenter)
            no_image_label.setStyleSheet("color: #666; font-size: 14px;")
            pose_layout.addWidget(no_image_label)
        
        pose_widget.setLayout(pose_layout)
        tab_widget.addTab(pose_widget, "姿态可视化")
    
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
            user_label = QLabel("用户姿态")
            user_label.setAlignment(Qt.AlignCenter)
            user_image_label = QLabel()
            pixmap = QPixmap(user_image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                user_image_label.setPixmap(scaled_pixmap)
            user_image_label.setAlignment(Qt.AlignCenter)
            
            user_frame = QFrame()
            user_frame_layout = QVBoxLayout()
            user_frame_layout.addWidget(user_label)
            user_frame_layout.addWidget(user_image_label)
            user_frame.setLayout(user_frame_layout)
            image_layout.addWidget(user_frame)
        
        # 标准姿态图像
        if standard_image_path and os.path.exists(standard_image_path):
            standard_label = QLabel("标准姿态")
            standard_label.setAlignment(Qt.AlignCenter)
            standard_image_label = QLabel()
            pixmap = QPixmap(standard_image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                standard_image_label.setPixmap(scaled_pixmap)
            standard_image_label.setAlignment(Qt.AlignCenter)
            
            standard_frame = QFrame()
            standard_frame_layout = QVBoxLayout()
            standard_frame_layout.addWidget(standard_label)
            standard_frame_layout.addWidget(standard_image_label)
            standard_frame.setLayout(standard_frame_layout)
            image_layout.addWidget(standard_frame)
        
        layout.addLayout(image_layout)
    
    def build_detailed_measurements_text(self):
        """构建详细测量信息文本"""
        info_lines = []
        info_lines.append("=== 对比分析报告 ===\n")
        
        # 基本信息
        info_lines.append(f"运动类型: {self.comparison_result.get('sport', '未知')}")
        info_lines.append(f"动作类型: {self.comparison_result.get('action', '未知')}")
        info_lines.append(f"分析类型: {'高级姿态分析' if self.is_experimental else '基础分析'}")
        
        # 对比信息
        if 'comparison_info' in self.comparison_result:
            comp_info = self.comparison_result['comparison_info']
            info_lines.append("")
            info_lines.append("=== 对比数据源 ===")
            info_lines.append(f"用户帧: {comp_info.get('user_frame', '未知')}")
            info_lines.append(f"标准帧: {comp_info.get('standard_frame', '未知')}")
            info_lines.append(f"应用规则: {', '.join(comp_info.get('rules_applied', []))}")
            info_lines.append(f"对比项目数: {comp_info.get('total_comparisons', 0)}")
        
        info_lines.append("")
        
        # 整体得分
        score = self.comparison_result.get('score', 0)
        detailed_score = self.comparison_result.get('detailed_score', 0)
        info_lines.append(f"综合得分: {score}/100")
        if self.is_experimental:
            info_lines.append(f"详细得分: {detailed_score:.2%}")
        info_lines.append("")
        
        # 各阶段分析
        for i, movement in enumerate(self.comparison_result.get('key_movements', []), 1):
            info_lines.append(f"=== 阶段 {i}: {movement['name']} ===")
            info_lines.append(f"分析结果: {movement['summary']}")
            info_lines.append(f"改进建议: {movement['suggestion']}")
            
            if self.is_experimental and 'score' in movement:
                info_lines.append(f"阶段得分: {movement['score']:.2%}")
            
            # 核心对比数据
            if 'detailed_measurements' in movement:
                info_lines.append("\n--- 对比数据 ---")
                for measurement in movement['detailed_measurements']:
                    info_lines.append(f"  {measurement}")
            
            info_lines.append("")
        
        # 错误信息
        if 'error' in self.comparison_result:
            info_lines.append("=== 错误信息 ===")
            info_lines.append(self.comparison_result['error'])
        
        return "\n".join(info_lines)
