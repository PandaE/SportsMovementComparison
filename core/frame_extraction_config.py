# 预配置关键帧与阶段数量配置
# 可以后续扩展为从外部 JSON / 数据库存储加载
from typing import Dict, List, Any

# 约定：关键帧信息结构 { 'frame': int, 'label': str | None }

PRECONFIG_KEYFRAMES: Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]] = {
    # sport -> action -> video_basename -> list of keyframe dicts
    'badminton': {
        'clear': {
            # 示例：标准视频文件名（不含路径）与关键帧（帧号示例值）
            'right1.mp4': [
                {'frame': 88, 'label': '架拍'},
                {'frame': 104, 'label': '引拍'},
                {'frame': 113, 'label': '击球'},
            ],
        }
    }
}

# 阶段数量配置（用于均分帧提取器），sport -> action -> stage_count
STAGE_COUNT_CONFIG: Dict[str, Dict[str, int]] = {
    'badminton': {
        'clear': 3  # 架拍 / 引拍 / 击球
    }
}


def get_preconfig_keyframes(sport: str, action: str, video_basename: str):
    sport_map = PRECONFIG_KEYFRAMES.get(sport.lower()) or {}
    action_map = sport_map.get(action.lower()) or {}
    frames = action_map.get(video_basename) or []
    return frames.copy()


def get_stage_count(sport: str, action: str, default: int = 4) -> int:
    return STAGE_COUNT_CONFIG.get(sport.lower(), {}).get(action.lower(), default)

__all__ = [
    'get_preconfig_keyframes',
    'get_stage_count',
    'PRECONFIG_KEYFRAMES',
    'STAGE_COUNT_CONFIG'
]
