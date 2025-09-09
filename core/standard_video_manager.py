"""
standard_video_manager.py
Lists and manages standard movement videos for selected sport and action type.
"""
import os
from typing import List

class StandardVideoManager:
    def __init__(self, standard_videos_dir: str):
        self.standard_videos_dir = standard_videos_dir

    def list_videos(self, sport: str, action: str) -> List[str]:
        """
        Returns a list of standard video file paths for the given sport and action.
        """
        # TODO: Implement actual filtering logic
        # For now, return all videos in the directory
        if not os.path.exists(self.standard_videos_dir):
            return []
        return [os.path.join(self.standard_videos_dir, f)
                for f in os.listdir(self.standard_videos_dir)
                if f.lower().endswith(('.mp4', '.avi', '.mov'))]
