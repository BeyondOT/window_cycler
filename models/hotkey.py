"""
Hotkey configuration models and utilities
"""

from dataclasses import dataclass
from typing import List, Set, Optional, Tuple
from enum import Enum


class HotkeyType(Enum):
    """Types of hotkeys supported"""
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    COMBINATION = "combination"


class ModifierKey(Enum):
    """Modifier keys"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    WIN = "win"


@dataclass
class HotkeyConfig:
    """Configuration for a hotkey"""
    raw_value: str  # e.g., "ctrl+mouse5"
    display_name: str  # e.g., "Ctrl+Mouse 5"
    modifiers: List[ModifierKey]
    main_key: str
    hotkey_type: HotkeyType
    
    @classmethod
    def parse(cls, hotkey_string: str) -> 'HotkeyConfig':
        """Parse a hotkey string into a HotkeyConfig"""
        raw_value = hotkey_string.lower().strip()
        parts = raw_value.split('+')
        
        # Separate modifiers from main key
        main_key = parts[-1]
        modifier_strings = parts[:-1]
        
        # Parse modifiers
        modifiers = []
        for mod_str in modifier_strings:
            try:
                modifiers.append(ModifierKey(mod_str))
            except ValueError:
                raise ValueError(f"Invalid modifier: {mod_str}")
        
        # Determine hotkey type
        if main_key in ['middle', 'mouse4', 'mouse5']:
            hotkey_type = HotkeyType.MOUSE if not modifiers else HotkeyType.COMBINATION
        else:
            hotkey_type = HotkeyType.KEYBOARD if not modifiers else HotkeyType.COMBINATION
        
        # Generate display name
        display_name = cls._generate_display_name(modifiers, main_key)
        
        return cls(
            raw_value=raw_value,
            display_name=display_name,
            modifiers=modifiers,
            main_key=main_key,
            hotkey_type=hotkey_type
        )
    
    @staticmethod
    def _generate_display_name(modifiers: List[ModifierKey], main_key: str) -> str:
        """Generate a user-friendly display name"""
        display_parts = []
        
        # Add modifiers
        for modifier in modifiers:
            if modifier == ModifierKey.CTRL:
                display_parts.append("Ctrl")
            elif modifier == ModifierKey.ALT:
                display_parts.append("Alt")
            elif modifier == ModifierKey.SHIFT:
                display_parts.append("Shift")
            elif modifier == ModifierKey.WIN:
                display_parts.append("Win")
        
        # Add main key
        if main_key == 'middle':
            display_parts.append("Middle Click")
        elif main_key == 'mouse4':
            display_parts.append("Mouse 4")
        elif main_key == 'mouse5':
            display_parts.append("Mouse 5")
        elif main_key == 'space':
            display_parts.append("Space")
        elif main_key == 'tab':
            display_parts.append("Tab")
        elif main_key.startswith('f') and main_key[1:].isdigit():
            display_parts.append(main_key.upper())
        else:
            display_parts.append(main_key.upper())
        
        return "+".join(display_parts)
    
    def is_valid(self) -> bool:
        """Check if this hotkey configuration is valid"""
        try:
            return HotkeyValidator.validate_hotkey(self.raw_value)
        except:
            return False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'raw_value': self.raw_value,
            'display_name': self.display_name,
            'modifiers': [m.value for m in self.modifiers],
            'main_key': self.main_key,
            'hotkey_type': self.hotkey_type.value
        }
    
    def __str__(self) -> str:
        return self.display_name
    
    def __repr__(self) -> str:
        return f"HotkeyConfig('{self.raw_value}' -> '{self.display_name}')"


class HotkeyValidator:
    """Validates hotkey configurations"""
    
    VALID_MODIFIERS = {'ctrl', 'alt', 'shift', 'win'}
    
    VALID_KEYS = {
        # Function keys
        'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
        # Special keys
        'space', 'tab', 'enter', 'escape', 'backspace', 'delete', 'insert', 
        'home', 'end', 'pageup', 'pagedown', 'up', 'down', 'left', 'right',
        # Mouse buttons
        'middle', 'mouse4', 'mouse5',
        # Numbers
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        # Letters
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
    }
    
    @classmethod
    def validate_hotkey(cls, hotkey_string: str) -> bool:
        """Validate a hotkey string"""
        if not hotkey_string or not hotkey_string.strip():
            return False
        
        parts = hotkey_string.lower().strip().split('+')
        
        if len(parts) < 1:
            return False
        
        # Last part should be the main key
        main_key = parts[-1]
        if main_key not in cls.VALID_KEYS:
            return False
        
        # All other parts should be modifiers
        modifiers = parts[:-1]
        for modifier in modifiers:
            if modifier not in cls.VALID_MODIFIERS:
                return False
        
        # Check for duplicate modifiers
        if len(modifiers) != len(set(modifiers)):
            return False
        
        return True
    
    @classmethod
    def get_validation_error(cls, hotkey_string: str) -> Optional[str]:
        """Get a descriptive validation error message"""
        if not hotkey_string or not hotkey_string.strip():
            return "Hotkey cannot be empty"
        
        parts = hotkey_string.lower().strip().split('+')
        
        if len(parts) < 1:
            return "Invalid hotkey format"
        
        main_key = parts[-1]
        modifiers = parts[:-1]
        
        # Check main key
        if main_key not in cls.VALID_KEYS:
            return f"Invalid key: '{main_key}'. Must be a letter, number, function key, or mouse button."
        
        # Check modifiers
        for modifier in modifiers:
            if modifier not in cls.VALID_MODIFIERS:
                return f"Invalid modifier: '{modifier}'. Valid modifiers: {', '.join(cls.VALID_MODIFIERS)}"
        
        # Check for duplicates
        if len(modifiers) != len(set(modifiers)):
            return "Duplicate modifiers are not allowed"
        
        return None


# Predefined hotkey presets
KEYBOARD_PRESETS = [
    ("Ctrl+Tab", "ctrl+tab"),
    ("Alt+Tab", "alt+tab"),
    ("Ctrl+Space", "ctrl+space"),
    ("Ctrl+Q", "ctrl+q"),
    ("F1", "f1"),
    ("F2", "f2"),
    ("F3", "f3"),
    ("F4", "f4"),
    ("Ctrl+F1", "ctrl+f1"),
    ("Ctrl+F2", "ctrl+f2")
]

MOUSE_PRESETS = [
    ("Middle Click", "middle"),
    ("Mouse 4", "mouse4"),
    ("Mouse 5", "mouse5"),
    ("Ctrl+Middle", "ctrl+middle"),
    ("Ctrl+Mouse 4", "ctrl+mouse4"),
    ("Ctrl+Mouse 5", "ctrl+mouse5"),
    ("Alt+Middle", "alt+middle"),
    ("Alt+Mouse 4", "alt+mouse4"),
    ("Alt+Mouse 5", "alt+mouse5"),
    ("Shift+Mouse 4", "shift+mouse4")
]