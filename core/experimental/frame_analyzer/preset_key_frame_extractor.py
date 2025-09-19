"""Preset (standard video) key frame extractor.

场景:
    标准演示视频的关键帧是事先人工标注 / 约定好的, 不需要再做智能/简单提取, 直接返回内置配置即可。

能力概览:
    1. O(1) 返回; 不读取视频内容。
    2. 支持按 (sport, action) 或 (sport, action, video_name) 精确注册。
       - video_name 为文件名(可含扩展名), 匹配大小写不敏感。
       - 若请求时提供 video_name 未命中, 会自动回退到通用 (sport, action) 预设 (若存在)。
    3. 同时支持 engine 使用的冗长阶段 key (setup_stage) 以及新 session 使用的精简 key (setup)。

默认内置:
    羽毛球 正手高远球 (Badminton / clear) 通用示例。

扩展示例::

    extractor = PresetKeyFrameExtractor()
    # 注册通用 (所有 clear 标准视频适用)
    extractor.register_preset('badminton','clear', {
        'setup_stage': 12, 'backswing_stage': 30, 'power_stage': 55,
        'setup': 12, 'backswing': 30, 'power': 55,
    })
    # 针对某个特定标准视频 demo_v2.mp4 提供更精细的帧
    extractor.register_preset('badminton','clear', {
        'setup_stage': 10, 'backswing_stage': 26, 'power_stage': 50,
        'setup': 10, 'backswing': 26, 'power': 50,
    }, video_name='demo_v2.mp4')
    frames = extractor.get_standard_frames('badminton','clear', video_name='demo_v2.mp4')
    # 若请求 demo_v3.mp4 (未注册), 则回退到通用配置。
"""
from __future__ import annotations
from typing import Dict, Tuple, Optional, Union
import os


class PresetKeyFrameExtractor:
    """Return preset key frames for a standard (reference) action video.

    兼容旧接口: 不传 video_name 时行为与原来一致。
    新特性: 可为同一 (sport, action) 配置多个标准视频版本。
    """

    def __init__(self, presets: Optional[Dict[Union[Tuple[str,str], Tuple[str,str,str]], Dict[str,int]]] = None):
        """初始化预置关键帧提取器。

        参数 presets 支持两种 key 形式:
        1. (sport, action)              -> 兼容旧结构, 作用于该动作下所有标准视频
        2. (sport, action, video_name)  -> 精确到某个标准视频文件名(不含路径, 可含扩展名)

        video_name 允许大小写不敏感匹配; 若调用时提供 video_name 未命中, 会回退到 (sport, action) 通用配置。
        """
        if presets is None:
            presets = self._default_presets()
        norm: Dict[Tuple[str,str,Optional[str]], Dict[str,int]] = {}
        for key, mapping in presets.items():
            if len(key) == 2:  # type: ignore[arg-type]
                s, a = key  # type: ignore[misc]
                norm[(s.lower(), a.lower(), None)] = mapping
            elif len(key) == 3:  # type: ignore[arg-type]
                s, a, v = key  # type: ignore[misc]
                norm[(s.lower(), a.lower(), (v.lower() if v else None))] = mapping
            else:
                raise ValueError("Preset key must be (sport, action) or (sport, action, video_name)")
        self._presets = norm

    # ------------------------------------------------------------------
    def _default_presets(self) -> Dict[Tuple[str,str], Dict[str,int]]:
        # 这些帧号来自当前测试 / demo 中使用的标准视频 (demo.mp4)
        return {
            ('badminton','clear'): {
                'setup_stage': 36,
                'backswing_stage': 57,
                'power_stage': 80,
                # 提供精简 key 以便新 session 直接复用（可选）
                'setup': 36,
                'backswing': 57,
                'power': 80,
            }
        }

    # ------------------------------------------------------------------
    def register_preset(self, sport: str, action: str, stage_frames: Dict[str,int], video_name: Optional[str] = None):
        """注册 / 覆盖一组预设帧。

        Args:
            sport: 运动
            action: 动作
            stage_frames: 阶段 -> 帧号
            video_name: (可选) 视频文件名(不含路径, 可含扩展名). 为空表示通用预设。
        """
        self._presets[(sport.lower(), action.lower(), (video_name.lower() if video_name else None))] = dict(stage_frames)

    def has_preset(self, sport: str, action: str, video_name: Optional[str] = None) -> bool:
        s, a = sport.lower(), action.lower()
        v = video_name.lower() if video_name else None
        return (s, a, v) in self._presets or (s, a, None) in self._presets

    def get_standard_frames(self, sport: str, action: str, video_name: Optional[str] = None) -> Dict[str,int]:
        """返回预设帧映射; 支持按视频名称细分。

        查找顺序:
            1. 精确 (sport, action, video_name.lower())
            2. 回退 (sport, action, None) 通用配置

        Raises:
            KeyError: 未找到任一匹配
        """
        s, a = sport.lower(), action.lower()
        if video_name:
            v = video_name.lower()
            exact_key = (s, a, v)
            if exact_key in self._presets:
                return dict(self._presets[exact_key])
        generic_key = (s, a, None)
        if generic_key in self._presets:
            return dict(self._presets[generic_key])
        raise KeyError(f"No preset key frames for sport={sport} action={action} video_name={video_name}")

    # 兼容旧接口名称（如果想在代码里用统一调用）
    def extract_stage_frames(self, video_path: str, sport: str, action: str, video_name: Optional[str] = None) -> Dict[str,int]:  # noqa: D401 - same semantics
        """与智能提取器保持同名接口, 但增加可选 video_name.

        video_name 为空时, 若提供 video_path 会尝试自动从文件名推断。
        """
        if not video_name and video_path:
            base = os.path.basename(video_path)
            if base:
                video_name = base
        return self.get_standard_frames(sport, action, video_name=video_name)


__all__ = ['PresetKeyFrameExtractor']
