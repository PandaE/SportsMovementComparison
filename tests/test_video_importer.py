"""
test_video_importer.py
Unit tests for VideoImporter.
"""
import unittest
from core.video_importer import VideoImporter

class TestVideoImporter(unittest.TestCase):
    def setUp(self):
        self.importer = VideoImporter()

    def test_validate_video_nonexistent(self):
        result = self.importer.validate_video('nonexistent.mp4')
        self.assertEqual(result, 'File does not exist.')

    def test_validate_video_wrong_format(self):
        result = self.importer.validate_video('video.txt')
        self.assertEqual(result, 'Unsupported video format.')

if __name__ == '__main__':
    unittest.main()
