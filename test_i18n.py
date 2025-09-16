"""
Test script for the new internationalization system.
新国际化系统的测试脚本
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.enhanced_main_window import EnhancedMainWindow
from ui.enhanced_settings_dialog import EnhancedSettingsDialog
from localization import I18nManager, tr, set_language


def test_i18n_system():
    """测试国际化系统"""
    print("🌍 测试国际化系统...")
    
    # 创建I18nManager实例
    i18n = I18nManager.instance()
    
    # 测试支持的语言
    langs = i18n.get_supported_languages()
    print(f"📋 支持的语言: {langs}")
    
    # 测试翻译功能
    print(f"🇨🇳 中文标题: {tr('ui.main_window.title')}")
    
    # 切换到英文
    set_language('en_US')
    print(f"🇺🇸 英文标题: {tr('ui.main_window.title')}")
    
    # 切换回中文
    set_language('zh_CN')
    print(f"🇨🇳 切换回中文: {tr('ui.main_window.title')}")
    
    # 测试带参数的翻译
    score_text = tr('analysis.results.score', score=85.5)
    print(f"📊 带参数翻译: {score_text}")
    
    print("✅ 国际化系统测试完成")


def test_enhanced_main_window():
    """测试增强的主窗口"""
    print("\n🖥️  测试增强主窗口...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = EnhancedMainWindow()
    window.show()
    
    print("✅ 增强主窗口创建成功")
    print("🔧 可以在界面中测试语言切换功能")
    
    # 运行应用
    sys.exit(app.exec_())


def test_settings_dialog():
    """测试设置对话框"""
    print("\n⚙️  测试设置对话框...")
    
    app = QApplication(sys.argv)
    
    # 创建设置对话框
    dialog = EnhancedSettingsDialog()
    dialog.show()
    
    print("✅ 设置对话框创建成功")
    print("🔧 可以在对话框中测试语言切换功能")
    
    # 运行应用
    sys.exit(app.exec_())


def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'i18n':
            test_i18n_system()
        elif sys.argv[1] == 'settings':
            test_settings_dialog()
        elif sys.argv[1] == 'main':
            test_enhanced_main_window()
        else:
            print("❌ 未知测试选项")
            print("📖 用法:")
            print("  python test_i18n.py i18n      # 测试国际化系统")
            print("  python test_i18n.py settings  # 测试设置对话框")
            print("  python test_i18n.py main      # 测试主窗口")
    else:
        print("🎯 运行所有测试...")
        test_i18n_system()
        
        print("\n📝 接下来您可以运行:")
        print("  python test_i18n.py main      # 测试主窗口")
        print("  python test_i18n.py settings  # 测试设置对话框")


if __name__ == '__main__':
    main()