"""
I18n mixin for PyQt5 widgets to support internationalization.
国际化混入类，为PyQt5组件提供多语言支持
"""

from localization import I18nManager


class I18nMixin:
    """国际化混入类"""
    
    def __init__(self):
        # 注意：这个mixin应该在其他__init__之后调用
        self.i18n = I18nManager.instance()
        self.i18n.register_observer(self._on_language_changed)
    
    def tr(self, key: str, **kwargs) -> str:
        """
        翻译函数 - 覆盖PyQt5的默认tr方法
        
        Args:
            key: 翻译键
            **kwargs: 格式化参数
            
        Returns:
            str: 翻译后的文本
        """
        return self.i18n.t(key, **kwargs)
    
    def translate(self, key: str, **kwargs) -> str:
        """
        翻译函数的备用名称，避免与PyQt5的tr方法冲突
        
        Args:
            key: 翻译键
            **kwargs: 格式化参数
            
        Returns:
            str: 翻译后的文本
        """
        return self.i18n.t(key, **kwargs)
    
    def _on_language_changed(self):
        """
        语言变更回调函数
        子类应该重写此方法来更新UI文本
        """
        if hasattr(self, 'update_ui_texts'):
            self.update_ui_texts()
    
    def set_language(self, lang_code: str) -> bool:
        """
        设置语言
        
        Args:
            lang_code: 语言代码
            
        Returns:
            bool: 设置是否成功
        """
        return self.i18n.set_language(lang_code)
    
    def get_current_language(self) -> str:
        """获取当前语言代码"""
        return self.i18n.get_current_language()
    
    def get_supported_languages(self):
        """获取支持的语言列表"""
        return self.i18n.get_supported_languages()