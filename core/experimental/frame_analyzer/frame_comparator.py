"""
Frame comparison engine for analyzing and comparing poses.
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
from ..models.pose_data import BodyPose, FrameAnalysis
from ..models.comparison_result import (
    MeasurementComparison, FrameComparison, ComprehensiveComparison
)
from ..config.sport_configs import ActionConfig, StageConfig, MeasurementRule
from ..config.comparison_rules import ComparisonRules
from .pose_extractor import PoseExtractor


class FrameComparator:
    """帧对比器 - 核心的帧对帧分析和对比功能"""
    
    def __init__(self, pose_extractor: Optional[PoseExtractor] = None):
        """
        初始化帧对比器
        
        Args:
            pose_extractor: 姿态提取器，如果为None则创建默认的
        """
        self.pose_extractor = pose_extractor if pose_extractor else PoseExtractor()
        self.comparison_rules = ComparisonRules()
    
    def analyze_frame(self, image: np.ndarray, stage_config: StageConfig, 
                     frame_index: int = 0) -> Optional[FrameAnalysis]:
        """
        分析单帧图像，提取姿态并计算所需的测量值
        
        Args:
            image: 输入图像
            stage_config: 阶段配置，定义需要计算的测量项
            frame_index: 帧索引
            
        Returns:
            FrameAnalysis对象或None
        """
        # 提取姿态
        pose = self.pose_extractor.extract_pose_from_image(image, frame_index)
        if not pose:
            return None
        
        # 创建帧分析对象
        frame_analysis = FrameAnalysis(frame_index=frame_index, pose=pose)
        
        # 根据配置计算各项测量值
        for measurement_rule in stage_config.measurements:
            value = self._calculate_measurement(pose, measurement_rule)
            if value is not None:
                frame_analysis.add_measurement(
                    measurement_rule.name, 
                    value, 
                    measurement_rule.unit
                )
        
        return frame_analysis
    
    def _calculate_measurement(self, pose: BodyPose, rule: MeasurementRule) -> Optional[float]:
        """
        根据测量规则计算具体的测量值
        
        Args:
            pose: 姿态数据
            rule: 测量规则
            
        Returns:
            测量值或None
        """
        if rule.measurement_type == "angle":
            # 角度计算需要三个点：keypoints[0], keypoints[1], keypoints[2]
            if len(rule.keypoints) >= 3:
                angle = pose.calculate_angle(rule.keypoints[0], rule.keypoints[1], rule.keypoints[2])
                if angle is not None:
                    return self.comparison_rules.normalize_angle(angle)
        
        elif rule.measurement_type == "distance":
            # 距离计算需要两个点
            if len(rule.keypoints) >= 2:
                pt1 = pose.get_keypoint(rule.keypoints[0])
                pt2 = pose.get_keypoint(rule.keypoints[1])
                if pt1 and pt2:
                    return np.sqrt((pt1.x - pt2.x)**2 + (pt1.y - pt2.y)**2)
        
        elif rule.measurement_type == "height":
            # 高度测量：关键点相对于参考点的垂直距离
            if len(rule.keypoints) >= 1 and rule.reference_point:
                target_pt = pose.get_keypoint(rule.keypoints[0])
                ref_pt = pose.get_keypoint(rule.reference_point)
                if target_pt and ref_pt:
                    return ref_pt.y - target_pt.y  # y坐标越小越靠上，所以ref_y - target_y为正表示target在上方
        
        elif rule.measurement_type == "vertical_distance":
            # 垂直距离测量：关键点相对于参考点的垂直距离
            if len(rule.keypoints) >= 1 and rule.reference_point:
                target_pt = pose.get_keypoint(rule.keypoints[0])
                ref_pt = pose.get_keypoint(rule.reference_point)
                if target_pt and ref_pt:
                    distance = ref_pt.y - target_pt.y  # y坐标越小越靠上
                    # 根据方向调整符号
                    if rule.direction == "up":
                        return distance   # target在ref上方为正值
                    elif rule.direction == "down":
                        return -distance  # target在ref下方为正值
                    else:
                        return distance   # 默认上方为正
        
        elif rule.measurement_type == "horizontal_distance":
            # 水平距离测量：关键点相对于参考点的水平距离
            if len(rule.keypoints) >= 1 and rule.reference_point:
                target_pt = pose.get_keypoint(rule.keypoints[0])
                ref_pt = pose.get_keypoint(rule.reference_point)
                if target_pt and ref_pt:
                    distance = target_pt.x - ref_pt.x
                    # 根据方向调整符号
                    if rule.direction == "back" or rule.direction == "backward":
                        return -distance  # 向后为正值
                    elif rule.direction == "forward":
                        return distance   # 向前为正值
                    else:
                        return abs(distance)  # 默认返回绝对值
        
        # 其他测量类型可以在这里扩展...
        
        return None
    
    def compare_frames(self, user_frame: FrameAnalysis, standard_frame: FrameAnalysis,
                      stage_config: StageConfig) -> FrameComparison:
        """
        对比两帧的分析结果
        
        Args:
            user_frame: 用户帧分析结果
            standard_frame: 标准帧分析结果 
            stage_config: 阶段配置
            
        Returns:
            FrameComparison对比结果
        """
        measurements = []
        total_weighted_score = 0
        total_weight = 0
        
        for rule in stage_config.measurements:
            user_value = user_frame.get_measurement(rule.name)
            standard_value = standard_frame.get_measurement(rule.name)
            
            if user_value is not None and standard_value is not None:
                # 计算差异和相似度
                difference = user_value - standard_value
                percentage_diff = self.comparison_rules.calculate_percentage_difference(
                    user_value, standard_value)
                is_within_tolerance = self.comparison_rules.is_within_tolerance(
                    user_value, rule.tolerance_range)
                similarity_score = self.comparison_rules.calculate_similarity_score(
                    user_value, standard_value, rule.tolerance_range)
                
                measurement_comparison = MeasurementComparison(
                    measurement_name=rule.name,
                    user_value=user_value,
                    standard_value=standard_value,
                    difference=difference,
                    percentage_diff=percentage_diff,
                    is_within_tolerance=is_within_tolerance,
                    tolerance_range=rule.tolerance_range
                )
                
                measurements.append(measurement_comparison)
                
                # 计算加权分数
                total_weighted_score += similarity_score * rule.weight
                total_weight += rule.weight
        
        # 计算整体评分
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        
        return FrameComparison(
            stage_name=stage_config.name,
            user_frame=user_frame,
            standard_frame=standard_frame,
            measurements=measurements,
            overall_score=overall_score
        )
    
    def compare_multiple_stages(self, user_images: Dict[str, np.ndarray], 
                              standard_images: Dict[str, np.ndarray],
                              action_config: ActionConfig) -> ComprehensiveComparison:
        """
        对比多个阶段的帧
        
        Args:
            user_images: 用户各阶段图像 {stage_name: image}
            standard_images: 标准各阶段图像 {stage_name: image}
            action_config: 动作配置
            
        Returns:
            ComprehensiveComparison综合对比结果
        """
        frame_comparisons = []
        stage_scores = {}
        stage_weights = {}
        
        for stage_config in action_config.stages:
            stage_name = stage_config.name
            
            if stage_name in user_images and stage_name in standard_images:
                # 分析用户和标准帧
                user_analysis = self.analyze_frame(
                    user_images[stage_name], stage_config)
                standard_analysis = self.analyze_frame(
                    standard_images[stage_name], stage_config)
                
                if user_analysis and standard_analysis:
                    # 进行对比
                    comparison = self.compare_frames(
                        user_analysis, standard_analysis, stage_config)
                    frame_comparisons.append(comparison)
                    
                    # 记录分数和权重
                    stage_scores[stage_name] = comparison.overall_score
                    stage_weights[stage_name] = stage_config.weight
        
        # 计算综合评分
        overall_score = self.comparison_rules.calculate_weighted_average(
            stage_scores, stage_weights)
        
        return ComprehensiveComparison(
            sport="Badminton",  # 可以从配置中获取
            action=action_config.name,
            frame_comparisons=frame_comparisons,
            overall_score=overall_score
        )
    
    def create_visualization(self, user_image: np.ndarray, standard_image: np.ndarray,
                           comparison: FrameComparison) -> Dict[str, np.ndarray]:
        """
        创建对比可视化图像
        
        Args:
            user_image: 用户图像
            standard_image: 标准图像
            comparison: 对比结果
            
        Returns:
            包含可视化图像的字典
        """
        # 在图像上标注姿态
        user_vis = self.pose_extractor.visualize_pose(
            user_image, comparison.user_frame.pose)
        standard_vis = self.pose_extractor.visualize_pose(
            standard_image, comparison.standard_frame.pose)
        
        # 创建并排对比图
        h1, w1 = user_vis.shape[:2]
        h2, w2 = standard_vis.shape[:2]
        
        # 调整尺寸一致
        target_h = max(h1, h2)
        target_w = max(w1, w2)
        
        user_resized = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        standard_resized = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        
        user_resized[:h1, :w1] = user_vis
        standard_resized[:h2, :w2] = standard_vis
        
        # 并排拼接
        comparison_vis = np.hstack([user_resized, standard_resized])
        
        # 添加文字说明
        cv2.putText(comparison_vis, f"User (Score: {comparison.overall_score:.1f})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(comparison_vis, "Standard", 
                   (target_w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        return {
            'user_annotated': user_vis,
            'standard_annotated': standard_vis, 
            'side_by_side': comparison_vis
        }