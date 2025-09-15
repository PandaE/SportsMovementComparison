"""
test_simple_measurements.py
测试简化的详细测量信息输出
"""
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt5.QtCore import Qt

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.experimental_comparison_engine import ExperimentalComparisonEngine


class SimpleMeasurementTestWindow(QMainWindow):
    """简化测量信息测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简化测量信息测试")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 测试按钮
        self.test_btn = QPushButton("运行简化测量分析测试")
        self.test_btn.clicked.connect(self.run_simple_test)
        layout.addWidget(self.test_btn)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Microsoft YaHei', sans-serif;
                font-size: 12px;
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.result_text)
        
        central_widget.setLayout(layout)
    
    def run_simple_test(self):
        """运行简化测量测试"""
        self.result_text.clear()
        self.result_text.append("🎯 简化测量信息测试\n")
        
        try:
            # 创建实验引擎
            engine = ExperimentalComparisonEngine(use_experimental_features=True)
            
            self.result_text.append("✓ 实验引擎初始化成功")
            self.result_text.append(f"实验功能状态: {'启用' if engine.experimental_ready else '禁用'}\n")
            
            if engine.experimental_ready:
                # 使用模拟的对比数据来展示格式
                mock_result = {
                    'score': 75,
                    'detailed_score': 0.75,
                    'analysis_type': 'experimental',
                    'sport': '羽毛球',
                    'action': '正手高远球',
                    'user_video_path': 'user_badminton.mp4',
                    'standard_video_path': 'standard_badminton.mp4',
                    'comparison_info': {
                        'user_frame': '从 user_badminton.mp4 提取的关键帧',
                        'standard_frame': '从 standard_badminton.mp4 提取的关键帧',
                        'rules_applied': ['大臂小臂夹角'],
                        'total_comparisons': 1
                    },
                    'key_movements': [{
                        'name': '架拍阶段结束',
                        'score': 0.75,
                        'summary': '架拍阶段结束: 基本正确，有改进空间 (得分: 75.0%)',
                        'suggestion': '大臂小臂夹角基本正确，可以进一步优化',
                        'detailed_measurements': [
                            '• 大臂小臂夹角: 用户 95.3° vs 标准 88.7°',
                            '  ✗ 偏大 6.6°',
                            '  测量点: right_shoulder → right_elbow → right_wrist'
                        ]
                    }]
                }
                
                self.result_text.append("📊 简化后的测量信息格式:")
                self.result_text.append("=" * 50)
                
                # 显示对比数据源
                comp_info = mock_result['comparison_info']
                self.result_text.append(f"📹 对比数据源:")
                self.result_text.append(f"  用户帧: {comp_info['user_frame']}")
                self.result_text.append(f"  标准帧: {comp_info['standard_frame']}")
                self.result_text.append(f"  应用规则: {', '.join(comp_info['rules_applied'])}")
                self.result_text.append(f"  对比项目数: {comp_info['total_comparisons']}")
                self.result_text.append("")
                
                # 显示得分
                self.result_text.append(f"🎯 综合得分: {mock_result['score']}/100")
                self.result_text.append("")
                
                # 显示各阶段对比
                for movement in mock_result['key_movements']:
                    self.result_text.append(f"📋 {movement['name']}")
                    self.result_text.append(f"  得分: {movement['score']:.1%}")
                    self.result_text.append(f"  结果: {movement['summary']}")
                    self.result_text.append(f"  建议: {movement['suggestion']}")
                    self.result_text.append("")
                    
                    self.result_text.append("📏 对比数据:")
                    for measurement in movement['detailed_measurements']:
                        self.result_text.append(f"    {measurement}")
                    
                self.result_text.append("")
                self.result_text.append("✅ 简化后的信息特点:")
                self.result_text.append("  • 清楚地显示对比了哪两帧")
                self.result_text.append("  • 明确列出应用的规则")
                self.result_text.append("  • 直接显示用户值 vs 标准值")
                self.result_text.append("  • 简洁的达标状态说明")
                self.result_text.append("  • 显示具体的测量点")
                
            else:
                self.result_text.append("⚠️ 实验功能未启用，无法展示简化测量信息")
                
        except Exception as e:
            self.result_text.append(f"❌ 测试失败: {str(e)}")


def main():
    app = QApplication(sys.argv)
    
    test_window = SimpleMeasurementTestWindow()
    test_window.show()
    
    print("🎯 简化测量信息测试程序")
    print("这个测试将展示简化后的测量信息格式:")
    print("1. ✅ 对比数据源 (哪两帧)")
    print("2. ✅ 应用的规则")
    print("3. ✅ 用户值 vs 标准值")
    print("4. ✅ 简洁的达标状态")
    print("5. ✅ 测量点信息")
    print()
    print("点击'运行简化测量分析测试'查看效果")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()