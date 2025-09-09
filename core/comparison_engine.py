"""
comparison_engine.py
Dummy interface for action comparison and analysis logic.
"""
from typing import Dict

class ComparisonEngine:
    def __init__(self):
        pass

    def compare(self, user_video_path: str, standard_video_path: str) -> Dict:
        """
        Mock comparison function. Returns dummy results.
        """
        # TODO: Implement actual comparison algorithm
        return {
            'score': 87,
            'key_movements': [
                {
                    'name': 'Arm Swing',
                    'user_image': None,
                    'standard_image': None,
                    'summary': 'Your arm swing is slightly late.',
                    'suggestion': 'Start swing earlier for better power.'
                },
                {
                    'name': 'Footwork',
                    'user_image': None,
                    'standard_image': None,
                    'summary': 'Footwork is good, but stance is narrow.',
                    'suggestion': 'Widen stance for stability.'
                }
            ]
        }
