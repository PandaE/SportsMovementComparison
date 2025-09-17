"""
Enhanced Dialogs - 增强版对话框
File selection and error dialogs with full internationalization support
"""
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QWidget

from localization.i18n_manager import I18nManager
from localization.translation_keys import TK


class EnhancedDialogs:
    """增强版对话框类 - 支持国际化"""
    
    @staticmethod
    def select_video(parent: QWidget, title_key: str = None) -> str:
        """选择视频文件对话框"""
        i18n_manager = I18nManager()
        
        # 使用提供的键或默认键
        if title_key:
            title = i18n_manager.t(title_key)
        else:
            title = i18n_manager.t(TK.UI.Dialogs.SELECT_VIDEO)
        
        file_filter = i18n_manager.t(TK.UI.Dialogs.VIDEO_FILES)
        
        file_path, _ = QFileDialog.getOpenFileName(parent, title, '', file_filter)
        return file_path

    @staticmethod
    def show_error(parent: QWidget, message: str, title_key: str = None):
        """显示错误对话框"""
        i18n_manager = I18nManager()
        
        # 使用提供的键或默认键
        if title_key:
            title = i18n_manager.t(title_key)
        else:
            title = i18n_manager.t(TK.UI.Dialogs.ERROR)
        
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_info(parent: QWidget, message: str, title_key: str = None):
        """显示信息对话框"""
        i18n_manager = I18nManager()
        
        # 使用提供的键或默认键
        if title_key:
            title = i18n_manager.t(title_key)
        else:
            title = i18n_manager.t(TK.UI.Dialogs.INFO)
        
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_warning(parent: QWidget, message: str, title_key: str = None):
        """显示警告对话框"""
        i18n_manager = I18nManager()
        
        # 使用提供的键或默认键
        if title_key:
            title = i18n_manager.t(title_key)
        else:
            title = i18n_manager.t(TK.UI.Dialogs.WARNING)
        
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def ask_question(parent: QWidget, message: str, title_key: str = None) -> bool:
        """询问确认对话框"""
        i18n_manager = I18nManager()
        
        # 使用提供的键或默认键
        if title_key:
            title = i18n_manager.t(title_key)
        else:
            title = i18n_manager.t(TK.UI.Dialogs.QUESTION)
        
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes


# 向后兼容的静态方法
class Dialogs:
    """旧版对话框类 - 保持向后兼容"""
    
    @staticmethod
    def select_video(parent: QWidget, title: str) -> str:
        """向后兼容的视频选择方法"""
        # 直接使用传入的标题，不进行翻译
        file_path, _ = QFileDialog.getOpenFileName(parent, title, '', 'Video Files (*.mp4 *.avi *.mov)')
        return file_path

    @staticmethod
    def show_error(parent: QWidget, message: str):
        """向后兼容的错误显示方法"""
        QMessageBox.critical(parent, 'Error', message)