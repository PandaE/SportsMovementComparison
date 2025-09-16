"""
Localization package for multi-language support.
多语言支持包
"""

from .i18n_manager import I18nManager, tr, set_language, get_current_language
from .translation_keys import TranslationKeys, TK

__all__ = [
    'I18nManager',
    'tr', 
    'set_language', 
    'get_current_language',
    'TranslationKeys',
    'TK'
]