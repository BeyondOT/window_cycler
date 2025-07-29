"""
Core window cycling functionality with advanced activation methods
"""

from typing import List, Optional, Callable
import time

from models.game_window import GameWindow
from models.hotkey import HotkeyConfig
from core.hotkey_manager import HotkeyManager
from utils.platform_utils import get_windows_api


class WindowCycler:
    """Handles window cycling logic and activation"""
    
    def __init__(self):
        self.windows: List[GameWindow] = []
        self.current_index = 0
        self.hotkey_manager = HotkeyManager()
        self.windows_api = get_windows_api()
        
        # Callbacks for status updates
        self.on_window_activated: Optional[Callable] = None
        self.on_window_removed: Optional[Callable] = None
        self.on_cycling_stopped: Optional[Callable] = None
        
        # Statistics
        self.total_cycles = 0
        self.successful_activations = 0
        self.failed_activations = 0
    
    def set_windows(self, windows: List[GameWindow]) -> bool:
        """Set the windows to cycle through"""
        if not windows:
            return False
        
        # Sort by order and validate
        valid_windows = [w for w in windows if w.is_valid_handle()]
        
        if not valid_windows:
            print("❌ No valid windows to cycle")
            return False
        
        self.windows = sorted(valid_windows, key=lambda w: w.order)
        self.current_index = 0
        
        print(f"✅ Window cycling set up with {len(self.windows)} windows:")
        for i, window in enumerate(self.windows):
            print(f"   {i+1}. {window.get_display_name()}")
        
        return True
    
    def set_hotkey(self, hotkey_config: HotkeyConfig) -> bool:
        """Set the hotkey for cycling"""
        return self.hotkey_manager.set_hotkey(hotkey_config, self.cycle_next)
    
    def start_cycling(self) -> bool:
        """Start the cycling system"""
        if not self.windows:
            print("❌ No windows configured for cycling")
            return False
        
        if not self.hotkey_manager.is_listening:
            print("❌ Hotkey not properly configured")
            return False
        
        print(f"🎮 Window cycling started with {len(self.windows)} windows")
        return True
    
    def stop_cycling(self):
        """Stop the cycling system"""
        self.hotkey_manager.stop_listening()
        
        if self.on_cycling_stopped:
            self.on_cycling_stopped()
        
        print("🔇 Window cycling stopped")
    
    def cycle_next(self):
        """Cycle to the next window"""
        if not self.windows:
            print("❌ No windows to cycle through")
            return
        
        self.total_cycles += 1
        max_attempts = len(self.windows)
        attempts = 0
        
        while attempts < max_attempts:
            # Ensure index is valid
            if self.current_index >= len(self.windows):
                self.current_index = 0
            
            window = self.windows[self.current_index]
            print(f"🔄 Attempting to cycle to window {self.current_index + 1}: {window.get_display_name()}")
            
            # Check if window still exists
            if not window.is_valid_handle():
                print(f"❌ Window no longer valid, removing from list")
                self._remove_invalid_window(self.current_index)
                
                if not self.windows:
                    print("❌ No valid windows remaining")
                    self.stop_cycling()
                    return
                
                # Don't increment index since we removed an item
                continue
            
            # Try to activate the window
            success = self._activate_window(window)
            
            if success:
                print(f"✅ Successfully activated: {window.get_display_name()}")
                self.successful_activations += 1
                
                # Move to next window for next cycle
                self.current_index = (self.current_index + 1) % len(self.windows)
                
                if self.on_window_activated:
                    self.on_window_activated(window)
                
                return
            else:
                print(f"⚠️ Failed to activate window, trying next...")
                self.failed_activations += 1
            
            # Move to next window and try again
            self.current_index = (self.current_index + 1) % len(self.windows)
            attempts += 1
        
        print("❌ Could not activate any window after trying all options")
    
    def cycle_to_specific(self, window_index: int) -> bool:
        """Cycle to a specific window by index"""
        if not self.windows or window_index < 0 or window_index >= len(self.windows):
            return False
        
        window = self.windows[window_index]
        
        if not window.is_valid_handle():
            self._remove_invalid_window(window_index)
            return False
        
        success = self._activate_window(window)
        
        if success:
            self.current_index = window_index
            if self.on_window_activated:
                self.on_window_activated(window)
        
        return success
    
    def cycle_to_character(self, character_name: str) -> bool:
        """Cycle to a specific character by name"""
        for i, window in enumerate(self.windows):
            if window.character_name.lower() == character_name.lower():
                return self.cycle_to_specific(i)
        return False
    
    def _activate_window(self, window: GameWindow) -> bool:
        """Activate a window using multiple fallback methods"""
        if not self.windows_api:
            print("❌ Windows API not available")
            return False
        
        print(f"   Attempting to activate: {window.get_display_name()}")
        
        return self.windows_api.activate_window(window.hwnd)
    
    def _remove_invalid_window(self, index: int):
        """Remove an invalid window from the cycling list"""
        if 0 <= index < len(self.windows):
            removed_window = self.windows.pop(index)
            
            # Adjust current index if needed
            if self.current_index >= len(self.windows) and self.windows:
                self.current_index = 0
            
            if self.on_window_removed:
                self.on_window_removed(removed_window)
            
            print(f"🗑️ Removed invalid window: {removed_window.get_display_name()}")
    
    def refresh_window_validity(self):
        """Check all windows and remove invalid ones"""
        original_count = len(self.windows)
        
        # Remove invalid windows (iterate backwards to avoid index issues)
        for i in range(len(self.windows) - 1, -1, -1):
            if not self.windows[i].is_valid_handle():
                self._remove_invalid_window(i)
        
        removed_count = original_count - len(self.windows)
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} invalid window(s)")
    
    def reorder_windows(self, new_order: List[int]) -> bool:
        """Reorder windows based on new order list"""
        if len(new_order) != len(self.windows):
            return False
        
        try:
            # Create new ordered list
            new_windows = []
            for order in new_order:
                if 0 <= order < len(self.windows):
                    new_windows.append(self.windows[order])
                else:
                    return False
            
            self.windows = new_windows
            self.current_index = 0
            
            print(f"🔀 Reordered {len(self.windows)} windows")
            return True
            
        except Exception as e:
            print(f"❌ Failed to reorder windows: {e}")
            return False
    
    def get_current_window(self) -> Optional[GameWindow]:
        """Get the currently selected window"""
        if self.windows and 0 <= self.current_index < len(self.windows):
            return self.windows[self.current_index]
        return None
    
    def get_next_window(self) -> Optional[GameWindow]:
        """Get the next window that would be activated"""
        if not self.windows:
            return None
        
        next_index = (self.current_index + 1) % len(self.windows)
        return self.windows[next_index]
    
    def get_window_count(self) -> int:
        """Get the number of windows in cycling"""
        return len(self.windows)
    
    def get_statistics(self) -> dict:
        """Get cycling statistics"""
        return {
            'total_cycles': self.total_cycles,
            'successful_activations': self.successful_activations,
            'failed_activations': self.failed_activations,
            'success_rate': (self.successful_activations / max(1, self.total_cycles)) * 100,
            'window_count': len(self.windows),
            'current_index': self.current_index,
            'is_listening': self.hotkey_manager.is_listening,
            'hotkey_status': self.hotkey_manager.get_status()
        }
    
    def reset_statistics(self):
        """Reset cycling statistics"""
        self.total_cycles = 0
        self.successful_activations = 0
        self.failed_activations = 0
    
    def is_cycling_active(self) -> bool:
        """Check if cycling is currently active"""
        return self.hotkey_manager.is_listening and len(self.windows) > 0
    
    def get_status_summary(self) -> str:
        """Get a human-readable status summary"""
        if not self.windows:
            return "No windows configured"
        
        if not self.hotkey_manager.is_listening:
            return f"{len(self.windows)} windows configured, but not listening for hotkey"
        
        current = self.get_current_window()
        next_window = self.get_next_window()
        
        status = f"Cycling {len(self.windows)} windows"
        
        if current:
            status += f", current: {current.get_short_title()}"
        
        if next_window and len(self.windows) > 1:
            status += f", next: {next_window.get_short_title()}"
        
        return status
    
    def __repr__(self) -> str:
        return f"WindowCycler(windows={len(self.windows)}, active={self.is_cycling_active()})"