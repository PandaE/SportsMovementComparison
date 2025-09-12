"""
调试实验模块的对比分析流程
"""

import sys
import os
import traceback

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.experimental_comparison_engine import ExperimentalComparisonEngine
from core.experimental.config.sport_configs import SportConfigs

def debug_experimental_analysis():
    """调试实验分析流程"""
    print("🔍 开始调试实验模块分析流程")
    
    # 1. 检查引擎初始化
    print("\n=== 步骤1: 初始化实验引擎 ===")
    try:
        engine = ExperimentalComparisonEngine(use_experimental_features=True)
        print(f"✅ 引擎初始化成功")
        print(f"📊 实验功能就绪: {engine.experimental_ready}")
        print(f"🔧 使用实验功能: {engine.use_experimental}")
        
        if hasattr(engine, 'pose_extractor'):
            print(f"👤 姿态提取器: {type(engine.pose_extractor).__name__}")
        if hasattr(engine, 'frame_comparator'):
            print(f"📐 帧对比器: {type(engine.frame_comparator).__name__}")
            
    except Exception as e:
        print(f"❌ 引擎初始化失败: {e}")
        traceback.print_exc()
        return
    
    # 2. 检查配置获取
    print("\n=== 步骤2: 获取运动配置 ===")
    try:
        config = SportConfigs.get_config("badminton", "clear")
        print(f"✅ 配置获取成功")
        print(f"📋 动作名称: {config.name}")
        print(f"📝 动作描述: {config.description}")
        print(f"🎯 阶段数量: {len(config.stages)}")
        
        for i, stage in enumerate(config.stages):
            print(f"  阶段 {i+1}: {stage.name}")
            print(f"    测量规则数: {len(stage.measurements)}")
            for j, measurement in enumerate(stage.measurements):
                print(f"      规则 {j+1}: {measurement.name} ({measurement.measurement_type})")
                
    except Exception as e:
        print(f"❌ 配置获取失败: {e}")
        traceback.print_exc()
        return
    
    # 3. 测试关键帧提取
    print("\n=== 步骤3: 测试关键帧提取 ===")
    
    # 使用你提供的视频路径
    user_video = "D:/code/badminton/badminton_v2/me.mp4"
    standard_video = "D:/code/badminton/badminton_v2/demo.mp4"
    
    print(f"📹 用户视频: {user_video}")
    print(f"📹 标准视频: {standard_video}")
    
    try:
        print("  正在提取用户视频关键帧...")
        user_frames = engine._extract_key_frames(user_video)
        print(f"  ✅ 用户视频帧数: {len(user_frames) if user_frames else 0}")
        
        print("  正在提取标准视频关键帧...")
        standard_frames = engine._extract_key_frames(standard_video)
        print(f"  ✅ 标准视频帧数: {len(standard_frames) if standard_frames else 0}")
        
        if not user_frames or not standard_frames:
            print("  ❌ 关键帧提取失败")
            return
            
    except Exception as e:
        print(f"  ❌ 关键帧提取异常: {e}")
        traceback.print_exc()
        return
    
    # 4. 测试姿态提取
    print("\n=== 步骤4: 测试姿态提取 ===")
    try:
        print("  正在提取用户姿态...")
        user_pose = engine.pose_extractor.extract_pose_from_image(user_frames[0])
        print(f"  ✅ 用户姿态提取: {'成功' if user_pose else '失败'}")
        
        print("  正在提取标准姿态...")
        standard_pose = engine.pose_extractor.extract_pose_from_image(standard_frames[0])
        print(f"  ✅ 标准姿态提取: {'成功' if standard_pose else '失败'}")
        
        if user_pose and standard_pose:
            user_confidence = engine._get_pose_confidence(user_pose)
            standard_confidence = engine._get_pose_confidence(standard_pose)
            print(f"  📊 用户姿态置信度: {user_confidence:.2f}")
            print(f"  📊 标准姿态置信度: {standard_confidence:.2f}")
            
    except Exception as e:
        print(f"  ❌ 姿态提取异常: {e}")
        traceback.print_exc()
        return
    
    # 5. 测试阶段分析
    print("\n=== 步骤5: 测试阶段分析 ===")
    try:
        stage = config.stages[0]  # 第一个阶段
        print(f"  分析阶段: {stage.name}")
        
        stage_result = engine._analyze_stage(user_frames[0], standard_frames[0], stage)
        print(f"  ✅ 阶段分析完成")
        print(f"  📊 阶段得分: {stage_result.get('score', 0):.2f}")
        print(f"  📏 测量数量: {len(stage_result.get('measurements', []))}")
        
        for measurement in stage_result.get('measurements', []):
            name = measurement.get('measurement_name', '未知')
            user_val = measurement.get('user_value', 0)
            standard_val = measurement.get('standard_value', 0)
            print(f"    {name}: 用户{user_val:.1f} vs 标准{standard_val:.1f}")
        
    except Exception as e:
        print(f"  ❌ 阶段分析异常: {e}")
        traceback.print_exc()
        return
    
    # 6. 完整对比分析
    print("\n=== 步骤6: 完整对比分析 ===")
    try:
        result = engine.compare(user_video, standard_video, "badminton", "clear")
        print(f"  ✅ 完整分析完成")
        print(f"  📊 总体得分: {result.get('score', 0)}")
        print(f"  🎭 分析类型: {result.get('analysis_type', '未知')}")
        print(f"  🎯 关键动作数: {len(result.get('key_movements', []))}")
        
        # 检查是否有阶段数据
        if 'stages' in result:
            print(f"  🔍 阶段数据: {len(result['stages'])} 个阶段")
            for stage_name, stage_data in result['stages'].items():
                score = stage_data.get('stage_info', {}).get('score', 0)
                measurements = len(stage_data.get('measurements', []))
                print(f"    {stage_name}: {score:.1f}分, {measurements}个测量")
        else:
            print(f"  ⚠️ 缺少阶段数据")
        
    except Exception as e:
        print(f"  ❌ 完整分析异常: {e}")
        traceback.print_exc()
        return
    
    print("\n🎉 调试完成！")

if __name__ == '__main__':
    debug_experimental_analysis()