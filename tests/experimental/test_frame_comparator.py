"""
帧对比器真实图像测试 - 方案3
"""
import sys
import os
import cv2
import numpy as np

# 添加项目根目录到路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(project_root)

def test_real_frame_comparison():
    """
    使用真实的用户和标准关键帧图像进行完整的对比测试
    
    测试文件结构:
    tests/experimental/
    ├── test_images/          # 测试图像存放处
    │   ├── user_setup.jpg    # 用户架拍关键帧
    │   └── standard_setup.jpg # 标准架拍关键帧
    ├── test_output/          # 测试结果输出
    └── test_frame_comparator.py # 本文件
    """
    
    print("🏸 帧对比器真实图像测试")
    print("=" * 50)
    
    # Step 1: 图像准备
    print("\n=== Step 1: 图像加载 ===")
    
    test_dir = os.path.dirname(__file__)
    image_dir = os.path.join(test_dir, "test_images")
    output_dir = os.path.join(test_dir, "test_output")
    
    user_image_path = os.path.join(image_dir, "user_setup.jpg")
    standard_image_path = os.path.join(image_dir, "standard_setup.jpg")
    
    # 检查图像文件是否存在
    if not os.path.exists(user_image_path):
        print(f"❌ 用户图像不存在: {user_image_path}")
        print("请将用户架拍关键帧图像放在 tests/experimental/test_images/user_setup.jpg")
        return False
        
    if not os.path.exists(standard_image_path):
        print(f"❌ 标准图像不存在: {standard_image_path}")
        print("请将标准架拍关键帧图像放在 tests/experimental/test_images/standard_setup.jpg")
        return False
    
    # 加载图像
    user_image = cv2.imread(user_image_path)
    standard_image = cv2.imread(standard_image_path)
    
    if user_image is None or standard_image is None:
        print("❌ 图像加载失败")
        return False
    
    print(f"✓ 用户图像尺寸: {user_image.shape}")
    print(f"✓ 标准图像尺寸: {standard_image.shape}")
    
    # Step 2: 初始化系统
    print("\n=== Step 2: 系统初始化 ===")
    
    try:
        from core.experimental.config.sport_configs import SportConfigs
        from core.experimental.frame_analyzer.frame_comparator import FrameComparator
        
        config = SportConfigs.get_badminton_forehand_clear()
        stage_config = config.stages[0]  # 架拍阶段结束
        comparator = FrameComparator()
        
        print(f"✓ 测试阶段: {stage_config.name}")
        print(f"✓ 测量项: {stage_config.measurements[0].name}")
        print(f"✓ 容忍范围: {stage_config.measurements[0].tolerance_range}")
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False
    
    # Step 3: 姿态提取验证
    print("\n=== Step 3: 姿态提取 ===")
    
    try:
        user_analysis = comparator.analyze_frame(user_image, stage_config, frame_index=0)
        standard_analysis = comparator.analyze_frame(standard_image, stage_config, frame_index=0)
        
        if not user_analysis:
            print("❌ 用户图像姿态提取失败")
            return False
        if not standard_analysis:
            print("❌ 标准图像姿态提取失败")
            return False
            
        print("✓ 两张图像姿态提取成功")
        
        # 检查关键点检测质量
        user_pose = user_analysis.pose
        standard_pose = standard_analysis.pose
        
        key_points = ["right_shoulder", "right_elbow", "right_wrist"]
        for point_name in key_points:
            user_pt = user_pose.get_keypoint(point_name)
            standard_pt = standard_pose.get_keypoint(point_name)
            
            if user_pt and standard_pt:
                print(f"✓ {point_name}: 用户({user_pt.x:.1f}, {user_pt.y:.1f}) "
                      f"标准({standard_pt.x:.1f}, {standard_pt.y:.1f}) "
                      f"置信度: {user_pt.confidence:.2f}/{standard_pt.confidence:.2f}")
            else:
                print(f"❌ {point_name}: 关键点检测失败")
                
    except Exception as e:
        print(f"❌ 姿态提取过程出错: {e}")
        return False
    
    # Step 4: 角度计算分析
    print("\n=== Step 4: 角度计算 ===")
    
    try:
        user_angle = user_analysis.get_measurement("大臂小臂夹角")
        standard_angle = standard_analysis.get_measurement("大臂小臂夹角")
        
        if user_angle is None or standard_angle is None:
            print("❌ 角度计算失败")
            return False
        
        print(f"✓ 用户大臂小臂夹角: {user_angle:.1f}度")
        print(f"✓ 标准大臂小臂夹角: {standard_angle:.1f}度")
        print(f"✓ 角度差异: {abs(user_angle - standard_angle):.1f}度")
        
        # 合理性检查
        if 60 <= user_angle <= 180 and 60 <= standard_angle <= 180:
            print("✓ 角度值在合理范围内")
        else:
            print("⚠️  角度值可能异常，需要检查")
        
        # 容忍度检查
        tolerance_range = stage_config.measurements[0].tolerance_range
        user_in_range = tolerance_range[0] <= user_angle <= tolerance_range[1]
        standard_in_range = tolerance_range[0] <= standard_angle <= tolerance_range[1]
        
        print(f"✓ 用户角度在容忍范围内: {user_in_range}")
        print(f"✓ 标准角度在容忍范围内: {standard_in_range}")
        
    except Exception as e:
        print(f"❌ 角度计算过程出错: {e}")
        return False
    
    # Step 5: 对比和评分
    print("\n=== Step 5: 对比评分 ===")
    
    try:
        comparison = comparator.compare_frames(user_analysis, standard_analysis, stage_config)
        measurement = comparison.measurements[0]  # 我们只有一个测量项
        
        print(f"✓ 测量项名称: {measurement.measurement_name}")
        print(f"✓ 用户值: {measurement.user_value:.1f}{stage_config.measurements[0].unit}")
        print(f"✓ 标准值: {measurement.standard_value:.1f}{stage_config.measurements[0].unit}")
        print(f"✓ 绝对差异: {abs(measurement.difference):.1f}{stage_config.measurements[0].unit}")
        print(f"✓ 百分比差异: {measurement.percentage_diff:.1f}%")
        print(f"✓ 在容忍范围内: {measurement.is_within_tolerance}")
        print(f"✓ 相似度评分: {measurement.similarity_score:.1f}/100")
        print(f"✓ 阶段总评分: {comparison.overall_score:.1f}/100")
        
    except Exception as e:
        print(f"❌ 对比评分过程出错: {e}")
        return False
    
    # Step 6: 可视化验证
    print("\n=== Step 6: 可视化生成 ===")
    
    try:
        vis_results = comparator.create_visualization(user_image, standard_image, comparison)
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存结果图像
        cv2.imwrite(os.path.join(output_dir, "user_pose_annotated.png"), vis_results['user_annotated'])
        cv2.imwrite(os.path.join(output_dir, "standard_pose_annotated.png"), vis_results['standard_annotated'])
        cv2.imwrite(os.path.join(output_dir, "side_by_side_comparison.png"), vis_results['side_by_side'])
        
        print("✓ 可视化图像已保存:")
        print(f"  - {os.path.join(output_dir, 'user_pose_annotated.png')}")
        print(f"  - {os.path.join(output_dir, 'standard_pose_annotated.png')}")
        print(f"  - {os.path.join(output_dir, 'side_by_side_comparison.png')}")
        
    except Exception as e:
        print(f"❌ 可视化生成过程出错: {e}")
        return False
    
    # Step 7: 结果解释
    print("\n=== Step 7: 结果解释 ===")
    
    score = comparison.overall_score
    if score >= 90:
        interpretation = "优秀：技术动作非常标准"
    elif score >= 75:
        interpretation = "良好：技术动作基本正确，略有改进空间"
    elif score >= 60:
        interpretation = "一般：技术动作有明显问题需要改进"
    else:
        interpretation = "较差：技术动作存在严重问题"
    
    print(f"✓ 评分解释: {interpretation}")
    
    # 改进建议
    tolerance_range = stage_config.measurements[0].tolerance_range
    if not measurement.is_within_tolerance:
        if measurement.user_value < tolerance_range[0]:
            print("💡 建议: 架拍时抬高肘部，增大手臂角度")
        elif measurement.user_value > tolerance_range[1]:
            print("💡 建议: 架拍时适当降低肘部，减小手臂角度")
    else:
        print("💡 建议: 动作已经很标准，继续保持")
    
    print("\n🎉 测试完成！请查看 test_output 文件夹中的可视化结果")
    return True


def setup_test_environment():
    """设置测试环境的辅助函数"""
    print("📁 测试环境设置")
    print("=" * 30)
    
    test_dir = os.path.dirname(__file__)
    image_dir = os.path.join(test_dir, "test_images")
    
    print(f"测试目录: {test_dir}")
    print(f"图像目录: {image_dir}")
    
    print("\n请确保以下文件存在:")
    print(f"  - {os.path.join(image_dir, 'user_setup.jpg')} (用户架拍关键帧)")
    print(f"  - {os.path.join(image_dir, 'standard_setup.jpg')} (标准架拍关键帧)")
    
    if not os.path.exists(image_dir):
        print(f"\n⚠️  图像目录不存在，正在创建: {image_dir}")
        os.makedirs(image_dir)
    
    # 检查文件是否存在
    user_exists = os.path.exists(os.path.join(image_dir, "user_setup.jpg"))
    standard_exists = os.path.exists(os.path.join(image_dir, "standard_setup.jpg"))
    
    print(f"\n文件状态:")
    print(f"  - user_setup.jpg: {'✓ 存在' if user_exists else '❌ 不存在'}")
    print(f"  - standard_setup.jpg: {'✓ 存在' if standard_exists else '❌ 不存在'}")
    
    return user_exists and standard_exists


if __name__ == "__main__":
    # 首先设置测试环境
    if setup_test_environment():
        print("\n" + "="*50)
        # 运行测试
        success = test_real_frame_comparison()
        sys.exit(0 if success else 1)
    else:
        print("\n❌ 测试环境未准备好，请先放置测试图像")
        sys.exit(1)