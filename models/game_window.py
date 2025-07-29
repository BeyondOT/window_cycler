"""
Game window data models and related utilities
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class GameWindow:
    """Represents a game window with all its properties"""
    hwnd: int
    title: str
    process_name: str
    process_id: int
    character_name: str = ""
    game_type: str = ""  # "dofus" or "wakfu"
    icon_path: str = ""
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameWindow':
        """Create from dictionary"""
        return cls(**data)
    
    def get_display_name(self) -> str:
        """Get the best display name for this window"""
        if self.character_name and self.character_name != "Unknown Character":
            return self.character_name
        return self.title[:50] + "..." if len(self.title) > 50 else self.title
    
    def get_short_title(self, max_length: int = 30) -> str:
        """Get shortened title for display"""
        display_name = self.get_display_name()
        if len(display_name) > max_length:
            return display_name[:max_length-3] + "..."
        return display_name
    
    def is_valid_handle(self) -> bool:
        """Check if the window handle is still valid"""
        try:
            if sys.platform == "win32":
                import win32gui
                return win32gui.IsWindow(self.hwnd) and win32gui.IsWindowVisible(self.hwnd)
            return True
        except:
            return False
    
    def __str__(self) -> str:
        return f"{self.game_type.title()}: {self.get_display_name()}"
    
    def __repr__(self) -> str:
        return f"GameWindow(hwnd={self.hwnd}, game_type='{self.game_type}', character='{self.character_name}')"


import sys