"""
Profile data models for saving and loading window configurations
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import time
import json


@dataclass
class WindowProfile:
    """Represents a saved window configuration"""
    title: str
    character_name: str
    game_type: str
    order: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowProfile':
        return cls(**data)


@dataclass
class Profile:
    """Represents a complete cycling profile"""
    name: str
    windows: List[WindowProfile]
    hotkey: str = "ctrl+tab"
    auto_detect: bool = True
    created_at: str = ""
    description: str = ""
    
    def __post_init__(self):
        """Set creation time if not provided"""
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert dict windows to WindowProfile objects if needed
        if self.windows and isinstance(self.windows[0], dict):
            self.windows = [WindowProfile.from_dict(w) for w in self.windows]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Ensure windows are dictionaries
        data['windows'] = [w.to_dict() if isinstance(w, WindowProfile) else w for w in self.windows]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create from dictionary"""
        # Convert window dictionaries to WindowProfile objects
        if 'windows' in data:
            data['windows'] = [WindowProfile.from_dict(w) if isinstance(w, dict) else w 
                              for w in data['windows']]
        return cls(**data)
    
    def get_window_count(self) -> int:
        """Get number of windows in this profile"""
        return len(self.windows)
    
    def get_summary(self) -> str:
        """Get a summary string for display"""
        window_count = self.get_window_count()
        game_types = set(w.game_type for w in self.windows)
        games_str = ", ".join(game_types).title()
        return f"{window_count} windows ({games_str}) - {self.created_at}"
    
    def validate(self) -> List[str]:
        """Validate profile data and return list of errors"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Profile name cannot be empty")
        
        if not self.windows:
            errors.append("Profile must contain at least one window")
        
        if not self.hotkey:
            errors.append("Profile must have a hotkey defined")
        
        # Check for duplicate orders
        orders = [w.order for w in self.windows]
        if len(orders) != len(set(orders)):
            errors.append("Window orders must be unique")
        
        return errors
    
    def __str__(self) -> str:
        return f"Profile '{self.name}': {self.get_summary()}"
    
    def __repr__(self) -> str:
        return f"Profile(name='{self.name}', windows={len(self.windows)}, hotkey='{self.hotkey}')"