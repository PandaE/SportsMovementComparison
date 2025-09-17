"""
Test script for core modules import and basic functionality
核心模块导入和基本功能测试脚本
"""

import sys
import os

# Add refactored directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有核心模块的导入"""
    print("🔍 Testing core module imports...")
    
    try:
        # Test config modules
        print("  📁 Testing config modules...")
        from config.settings import AppSettings, SportSettings
        from config.sports_config import get_sport_config, get_badminton_forehand_clear
        print("  ✅ Config modules imported successfully")
        
        # Test core modules
        print("  🔧 Testing core modules...")
        from core.analyzer import MovementAnalyzer
        from core.video_processor import VideoProcessor  
        from core.pose_detector import PoseDetector
        print("  ✅ Core modules imported successfully")
        
        # Test localization
        print("  🌐 Testing localization modules...")
        from localization.i18n_manager import I18nManager
        from localization.translation_keys import TK
        print("  ✅ Localization modules imported successfully")
        
        # Test UI modules (without running GUI)
        print("  🖼️ Testing UI modules...")
        # Only test imports, don't create instances
        from ui.main_window import MainWindow
        from ui.video_player import VideoPlayer
        from ui.result_window import ResultWindow
        print("  ✅ UI modules imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\\n🧪 Testing basic functionality...")
    
    try:
        # Re-import modules for local scope
        from config.settings import AppSettings, SportSettings
        from config.sports_config import get_badminton_forehand_clear
        from localization.i18n_manager import I18nManager
        from core.analyzer import MovementAnalyzer
        from core.video_processor import VideoProcessor  
        from core.pose_detector import PoseDetector
        
        # Test AppSettings
        print("  ⚙️ Testing AppSettings...")
        settings = AppSettings()
        default_settings = AppSettings.get_default_settings()
        print(f"    Default language: {default_settings.get('language', 'zh_CN')}")
        print("  ✅ AppSettings working")
        
        # Test SportSettings
        print("  🏸 Testing SportSettings...")
        sports = SportSettings.get_supported_sports()
        print(f"    Supported sports: {sports}")
        actions = SportSettings.get_sport_actions('badminton')
        print(f"    Badminton actions: {actions}")
        print("  ✅ SportSettings working")
        
        # Test sports config
        print("  📋 Testing sports config...")
        config = get_badminton_forehand_clear()
        print(f"    Config name: {config.name}")
        print(f"    Number of stages: {len(config.stages)}")
        print("  ✅ Sports config working")
        
        # Test I18nManager
        print("  🌍 Testing I18nManager...")
        i18n = I18nManager.instance()
        current_lang = i18n.get_current_language()
        print(f"    Current language: {current_lang}")
        
        # Test translation
        test_key = "ui.main_window.title"
        translated = i18n.t(test_key)
        print(f"    Translation test: '{test_key}' -> '{translated}'")
        print("  ✅ I18nManager working")
        
        # Test VideoProcessor
        print("  🎥 Testing VideoProcessor...")
        processor = VideoProcessor()
        print(f"    VideoProcessor initialized: {processor is not None}")
        print("  ✅ VideoProcessor working")
        
        # Test PoseDetector
        print("  🤸 Testing PoseDetector...")
        detector = PoseDetector()
        print(f"    Backend: {detector.backend}")
        print(f"    Detector initialized: {detector.detector is not None}")
        print("  ✅ PoseDetector working")
        
        # Test MovementAnalyzer
        print("  🔬 Testing MovementAnalyzer...")
        analyzer = MovementAnalyzer()
        print(f"    Analyzer initialized: {analyzer is not None}")
        print("  ✅ MovementAnalyzer working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Functionality test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 Starting core modules test...")
    print("=" * 50)
    
    # Test imports
    import_success = test_imports()
    
    if import_success:
        # Test basic functionality
        func_success = test_basic_functionality()
        
        print("\\n" + "=" * 50)
        if import_success and func_success:
            print("🎉 All tests passed! Core modules are working correctly.")
            return 0
        else:
            print("❌ Some tests failed. Please check the error messages above.")
            return 1
    else:
        print("\\n" + "=" * 50)
        print("❌ Import tests failed. Cannot proceed with functionality tests.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)