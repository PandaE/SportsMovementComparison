"""
experimental_comparison_engine.py
集成实验模块的高级对比引擎，兼容原有接口
"""
import cv2
import os
import tempfile
from typing import Dict, List, Tuple, Optional
from .comparison_engine import ComparisonEngine
from .experimental.frame_analyzer.frame_comparator import FrameComparator
from .experimental.frame_analyzer.pose_extractor import PoseExtractor
from .experimental.frame_analyzer.key_frame_extractor import KeyFrameExtractor
from .experimental.config.sport_configs import SportConfigs
from .pipeline.evaluation_pipeline import run_action_evaluation


class ExperimentalComparisonEngine(ComparisonEngine):
    """
    实验对比引擎 - 继承原有接口，添加高级分析功能
    """
    
    def __init__(self, use_experimental_features: bool = True):
        """
        初始化引擎
        
        Args:
            use_experimental_features: 是否启用实验功能
        """
        super().__init__()
        self.use_experimental = use_experimental_features
        
        if self.use_experimental:
            try:
                self.pose_extractor = PoseExtractor(backend="mediapipe")
                self.frame_comparator = FrameComparator(pose_extractor=self.pose_extractor)
                self.key_frame_extractor = KeyFrameExtractor()
                self.experimental_ready = True
                print("实验模块初始化成功")
            except Exception as e:
                print(f"实验模块初始化失败，回退到基础模式: {e}")
                self.experimental_ready = False
        else:
            self.experimental_ready = False
    
    def compare(self, user_video_path: str, standard_video_path: str, 
                sport: str = "badminton", action: str = "clear") -> Dict:
        """
        对比两个视频
        
        Args:
            user_video_path: 用户视频路径
            standard_video_path: 标准视频路径
            sport: 运动类型
            action: 动作类型
            
        Returns:
            对比结果字典
        """
        if self.experimental_ready and self.use_experimental:
            return self._experimental_compare(user_video_path, standard_video_path, sport, action)
        else:
            # 回退到原有的dummy实现
            return super().compare(user_video_path, standard_video_path)
    
    def _experimental_compare(self, user_video_path: str, standard_video_path: str, 
                            sport: str, action: str) -> Dict:
        """实验模块的对比实现"""
        try:
            # 1. 获取运动配置
            config = SportConfigs.get_config(sport, action)
            
            # 2. 自动提取关键帧
            print(f"🎯 开始提取关键帧: {sport} - {action}")
            user_stage_frames = self.key_frame_extractor.extract_stage_images(user_video_path, sport, action)
            standard_stage_frames = self.key_frame_extractor.extract_stage_images(standard_video_path, sport, action)
            
            if not user_stage_frames or not standard_stage_frames:
                return self._create_error_result("无法提取有效的关键帧")
            
            print(f"✅ 关键帧提取完成，共提取 {len(user_stage_frames)} 个阶段的帧")
            
            # 3. 执行多阶段对比分析 (旧对比逻辑保留)
            results = []
            overall_score = 0.0
            
            for stage in config.stages:
                stage_name = stage.name
                
                # 检查是否有对应的关键帧
                if stage_name in user_stage_frames and stage_name in standard_stage_frames:
                    stage_result = self._analyze_stage(
                        user_stage_frames[stage_name], 
                        standard_stage_frames[stage_name], 
                        stage
                    )
                    results.append(stage_result)
                    overall_score += stage_result['score'] * stage.weight
                    print(f"   📊 {stage_name}: {stage_result['score']:.2f} (权重: {stage.weight})")
                else:
                    print(f"   ⚠️  {stage_name}: 缺少关键帧，跳过分析")
            
            # 4. 生成对比可视化 (使用第一个可用的关键帧对)
            comparison_images = {}
            if user_stage_frames and standard_stage_frames:
                first_stage = list(user_stage_frames.keys())[0]
                comparison_images = self._generate_comparison_images(
                    user_stage_frames[first_stage], 
                    standard_stage_frames[first_stage], 
                    results
                )
            
            # 5. 构建兼容的返回格式，包含关键帧信息
            # 获取关键帧位置信息用于传递
            user_frame_positions = self.key_frame_extractor.extract_stage_frames(user_video_path, sport, action)
            standard_frame_positions = self.key_frame_extractor.extract_stage_frames(standard_video_path, sport, action)
            
            result = self._format_experimental_results(
                overall_score, results, comparison_images, user_video_path, standard_video_path,
                user_frame_positions, standard_frame_positions
            )
            
            # 6. 添加关键帧信息到结果中
            result['key_frame_info'] = {
                'user_frames': user_frame_positions,
                'standard_frames': standard_frame_positions,
                'extraction_method': 'intelligent' if self.key_frame_extractor.use_intelligent_extraction else 'time_based',
                'sport': sport,
                'action': action
            }
            
            print(f"🏆 旧对比分析完成，总分: {overall_score:.2f}")

            # 7. 新增：基于 Metrics + Evaluation 的统一评分 (仅使用用户视频关键帧，不再与标准逐帧差分)
            try:
                # 复用已抽取的用户阶段帧作为 pose 计算输入
                # 仅当用户帧存在时执行
                if user_stage_frames:
                    # 提取每阶段 pose（单帧）
                    stage_pose_map = {}
                    for stage in config.stages:
                        if stage.name in user_stage_frames:
                            pose = self.frame_comparator.pose_extractor.extract_pose_from_image(user_stage_frames[stage.name], 0)
                            if pose:
                                stage_pose_map[stage.name] = (pose, 0)
                    if stage_pose_map:
                        metrics_result, evaluation = run_action_evaluation(config, stage_pose_map, language='zh_CN')
                        result['new_evaluation'] = {
                            'overall_score': evaluation.score,
                            'summary': evaluation.summary,
                            'stages': [
                                {
                                    'name': st.name,
                                    'score': st.score,
                                    'measurements': [
                                        {
                                            'key': mv.key,
                                            'value': mv.value,
                                            'score': mv.score,
                                            'passed': mv.passed,
                                            'feedback': mv.feedback,
                                        } for mv in st.measurements
                                    ]
                                } for st in evaluation.stages
                            ]
                        }
                        print("🆕 新评价模块输出完成 (new_evaluation 键)")
            except Exception as ee:
                print(f"新评价模块执行失败: {ee}")

            return result
            
        except Exception as e:
            print(f"实验分析失败: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_result(f"分析失败: {str(e)}")
    
    def _extract_key_frames(self, video_path: str, num_frames: int = 1) -> List:
        """从视频中提取关键帧"""
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return frames
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 简单策略：提取中间帧
        frame_indices = [total_frames // 2] if num_frames == 1 else \
                       [int(i * total_frames / num_frames) for i in range(num_frames)]
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        cap.release()
        return frames
    
    def _analyze_stage(self, user_frame, standard_frame, stage_config) -> Dict:
        """分析单个阶段"""
        try:
            # 使用analyze_frame方法进行帧分析
            user_analysis = self.frame_comparator.analyze_frame(user_frame, stage_config)
            standard_analysis = self.frame_comparator.analyze_frame(standard_frame, stage_config)
            
            if not user_analysis or not standard_analysis:
                return {
                    'stage_name': stage_config.name,
                    'score': 0.0,
                    'measurements': [],
                    'error': '帧分析失败'
                }
            
            # 执行帧对比
            comparison_result = self.frame_comparator.compare_frames(
                user_analysis, standard_analysis, stage_config
            )
            
            # 转换对比结果格式
            enhanced_measurements = []
            for measurement_comp in comparison_result.measurements:
                enhanced_measurement = {
                    'measurement_name': measurement_comp.measurement_name,
                    'user_value': measurement_comp.user_value,
                    'standard_value': measurement_comp.standard_value,
                    'difference': measurement_comp.difference,
                    'percentage_diff': measurement_comp.percentage_diff,
                    'is_within_tolerance': measurement_comp.is_within_tolerance,
                    'tolerance_range': measurement_comp.tolerance_range,
                    'unit': '°',  # 大部分是角度测量
                    'keypoints': [],  # 可以从stage_config.measurements中查找
                    'score': 1.0 if measurement_comp.is_within_tolerance else 0.5
                }
                
                # 找到对应的规则来获取keypoints和unit
                for rule in stage_config.measurements:
                    if rule.name == measurement_comp.measurement_name:
                        enhanced_measurement['keypoints'] = rule.keypoints
                        enhanced_measurement['unit'] = rule.unit
                        break
                
                enhanced_measurements.append(enhanced_measurement)
            
            return {
                'stage_name': stage_config.name,
                'score': comparison_result.overall_score / 100.0,  # 转换为0-1范围
                'measurements': enhanced_measurements,
                'suggestions': self._generate_suggestions_from_comparison(comparison_result)
            }
            
            # 增强测量结果信息
            enhanced_measurements = []
            for measurement in comparison_result['measurement_results']:
                # 找到对应的规则配置
                rule = next((r for r in stage_config.measurements 
                           if r.name == measurement.get('measurement_name')), None)
                
                enhanced_measurement = {
                    'measurement_name': measurement.get('measurement_name'),
                    'user_value': measurement.get('user_value'),
                    'standard_value': measurement.get('standard_value'),
                    'difference': measurement.get('difference'),
                    'percentage_diff': measurement.get('percentage_diff', 0),
                    'is_within_tolerance': measurement.get('is_within_tolerance'),
                    'tolerance_range': measurement.get('tolerance_range'),
                    'unit': rule.unit if rule else '°',
                    'keypoints': rule.keypoints if rule else [],
                    'measurement_type': rule.measurement_type if rule else 'unknown',
                    'description': rule.description if rule else '',
                    'weight': rule.weight if rule else 1.0,
                    'score': measurement.get('score', 0)
                }
                enhanced_measurements.append(enhanced_measurement)
            
            return {
                'stage_name': stage_config.name,
                'score': comparison_result['overall_score'],
                'measurements': enhanced_measurements,
                'suggestions': self._generate_suggestions(comparison_result),
                'processing_info': {
                    'pose_detection_confidence': {
                        'user': self._get_pose_confidence(user_pose),
                        'standard': self._get_pose_confidence(standard_pose)
                    },
                    'keypoints_detected': {
                        'user': self._count_valid_keypoints(user_pose),
                        'standard': self._count_valid_keypoints(standard_pose)
                    }
                }
            }
            
        except Exception as e:
            return {
                'stage_name': stage_config.name,
                'score': 0.0,
                'measurements': [],
                'error': f'分析错误: {str(e)}'
            }
    
    def _generate_comparison_images(self, user_frame, standard_frame, results) -> Dict:
        """生成对比可视化图像"""
        comparison_images = {}
        
        try:
            # 提取并可视化姿态
            user_pose = self.pose_extractor.extract_pose_from_image(user_frame)
            standard_pose = self.pose_extractor.extract_pose_from_image(standard_frame)
            
            if user_pose and standard_pose:
                user_vis = self.pose_extractor.visualize_pose(user_frame, user_pose)
                standard_vis = self.pose_extractor.visualize_pose(standard_frame, standard_pose)
                
                # 保存临时图像
                temp_dir = tempfile.gettempdir()
                user_img_path = os.path.join(temp_dir, "user_pose_analysis.jpg")
                standard_img_path = os.path.join(temp_dir, "standard_pose_analysis.jpg")
                
                cv2.imwrite(user_img_path, user_vis)
                cv2.imwrite(standard_img_path, standard_vis)
                
                comparison_images = {
                    'user_pose': user_img_path,
                    'standard_pose': standard_img_path
                }
        
        except Exception as e:
            print(f"生成对比图像失败: {e}")
        
        return comparison_images
    
    def _generate_suggestions_from_comparison(self, comparison_result) -> List[str]:
        """从FrameComparison结果生成建议"""
        suggestions = []
        
        for measurement in comparison_result.measurements:
            name = measurement.measurement_name
            if not measurement.is_within_tolerance:
                if '角度' in name or 'angle' in name.lower():
                    if measurement.difference > 0:
                        suggestions.append(f"{name}偏大，建议调整手臂角度")
                    else:
                        suggestions.append(f"{name}偏小，建议加大手臂角度")
                else:
                    suggestions.append(f"{name}需要调整")
            else:
                suggestions.append(f"{name}表现良好")
        
        if not suggestions:
            suggestions.append("动作标准，继续保持！")
        
        return suggestions
    
    def _generate_suggestions(self, comparison_result: Dict) -> List[str]:
        """根据对比结果生成建议"""
        suggestions = []
        
        for measurement in comparison_result.get('measurement_results', []):
            score = measurement.get('score', 0)
            name = measurement.get('measurement_name', '未知测量')
            
            if score < 0.6:
                if '角度' in name:
                    suggestions.append(f"{name}偏差较大，注意调整手臂姿势")
                elif '高度' in name:
                    suggestions.append(f"{name}不够理想，注意身体姿态")
                else:
                    suggestions.append(f"{name}需要改进")
            elif score < 0.8:
                suggestions.append(f"{name}基本正确，可以进一步优化")
        
        if not suggestions:
            suggestions.append("动作标准，继续保持！")
        
        return suggestions
    
    def _get_measurement_type_description(self, measurement_type: str) -> str:
        """获取测量类型的描述"""
        descriptions = {
            'angle': '角度测量 - 通过三个关键点计算夹角',
            'distance': '距离测量 - 计算两点间的直线距离',
            'height': '高度测量 - 相对于参考点的垂直距离',
            'horizontal_distance': '水平距离 - 两点间的水平距离',
            'vertical_distance': '垂直距离 - 两点间的垂直距离',
            'ratio': '比例测量 - 计算两个距离的比值',
            'position': '位置测量 - 关键点的绝对位置'
        }
        return descriptions.get(measurement_type, f'自定义测量类型: {measurement_type}')
    
    def _get_pose_confidence(self, pose) -> float:
        """获取姿态检测的平均置信度"""
        if not pose:
            return 0.0
        
        confidences = []
        keypoints = [
            pose.nose, pose.left_shoulder, pose.right_shoulder,
            pose.left_elbow, pose.right_elbow, pose.left_wrist, pose.right_wrist,
            pose.left_hip, pose.right_hip, pose.left_knee, pose.right_knee,
            pose.left_ankle, pose.right_ankle
        ]
        
        for kp in keypoints:
            if kp and hasattr(kp, 'confidence'):
                confidences.append(kp.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _count_valid_keypoints(self, pose) -> int:
        """统计有效关键点数量"""
        if not pose:
            return 0
        
        count = 0
        keypoints = [
            pose.nose, pose.left_shoulder, pose.right_shoulder,
            pose.left_elbow, pose.right_elbow, pose.left_wrist, pose.right_wrist,
            pose.left_hip, pose.right_hip, pose.left_knee, pose.right_knee,
            pose.left_ankle, pose.right_ankle
        ]
        
        for kp in keypoints:
            if kp and (not hasattr(kp, 'confidence') or kp.confidence > 0.5):
                count += 1
        
        return count
    
    def _format_experimental_results(self, overall_score: float, stage_results: List, 
                                   comparison_images: Dict, user_video_path: str, 
                                   standard_video_path: str, user_frame_positions: Dict[str, int] = None,
                                   standard_frame_positions: Dict[str, int] = None) -> Dict:
        """格式化结果以兼容原有接口并提供高级分析数据"""
        
        # 构建key_movements列表（兼容原接口）
        key_movements = []
        stages_data = {}  # 为高级分析窗口提供的阶段数据
        
        for i, stage_result in enumerate(stage_results):
            stage_name = stage_result.get('stage_name', f'阶段{i+1}')
            score = stage_result.get('score', 0)
            suggestions = stage_result.get('suggestions', [])
            measurements = stage_result.get('measurements', [])
            
            # 生成摘要
            if score >= 0.8:
                summary = f"{stage_name}: 动作标准 (得分: {score:.1%})"
            elif score >= 0.6:
                summary = f"{stage_name}: 基本正确，有改进空间 (得分: {score:.1%})"
            else:
                summary = f"{stage_name}: 需要改进 (得分: {score:.1%})"
            
            # 简化的详细测量信息 - 只显示核心对比数据
            measurement_details = []
            stage_measurements = []  # 为高级分析窗口准备的测量数据
            
            for m in measurements:
                measurement_name = m.get('measurement_name', '测量')
                user_value = m.get('user_value', 0)
                standard_value = m.get('standard_value', 0)
                unit = m.get('unit', '')
                difference = m.get('difference', 0)
                is_within_tolerance = m.get('is_within_tolerance', False)
                keypoints = m.get('keypoints', [])
                
                # 核心对比信息
                basic_info = f"• {measurement_name}: 用户 {user_value:.1f}{unit} vs 标准 {standard_value:.1f}{unit}"
                measurement_details.append(basic_info)
                
                # 简洁的差异说明
                if is_within_tolerance:
                    status = "✓ 达标"
                else:
                    direction = "偏大" if difference > 0 else "偏小"
                    status = f"✗ {direction} {abs(difference):.1f}{unit}"
                
                measurement_details.append(f"  {status}")
                
                # 测量点信息（如果有）
                if keypoints:
                    measurement_details.append(f"  测量点: {' → '.join(keypoints)}")
                
                # 为高级分析窗口准备测量数据
                stage_measurements.append({
                    'rule_name': measurement_name,
                    'user_value': user_value,
                    'standard_value': standard_value,
                    'is_within_range': is_within_tolerance,
                    'measurement_points': keypoints
                })
            
            # 为高级分析窗口构建阶段数据，使用传入的关键帧位置
            user_frame = user_frame_positions.get(stage_name, 0) if user_frame_positions else 0
            standard_frame = standard_frame_positions.get(stage_name, 0) if standard_frame_positions else 0
            
            stages_data[stage_name] = {
                'user_frame': user_frame,
                'standard_frame': standard_frame,
                'stage_info': {
                    'score': score * 100,
                    'status': summary
                },
                'measurements': stage_measurements
            }
            
            key_movements.append({
                'name': stage_name,
                'user_image': comparison_images.get('user_pose'),
                'standard_image': comparison_images.get('standard_pose'),
                'summary': summary,
                'suggestion': '; '.join(suggestions) if suggestions else '继续保持',
                'detailed_measurements': measurement_details,
                'measurements_data': measurements,  # 保留原始数据用于详细展示
                'score': score
            })
        
        return {
            'score': int(overall_score * 100),  # 转换为百分制
            'detailed_score': overall_score,
            'key_movements': key_movements,
            'analysis_type': 'experimental_with_key_frames',
            'sport': '羽毛球',
            'action': '正手高远球',
            'user_video_path': user_video_path,
            'standard_video_path': standard_video_path,
            'comparison_info': {
                'user_frame': f"从 {user_video_path} 自动提取的关键帧",
                'standard_frame': f"从 {standard_video_path} 自动提取的关键帧",
                'rules_applied': [m.get('measurement_name') for sr in stage_results for m in sr.get('measurements', [])],
                'total_comparisons': sum(len(sr.get('measurements', [])) for sr in stage_results),
                'extraction_method': '基于时间等分的自动关键帧提取'
            },
            # 为高级分析窗口添加阶段数据
            'stages': stages_data,
            'comparison_images': comparison_images,
            'analysis_summary': {
                'total_stages': len(stage_results),
                'avg_score': overall_score * 100,
                'suggestions': [s for sr in stage_results for s in sr.get('suggestions', [])],
                'key_frame_extraction': '✅ 已自动提取关键帧'
            }
        }
    
    def _create_error_result(self, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            'score': 0,
            'error': error_message,
            'key_movements': [{
                'name': '分析错误',
                'user_image': None,
                'standard_image': None,
                'summary': error_message,
                'suggestion': '请检查视频文件或联系技术支持'
            }],
            'analysis_type': 'error'
        }
    
    def get_available_configs(self) -> List[Tuple[str, str]]:
        """获取可用的运动配置"""
        if self.experimental_ready:
            return SportConfigs.list_available_configs()
        else:
            return [("Badminton", "Clear Shot (Basic)")]
    
    def set_experimental_mode(self, enabled: bool):
        """设置实验模式开关"""
        self.use_experimental = enabled and self.experimental_ready
        print(f"实验模式: {'启用' if self.use_experimental else '禁用'}")