"""
Key frame extraction for sports movement analysis.
Automatically extracts important frames based on sport and action type.
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from ...video_frame_extractor import VideoFrameExtractor
from .pose_extractor import PoseExtractor


class MotionAnalyzer:
    """运动分析器 - 分析人体运动的运动学特征"""
    
    def __init__(self, pose_extractor: PoseExtractor):
        self.pose_extractor = pose_extractor
    
    def analyze_video_motion(self, video_path: str, sample_rate: int = 3) -> Dict:
        """
        分析视频中的运动特征
        
        Args:
            video_path: 视频路径
            sample_rate: 采样率，每几帧采样一次
            
        Returns:
            包含运动分析数据的字典
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 存储分析数据
        motion_data = {
            'frame_numbers': [],
            'center_of_mass_x': [],  # 重心X坐标
            'center_of_mass_y': [],  # 重心Y坐标
            'right_arm_angle': [],   # 右臂角度（肩-肘-腕）
            'right_forearm_angle': [], # 右前臂相对角度
            'pose_confidence': []    # 姿态检测置信度
        }
        
        try:
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按采样率处理
                if frame_idx % sample_rate == 0:
                    # 提取姿态
                    pose = self.pose_extractor.extract_pose_from_image(frame, frame_idx)
                    
                    if pose:
                        # 计算重心位置
                        com_x, com_y = self._calculate_center_of_mass(pose)
                        
                        # 计算手臂角度
                        arm_angle = self._calculate_arm_angle(pose)
                        forearm_angle = self._calculate_forearm_relative_angle(pose)
                        
                        # 计算平均置信度
                        confidence = self._calculate_average_confidence(pose)
                        
                        # 存储数据
                        motion_data['frame_numbers'].append(frame_idx)
                        motion_data['center_of_mass_x'].append(com_x)
                        motion_data['center_of_mass_y'].append(com_y)
                        motion_data['right_arm_angle'].append(arm_angle)
                        motion_data['right_forearm_angle'].append(forearm_angle)
                        motion_data['pose_confidence'].append(confidence)
                
                frame_idx += 1
                
                # 显示进度
                if frame_idx % 30 == 0:
                    progress = frame_idx / total_frames * 100
                    print(f"   分析进度: {progress:.1f}% ({frame_idx}/{total_frames})")
        
        finally:
            cap.release()
        
        # 计算运动速度（角速度等）
        motion_data = self._calculate_motion_velocities(motion_data, fps, sample_rate)
        
        return motion_data
    
    def _calculate_center_of_mass(self, pose) -> Tuple[float, float]:
        """计算重心位置（基于主要身体关键点）"""
        key_points = []
        weights = []
        
        # 主要身体部位及其权重
        body_parts = [
            (pose.nose, 0.1),
            (pose.left_shoulder, 0.15), (pose.right_shoulder, 0.15),
            (pose.left_hip, 0.2), (pose.right_hip, 0.2),
            (pose.left_knee, 0.1), (pose.right_knee, 0.1)
        ]
        
        for point, weight in body_parts:
            if point and hasattr(point, 'x') and hasattr(point, 'y'):
                key_points.append((point.x, point.y))
                weights.append(weight)
        
        if not key_points:
            return 0.0, 0.0
        
        # 加权平均
        total_weight = sum(weights)
        weighted_x = sum(p[0] * w for p, w in zip(key_points, weights)) / total_weight
        weighted_y = sum(p[1] * w for p, w in zip(key_points, weights)) / total_weight
        
        return weighted_x, weighted_y
    
    def _calculate_arm_angle(self, pose) -> float:
        """计算右臂角度（肩-肘-腕）"""
        if not (pose.right_shoulder and pose.right_elbow and pose.right_wrist):
            return 0.0
        
        # 计算向量
        v1 = np.array([pose.right_shoulder.x - pose.right_elbow.x, 
                      pose.right_shoulder.y - pose.right_elbow.y])
        v2 = np.array([pose.right_wrist.x - pose.right_elbow.x, 
                      pose.right_wrist.y - pose.right_elbow.y])
        
        # 计算角度
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        return angle
    
    def _calculate_forearm_relative_angle(self, pose) -> float:
        """计算前臂相对于垂直方向的角度"""
        if not (pose.right_elbow and pose.right_wrist):
            return 0.0
        
        # 前臂向量
        forearm_vector = np.array([pose.right_wrist.x - pose.right_elbow.x,
                                 pose.right_wrist.y - pose.right_elbow.y])
        
        # 垂直向量（向下）
        vertical_vector = np.array([0, 1])
        
        # 计算角度
        cos_angle = np.dot(forearm_vector, vertical_vector) / np.linalg.norm(forearm_vector)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        return angle
    
    def _calculate_average_confidence(self, pose) -> float:
        """计算姿态检测的平均置信度"""
        key_points = [
            pose.right_shoulder, pose.right_elbow, pose.right_wrist,
            pose.left_shoulder, pose.left_hip, pose.right_hip
        ]
        
        confidences = []
        for point in key_points:
            if point and hasattr(point, 'confidence'):
                confidences.append(point.confidence)
        
        return np.mean(confidences) if confidences else 0.0
    
    def _calculate_motion_velocities(self, motion_data: Dict, fps: float, sample_rate: int) -> Dict:
        """计算运动速度和角速度"""
        frame_numbers = motion_data['frame_numbers']
        
        if len(frame_numbers) < 2:
            motion_data['com_velocity_x'] = [0.0]
            motion_data['com_velocity_y'] = [0.0]
            motion_data['arm_angular_velocity'] = [0.0]
            motion_data['forearm_angular_velocity'] = [0.0]
            return motion_data
        
        # 计算时间间隔
        dt = sample_rate / fps
        
        # 计算重心速度
        com_vel_x = np.gradient(motion_data['center_of_mass_x']) / dt
        com_vel_y = np.gradient(motion_data['center_of_mass_y']) / dt
        
        # 计算角速度
        arm_angular_vel = np.gradient(motion_data['right_arm_angle']) / dt
        forearm_angular_vel = np.gradient(motion_data['right_forearm_angle']) / dt
        
        motion_data['com_velocity_x'] = com_vel_x.tolist()
        motion_data['com_velocity_y'] = com_vel_y.tolist()
        motion_data['arm_angular_velocity'] = arm_angular_vel.tolist()
        motion_data['forearm_angular_velocity'] = forearm_angular_vel.tolist()
        
        return motion_data


class KeyFrameExtractor:
    """关键帧提取器 - 根据运动类型自动提取关键帧"""
    
    def __init__(self, use_intelligent_extraction: bool = True):
        """
        初始化关键帧提取器
        
        Args:
            use_intelligent_extraction: 是否使用智能提取（基于运动学特征）
        """
        self.frame_extractor = VideoFrameExtractor()
        self.use_intelligent_extraction = use_intelligent_extraction
        
        if self.use_intelligent_extraction:
            try:
                self.pose_extractor = PoseExtractor(backend="mediapipe")
                self.motion_analyzer = MotionAnalyzer(self.pose_extractor)
                print("🧠 智能关键帧提取器初始化成功")
            except Exception as e:
                print(f"⚠️ 智能提取器初始化失败，回退到时间等分模式: {e}")
                self.use_intelligent_extraction = False
    
    def extract_stage_frames(self, video_path: str, sport: str, action: str) -> Dict[str, int]:
        """
        根据运动和动作类型提取关键帧位置
        
        Args:
            video_path: 视频文件路径
            sport: 运动类型 (如 "badminton")
            action: 动作类型 (如 "clear", "正手高远球")
            
        Returns:
            Dict[stage_name, frame_number] - 阶段名称到帧号的映射
        """
        if sport.lower() == "badminton" and ("clear" in action.lower() or "正手高远" in action):
            if self.use_intelligent_extraction:
                return self._extract_badminton_clear_frames_intelligent(video_path)
            else:
                return self._extract_badminton_clear_frames_simple(video_path)
        else:
            raise ValueError(f"不支持的运动动作组合: {sport} - {action}")
    
    def _extract_badminton_clear_frames_intelligent(self, video_path: str) -> Dict[str, int]:
        """
        基于运动学特征的羽毛球正手高远球关键帧提取
        
        提取策略：
        - 架拍阶段结束: 重心最靠后的帧
        - 引拍阶段结束: 两个阶段之间小臂角速度最低点  
        - 发力阶段结束: 大臂或小臂角速度最高点
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[stage_name, frame_number] - 阶段到帧号的映射
        """
        print(f"🧠 开始智能分析羽毛球正手高远球关键帧...")
        
        try:
            # 1. 分析视频运动特征
            motion_data = self.motion_analyzer.analyze_video_motion(video_path, sample_rate=2)
            
            if len(motion_data['frame_numbers']) < 10:
                print("⚠️ 运动数据不足，回退到简单模式")
                return self._extract_badminton_clear_frames_simple(video_path)
            
            # 2. 找到关键帧
            key_frames = self._find_badminton_key_frames(motion_data)
            
            print(f"✅ 智能关键帧提取完成:")
            for stage_name, frame_number in key_frames.items():
                print(f"   {stage_name}: 第 {frame_number} 帧")
            
            return key_frames
            
        except Exception as e:
            print(f"❌ 智能提取失败: {e}")
            print("   回退到简单时间等分模式")
            return self._extract_badminton_clear_frames_simple(video_path)
    
    def _find_badminton_key_frames(self, motion_data: Dict) -> Dict[str, int]:
        """
        基于运动数据找到羽毛球关键帧
        
        Args:
            motion_data: 运动分析数据
            
        Returns:
            关键帧字典
        """
        frame_numbers = motion_data['frame_numbers']
        com_x = motion_data['center_of_mass_x']
        arm_angular_vel = motion_data['arm_angular_velocity']
        forearm_angular_vel = motion_data['forearm_angular_velocity']
        
        # 1. 架拍阶段结束：重心最靠后的帧
        # 找到重心X坐标最小值（最靠左/后）
        setup_idx = np.argmin(com_x)
        setup_frame = frame_numbers[setup_idx]
        
        # 2. 发力阶段结束：大臂或小臂角速度最高点
        # 计算综合角速度（大臂和小臂的绝对值之和）
        combined_angular_vel = [abs(a) + abs(f) for a, f in zip(arm_angular_vel, forearm_angular_vel)]
        power_idx = np.argmax(combined_angular_vel)
        power_frame = frame_numbers[power_idx]
        
        # 3. 引拍阶段结束：架拍和发力之间小臂角速度最低点
        # 确定搜索范围
        start_idx = min(setup_idx, power_idx)
        end_idx = max(setup_idx, power_idx)
        
        if start_idx == end_idx:
            # 如果两点重合，扩大搜索范围
            mid_idx = len(frame_numbers) // 2
            start_idx = max(0, mid_idx - 5)
            end_idx = min(len(frame_numbers) - 1, mid_idx + 5)
        
        # 在范围内找到小臂角速度最低点
        search_range = range(start_idx, end_idx + 1)
        forearm_vel_in_range = [abs(forearm_angular_vel[i]) for i in search_range]
        
        if forearm_vel_in_range:
            min_vel_idx = np.argmin(forearm_vel_in_range)
            backswing_idx = start_idx + min_vel_idx
            backswing_frame = frame_numbers[backswing_idx]
        else:
            # 备选方案：取中间帧
            backswing_frame = frame_numbers[len(frame_numbers) // 2]
        
        # 验证帧的时间顺序，确保合理性
        frames = [setup_frame, backswing_frame, power_frame]
        frames.sort()
        
        key_frames = {
            "架拍阶段结束": frames[0],
            "引拍阶段结束": frames[1], 
            "发力阶段结束": frames[2]
        }
        
        # 调试信息
        print(f"   🎯 分析结果:")
        print(f"     重心最靠后: 第 {setup_frame} 帧 (重心X: {com_x[setup_idx]:.1f})")
        print(f"     角速度最高: 第 {power_frame} 帧 (角速度: {combined_angular_vel[power_idx]:.1f})")
        print(f"     小臂角速度最低: 第 {backswing_frame} 帧")
        
        return key_frames
    
    def extract_stage_images(self, video_path: str, sport: str, action: str) -> Dict[str, np.ndarray]:
        """
        提取关键帧图像
        
        Args:
            video_path: 视频文件路径
            sport: 运动类型
            action: 动作类型
            
        Returns:
            Dict[stage_name, image] - 阶段名称到图像的映射
        """
        # 1. 获取关键帧位置
        frame_positions = self.extract_stage_frames(video_path, sport, action)
        
        # 2. 提取对应的图像
        stage_images = {}
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        try:
            for stage_name, frame_number in frame_positions.items():
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    stage_images[stage_name] = frame
                    print(f"✅ 提取 {stage_name} 关键帧: 第 {frame_number} 帧")
                else:
                    print(f"❌ 无法提取 {stage_name} 关键帧: 第 {frame_number} 帧")
        
        finally:
            cap.release()
        
        return stage_images
    
    def _extract_badminton_clear_frames_simple(self, video_path: str) -> Dict[str, int]:
        """
        羽毛球正手高远球关键帧提取（简单时间等分方法）
        
        使用简单的时间等分策略：
        - 架拍阶段结束: 30% 位置
        - 引拍阶段结束: 50% 位置  
        - 发力阶段结束: 80% 位置
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[stage_name, frame_number] - 阶段到帧号的映射
        """
        # 获取视频信息
        video_info = self.frame_extractor.get_video_info(video_path)
        total_frames = video_info.get('total_frames', 0)
        
        if total_frames == 0:
            raise ValueError(f"无法获取视频帧数: {video_path}")
        
        # 定义各阶段的时间比例
        stage_ratios = {
            "架拍阶段结束": 0.30,  # 30% 位置
            "引拍阶段结束": 0.50,  # 50% 位置
            "发力阶段结束": 0.80   # 80% 位置
        }
        
        # 计算各阶段的帧位置
        stage_frames = {}
        for stage_name, ratio in stage_ratios.items():
            frame_number = int(total_frames * ratio)
            # 确保帧号在有效范围内
            frame_number = max(0, min(frame_number, total_frames - 1))
            stage_frames[stage_name] = frame_number
        
        print(f"📐 羽毛球正手高远球关键帧提取完成 (简单模式):")
        print(f"   总帧数: {total_frames}")
        for stage_name, frame_number in stage_frames.items():
            ratio = frame_number / total_frames * 100
            print(f"   {stage_name}: 第 {frame_number} 帧 ({ratio:.1f}%)")
        
        return stage_frames
    
    def validate_extracted_frames(self, video_path: str, stage_frames: Dict[str, int]) -> Dict[str, bool]:
        """
        验证提取的关键帧质量
        
        Args:
            video_path: 视频文件路径
            stage_frames: 阶段帧位置映射
            
        Returns:
            Dict[stage_name, is_valid] - 各阶段帧的有效性
        """
        validation_results = {}
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return {stage: False for stage in stage_frames.keys()}
        
        try:
            for stage_name, frame_number in stage_frames.items():
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # 简单的质量检验
                    is_valid = self._validate_frame_quality(frame)
                    validation_results[stage_name] = is_valid
                    
                    status = "✅ 有效" if is_valid else "⚠️ 质量问题"
                    print(f"   {stage_name}: {status}")
                else:
                    validation_results[stage_name] = False
                    print(f"   {stage_name}: ❌ 无法读取")
        
        finally:
            cap.release()
        
        return validation_results
    
    def _validate_frame_quality(self, frame: np.ndarray) -> bool:
        """
        简单的帧质量验证
        
        Args:
            frame: 输入帧
            
        Returns:
            bool - 是否为有效帧
        """
        if frame is None or frame.size == 0:
            return False
        
        # 检查图像是否太暗或太亮
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        # 亮度范围检查 (0-255)
        if mean_brightness < 20 or mean_brightness > 240:
            return False
        
        # 检查图像是否太模糊 (使用拉普拉斯算子)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 清晰度阈值
        if laplacian_var < 50:  # 经验值，可调整
            return False
        
        return True
    
    def get_supported_sports(self) -> List[Tuple[str, str]]:
        """
        获取支持的运动项目列表
        
        Returns:
            List[Tuple[sport, action]] - 支持的运动动作组合
        """
        return [
            ("Badminton", "正手高远球"),
            ("badminton", "clear"),
            ("badminton", "forehand_clear")
        ]
    
    def get_default_stage_ratios(self, sport: str, action: str) -> Dict[str, float]:
        """
        获取默认的阶段时间比例（仅用于简单模式）
        
        Args:
            sport: 运动类型
            action: 动作类型
            
        Returns:
            Dict[stage_name, ratio] - 阶段名称到时间比例的映射
        """
        if sport.lower() == "badminton" and ("clear" in action.lower() or "正手高远" in action):
            return {
                "架拍阶段结束": 0.30,
                "引拍阶段结束": 0.50,
                "发力阶段结束": 0.80
            }
        else:
            raise ValueError(f"不支持的运动动作组合: {sport} - {action}")
    
    def set_extraction_mode(self, use_intelligent: bool):
        """
        设置提取模式
        
        Args:
            use_intelligent: True为智能模式，False为简单模式
        """
        if use_intelligent and not hasattr(self, 'motion_analyzer'):
            try:
                self.pose_extractor = PoseExtractor(backend="mediapipe")
                self.motion_analyzer = MotionAnalyzer(self.pose_extractor)
                self.use_intelligent_extraction = True
                print("🧠 切换到智能提取模式")
            except Exception as e:
                print(f"⚠️ 无法切换到智能模式: {e}")
                self.use_intelligent_extraction = False
        else:
            self.use_intelligent_extraction = use_intelligent
            mode_name = "智能模式" if use_intelligent else "简单模式"
            print(f"📐 切换到{mode_name}")
    
    def get_extraction_mode(self) -> str:
        """
        获取当前提取模式
        
        Returns:
            模式描述字符串
        """
        return "智能提取模式" if self.use_intelligent_extraction else "简单时间等分模式"