#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auPunch i18n Bridge Module
Adheres to ATG App Standards by leveraging _lib.i18n with _lang/languages.tsv.
Maintains backward compatibility with get_text(key, lang) and detect_language().
"""

import os
import sys
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add _lib to sys.path if not present
BASE_DIR = Path(__file__).resolve().parent
for p in [BASE_DIR, BASE_DIR.parent, BASE_DIR.parent.parent]:
    lib_dir = p / "_lib"
    if lib_dir.is_dir():
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        break

try:
    from _lib import i18n as _lib_i18n
    _LANG_DIR = str(BASE_DIR / "_lang")
    _lib_i18n.init(_LANG_DIR, default_lang="zh_TW", fallback_lang="zh_TW")
    _HAS_LIB_I18N = True
except Exception:
    _HAS_LIB_I18N = False

def detect_language():
    """Detect system language."""
    if _HAS_LIB_I18N:
        return _lib_i18n.detect_system_language()
    
    # Fallback heuristic
    env_lang = os.environ.get('LC_ALL') or os.environ.get('LC_MESSAGES') or os.environ.get('LANG') or ''
    if env_lang:
        lang_str = env_lang.lower()
        if 'tw' in lang_str or 'hk' in lang_str or 'hant' in lang_str:
            return 'zh_TW'
        elif 'cn' in lang_str or 'hans' in lang_str or 'sg' in lang_str:
            return 'zh_CN'
        elif 'ja' in lang_str:
            return 'ja_JP'
        elif 'en' in lang_str:
            return 'en_US'

    if sys.platform == 'win32':
        try:
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lcid in (0x0404, 0x0c04, 0x1404):
                return 'zh_TW'
            elif lcid in (0x0804, 0x1004):
                return 'zh_CN'
            elif lcid == 0x0411:
                return 'ja_JP'
        except Exception:
            pass

    return 'zh_TW'

def get_text(key, lang=None, **kwargs):
    """Retrieve localized text for a key."""
    if _HAS_LIB_I18N:
        if lang:
            cur = _lib_i18n.get_language()
            if cur != lang:
                _lib_i18n.set_language(lang)
            res = _lib_i18n.t(key, **kwargs)
            if cur != lang:
                _lib_i18n.set_language(cur)
            return res
        return _lib_i18n.t(key, **kwargs)
    return key

def t(key, **kwargs):
    """Shortcut for translation."""
    return get_text(key, **kwargs)

_ = t

if __name__ == '__main__':
    print(f"Detected Language: {detect_language()}")
    print(f"app_title: {t('app_title')}")
    print(f"desc: {t('desc')}")
    print(f"gui_chk_edit: {t('gui_chk_edit')}")
