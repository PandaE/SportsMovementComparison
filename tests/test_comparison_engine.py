"""
test_comparison_engine.py
Unit tests for ComparisonEngine.
"""
import unittest
from core.comparison_engine import ComparisonEngine

class TestComparisonEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ComparisonEngine()

    def test_compare_returns_result(self):
        result = self.engine.compare('user.mp4', 'standard.mp4')
        self.assertIn('score', result)
        self.assertIn('key_movements', result)

if __name__ == '__main__':
    unittest.main()
