# ===== models/__init__.py =====
"""
Data models for the Dofus/Wakfu Window Cycler
"""

from .game_window import GameWindow
from .profile import Profile, WindowProfile
from .hotkey import HotkeyConfig, HotkeyValidator, KEYBOARD_PRESETS, MOUSE_PRESETS

__all__ = [
    'GameWindow',
    'Profile', 
    'WindowProfile',
    'HotkeyConfig',
    'HotkeyValidator',
    'KEYBOARD_PRESETS',
    'MOUSE_PRESETS'
]