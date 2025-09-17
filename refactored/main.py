"""
Sports Movement Comparator - Refactored Version
运动动作对比分析系统 - 重构版本

A simplified desktop application for comparing user sports movements 
with standard reference videos.

Main entry point of the application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from localization.manager import I18nManager


def main():
    """
    Application entry point.
    应用程序入口点
    """
    try:
        # Create Qt Application
        app = QApplication(sys.argv)
        app.setApplicationName("Sports Movement Comparator")
        app.setApplicationVersion("2.0.0")
        
        # Initialize internationalization
        i18n = I18nManager.instance()
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()