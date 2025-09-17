"""
Application Settings and Configuration
应用程序设置和配置

Centralized configuration management for the Sports Movement Comparator.
"""

import os
from pathlib import Path
from typing import Dict, Any, List


class AppSettings:
    """Application settings manager"""
    
    # Application Info
    APP_NAME = "Sports Movement Comparator"
    APP_VERSION = "2.0.0"
    
    # Window Settings
    WINDOW_TITLE = "运动动作对比分析系统"
    WINDOW_MIN_WIDTH = 1200
    WINDOW_MIN_HEIGHT = 800
    
    # Video Settings
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']
    MAX_VIDEO_DURATION = 30  # seconds
    VIDEO_QUALITY_THRESHOLD = 0.5
    
    # Analysis Settings
    DEFAULT_ANGLE_TOLERANCE = 10.0  # degrees
    DEFAULT_DISTANCE_TOLERANCE = 0.1  # normalized
    POSE_CONFIDENCE_THRESHOLD = 0.5
    
    # UI Settings
    VIDEO_PLAYER_SIZE = (400, 300)
    RESULT_IMAGE_SIZE = (200, 150)
    
    # File Paths
    @staticmethod
    def get_app_dir() -> Path:
        """Get application directory"""
        return Path(__file__).parent.parent
    
    @staticmethod
    def get_assets_dir() -> Path:
        """Get assets directory"""
        return AppSettings.get_app_dir() / "assets"
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get config directory"""
        return AppSettings.get_app_dir() / "config"
    
    # Default Settings
    DEFAULT_SETTINGS = {
        'language': 'zh_CN',
        'experimental_enabled': True,
        'pose_backend': 'mediapipe',
        'angle_tolerance': DEFAULT_ANGLE_TOLERANCE,
        'save_analysis_images': True,
        'video_quality_check': True,
    }
    
    @classmethod
    def get_default_settings(cls) -> Dict[str, Any]:
        """Get default application settings"""
        return cls.DEFAULT_SETTINGS.copy()
    
    @classmethod
    def validate_settings(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize settings"""
        validated = cls.get_default_settings()
        
        for key, value in settings.items():
            if key in validated:
                # Type validation
                if key == 'language' and isinstance(value, str):
                    validated[key] = value
                elif key == 'experimental_enabled' and isinstance(value, bool):
                    validated[key] = value
                elif key == 'pose_backend' and value in ['mediapipe', 'opencv']:
                    validated[key] = value
                elif key == 'angle_tolerance' and isinstance(value, (int, float)):
                    validated[key] = max(1.0, min(30.0, float(value)))
                elif key in ['save_analysis_images', 'video_quality_check'] and isinstance(value, bool):
                    validated[key] = value
        
        return validated


class SportSettings:
    """Sport-specific settings"""
    
    # Supported Sports and Actions
    SUPPORTED_SPORTS = {
        'badminton': {
            'name': '羽毛球',
            'actions': {
                'clear': '正手高远球',
                'smash': '扣杀',
                'drop': '网前球'
            }
        }
    }
    
    @classmethod
    def get_supported_sports(cls) -> List[str]:
        """Get list of supported sports"""
        return list(cls.SUPPORTED_SPORTS.keys())
    
    @classmethod
    def get_sport_actions(cls, sport: str) -> List[str]:
        """Get actions for a specific sport"""
        if sport in cls.SUPPORTED_SPORTS:
            return list(cls.SUPPORTED_SPORTS[sport]['actions'].keys())
        return []
    
    @classmethod
    def get_sport_name(cls, sport: str, language: str = 'zh_CN') -> str:
        """Get display name for sport"""
        if sport in cls.SUPPORTED_SPORTS:
            if language.startswith('zh'):
                return cls.SUPPORTED_SPORTS[sport]['name']
            else:
                return sport.title()
        return sport
    
    @classmethod
    def get_action_name(cls, sport: str, action: str, language: str = 'zh_CN') -> str:
        """Get display name for action"""
        if sport in cls.SUPPORTED_SPORTS and action in cls.SUPPORTED_SPORTS[sport]['actions']:
            if language.startswith('zh'):
                return cls.SUPPORTED_SPORTS[sport]['actions'][action]
            else:
                return action.replace('_', ' ').title()
        return action


# Environment Detection
def get_system_info() -> Dict[str, Any]:
    """Get system information for diagnostics"""
    info = {
        'platform': os.name,
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
    }
    
    # Check for required libraries
    try:
        import cv2
        info['opencv_version'] = cv2.__version__
    except ImportError:
        info['opencv_version'] = 'Not installed'
    
    try:
        import mediapipe
        info['mediapipe_version'] = mediapipe.__version__
    except ImportError:
        info['mediapipe_version'] = 'Not installed'
    
    try:
        from PyQt5.QtCore import QT_VERSION_STR
        info['pyqt5_version'] = QT_VERSION_STR
    except ImportError:
        info['pyqt5_version'] = 'Not installed'
    
    return info