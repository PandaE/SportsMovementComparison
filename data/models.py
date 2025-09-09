"""
models.py
Data models for video info, comparison results, and key movements.
"""
from typing import List, Optional

class VideoInfo:
    def __init__(self, path: str, duration: float, sport: str, action: str):
        self.path = path
        self.duration = duration
        self.sport = sport
        self.action = action

class KeyMovement:
    def __init__(self, name: str, user_image: Optional[str], standard_image: Optional[str], summary: str, suggestion: str):
        self.name = name
        self.user_image = user_image
        self.standard_image = standard_image
        self.summary = summary
        self.suggestion = suggestion

class ComparisonResult:
    def __init__(self, score: int, key_movements: List[KeyMovement]):
        self.score = score
        self.key_movements = key_movements
