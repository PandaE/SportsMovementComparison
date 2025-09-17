"""
Configuration Validation and Testing
配置验证和测试工具

Tools for validating evaluation configurations and testing the rule engine.
"""

from typing import Dict, List, Any
import json
from .evaluation_config import get_config_manager, ActionSpec
from .rule_evaluator import create_evaluator


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """验证所有配置"""
        results = {}
        
        for key, config in self.config_manager.actions.items():
            errors = self.validate_config(config)
            if errors:
                results[key] = errors
        
        return results
    
    def validate_config(self, config: ActionSpec) -> List[str]:
        """验证单个配置"""
        errors = []
        
        # 1. 检查基本字段
        if not config.name or not config.display_name:
            errors.append("缺少必要的名称字段")
        
        if not config.stages:
            errors.append("没有定义任何阶段")
            return errors
        
        # 2. 检查阶段权重
        total_weight = sum(stage.weight for stage in config.stages)
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"阶段权重总和 {total_weight:.3f} 不等于 1.0")
        
        # 3. 检查每个阶段
        for i, stage in enumerate(config.stages):
            stage_errors = self._validate_stage(stage, i)
            errors.extend(stage_errors)
        
        # 4. 检查测量项名称重复
        all_measurement_names = []
        for stage in config.stages:
            for measurement in stage.measurements:
                if measurement.name in all_measurement_names:
                    errors.append(f"测量项名称重复: {measurement.name}")
                all_measurement_names.append(measurement.name)
        
        return errors
    
    def _validate_stage(self, stage, stage_index: int) -> List[str]:
        """验证阶段配置"""
        errors = []
        prefix = f"阶段 {stage_index + 1} ({stage.name})"
        
        if not stage.measurements:
            errors.append(f"{prefix}: 没有定义测量项")
            return errors
        
        # 检查测量权重
        if len(stage.measurements) > 1:
            total_weight = sum(m.weight for m in stage.measurements)
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"{prefix}: 测量权重总和 {total_weight:.3f} 不等于 1.0")
        
        # 检查每个测量项
        for j, measurement in enumerate(stage.measurements):
            measurement_errors = self._validate_measurement(measurement, j, prefix)
            errors.extend(measurement_errors)
        
        return errors
    
    def _validate_measurement(self, measurement, measurement_index: int, stage_prefix: str) -> List[str]:
        """验证测量项配置"""
        errors = []
        prefix = f"{stage_prefix} 测量项 {measurement_index + 1} ({measurement.name})"
        
        # 检查范围逻辑
        ranges = [
            ("excellent_range", measurement.excellent_range),
            ("good_range", measurement.good_range), 
            ("acceptable_range", measurement.acceptable_range)
        ]
        
        for range_name, range_tuple in ranges:
            if len(range_tuple) != 2:
                errors.append(f"{prefix}: {range_name} 格式错误")
                continue
            
            min_val, max_val = range_tuple
            if min_val >= max_val:
                errors.append(f"{prefix}: {range_name} 最小值不能大于等于最大值")
        
        # 检查理想值是否在优秀范围内
        if not (measurement.excellent_range[0] <= measurement.ideal_value <= measurement.excellent_range[1]):
            errors.append(f"{prefix}: 理想值 {measurement.ideal_value} 不在优秀范围内")
        
        # 检查范围包含关系
        if not self._range_contains(measurement.good_range, measurement.excellent_range):
            errors.append(f"{prefix}: 良好范围应该包含优秀范围")
        
        if not self._range_contains(measurement.acceptable_range, measurement.good_range):
            errors.append(f"{prefix}: 可接受范围应该包含良好范围")
        
        return errors
    
    def _range_contains(self, outer_range: tuple, inner_range: tuple) -> bool:
        """检查外层范围是否包含内层范围"""
        return (outer_range[0] <= inner_range[0] and 
                outer_range[1] >= inner_range[1])


class EvaluatorTester:
    """评价器测试工具"""
    
    def __init__(self):
        self.evaluator = create_evaluator()
    
    def run_basic_tests(self) -> Dict[str, Any]:
        """运行基础测试"""
        results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "test_results": []
        }
        
        # 测试1: 完美数据
        perfect_result = self._test_perfect_performance()
        results["test_results"].append(perfect_result)
        if perfect_result["passed"]:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
        
        # 测试2: 差劣数据
        poor_result = self._test_poor_performance()
        results["test_results"].append(poor_result)
        if poor_result["passed"]:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
        
        # 测试3: 混合数据
        mixed_result = self._test_mixed_performance()
        results["test_results"].append(mixed_result)
        if mixed_result["passed"]:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
        
        return results
    
    def _test_perfect_performance(self) -> Dict[str, Any]:
        """测试完美表现"""
        test_data = {
            "stance_width": 50,          # 理想值
            "racket_ready_angle": 110,   # 理想值
            "shoulder_rotation": 45,     # 理想值
            "elbow_height": 0,           # 理想值
            "wrist_extension": 25,       # 理想值
            "arm_extension": 160,        # 理想值
            "contact_height": 30,        # 理想值
            "body_lean": 15              # 理想值
        }
        
        try:
            result = self.evaluator.evaluate("badminton", "clear", test_data)
            
            # 验证结果
            passed = (
                result.total_score >= 95 and  # 应该得到高分
                result.level in ["excellent", "perfect"] and
                len(result.stages) == 3 and
                all(stage.stage_score >= 90 for stage in result.stages)
            )
            
            return {
                "test_name": "完美表现测试",
                "passed": passed,
                "score": result.total_score,
                "level": result.level,
                "details": f"得分: {result.total_score:.1f}, 等级: {result.level}"
            }
            
        except Exception as e:
            return {
                "test_name": "完美表现测试",
                "passed": False,
                "error": str(e),
                "details": "测试执行失败"
            }
    
    def _test_poor_performance(self) -> Dict[str, Any]:
        """测试差劣表现"""
        test_data = {
            "stance_width": 80,          # 远超可接受范围
            "racket_ready_angle": 60,    # 远低于可接受范围
            "shoulder_rotation": 100,    # 远超可接受范围
            "elbow_height": -30,         # 远低于可接受范围
            "wrist_extension": 60,       # 远超可接受范围
            "arm_extension": 100,        # 远低于可接受范围
            "contact_height": 60,        # 远超可接受范围
            "body_lean": 50              # 远超可接受范围
        }
        
        try:
            result = self.evaluator.evaluate("badminton", "clear", test_data)
            
            # 验证结果
            passed = (
                result.total_score <= 60 and  # 应该得到低分
                result.level in ["poor", "needs_improvement"] and
                len(result.improvement_suggestions) > 0
            )
            
            return {
                "test_name": "差劣表现测试",
                "passed": passed,
                "score": result.total_score,
                "level": result.level,
                "details": f"得分: {result.total_score:.1f}, 等级: {result.level}, 建议数: {len(result.improvement_suggestions)}"
            }
            
        except Exception as e:
            return {
                "test_name": "差劣表现测试",
                "passed": False,
                "error": str(e),
                "details": "测试执行失败"
            }
    
    def _test_mixed_performance(self) -> Dict[str, Any]:
        """测试混合表现"""
        test_data = {
            "stance_width": 52,          # 良好范围
            "racket_ready_angle": 108,   # 优秀范围
            "shoulder_rotation": 35,     # 良好范围
            "elbow_height": 8,           # 良好范围
            "arm_extension": 150,        # 良好范围
            "contact_height": 25,        # 优秀范围
        }
        
        try:
            result = self.evaluator.evaluate("badminton", "clear", test_data)
            
            # 验证结果
            passed = (
                50 <= result.total_score <= 90 and  # 应该得到中等分数
                result.level in ["good", "excellent"] and
                len(result.stages) == 3
            )
            
            return {
                "test_name": "混合表现测试",
                "passed": passed,
                "score": result.total_score,
                "level": result.level,
                "details": f"得分: {result.total_score:.1f}, 等级: {result.level}"
            }
            
        except Exception as e:
            return {
                "test_name": "混合表现测试",
                "passed": False,
                "error": str(e),
                "details": "测试执行失败"
            }
    
    def test_single_measurement(self, measurement_name: str, test_values: List[float]) -> Dict[str, Any]:
        """测试单个测量项的评分曲线"""
        results = []
        
        # 创建基准数据（所有项目都是理想值）
        base_data = {
            "stance_width": 50,
            "racket_ready_angle": 110,
            "shoulder_rotation": 45,
            "elbow_height": 0,
            "wrist_extension": 25,
            "arm_extension": 160,
            "contact_height": 30,
            "body_lean": 15
        }
        
        for value in test_values:
            test_data = base_data.copy()
            test_data[measurement_name] = value
            
            try:
                result = self.evaluator.evaluate("badminton", "clear", test_data)
                
                # 找到对应的测量结果
                measurement_result = None
                for stage in result.stages:
                    for measurement in stage.measurements:
                        if measurement.name == measurement_name:
                            measurement_result = measurement
                            break
                
                if measurement_result:
                    results.append({
                        "value": value,
                        "score": measurement_result.score,
                        "level": measurement_result.level,
                        "feedback": measurement_result.feedback
                    })
                else:
                    results.append({
                        "value": value,
                        "error": "测量项未找到"
                    })
                    
            except Exception as e:
                results.append({
                    "value": value,
                    "error": str(e)
                })
        
        return {
            "measurement_name": measurement_name,
            "test_results": results
        }


def run_full_validation() -> Dict[str, Any]:
    """运行完整的验证测试"""
    print("🔍 开始评价系统验证...")
    
    # 1. 配置验证
    print("\\n1. 验证配置文件...")
    validator = ConfigValidator()
    config_errors = validator.validate_all_configs()
    
    if config_errors:
        print("❌ 发现配置错误:")
        for config_name, errors in config_errors.items():
            print(f"  {config_name}:")
            for error in errors:
                print(f"    - {error}")
    else:
        print("✅ 配置验证通过")
    
    # 2. 评价器测试
    print("\\n2. 测试评价引擎...")
    tester = EvaluatorTester()
    test_results = tester.run_basic_tests()
    
    print(f"✅ 通过测试: {test_results['tests_passed']}")
    print(f"❌ 失败测试: {test_results['tests_failed']}")
    
    for test in test_results['test_results']:
        status = "✅" if test['passed'] else "❌"
        print(f"  {status} {test['test_name']}: {test['details']}")
    
    # 3. 测试评分曲线
    print("\\n3. 测试评分曲线...")
    curve_test = tester.test_single_measurement("arm_extension", [120, 140, 150, 160, 170, 180, 200])
    
    print("手臂伸展角度评分曲线:")
    for result in curve_test['test_results']:
        if 'error' not in result:
            print(f"  {result['value']}° → {result['score']:.1f}分 ({result['level']})")
    
    return {
        "config_errors": config_errors,
        "test_results": test_results,
        "validation_passed": len(config_errors) == 0 and test_results['tests_failed'] == 0
    }


if __name__ == "__main__":
    # 运行验证
    results = run_full_validation()
    
    if results["validation_passed"]:
        print("\\n🎉 评价系统验证完全通过！")
    else:
        print("\\n⚠️ 评价系统验证发现问题，请检查上述输出。")