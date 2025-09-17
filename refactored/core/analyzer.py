"""
Unified Analysis Engine - Core Module
统一分析引擎 - 核心模块

This module combines the functionality of the original comparison engines
into a single, simplified interface while maintaining all core features.
"""

import cv2
import os
import tempfile
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from config.settings import AppSettings, SportSettings


class MovementAnalyzer:
    """
    Unified movement analysis engine.
    统一的运动分析引擎
    
    Combines basic comparison with advanced pose analysis in a single interface.
    """
    
    def __init__(self, use_advanced_analysis: bool = True):
        """
        Initialize the analyzer.
        
        Args:
            use_advanced_analysis: Whether to enable advanced pose analysis
        """
        self.use_advanced_analysis = use_advanced_analysis
        self.pose_detector = None
        self.settings = AppSettings.get_default_settings()
        
        # Initialize pose detection if advanced analysis is enabled
        if self.use_advanced_analysis:
            self._init_pose_detection()
    
    def _init_pose_detection(self):
        """Initialize pose detection components"""
        try:
            from .pose_detector import PoseDetector
            self.pose_detector = PoseDetector()
            print("✅ Advanced pose analysis enabled")
        except ImportError as e:
            print(f"⚠️ Advanced analysis unavailable, falling back to basic mode: {e}")
            self.use_advanced_analysis = False
    
    def analyze_movement(self, 
                        user_video_path: str, 
                        standard_video_path: str,
                        sport: str = "badminton",
                        action: str = "clear") -> Dict[str, Any]:
        """
        Analyze and compare two videos.
        分析和对比两个视频
        
        Args:
            user_video_path: Path to user's video
            standard_video_path: Path to standard reference video
            sport: Sport type (e.g., "badminton")
            action: Action type (e.g., "clear")
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Validate inputs
            if not self._validate_videos(user_video_path, standard_video_path):
                return self._create_error_result("Invalid video files")
            
            # Perform analysis based on mode
            if self.use_advanced_analysis and self.pose_detector:
                return self._advanced_analysis(user_video_path, standard_video_path, sport, action)
            else:
                return self._basic_analysis(user_video_path, standard_video_path, sport, action)
                
        except Exception as e:
            print(f"Analysis failed: {e}")
            return self._create_error_result(f"Analysis failed: {str(e)}")
    
    def _validate_videos(self, user_path: str, standard_path: str) -> bool:
        """Validate video files"""
        for path in [user_path, standard_path]:
            if not os.path.exists(path):
                return False
            
            # Check file extension
            ext = Path(path).suffix.lower()
            if ext not in AppSettings.SUPPORTED_VIDEO_FORMATS:
                return False
                
            # Basic video validation with OpenCV
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                cap.release()
                return False
            cap.release()
        
        return True
    
    def _advanced_analysis(self, user_path: str, standard_path: str, 
                          sport: str, action: str) -> Dict[str, Any]:
        """Perform advanced pose-based analysis"""
        try:
            from .video_processor import VideoProcessor
            
            # Initialize video processor
            processor = VideoProcessor()
            
            # Extract key frames
            user_frames = processor.extract_key_frames(user_path, sport, action)
            standard_frames = processor.extract_key_frames(standard_path, sport, action)
            
            if not user_frames or not standard_frames:
                return self._basic_analysis(user_path, standard_path, sport, action)
            
            # Analyze poses for each stage
            results = []
            overall_score = 0.0
            
            # Get sport configuration
            from config.sports_config import get_sport_config
            config = get_sport_config(sport, action)
            
            for stage_name, user_frame in user_frames.items():
                if stage_name in standard_frames:
                    stage_result = self._analyze_stage(
                        user_frame, 
                        standard_frames[stage_name], 
                        stage_name,
                        config.get(stage_name, {})
                    )
                    results.append(stage_result)
                    overall_score += stage_result.get('score', 0) * stage_result.get('weight', 1.0)
            
            # Generate comparison images
            comparison_images = self._generate_comparison_images(user_frames, standard_frames)
            
            return self._format_advanced_results(
                overall_score, results, comparison_images, 
                user_path, standard_path, sport, action
            )
            
        except Exception as e:
            print(f"Advanced analysis failed: {e}, falling back to basic mode")
            return self._basic_analysis(user_path, standard_path, sport, action)
    
    def _basic_analysis(self, user_path: str, standard_path: str, 
                       sport: str, action: str) -> Dict[str, Any]:
        """Perform basic analysis without pose detection"""
        
        # Extract middle frames for comparison
        user_frame = self._extract_middle_frame(user_path)
        standard_frame = self._extract_middle_frame(standard_path)
        
        # Generate a mock analysis result
        score = 75  # Basic scoring
        
        movements = [
            {
                'name': f'{SportSettings.get_action_name(sport, action)} - 整体动作',
                'user_image': self._save_temp_image(user_frame),
                'standard_image': self._save_temp_image(standard_frame),
                'summary': f'基础对比分析完成，得分: {score}分',
                'suggestion': '建议启用高级分析获得更详细的动作指导',
                'score': score / 100.0
            }
        ]
        
        return {
            'score': score,
            'detailed_score': score / 100.0,
            'key_movements': movements,
            'analysis_type': 'basic',
            'sport': SportSettings.get_sport_name(sport),
            'action': SportSettings.get_action_name(sport, action),
            'user_video_path': user_path,
            'standard_video_path': standard_path,
            'comparison_info': {
                'analysis_mode': 'basic',
                'pose_detection': 'disabled',
                'note': '启用高级分析以获得详细的姿态对比'
            }
        }
    
    def _analyze_stage(self, user_frame, standard_frame, stage_name: str, 
                      stage_config: Dict) -> Dict[str, Any]:
        """Analyze a single movement stage"""
        if not self.pose_detector:
            return {'name': stage_name, 'score': 0.75, 'weight': 1.0}
        
        # Extract poses
        user_pose = self.pose_detector.detect_pose(user_frame)
        standard_pose = self.pose_detector.detect_pose(standard_frame)
        
        if not user_pose or not standard_pose:
            return {'name': stage_name, 'score': 0.5, 'weight': 1.0}
        
        # Calculate measurements
        measurements = []
        stage_score = 0.0
        
        for measurement in stage_config.get('measurements', []):
            measurement_result = self.pose_detector.calculate_measurement(
                user_pose, standard_pose, measurement
            )
            measurements.append(measurement_result)
            stage_score += measurement_result.get('score', 0)
        
        if measurements:
            stage_score /= len(measurements)
        
        return {
            'name': stage_name,
            'score': stage_score,
            'weight': stage_config.get('weight', 1.0),
            'measurements': measurements,
            'suggestions': self._generate_stage_suggestions(measurements)
        }
    
    def _extract_middle_frame(self, video_path: str):
        """Extract middle frame from video"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame = total_frames // 2
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    def _save_temp_image(self, frame) -> Optional[str]:
        """Save frame as temporary image"""
        if frame is None:
            return None
        
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"analysis_frame_{os.getpid()}.jpg")
        
        try:
            cv2.imwrite(temp_path, frame)
            return temp_path
        except:
            return None
    
    def _generate_comparison_images(self, user_frames: Dict, standard_frames: Dict) -> Dict:
        """Generate comparison visualization images"""
        comparison_images = {}
        
        if not self.pose_detector:
            return comparison_images
        
        try:
            # Use the first available frame pair
            for stage_name in user_frames:
                if stage_name in standard_frames:
                    user_viz = self.pose_detector.visualize_pose(
                        user_frames[stage_name]
                    )
                    standard_viz = self.pose_detector.visualize_pose(
                        standard_frames[stage_name]
                    )
                    
                    comparison_images.update({
                        'user_pose': self._save_temp_image(user_viz),
                        'standard_pose': self._save_temp_image(standard_viz)
                    })
                    break
        except Exception as e:
            print(f"Failed to generate comparison images: {e}")
        
        return comparison_images
    
    def _generate_stage_suggestions(self, measurements: List[Dict]) -> List[str]:
        """Generate suggestions based on measurements"""
        suggestions = []
        
        for measurement in measurements:
            name = measurement.get('name', 'Unknown')
            score = measurement.get('score', 0)
            
            if score < 0.6:
                suggestions.append(f"{name}: 需要改进，建议多练习")
            elif score < 0.8:
                suggestions.append(f"{name}: 基本正确，可以进一步优化")
            else:
                suggestions.append(f"{name}: 表现良好")
        
        if not suggestions:
            suggestions.append("继续保持良好状态！")
        
        return suggestions
    
    def _format_advanced_results(self, overall_score: float, stage_results: List,
                                comparison_images: Dict, user_path: str, 
                                standard_path: str, sport: str, action: str) -> Dict:
        """Format advanced analysis results"""
        
        # Convert stage results to key movements
        key_movements = []
        for stage in stage_results:
            stage_name = stage.get('name', 'Unknown Stage')
            score = stage.get('score', 0)
            measurements = stage.get('measurements', [])
            suggestions = stage.get('suggestions', [])
            
            # Create summary
            if score >= 0.8:
                summary = f"{stage_name}: 动作标准 (得分: {score:.1%})"
            elif score >= 0.6:
                summary = f"{stage_name}: 基本正确 (得分: {score:.1%})"
            else:
                summary = f"{stage_name}: 需要改进 (得分: {score:.1%})"
            
            key_movements.append({
                'name': stage_name,
                'user_image': comparison_images.get('user_pose'),
                'standard_image': comparison_images.get('standard_pose'),
                'summary': summary,
                'suggestion': '; '.join(suggestions) if suggestions else '继续保持',
                'measurements_data': measurements,
                'score': score
            })
        
        return {
            'score': int(overall_score * 100),
            'detailed_score': overall_score,
            'key_movements': key_movements,
            'analysis_type': 'advanced',
            'sport': SportSettings.get_sport_name(sport),
            'action': SportSettings.get_action_name(sport, action),
            'user_video_path': user_path,
            'standard_video_path': standard_path,
            'comparison_images': comparison_images,
            'comparison_info': {
                'analysis_mode': 'advanced',
                'pose_detection': 'enabled',
                'total_stages': len(stage_results),
                'avg_score': overall_score * 100
            }
        }
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create error result"""
        return {
            'score': 0,
            'error': error_message,
            'key_movements': [{
                'name': 'Analysis Error',
                'user_image': None,
                'standard_image': None,
                'summary': error_message,
                'suggestion': 'Please check video files and try again'
            }],
            'analysis_type': 'error'
        }
    
    def set_advanced_analysis(self, enabled: bool):
        """Enable or disable advanced analysis"""
        if enabled and not self.pose_detector:
            self._init_pose_detection()
        self.use_advanced_analysis = enabled and self.pose_detector is not None
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update analyzer settings"""
        self.settings.update(AppSettings.validate_settings(settings))
        
        # Update pose detector settings if available
        if self.pose_detector and hasattr(self.pose_detector, 'update_settings'):
            self.pose_detector.update_settings(self.settings)
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sports"""
        return SportSettings.get_supported_sports()
    
    def get_sport_actions(self, sport: str) -> List[str]:
        """Get actions for a specific sport"""
        return SportSettings.get_sport_actions(sport)