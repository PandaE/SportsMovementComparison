#!/usr/bin/env python3
"""测试视频导入功能"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.enhanced_main_window import EnhancedMainWindow

def test_video_import():
    app = QApplication(sys.argv)
    window = EnhancedMainWindow()
    
    print("=== 测试视频导入功能 ===")
    print(f"用户视频路径初始值: {repr(window.user_video_path)}")
    print(f"标准视频路径初始值: {repr(window.standard_video_path)}")
    print(f"对比按钮初始状态: {window.compare_btn.isEnabled()}")
    
    # 手动调用导入方法
    print("\n=== 模拟点击用户视频导入按钮 ===")
    window.import_user_video()
    
    print(f"用户视频路径: {repr(window.user_video_path)}")
    print(f"对比按钮状态: {window.compare_btn.isEnabled()}")
    
    print("\n=== 模拟点击标准视频导入按钮 ===")
    window.import_standard_video()
    
    print(f"标准视频路径: {repr(window.standard_video_path)}")
    print(f"对比按钮状态: {window.compare_btn.isEnabled()}")

if __name__ == "__main__":
    test_video_import()