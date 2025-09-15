"""
测试高级分析窗口的功能
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.advanced_analysis_window import AdvancedAnalysisWindow

def create_test_data():
    """创建测试数据"""
    return {
        'analysis_type': 'experimental',
        'sport': '羽毛球',
        'action': '正手高远球',
        'score': 78,
        'detailed_score': 0.78,
        'stages': {
            '架拍阶段结束': {
                'user_frame': 30,
                'standard_frame': 25,
                'stage_info': {
                    'score': 75.0,
                    'status': '架拍阶段结束: 基本正确，有改进空间 (得分: 75.0%)'
                },
                'measurements': [
                    {
                        'rule_name': '大臂小臂夹角',
                        'user_value': 95.3,
                        'standard_value': 88.7,
                        'is_within_range': False,
                        'measurement_points': ['right_shoulder', 'right_elbow', 'right_wrist']
                    },
                    {
                        'rule_name': '身体前倾角度',
                        'user_value': 15.2,
                        'standard_value': 12.8,
                        'is_within_range': True,
                        'measurement_points': ['neck', 'hip', 'knee']
                    }
                ]
            },
            '击球瞬间': {
                'user_frame': 60,
                'standard_frame': 55,
                'stage_info': {
                    'score': 82.0,
                    'status': '击球瞬间: 时机基本准确 (得分: 82.0%)'
                },
                'measurements': [
                    {
                        'rule_name': '球拍与身体角度',
                        'user_value': 45.2,
                        'standard_value': 42.8,
                        'is_within_range': True,
                        'measurement_points': ['right_wrist', 'right_shoulder', 'left_shoulder']
                    },
                    {
                        'rule_name': '击球高度',
                        'user_value': 180.5,
                        'standard_value': 185.3,
                        'is_within_range': True,
                        'measurement_points': ['right_wrist', 'ground_reference']
                    }
                ]
            },
            '随挥完成': {
                'user_frame': 90,
                'standard_frame': 85,
                'stage_info': {
                    'score': 70.0,
                    'status': '随挥完成: 动作幅度可以更大 (得分: 70.0%)'
                },
                'measurements': [
                    {
                        'rule_name': '手臂伸展角度',
                        'user_value': 160.5,
                        'standard_value': 170.2,
                        'is_within_range': False,
                        'measurement_points': ['right_shoulder', 'right_elbow', 'right_wrist']
                    }
                ]
            }
        },
        'comparison_images': {
            'user_pose': None,
            'standard_pose': None
        },
        'analysis_summary': {
            'total_stages': 3,
            'avg_score': 75.7,
            'suggestions': ['注意大臂小臂夹角', '加大随挥幅度', '保持击球时机']
        }
    }

def main():
    """主测试函数"""
    app = QApplication(sys.argv)
    
    # 创建测试数据
    test_data = create_test_data()
    
    # 测试视频路径（这些路径在测试中可以是任意的）
    user_video_path = "test_user_video.mp4"
    standard_video_path = "test_standard_video.mp4"
    
    # 创建高级分析窗口
    window = AdvancedAnalysisWindow(
        comparison_results=test_data,
        user_video_path=user_video_path,
        standard_video_path=standard_video_path
    )
    
    window.show()
    
    print("🎯 高级分析窗口已启动")
    print("📊 测试数据包含:")
    print(f"  - 总阶段数: {test_data['analysis_summary']['total_stages']}")
    print(f"  - 平均得分: {test_data['analysis_summary']['avg_score']:.1f}%")
    print(f"  - 阶段列表: {list(test_data['stages'].keys())}")
    print("\n🔍 功能测试项目:")
    print("  1. 左侧视频预览区域 (无实际视频时显示占位符)")
    print("  2. 右侧阶段分析区域显示多个阶段")
    print("  3. 每个阶段显示关键帧图像 (测试模式下显示占位符)")
    print("  4. 帧数调整控件和更新按钮")
    print("  5. 阶段对比结果显示")
    print("\n💡 在实际使用中，需要提供真实的视频文件路径")
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()