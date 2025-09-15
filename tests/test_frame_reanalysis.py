"""
测试手动更新帧数后的重新分析功能
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.advanced_analysis_window import AdvancedAnalysisWindow

def create_test_data_with_reanalysis():
    """创建用于重新分析测试的数据"""
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
                    }
                ]
            }
        },
        'comparison_images': {
            'user_pose': None,
            'standard_pose': None
        },
        'analysis_summary': {
            'total_stages': 1,
            'avg_score': 75.0,
            'suggestions': ['注意大臂小臂夹角调整']
        }
    }

def main():
    """主测试函数"""
    app = QApplication(sys.argv)
    
    # 创建测试数据
    test_data = create_test_data_with_reanalysis()
    
    # 使用真实的视频路径进行测试
    user_video_path = "D:/code/badminton/badminton_v2/me.mp4"
    standard_video_path = "D:/code/badminton/badminton_v2/demo.mp4"
    
    # 检查视频文件是否存在
    if not os.path.exists(user_video_path) or not os.path.exists(standard_video_path):
        msg = QMessageBox()
        msg.setWindowTitle("视频文件检查")
        msg.setText(f"""
视频文件路径检查:
用户视频: {user_video_path} {'✅存在' if os.path.exists(user_video_path) else '❌不存在'}
标准视频: {standard_video_path} {'✅存在' if os.path.exists(standard_video_path) else '❌不存在'}

如果视频文件不存在，重新分析功能将无法正常工作。
但界面的其他功能仍可以测试。
        """)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
    
    # 创建高级分析窗口
    window = AdvancedAnalysisWindow(
        comparison_results=test_data,
        user_video_path=user_video_path,
        standard_video_path=standard_video_path
    )
    
    window.show()
    
    print("🎯 手动更新帧数测试窗口已启动")
    print("\n📋 测试说明:")
    print("  1. 界面显示了一个阶段分析组件")
    print("  2. 每个阶段有用户帧和标准帧的SpinBox控件")
    print("  3. 修改帧数后点击'更新'按钮")
    print("  4. 系统会重新提取对应帧并进行分析")
    print("  5. 结果会实时更新显示")
    
    print("\n🔍 测试步骤:")
    print("  📌 步骤1: 观察当前的分析结果")
    print("  📌 步骤2: 修改用户帧数(如从30改为60)")
    print("  📌 步骤3: 修改标准帧数(如从25改为50)")
    print("  📌 步骤4: 点击'更新'按钮")
    print("  📌 步骤5: 观察控制台输出的重新分析过程")
    print("  📌 步骤6: 查看更新后的分析结果")
    
    print("\n💡 预期效果:")
    print("  ✅ 控制台显示'🔄 开始重新分析阶段'")
    print("  ✅ 显示新的得分和测量数据")
    print("  ✅ 帧图像更新为新的帧位置")
    print("  ✅ 对比结果更新为新帧的分析结果")
    
    # 设置一个定时器来模拟自动测试（可选）
    def auto_test():
        """自动测试帧数更新"""
        try:
            # 获取第一个阶段组件
            if window.stage_widgets:
                widget = window.stage_widgets[0]
                print("\n🤖 开始自动测试...")
                print("  ⏱️ 3秒后自动更改帧数进行测试")
                
                # 3秒后更改帧数
                QTimer.singleShot(3000, lambda: test_frame_change(widget))
        except Exception as e:
            print(f"自动测试失败: {e}")
    
    def test_frame_change(widget):
        """测试帧数更改"""
        try:
            print("\n🎯 执行自动帧数更改测试...")
            old_user_frame = widget.user_frame_spinbox.value()
            old_standard_frame = widget.standard_frame_spinbox.value()
            
            # 更改帧数
            new_user_frame = old_user_frame + 30
            new_standard_frame = old_standard_frame + 20
            
            print(f"  📊 用户帧: {old_user_frame} → {new_user_frame}")
            print(f"  📊 标准帧: {old_standard_frame} → {new_standard_frame}")
            
            widget.user_frame_spinbox.setValue(new_user_frame)
            widget.standard_frame_spinbox.setValue(new_standard_frame)
            
            # 触发更新
            widget.update_frames()
            
        except Exception as e:
            print(f"自动测试执行失败: {e}")
    
    # 启动自动测试（可选）
    # QTimer.singleShot(1000, auto_test)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()