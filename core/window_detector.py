"""
Game window detection and analysis for Dofus and Wakfu
"""

from typing import List, Dict, Optional
import sys

from models.game_window import GameWindow
from utils.platform_utils import get_windows_api


class GameWindowDetector:
    """Detects and analyzes Dofus/Wakfu windows"""
    
    # Supported game processes and their types
    GAME_PROCESSES = {
        'dofus.exe': 'dofus',
        'Dofus.exe': 'dofus',
        'java.exe': 'wakfu',  # Could be either game
        'wakfu.exe': 'wakfu',
        'Wakfu.exe': 'wakfu'
    }
    
    # Keywords for game type detection
    DOFUS_KEYWORDS = ['dofus', 'dofus retro', 'dofus unity', '- dofus', 'dofus -', '[dofus]']
    WAKFU_KEYWORDS = ['wakfu', '- wakfu', 'wakfu -', '[wakfu]']
    
    def __init__(self):
        self.windows_api = get_windows_api()
        if not self.windows_api:
            raise RuntimeError("Windows API not available")
        
        # Import psutil for process information
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            raise RuntimeError("psutil library required")
    
    def get_all_game_windows(self) -> List[GameWindow]:
        """Find all Dofus/Wakfu windows currently open"""
        windows = []
        
        def enum_callback(hwnd, window_list):
            if self.windows_api.is_window_visible(hwnd):
                title = self.windows_api.get_window_title(hwnd)
                if title:  # Skip windows without titles
                    process_id = self.windows_api.get_window_process_id(hwnd)
                    if process_id:
                        try:
                            process = self.psutil.Process(process_id)
                            process_name = process.name()
                            
                            # Check if it's a game we care about
                            if self._is_game_process(process_name):
                                game_window = self._create_game_window(
                                    hwnd, title, process_name, process_id
                                )
                                if game_window:
                                    window_list.append(game_window)
                                    
                        except (self.psutil.NoSuchProcess, self.psutil.AccessDenied):
                            pass
            return True
        
        self.windows_api.enum_windows(enum_callback)
        return windows
    
    def _is_game_process(self, process_name: str) -> bool:
        """Check if process name matches a supported game"""
        return process_name.lower() in [p.lower() for p in self.GAME_PROCESSES.keys()]
    
    def _create_game_window(self, hwnd: int, title: str, process_name: str, 
                           process_id: int) -> Optional[GameWindow]:
        """Create a GameWindow object from window information"""
        game_type = self._detect_game_type(title, process_name)
        if not game_type:
            return None
        
        character_name = self._extract_character_name(title, game_type)
        
        return GameWindow(
            hwnd=hwnd,
            title=title,
            process_name=process_name,
            process_id=process_id,
            character_name=character_name,
            game_type=game_type
        )
    
    def _detect_game_type(self, title: str, process_name: str) -> str:
        """Determine if window is Dofus or Wakfu"""
        title_lower = title.lower()
        
        # Direct process name detection
        process_lower = process_name.lower()
        if 'dofus' in process_lower:
            return 'dofus'
        elif 'wakfu' in process_lower:
            return 'wakfu'
        
        # Title-based detection for direct matches
        for keyword in self.DOFUS_KEYWORDS:
            if keyword in title_lower:
                return 'dofus'
        
        for keyword in self.WAKFU_KEYWORDS:
            if keyword in title_lower:
                return 'wakfu'
        
        # Special handling for Java processes
        if process_lower == 'java.exe':
            return self._detect_java_game_type(title_lower)
        
        return ""
    
    def _detect_java_game_type(self, title_lower: str) -> str:
        """Detect game type for Java processes (more sophisticated logic)"""
        # Look for specific patterns that indicate the game type
        dofus_patterns = ['- dofus', 'dofus -', '[dofus]', 'dofus retro', 'dofus unity']
        wakfu_patterns = ['- wakfu', 'wakfu -', '[wakfu]', 'wakfu client']
        
        for pattern in dofus_patterns:
            if pattern in title_lower:
                return 'dofus'
        
        for pattern in wakfu_patterns:
            if pattern in title_lower:
                return 'wakfu'
        
        # If no specific patterns found, check for general keywords
        if 'dofus' in title_lower:
            return 'dofus'
        elif 'wakfu' in title_lower:
            return 'wakfu'
        
        return ""
    
    def _extract_character_name(self, title: str, game_type: str) -> str:
        """Extract character name from window title"""
        try:
            return self._extract_character_name_advanced(title, game_type)
        except Exception:
            # Fallback to simple extraction
            return self._extract_character_name_simple(title)
    
    def _extract_character_name_advanced(self, title: str, game_type: str) -> str:
        """Advanced character name extraction with game-specific logic"""
        if not title or len(title.strip()) < 3:
            return "Unknown Character"
        
        # Common separators used in game window titles
        separators = [' - ', ' | ', ' : ', '[', ']', '(', ')']
        
        # Try to split by separators and find the character name
        parts = [title]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        # Clean and filter parts
        clean_parts = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 1:
                clean_parts.append(part)
        
        # Game-specific filtering
        if game_type == 'dofus':
            return self._filter_dofus_character_name(clean_parts)
        elif game_type == 'wakfu':
            return self._filter_wakfu_character_name(clean_parts)
        
        return self._extract_character_name_generic(clean_parts)
    
    def _filter_dofus_character_name(self, parts: List[str]) -> str:
        """Filter parts to find Dofus character name"""
        # Skip common Dofus-related terms
        skip_terms = {
            'dofus', 'retro', 'unity', 'client', 'launcher', 'game', 
            'ankama', 'server', 'beta', 'alpha', 'test'
        }
        
        candidates = []
        for part in parts:
            part_lower = part.lower()
            if not any(term in part_lower for term in skip_terms):
                # Check if it looks like a character name (letters, maybe numbers)
                if self._looks_like_character_name(part):
                    candidates.append(part)
        
        if candidates:
            # Prefer shorter names (likely character names vs server names)
            candidates.sort(key=len)
            return candidates[0]
        
        return self._extract_character_name_generic(parts)
    
    def _filter_wakfu_character_name(self, parts: List[str]) -> str:
        """Filter parts to find Wakfu character name"""
        skip_terms = {
            'wakfu', 'client', 'launcher', 'game', 'ankama', 
            'server', 'beta', 'alpha', 'test'
        }
        
        candidates = []
        for part in parts:
            part_lower = part.lower()
            if not any(term in part_lower for term in skip_terms):
                if self._looks_like_character_name(part):
                    candidates.append(part)
        
        if candidates:
            candidates.sort(key=len)
            return candidates[0]
        
        return self._extract_character_name_generic(parts)
    
    def _extract_character_name_generic(self, parts: List[str]) -> str:
        """Generic character name extraction"""
        if not parts:
            return "Unknown Character"
        
        # Try to find the most likely character name
        # Usually it's a shorter part that's not too generic
        candidates = [p for p in parts if 2 < len(p) < 20]
        
        if candidates:
            # Sort by length and take the shortest reasonable one
            candidates.sort(key=len)
            return candidates[0]
        
        # Fallback to first part or truncated title
        first_part = parts[0] if parts else "Unknown"
        return first_part[:30] + "..." if len(first_part) > 30 else first_part
    
    def _extract_character_name_simple(self, title: str) -> str:
        """Simple fallback character name extraction"""
        if not title:
            return "Unknown Character"
        
        # Just return truncated title as fallback
        return title[:30] + "..." if len(title) > 30 else title
    
    def _looks_like_character_name(self, text: str) -> bool:
        """Check if text looks like a character name"""
        if not text or len(text) < 2 or len(text) > 25:
            return False
        
        # Character names usually contain letters
        if not any(c.isalpha() for c in text):
            return False
        
        # Skip parts that look like version numbers or IDs
        if text.replace('.', '').replace('-', '').isdigit():
            return False
        
        # Skip common non-character terms
        common_terms = {
            'version', 'build', 'client', 'server', 'beta', 'alpha',
            'launcher', 'game', 'window', 'main', 'login'
        }
        
        if text.lower() in common_terms:
            return False
        
        return True
    
    def refresh_window_info(self, game_window: GameWindow) -> bool:
        """Refresh information for an existing game window"""
        try:
            # Check if window still exists
            if not self.windows_api.is_window_valid(game_window.hwnd):
                return False
            
            # Update title (character might have changed)
            new_title = self.windows_api.get_window_title(game_window.hwnd)
            if new_title:
                game_window.title = new_title
                game_window.character_name = self._extract_character_name(
                    new_title, game_window.game_type
                )
            
            return True
            
        except Exception:
            return False
    
    def get_game_statistics(self) -> Dict[str, int]:
        """Get statistics about detected games"""
        windows = self.get_all_game_windows()
        
        stats = {
            'total_windows': len(windows),
            'dofus_windows': len([w for w in windows if w.game_type == 'dofus']),
            'wakfu_windows': len([w for w in windows if w.game_type == 'wakfu']),
            'unique_characters': len(set(w.character_name for w in windows if w.character_name))
        }
        
        return stats