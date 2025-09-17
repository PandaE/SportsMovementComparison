"""
Test Script for New Evaluation System
新评价系统测试脚本

Simple test script to verify the new rule-based evaluation system works correctly.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.evaluation_config import get_config_manager
from core.rule_evaluator import create_evaluator
from core.evaluation_validator import run_full_validation


def test_new_evaluation_system():
    """测试新评价系统的基本功能"""
    
    print("🚀 测试新评价系统")
    print("=" * 50)
    
    # 1. 测试配置管理器
    print("\\n1️⃣ 测试配置管理器...")
    try:
        config_manager = get_config_manager()
        actions = config_manager.list_available_actions()
        print(f"✅ 配置管理器初始化成功")
        print(f"📋 可用动作配置: {len(actions)} 个")
        for sport, action, display_name in actions:
            print(f"   - {sport}: {action} ({display_name})")
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False
    
    # 2. 测试评价器
    print("\\n2️⃣ 测试评价器...")
    try:
        evaluator = create_evaluator()
        print("✅ 评价器创建成功")
    except Exception as e:
        print(f"❌ 评价器创建失败: {e}")
        return False
    
    # 3. 测试实际评价
    print("\\n3️⃣ 测试实际评价...")
    
    # 测试数据1: 良好表现
    test_data_good = {
        "stance_width": 48,          # 略窄但在良好范围
        "racket_ready_angle": 112,   # 略高但在优秀范围
        "shoulder_rotation": 42,     # 略低但在优秀范围
        "elbow_height": 3,           # 略高但在良好范围
        "wrist_extension": 28,       # 略高但在优秀范围
        "arm_extension": 158,        # 略低但在良好范围
        "contact_height": 32,        # 略高但在优秀范围
        "body_lean": 18              # 略高但在良好范围
    }
    
    try:
        result = evaluator.evaluate("badminton", "clear", test_data_good)
        
        print(f"✅ 评价执行成功")
        print(f"📊 总分: {result.total_score:.1f}/100")
        print(f"🏆 等级: {result.level}")
        print(f"📝 总结: {result.summary}")
        
        print(f"\\n📈 各阶段得分:")
        for stage in result.stages:
            print(f"   {stage.display_name}: {stage.stage_score:.1f}/100 (权重: {stage.weight})")
            print(f"     有效测量: {stage.valid_measurements_count}/{len(stage.measurements)}")
        
        print(f"\\n💡 改进建议:")
        for i, suggestion in enumerate(result.improvement_suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print(f"\\n⭐ 优势:")
        for i, strength in enumerate(result.strengths, 1):
            print(f"   {i}. {strength}")
            
    except Exception as e:
        print(f"❌ 评价执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试边界情况
    print("\\n4️⃣ 测试边界情况...")
    
    # 测试数据2: 部分数据缺失
    test_data_partial = {
        "stance_width": 50,
        "arm_extension": 160,
        "contact_height": 30
        # 缺少其他测量项
    }
    
    try:
        result_partial = evaluator.evaluate("badminton", "clear", test_data_partial)
        print(f"✅ 部分数据评价成功，得分: {result_partial.total_score:.1f}")
    except Exception as e:
        print(f"❌ 部分数据评价失败: {e}")
        return False
    
    # 5. 测试极端值
    print("\\n5️⃣ 测试极端值...")
    
    test_data_extreme = {
        "stance_width": 200,         # 极端值
        "racket_ready_angle": 30,    # 极端值
        "arm_extension": 90,         # 极端值
    }
    
    try:
        result_extreme = evaluator.evaluate("badminton", "clear", test_data_extreme)
        print(f"✅ 极端值评价成功，得分: {result_extreme.total_score:.1f}")
        print(f"   等级: {result_extreme.level}")
    except Exception as e:
        print(f"❌ 极端值评价失败: {e}")
        return False
    
    print("\\n🎉 所有基础测试通过！")
    return True


def demo_evaluation_process():
    """演示评价过程"""
    
    print("\\n" + "=" * 50)
    print("🎮 评价过程演示")
    print("=" * 50)
    
    evaluator = create_evaluator()
    
    # 模拟不同水平的用户数据
    user_scenarios = [
        {
            "name": "新手用户",
            "data": {
                "stance_width": 30,          # 太窄
                "racket_ready_angle": 80,    # 太低
                "shoulder_rotation": 20,     # 不足
                "elbow_height": -20,         # 太低
                "wrist_extension": 10,       # 不足
                "arm_extension": 120,        # 不足
                "contact_height": 10,        # 太低
                "body_lean": 5               # 不足
            }
        },
        {
            "name": "中级用户", 
            "data": {
                "stance_width": 45,          # 良好
                "racket_ready_angle": 105,   # 良好
                "shoulder_rotation": 40,     # 良好
                "elbow_height": 5,           # 良好
                "wrist_extension": 22,       # 良好
                "arm_extension": 155,        # 良好
                "contact_height": 28,        # 良好
                "body_lean": 12              # 良好
            }
        },
        {
            "name": "高级用户",
            "data": {
                "stance_width": 50,          # 完美
                "racket_ready_angle": 110,   # 完美
                "shoulder_rotation": 45,     # 完美
                "elbow_height": 0,           # 完美
                "wrist_extension": 25,       # 完美
                "arm_extension": 160,        # 完美
                "contact_height": 30,        # 完美
                "body_lean": 15              # 完美
            }
        }
    ]
    
    for scenario in user_scenarios:
        print(f"\\n👤 {scenario['name']}评价结果:")
        print("-" * 30)
        
        result = evaluator.evaluate("badminton", "clear", scenario['data'])
        
        print(f"总分: {result.total_score:.1f}/100 ({result.level})")
        print(f"评价: {result.summary}")
        
        if result.improvement_suggestions:
            print("主要建议:")
            for suggestion in result.improvement_suggestions[:2]:
                print(f"  • {suggestion}")
        
        if result.strengths:
            print("优势:")
            for strength in result.strengths[:2]:
                print(f"  • {strength}")


if __name__ == "__main__":
    print("🧪 新评价系统测试")
    print("📅 测试时间:", "2025-09-17")
    
    # 运行基础测试
    if test_new_evaluation_system():
        # 运行演示
        demo_evaluation_process()
        
        # 运行完整验证
        print("\\n" + "=" * 50)
        print("🔬 运行完整验证")
        print("=" * 50)
        run_full_validation()
        
        print("\\n🎊 测试完成！新评价系统运行正常。")
    else:
        print("\\n❌ 基础测试失败，请检查配置。")