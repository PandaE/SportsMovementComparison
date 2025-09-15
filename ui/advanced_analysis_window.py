"""
Advanced Analysis Window - 高级分析结果窗口
包含视频预览区域和阶段分析区域的新布局
"""

import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QScrollArea, QLabel, QFrame, QSpinBox, QPushButton,
                            QGroupBox, QGridLayout, QSplitter, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

from .video_player import VideoPlayer


class StageAnalysisWidget(QWidget):
    """单个阶段分析组件"""
    
    frameChanged = pyqtSignal(str, int, int)  # 阶段名, 用户帧, 标准帧
    
    def __init__(self, stage_name: str, user_frame: int, standard_frame: int, 
                 user_video_path: str, standard_video_path: str, 
                 comparison_results: dict = None):
        super().__init__()
        self.stage_name = stage_name
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        self.comparison_results = comparison_results or {}
        
        self.init_ui()
        self.set_frames(user_frame, standard_frame)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 阶段标题
        title_label = QLabel(f"📊 {self.stage_name}")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 关键帧对比区域
        frames_group = QGroupBox("关键帧对比")
        frames_layout = QHBoxLayout(frames_group)
        
        # 用户视频帧
        user_frame_widget = self.create_frame_widget("用户视频", True)
        frames_layout.addWidget(user_frame_widget)
        
        # 标准视频帧
        standard_frame_widget = self.create_frame_widget("标准视频", False)
        frames_layout.addWidget(standard_frame_widget)
        
        layout.addWidget(frames_group)
        
        # 对比结果区域
        results_group = QGroupBox("对比分析结果")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # 更新对比结果显示
        self.update_comparison_results()
    
    def create_frame_widget(self, title: str, is_user: bool) -> QWidget:
        """创建单个帧显示组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 图像显示
        image_label = QLabel()
        image_label.setFixedSize(200, 150)
        image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setText("加载中...")
        
        if is_user:
            self.user_image_label = image_label
        else:
            self.standard_image_label = image_label
        
        layout.addWidget(image_label)
        
        # 帧数控制
        frame_control_layout = QHBoxLayout()
        
        frame_label = QLabel("帧数:")
        frame_control_layout.addWidget(frame_label)
        
        frame_spinbox = QSpinBox()
        frame_spinbox.setMinimum(0)
        frame_spinbox.setMaximum(9999)
        
        if is_user:
            self.user_frame_spinbox = frame_spinbox
            # 不自动连接valueChanged信号
        else:
            self.standard_frame_spinbox = frame_spinbox
            # 不自动连接valueChanged信号
        
        frame_control_layout.addWidget(frame_spinbox)
        
        # 更新按钮
        update_btn = QPushButton("更新")
        update_btn.clicked.connect(self.on_update_clicked)
        frame_control_layout.addWidget(update_btn)
        
        layout.addLayout(frame_control_layout)
        
        return widget
    
    def set_frames(self, user_frame: int, standard_frame: int):
        """设置帧数"""
        self.user_frame_spinbox.setValue(user_frame)
        self.standard_frame_spinbox.setValue(standard_frame)
        self.load_frame_images()
    
    def load_frame_images(self):
        """加载并显示帧图像"""
        # 加载用户视频帧
        user_frame = self.extract_frame(self.user_video_path, self.user_frame_spinbox.value())
        if user_frame is not None:
            self.display_frame(user_frame, self.user_image_label)
        
        # 加载标准视频帧
        standard_frame = self.extract_frame(self.standard_video_path, self.standard_frame_spinbox.value())
        if standard_frame is not None:
            self.display_frame(standard_frame, self.standard_image_label)
    
    def extract_frame(self, video_path: str, frame_number: int) -> np.ndarray:
        """从视频中提取指定帧"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return frame
        except Exception as e:
            print(f"提取帧失败: {e}")
        
        return None
    
    def display_frame(self, frame: np.ndarray, label: QLabel):
        """在标签中显示帧"""
        try:
            # 转换颜色空间
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 调整大小
            h, w, ch = rgb_frame.shape
            target_w, target_h = 200, 150
            
            # 计算缩放比例，保持宽高比
            scale = min(target_w/w, target_h/h)
            new_w, new_h = int(w*scale), int(h*scale)
            
            resized = cv2.resize(rgb_frame, (new_w, new_h))
            
            # 转换为QPixmap - 修复图像格式
            from PyQt5.QtGui import QImage
            bytes_per_line = 3 * new_w
            q_image = QImage(resized.data, new_w, new_h, bytes_per_line, QImage.Format_RGB888)
            q_pixmap = QPixmap.fromImage(q_image)
            
            label.setPixmap(q_pixmap)
            label.setScaledContents(True)
            
        except Exception as e:
            print(f"显示帧失败: {e}")
            label.setText("显示失败")
    
    def on_update_clicked(self):
        """点击更新按钮时的处理"""
        # 更新帧显示
        self.load_frame_images()
        
        # 发射帧数改变信号，触发重新分析
        user_frame = self.user_frame_spinbox.value()
        standard_frame = self.standard_frame_spinbox.value()
        self.frameChanged.emit(self.stage_name, user_frame, standard_frame)
        
        print(f"🔄 手动更新阶段 '{self.stage_name}' 的帧数: 用户帧 {user_frame}, 标准帧 {standard_frame}")
    
    def update_frames(self):
        """更新帧显示（兼容旧接口）"""
        self.on_update_clicked()
    
    def update_comparison_results(self):
        """更新对比结果显示"""
        if not self.comparison_results:
            self.results_text.setText("暂无对比数据")
            return
        
        # 构建对比结果文本
        results_text = ""
        
        # 显示阶段信息
        stage_info = self.comparison_results.get('stage_info', {})
        if stage_info:
            score = stage_info.get('score', 0)
            status = stage_info.get('status', '未知')
            results_text += f"📈 阶段得分: {score:.1f}%\n"
            results_text += f"📊 分析结果: {status}\n\n"
        
        # 显示测量对比
        measurements = self.comparison_results.get('measurements', [])
        if measurements:
            results_text += "📏 测量对比:\n"
            for measurement in measurements:
                rule_name = measurement.get('rule_name', '未知规则')
                user_value = measurement.get('user_value', 0)
                standard_value = measurement.get('standard_value', 0)
                is_within_range = measurement.get('is_within_range', False)
                
                status_icon = "✅" if is_within_range else "❌"
                results_text += f"  {status_icon} {rule_name}: 用户 {user_value:.1f}° vs 标准 {standard_value:.1f}°\n"
        
        if not results_text.strip():
            results_text = "暂无详细对比数据"
        
        self.results_text.setText(results_text)


class AdvancedAnalysisWindow(QMainWindow):
    """高级分析结果窗口"""
    
    def __init__(self, comparison_results: dict, user_video_path: str, standard_video_path: str, language='zh'):
        super().__init__()
        self.comparison_results = comparison_results
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        self.language = language
        self.translations = {
            'zh': {
                'title': '高级分析结果 - 动作对比分析',
                'video_preview': '🎬 视频预览区域',
                'user_video': '用户视频',
                'standard_video': '标准视频',
                'stage_analysis': '📈 阶段分析区域',
            },
            'en': {
                'title': 'Advanced Analysis - Movement Comparison',
                'video_preview': '🎬 Video Preview',
                'user_video': 'User Video',
                'standard_video': 'Standard Video',
                'stage_analysis': '📈 Stage Analysis',
            }
        }
        self.init_ui()
        self.setup_data()

    def tr_text(self, key):
        return self.translations.get(self.language, self.translations['zh']).get(key, key)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.tr_text('title'))
        self.setGeometry(100, 100, 1400, 800)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局 - 水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)

        # 第一块：视频预览区域
        self.create_video_preview_area(main_splitter)

        # 第二块：阶段分析区域
        self.create_stage_analysis_area(main_splitter)

        # 设置分割器比例
        main_splitter.setSizes([500, 900])
    
    def create_video_preview_area(self, parent_splitter):
        """创建视频预览区域"""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        # 标题
        title_label = QLabel(self.tr_text('video_preview'))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        preview_layout.addWidget(title_label)

        # 用户视频播放器
        user_group = QGroupBox(self.tr_text('user_video'))
        user_layout = QVBoxLayout(user_group)

        self.user_video_player = VideoPlayer()
        self.user_video_player.setMaximumHeight(200)
        user_layout.addWidget(self.user_video_player)

        preview_layout.addWidget(user_group)

        # 标准视频播放器
        standard_group = QGroupBox(self.tr_text('standard_video'))
        standard_layout = QVBoxLayout(standard_group)

        self.standard_video_player = VideoPlayer()
        self.standard_video_player.setMaximumHeight(200)
        standard_layout.addWidget(self.standard_video_player)

        preview_layout.addWidget(standard_group)

        # 添加伸缩空间
        preview_layout.addStretch()

        parent_splitter.addWidget(preview_widget)
    
    def create_stage_analysis_area(self, parent_splitter):
        """创建阶段分析区域"""
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 滚动内容
        scroll_content = QWidget()
        self.stages_layout = QVBoxLayout(scroll_content)

        # 标题
        title_label = QLabel(self.tr_text('stage_analysis'))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.stages_layout.addWidget(title_label)

        # 这里将添加各个阶段的分析组件
        self.stage_widgets = []

        # 添加伸缩空间
        self.stages_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        parent_splitter.addWidget(scroll_area)
    
    def setup_data(self):
        """设置数据和加载视频"""
        # 加载视频 (仅当文件存在时)
        try:
            if self.user_video_path:
                self.user_video_player.set_video(self.user_video_path)
        except Exception as e:
            print(f"加载用户视频失败: {e}")
        
        try:
            if self.standard_video_path:
                self.standard_video_player.set_video(self.standard_video_path)
        except Exception as e:
            print(f"加载标准视频失败: {e}")
        
        # 创建阶段分析组件
        self.create_stage_widgets()
    
    def create_stage_widgets(self):
        """根据分析结果创建阶段组件"""
        # 从对比结果中提取阶段信息
        stages_data = self.extract_stages_data()
        
        for stage_data in stages_data:
            stage_widget = StageAnalysisWidget(
                stage_name=stage_data['name'],
                user_frame=stage_data['user_frame'],
                standard_frame=stage_data['standard_frame'],
                user_video_path=self.user_video_path,
                standard_video_path=self.standard_video_path,
                comparison_results=stage_data['results']
            )
            
            # 连接信号
            stage_widget.frameChanged.connect(self.on_stage_frame_changed)
            
            self.stage_widgets.append(stage_widget)
            self.stages_layout.insertWidget(-1, stage_widget)  # 在stretch之前插入
    
    def extract_stages_data(self) -> list:
        """从对比结果中提取阶段数据"""
        stages_data = []
        
        # 如果有详细的阶段数据，使用它们
        if 'stages' in self.comparison_results:
            for stage_name, stage_info in self.comparison_results['stages'].items():
                stages_data.append({
                    'name': stage_name,
                    'user_frame': stage_info.get('user_frame', 0),
                    'standard_frame': stage_info.get('standard_frame', 0),
                    'results': stage_info
                })
        else:
            # 否则创建默认阶段
            stages_data = [
                {
                    'name': '架拍阶段结束',
                    'user_frame': 30,
                    'standard_frame': 25,
                    'results': self.comparison_results
                },
                {
                    'name': '击球瞬间',
                    'user_frame': 60,
                    'standard_frame': 55,
                    'results': {}
                },
                {
                    'name': '随挥完成',
                    'user_frame': 90,
                    'standard_frame': 85,
                    'results': {}
                }
            ]
        
        return stages_data
    
    def on_stage_frame_changed(self, stage_name: str, user_frame: int, standard_frame: int):
        """阶段帧数改变处理"""
        print(f"阶段 {stage_name} 帧数更新: 用户帧 {user_frame}, 标准帧 {standard_frame}")
        
        # 触发该阶段的重新分析
        self.reanalyze_stage(stage_name, user_frame, standard_frame)
    
    def reanalyze_stage(self, stage_name: str, user_frame: int, standard_frame: int):
        """重新分析指定阶段"""
        try:
            print(f"🔄 开始重新分析阶段: {stage_name}")
            
            # 检查是否有可用的分析引擎
            if not hasattr(self, 'analysis_engine'):
                # 尝试创建分析引擎
                from core.experimental_comparison_engine import ExperimentalComparisonEngine
                self.analysis_engine = ExperimentalComparisonEngine(use_experimental_features=True)
            
            if not self.analysis_engine or not self.analysis_engine.experimental_ready:
                print("❌ 分析引擎未就绪")
                return
            
            # 从视频中提取指定帧
            user_frame_image = self.extract_frame_from_video(self.user_video_path, user_frame)
            standard_frame_image = self.extract_frame_from_video(self.standard_video_path, standard_frame)
            
            if user_frame_image is None or standard_frame_image is None:
                print("❌ 无法提取指定帧")
                return
            
            # 获取运动配置
            from core.experimental.config.sport_configs import SportConfigs
            config = SportConfigs.get_config("badminton", "clear")
            
            # 找到对应的阶段配置
            stage_config = None
            for stage in config.stages:
                if stage.name == stage_name:
                    stage_config = stage
                    break
            
            if not stage_config:
                print(f"❌ 找不到阶段配置: {stage_name}")
                return
            
            # 执行阶段分析
            stage_result = self.analysis_engine._analyze_stage(
                user_frame_image, standard_frame_image, stage_config
            )
            
            # 更新对应阶段组件的显示
            self.update_stage_widget_results(stage_name, stage_result, user_frame, standard_frame)
            
            print(f"✅ 阶段 {stage_name} 重新分析完成，得分: {stage_result.get('score', 0):.2f}")
            
        except Exception as e:
            print(f"❌ 重新分析失败: {e}")
            import traceback
            traceback.print_exc()
    
    def extract_frame_from_video(self, video_path: str, frame_number: int):
        """从视频中提取指定帧"""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            
            # 检查视频是否成功打开
            if not cap.isOpened():
                print(f"无法打开视频: {video_path}")
                return None
            
            # 设置帧位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return frame
            else:
                print(f"无法读取帧 {frame_number}")
                return None
                
        except Exception as e:
            print(f"提取帧失败: {e}")
            return None
    
    def update_stage_widget_results(self, stage_name: str, stage_result: dict, user_frame: int, standard_frame: int):
        """更新阶段组件的结果显示"""
        try:
            # 找到对应的阶段组件
            target_widget = None
            for widget in self.stage_widgets:
                if widget.stage_name == stage_name:
                    target_widget = widget
                    break
            
            if not target_widget:
                print(f"找不到阶段组件: {stage_name}")
                return
            
            # 更新帧数（如果不一致）
            if target_widget.user_frame_spinbox.value() != user_frame:
                target_widget.user_frame_spinbox.setValue(user_frame)
            if target_widget.standard_frame_spinbox.value() != standard_frame:
                target_widget.standard_frame_spinbox.setValue(standard_frame)
            
            # 更新比较结果数据
            target_widget.comparison_results = {
                'stage_info': {
                    'score': stage_result.get('score', 0) * 100,
                    'status': f"{stage_name}: 重新分析完成 (得分: {stage_result.get('score', 0)*100:.1f}%)"
                },
                'measurements': []
            }
            
            # 转换测量数据格式
            for measurement in stage_result.get('measurements', []):
                measurement_info = {
                    'rule_name': measurement.get('measurement_name', '未知规则'),
                    'user_value': measurement.get('user_value', 0),
                    'standard_value': measurement.get('standard_value', 0),
                    'is_within_range': measurement.get('is_within_tolerance', False),
                    'measurement_points': measurement.get('keypoints', [])
                }
                target_widget.comparison_results['measurements'].append(measurement_info)
            
            # 刷新显示
            target_widget.update_comparison_results()
            target_widget.load_frame_images()  # 重新加载帧图像
            
            print(f"✅ 更新阶段组件 {stage_name} 显示完成")
            
        except Exception as e:
            print(f"❌ 更新阶段组件显示失败: {e}")
            import traceback
            traceback.print_exc()
        
    def load_video_files(self, user_video_path: str, standard_video_path: str):
        """加载视频文件"""
        self.user_video_path = user_video_path
        self.standard_video_path = standard_video_path
        
        if self.user_video_player:
            try:
                self.user_video_player.set_video(user_video_path)
            except Exception as e:
                print(f"加载用户视频失败: {e}")
        
        if self.standard_video_player:
            try:
                self.standard_video_player.set_video(standard_video_path)
            except Exception as e:
                print(f"加载标准视频失败: {e}")