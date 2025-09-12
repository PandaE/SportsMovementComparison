"""
修复版本：调试实验模块的对比分析流程
修复FrameComparator接口调用问题
"""

import sys
import os
import traceback

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.experimental.frame_analyzer.frame_comparator import FrameComparator
from core.experimental.frame_analyzer.pose_extractor import PoseExtractor
from core.experimental.config.sport_configs import SportConfigs

def debug_frame_comparison():
    """调试帧对比流程"""
    print("🔍 开始调试帧对比流程")
    
    # 1. 初始化组件
    print("\n=== 步骤1: 初始化组件 ===")
    try:
        pose_extractor = PoseExtractor(backend="mediapipe")
        frame_comparator = FrameComparator(pose_extractor=pose_extractor)
        print("✅ 组件初始化成功")
    except Exception as e:
        print(f"❌ 组件初始化失败: {e}")
        traceback.print_exc()
        return
    
    # 2. 获取配置
    print("\n=== 步骤2: 获取运动配置 ===")
    try:
        config = SportConfigs.get_config("badminton", "clear")
        stage = config.stages[0]  # 第一个阶段
        print(f"✅ 获取阶段配置: {stage.name}")
        print(f"📏 测量规则数: {len(stage.measurements)}")
        for rule in stage.measurements:
            print(f"  - {rule.name}: {rule.measurement_type}")
            print(f"    关键点: {rule.keypoints}")
    except Exception as e:
        print(f"❌ 配置获取失败: {e}")
        traceback.print_exc()
        return
    
    # 3. 加载测试图像
    print("\n=== 步骤3: 加载测试图像 ===")
    import cv2
    
    user_video = "D:/code/badminton/badminton_v2/me.mp4"
    standard_video = "D:/code/badminton/badminton_v2/demo.mp4"
    
    try:
        # 提取一帧图像
        user_cap = cv2.VideoCapture(user_video)
        user_cap.set(cv2.CAP_PROP_POS_FRAMES, user_cap.get(cv2.CAP_PROP_FRAME_COUNT) // 2)
        ret1, user_frame = user_cap.read()
        user_cap.release()
        
        standard_cap = cv2.VideoCapture(standard_video)
        standard_cap.set(cv2.CAP_PROP_POS_FRAMES, standard_cap.get(cv2.CAP_PROP_FRAME_COUNT) // 2)
        ret2, standard_frame = standard_cap.read()
        standard_cap.release()
        
        if not ret1 or not ret2:
            print("❌ 无法读取视频帧")
            return
        
        print("✅ 视频帧加载成功")
        print(f"  用户帧尺寸: {user_frame.shape}")
        print(f"  标准帧尺寸: {standard_frame.shape}")
        
    except Exception as e:
        print(f"❌ 视频帧加载失败: {e}")
        traceback.print_exc()
        return
    
    # 4. 使用正确的接口进行帧分析
    print("\n=== 步骤4: 帧分析 ===")
    try:
        # 使用analyze_frame方法而不是直接extract_pose
        print("  分析用户帧...")
        user_analysis = frame_comparator.analyze_frame(user_frame, stage, frame_index=0)
        print(f"  ✅ 用户帧分析: {'成功' if user_analysis else '失败'}")
        
        print("  分析标准帧...")
        standard_analysis = frame_comparator.analyze_frame(standard_frame, stage, frame_index=0)
        print(f"  ✅ 标准帧分析: {'成功' if standard_analysis else '失败'}")
        
        if user_analysis and standard_analysis:
            print(f"  📊 用户帧测量数: {len(user_analysis.analysis_data)}")
            print(f"  📊 标准帧测量数: {len(standard_analysis.analysis_data)}")
            
            # 显示测量结果
            for name, data in user_analysis.analysis_data.items():
                value = data.get('value', 0)
                unit = data.get('unit', '')
                print(f"    用户 {name}: {value:.2f}{unit}")
            for name, data in standard_analysis.analysis_data.items():
                value = data.get('value', 0)
                unit = data.get('unit', '')
                print(f"    标准 {name}: {value:.2f}{unit}")
        
    except Exception as e:
        print(f"  ❌ 帧分析失败: {e}")
        traceback.print_exc()
        return
    
    # 5. 帧对比
    print("\n=== 步骤5: 帧对比 ===")
    try:
        if user_analysis and standard_analysis:
            comparison_result = frame_comparator.compare_frames(
                user_analysis, standard_analysis, stage
            )
            print("  ✅ 帧对比成功")
            print(f"  📊 整体得分: {comparison_result.overall_score:.2f}")
            print(f"  📏 对比测量数: {len(comparison_result.measurements)}")
            
            for measurement in comparison_result.measurements:
                print(f"    {measurement.measurement_name}:")
                print(f"      用户值: {measurement.user_value:.2f}")
                print(f"      标准值: {measurement.standard_value:.2f}")
                print(f"      差异: {measurement.difference:.2f}")
                print(f"      达标: {measurement.is_within_tolerance}")
        
    except Exception as e:
        print(f"  ❌ 帧对比失败: {e}")
        traceback.print_exc()
        return
    
    print("\n🎉 调试完成！")
    print("\n💡 发现的问题:")
    print("  - ExperimentalComparisonEngine需要使用FrameComparator.analyze_frame方法")
    print("  - 然后用analyze_frame的结果调用compare_frames方法")
    print("  - 而不是直接传递BodyPose对象给compare_frames")

if __name__ == '__main__':
    debug_frame_comparison()