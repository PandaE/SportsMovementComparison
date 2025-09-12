"""
test_detailed_measurements.py
测试增强的详细测量信息输出
"""
import sys
import os
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.experimental_comparison_engine import ExperimentalComparisonEngine
from ui.results_window import ResultsWindow


def create_test_image(width=640, height=480, person_type="standard"):
    """创建测试图像"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img.fill(200)  # 浅灰色背景
    
    # 绘制一个简单的人形轮廓用于测试
    center_x, center_y = width // 2, height // 2
    
    if person_type == "standard":
        # 标准姿势 - 手臂略微弯曲
        points = [
            (center_x, center_y - 100),  # 头部
            (center_x, center_y - 50),   # 颈部
            (center_x - 50, center_y - 30),  # 左肩
            (center_x + 50, center_y - 30),  # 右肩
            (center_x - 80, center_y + 20),  # 左肘
            (center_x + 80, center_y + 20),  # 右肘
            (center_x - 100, center_y + 70), # 左腕
            (center_x + 100, center_y + 70), # 右腕
        ]
    else:
        # 用户姿势 - 手臂角度稍有不同
        points = [
            (center_x, center_y - 100),  # 头部
            (center_x, center_y - 50),   # 颈部
            (center_x - 50, center_y - 30),  # 左肩
            (center_x + 50, center_y - 30),  # 右肩
            (center_x - 90, center_y + 10),  # 左肘 - 角度稍有不同
            (center_x + 70, center_y + 30),  # 右肘 - 角度稍有不同
            (center_x - 110, center_y + 80), # 左腕
            (center_x + 90, center_y + 80),  # 右腕
        ]
    
    # 绘制关键点
    for i, point in enumerate(points):
        cv2.circle(img, point, 5, (255, 0, 0), -1)
        cv2.putText(img, str(i), (point[0] + 10, point[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # 绘制连接线
    connections = [(1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7)]
    for start, end in connections:
        if start < len(points) and end < len(points):
            cv2.line(img, points[start], points[end], (0, 255, 0), 2)
    
    return img


class DetailedMeasurementTestWindow(QMainWindow):
    """详细测量信息测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("详细测量信息测试")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 测试按钮
        self.test_btn = QPushButton("运行详细测量分析测试")
        self.test_btn.clicked.connect(self.run_detailed_test)
        layout.addWidget(self.test_btn)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
            }
        """)
        layout.addWidget(self.result_text)
        
        # 显示结果窗口按钮
        self.show_results_btn = QPushButton("显示增强结果窗口")
        self.show_results_btn.clicked.connect(self.show_results_window)
        self.show_results_btn.setEnabled(False)
        layout.addWidget(self.show_results_btn)
        
        central_widget.setLayout(layout)
        
        self.comparison_result = None
    
    def run_detailed_test(self):
        """运行详细测量测试"""
        self.result_text.append("🔬 开始详细测量分析测试...\n")
        
        try:
            # 创建实验引擎
            engine = ExperimentalComparisonEngine(use_experimental_features=True)
            
            self.result_text.append("✓ 实验引擎初始化成功")
            self.result_text.append(f"实验功能状态: {'启用' if engine.experimental_ready else '禁用'}\n")
            
            # 创建测试图像
            self.result_text.append("📸 创建测试图像...")
            
            # 创建临时图像文件
            import tempfile
            temp_dir = tempfile.gettempdir()
            
            user_img = create_test_image(person_type="user")
            standard_img = create_test_image(person_type="standard")
            
            user_path = os.path.join(temp_dir, "test_user.jpg")
            standard_path = os.path.join(temp_dir, "test_standard.jpg")
            
            cv2.imwrite(user_path, user_img)
            cv2.imwrite(standard_path, standard_img)
            
            self.result_text.append(f"✓ 测试图像已保存:")
            self.result_text.append(f"  用户图像: {user_path}")
            self.result_text.append(f"  标准图像: {standard_path}\n")
            
            # 执行分析
            self.result_text.append("🔍 执行详细分析...")
            
            if engine.experimental_ready:
                result = engine.compare(user_path, standard_path, "badminton", "clear")
                self.comparison_result = result
                
                self.result_text.append("✅ 分析完成！\n")
                self.result_text.append("📊 分析结果概览:")
                self.result_text.append(f"综合得分: {result.get('score', 0)}")
                self.result_text.append(f"详细得分: {result.get('detailed_score', 0):.2%}")
                self.result_text.append(f"分析类型: {result.get('analysis_type', '未知')}\n")
                
                # 显示详细信息
                if 'analysis_details' in result:
                    details = result['analysis_details']
                    self.result_text.append("🔬 分析详细信息:")
                    self.result_text.append(f"  总测量项目: {details.get('total_measurements', 0)}")
                    self.result_text.append(f"  处理方法: {details.get('processing_method', '未知')}")
                    self.result_text.append(f"  测量类型: {', '.join(details.get('measurement_types', []))}\n")
                
                # 显示各阶段详细信息
                for i, movement in enumerate(result.get('key_movements', []), 1):
                    self.result_text.append(f"📋 阶段 {i}: {movement['name']}")
                    self.result_text.append(f"  得分: {movement.get('score', 0):.2%}")
                    self.result_text.append(f"  摘要: {movement['summary']}")
                    
                    if 'measurements_data' in movement:
                        self.result_text.append(f"  测量项目数: {len(movement['measurements_data'])}")
                        
                        for measurement in movement['measurements_data']:
                            self.result_text.append(f"\n    📏 {measurement.get('measurement_name', '未知')}")
                            self.result_text.append(f"      类型: {measurement.get('measurement_type', '未知')}")
                            self.result_text.append(f"      测量点: {' → '.join(measurement.get('keypoints', []))}")
                            self.result_text.append(f"      用户值: {measurement.get('user_value', 0):.2f}{measurement.get('unit', '')}")
                            self.result_text.append(f"      标准值: {measurement.get('standard_value', 0):.2f}{measurement.get('unit', '')}")
                            self.result_text.append(f"      差异: {measurement.get('difference', 0):+.2f}{measurement.get('unit', '')}")
                            self.result_text.append(f"      容差状态: {'✓ 达标' if measurement.get('is_within_tolerance', False) else '✗ 超标'}")
                    
                    self.result_text.append("")
                
                self.show_results_btn.setEnabled(True)
                
            else:
                self.result_text.append("⚠️ 实验功能未启用，无法执行详细分析")
                
        except Exception as e:
            self.result_text.append(f"❌ 测试失败: {str(e)}")
            import traceback
            self.result_text.append(f"详细错误:\n{traceback.format_exc()}")
    
    def show_results_window(self):
        """显示结果窗口"""
        if self.comparison_result:
            self.results_window = ResultsWindow(
                self.comparison_result, 
                "test_user_video.mp4", 
                "test_standard_video.mp4"
            )
            self.results_window.show()


def main():
    app = QApplication(sys.argv)
    
    test_window = DetailedMeasurementTestWindow()
    test_window.show()
    
    print("🔬 详细测量信息测试程序")
    print("这个测试将验证:")
    print("1. ✅ 增强的测量数据输出")
    print("2. ✅ 详细的对比信息")
    print("3. ✅ 关键点和置信度信息")
    print("4. ✅ 容差状态和改进建议")
    print("5. ✅ 技术参数和处理详情")
    print()
    print("点击'运行详细测量分析测试'开始测试")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()