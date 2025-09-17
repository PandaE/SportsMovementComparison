"""
Internationalization Manager for multi-language support.
国际化管理器，支持多语言切换和文本翻译
"""

import json
import os
import logging
from typing import Dict, List, Callable, Any, Optional
from pathlib import Path


class I18nManager:
    """国际化管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.current_language = 'zh_CN'  # 默认简体中文
        self.translations: Dict[str, Dict] = {}
        self.observers: List[Callable[[], None]] = []
        self.fallback_language = 'en_US'  # 回退语言
        
        # 获取localization目录路径
        self.localization_dir = Path(__file__).parent
        self.languages_dir = self.localization_dir / 'languages'
        
        # 支持的语言列表
        self.supported_languages = {
            'zh_CN': '简体中文',
            'en_US': 'English'
        }
        
        # 初始化日志
        self.logger = logging.getLogger(__name__)
        
        # 加载所有语言文件
        self._load_all_languages()
        
        # 自动检测系统语言
        self._detect_system_language()
        
        self._initialized = True
    
    @classmethod
    def instance(cls) -> 'I18nManager':
        """获取单例实例"""
        return cls()
    
    def _load_all_languages(self):
        """加载所有语言文件"""
        try:
            for lang_code in self.supported_languages:
                lang_file = self.languages_dir / f"{lang_code}.json"
                if lang_file.exists():
                    self._load_language_file(lang_code, lang_file)
                else:
                    self.logger.warning(f"Language file not found: {lang_file}")
        except Exception as e:
            self.logger.error(f"Error loading language files: {e}")
    
    def _load_language_file(self, lang_code: str, file_path: Path):
        """加载指定语言文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations[lang_code] = json.load(f)
            self.logger.info(f"Loaded language file: {lang_code}")
        except Exception as e:
            self.logger.error(f"Error loading {lang_code}: {e}")
            self.translations[lang_code] = {}
    
    def _detect_system_language(self):
        """自动检测系统语言"""
        try:
            import locale
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                if system_locale.startswith('zh'):
                    self.current_language = 'zh_CN'
                else:
                    self.current_language = 'en_US'
        except Exception as e:
            self.logger.warning(f"Failed to detect system language: {e}")
            self.current_language = 'zh_CN'  # 默认中文
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.supported_languages.copy()
    
    def get_current_language(self) -> str:
        """获取当前语言代码"""
        return self.current_language
    
    def get_current_language_name(self) -> str:
        """获取当前语言名称"""
        return self.supported_languages.get(self.current_language, self.current_language)
    
    def set_language(self, lang_code: str) -> bool:
        """
        设置当前语言
        
        Args:
            lang_code: 语言代码 (如 'zh_CN', 'en_US')
            
        Returns:
            bool: 设置是否成功
        """
        if lang_code not in self.supported_languages:
            self.logger.warning(f"Unsupported language: {lang_code}")
            return False
        
        if lang_code == self.current_language:
            return True  # 语言相同，无需切换
        
        old_language = self.current_language
        self.current_language = lang_code
        
        # 通知所有观察者语言已变更
        self._notify_observers()
        
        self.logger.info(f"Language changed from {old_language} to {lang_code}")
        return True
    
    def t(self, key: str, **kwargs) -> str:
        """
        翻译文本
        
        Args:
            key: 翻译键，支持点号分隔的层次结构 (如 'ui.main_window.title')
            **kwargs: 用于字符串格式化的参数
            
        Returns:
            str: 翻译后的文本
        """
        # 获取当前语言的翻译
        text = self._get_translation(self.current_language, key)
        
        # 如果当前语言没有翻译，尝试回退语言
        if text is None and self.current_language != self.fallback_language:
            text = self._get_translation(self.fallback_language, key)
        
        # 如果仍然没有翻译，返回键名作为默认值
        if text is None:
            text = key
            self.logger.warning(f"Missing translation for key: {key}")
        
        # 应用参数替换
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception as e:
                self.logger.error(f"Error formatting text for key '{key}': {e}")
        
        return text
    
    def _get_translation(self, lang_code: str, key: str) -> Optional[str]:
        """
        从指定语言获取翻译
        
        Args:
            lang_code: 语言代码
            key: 翻译键
            
        Returns:
            Optional[str]: 翻译文本，如果不存在返回None
        """
        if lang_code not in self.translations:
            return None
        
        # 按点号分割键名，逐层查找
        keys = key.split('.')
        current_dict = self.translations[lang_code]
        
        try:
            for k in keys:
                current_dict = current_dict[k]
            return str(current_dict)
        except (KeyError, TypeError):
            return None
    
    def register_observer(self, callback: Callable[[], None]):
        """
        注册语言变更观察者
        
        Args:
            callback: 语言变更时的回调函数
        """
        if callback not in self.observers:
            self.observers.append(callback)
    
    def unregister_observer(self, callback: Callable[[], None]):
        """
        取消注册语言变更观察者
        
        Args:
            callback: 要取消的回调函数
        """
        if callback in self.observers:
            self.observers.remove(callback)
    
    def _notify_observers(self):
        """通知所有观察者语言已变更"""
        for callback in self.observers:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error notifying observer: {e}")
    
    def has_translation(self, key: str, lang_code: str = None) -> bool:
        """
        检查是否存在指定键的翻译
        
        Args:
            key: 翻译键
            lang_code: 语言代码，默认为当前语言
            
        Returns:
            bool: 是否存在翻译
        """
        if lang_code is None:
            lang_code = self.current_language
        
        return self._get_translation(lang_code, key) is not None
    
    def get_missing_translations(self, lang_code: str = None) -> List[str]:
        """
        获取缺失的翻译键列表
        
        Args:
            lang_code: 要检查的语言代码，默认为当前语言
            
        Returns:
            List[str]: 缺失的翻译键列表
        """
        if lang_code is None:
            lang_code = self.current_language
        
        missing_keys = []
        # 这里可以实现更复杂的缺失翻译检查逻辑
        # 暂时返回空列表
        return missing_keys
    
    def reload_translations(self):
        """重新加载所有翻译文件"""
        self.translations.clear()
        self._load_all_languages()
        self._notify_observers()
        self.logger.info("Translations reloaded")


# 便利的全局函数
def tr(key: str, **kwargs) -> str:
    """
    全局翻译函数
    
    Args:
        key: 翻译键
        **kwargs: 格式化参数
        
    Returns:
        str: 翻译后的文本
    """
    return I18nManager.instance().t(key, **kwargs)


def set_language(lang_code: str) -> bool:
    """
    全局语言设置函数
    
    Args:
        lang_code: 语言代码
        
    Returns:
        bool: 设置是否成功
    """
    return I18nManager.instance().set_language(lang_code)


def get_current_language() -> str:
    """获取当前语言代码"""
    return I18nManager.instance().get_current_language()