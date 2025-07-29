"""
Global hotkey management with multiple fallback methods
"""

import threading
import time
from typing import Callable, Optional, List, Set
from enum import Enum

from models.hotkey import HotkeyConfig
from utils.platform_utils import get_windows_api


class HotkeyMethod(Enum):
    """Available hotkey detection methods"""
    KEYBOARD_LIB = "keyboard"
    WIN32_REGISTER = "win32"
    PYNPUT = "pynput"


class HotkeyManager:
    """Manages global hotkeys with multiple fallback methods"""
    
    def __init__(self):
        self.current_config: Optional[HotkeyConfig] = None
        self.callback: Optional[Callable] = None
        self.is_listening = False
        self.last_trigger_time = 0
        self.min_trigger_interval = 0.2  # 200ms debounce
        
        # Method management
        self.active_method: Optional[HotkeyMethod] = None
        self.method_priority = [HotkeyMethod.KEYBOARD_LIB, HotkeyMethod.WIN32_REGISTER, HotkeyMethod.PYNPUT]
        
        # Threading
        self.hotkey_thread: Optional[threading.Thread] = None
        self.stop_thread = False
        
        # Method-specific attributes
        self._init_keyboard_lib()
        self._init_pynput()
        self.windows_api = get_windows_api()
    
    def _init_keyboard_lib(self):
        """Initialize keyboard library if available"""
        try:
            import keyboard
            self.keyboard = keyboard
            self.keyboard_available = True
        except ImportError:
            self.keyboard = None
            self.keyboard_available = False
    
    def _init_pynput(self):
        """Initialize pynput libraries"""
        try:
            import pynput.keyboard as pynput_keyboard
            import pynput.mouse as pynput_mouse
            self.pynput_keyboard = pynput_keyboard
            self.pynput_mouse = pynput_mouse
            self.pynput_available = True
            
            # Pynput state tracking
            self.pressed_keys: Set = set()
            self.pressed_mouse: Set = set()
            self.last_combo_state = False
            self.key_listener = None
            self.mouse_listener = None
            
        except ImportError:
            self.pynput_available = False
    
    def set_hotkey(self, hotkey_config: HotkeyConfig, callback: Callable) -> bool:
        """Set the global hotkey for cycling"""
        self.stop_listening()
        
        self.current_config = hotkey_config
        self.callback = callback
        
        print(f"🎹 Setting up hotkey: {hotkey_config.display_name}")
        
        return self.start_listening()
    
    def start_listening(self) -> bool:
        """Start listening for the hotkey using the best available method"""
        if self.is_listening or not self.current_config:
            return False
        
        methods_tried = []
        
        for method in self.method_priority:
            try:
                success = False
                
                if method == HotkeyMethod.KEYBOARD_LIB and self.keyboard_available:
                    success = self._start_keyboard_method()
                    method_name = "keyboard library"
                    
                elif method == HotkeyMethod.WIN32_REGISTER and self.windows_api:
                    success = self._start_win32_method()
                    method_name = "Win32 RegisterHotKey"
                    
                elif method == HotkeyMethod.PYNPUT and self.pynput_available:
                    success = self._start_pynput_method()
                    method_name = "pynput"
                
                if success:
                    self.active_method = method
                    self.is_listening = True
                    print(f"✅ Using {method_name} method")
                    return True
                else:
                    methods_tried.append(f"{method_name} (failed)")
                    
            except Exception as e:
                methods_tried.append(f"{method.value} (error: {e})")
                continue
        
        print(f"❌ All hotkey methods failed: {', '.join(methods_tried)}")
        return False
    
    def _start_keyboard_method(self) -> bool:
        """Method 1: Use keyboard library"""
        if not self.keyboard_available or not self.current_config:
            return False
        
        try:
            hotkey_string = self._convert_for_keyboard_lib(self.current_config.raw_value)
            
            def on_hotkey():
                if self._should_trigger():
                    self._trigger_callback()
            
            # Clear existing hotkeys
            self.keyboard.unhook_all()
            
            # Register new hotkey
            self.keyboard.add_hotkey(
                hotkey_string, 
                on_hotkey, 
                suppress=False, 
                trigger_on_release=False
            )
            
            return True
            
        except Exception as e:
            print(f"Keyboard library method failed: {e}")
            return False
    
    def _start_win32_method(self) -> bool:
        """Method 2: Use Win32 RegisterHotKey"""
        if not self.windows_api or not self.current_config:
            return False
        
        try:
            vk_code, modifiers = self._convert_for_win32(self.current_config)
            if vk_code is None:
                return False
            
            # Start background thread
            self.stop_thread = False
            self.hotkey_thread = threading.Thread(
                target=self._win32_hotkey_thread,
                args=(vk_code, modifiers),
                daemon=True
            )
            self.hotkey_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Win32 method failed: {e}")
            return False
    
    def _start_pynput_method(self) -> bool:
        """Method 3: Use pynput (supports mouse buttons)"""
        if not self.pynput_available or not self.current_config:
            return False
        
        try:
            self.pressed_keys = set()
            self.pressed_mouse = set()
            self.last_combo_state = False
            
            # Keyboard listener
            self.key_listener = self.pynput_keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            # Mouse listener (for mouse button hotkeys)
            self.mouse_listener = self.pynput_mouse.Listener(
                on_click=self._on_mouse_click
            )
            
            self.key_listener.start()
            self.mouse_listener.start()
            
            return True
            
        except Exception as e:
            print(f"Pynput method failed: {e}")
            return False
    
    def _win32_hotkey_thread(self, vk_code: int, modifiers: int):
        """Background thread for Win32 hotkey handling"""
        try:
            import win32gui
            import win32con
            
            # Register hotkey
            hotkey_id = 1
            if not win32gui.RegisterHotKey(None, hotkey_id, modifiers, vk_code):
                print("Failed to register Win32 hotkey")
                return
            
            try:
                # Message loop
                while not self.stop_thread:
                    try:
                        msg = win32gui.GetMessage(None, 0, 0)
                        if msg and len(msg) > 1 and len(msg[1]) > 1:
                            if msg[1][1] == win32con.WM_HOTKEY:
                                if self._should_trigger():
                                    self._trigger_callback()
                    except:
                        time.sleep(0.01)
                        
            finally:
                win32gui.UnregisterHotKey(None, hotkey_id)
                
        except Exception as e:
            print(f"Win32 hotkey thread error: {e}")
    
    def _on_key_press(self, key):
        """Handle key press events (pynput)"""
        self.pressed_keys.add(key)
        self._check_combo_and_trigger()
    
    def _on_key_release(self, key):
        """Handle key release events (pynput)"""
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        self._check_combo_and_trigger()
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events (pynput)"""
        if pressed:
            self.pressed_mouse.add(button)
        else:
            if button in self.pressed_mouse:
                self.pressed_mouse.remove(button)
        
        self._check_combo_and_trigger()
    
    def _check_combo_and_trigger(self):
        """Check if hotkey combination is active and trigger if needed (pynput)"""
        if not self.current_config:
            return
        
        combo_active = self._is_combo_active_pynput()
        
        # Only trigger on state change from False to True
        if combo_active and not self.last_combo_state and self._should_trigger():
            self._trigger_callback()
        
        self.last_combo_state = combo_active
    
    def _is_combo_active_pynput(self) -> bool:
        """Check if the current combination matches our hotkey (pynput)"""
        if not self.current_config:
            return False
        
        try:
            # Check modifiers
            for modifier in self.current_config.modifiers:
                if not self._is_modifier_pressed(modifier):
                    return False
            
            # Check main key
            return self._is_main_key_pressed(self.current_config.main_key)
            
        except Exception:
            return False
    
    def _is_modifier_pressed(self, modifier) -> bool:
        """Check if a modifier key is pressed (pynput)"""
        from models.hotkey import ModifierKey
        
        if modifier == ModifierKey.CTRL:
            return (self.pynput_keyboard.Key.ctrl_l in self.pressed_keys or 
                   self.pynput_keyboard.Key.ctrl_r in self.pressed_keys)
        elif modifier == ModifierKey.ALT:
            return (self.pynput_keyboard.Key.alt_l in self.pressed_keys or 
                   self.pynput_keyboard.Key.alt_r in self.pressed_keys)
        elif modifier == ModifierKey.SHIFT:
            return (self.pynput_keyboard.Key.shift_l in self.pressed_keys or 
                   self.pynput_keyboard.Key.shift_r in self.pressed_keys)
        return False
    
    def _is_main_key_pressed(self, main_key: str) -> bool:
        """Check if the main key is pressed (pynput)"""
        # Function keys
        if main_key.startswith('f') and main_key[1:].isdigit():
            f_num = int(main_key[1:])
            f_key_map = {
                1: self.pynput_keyboard.Key.f1, 2: self.pynput_keyboard.Key.f2,
                3: self.pynput_keyboard.Key.f3, 4: self.pynput_keyboard.Key.f4,
                5: self.pynput_keyboard.Key.f5, 6: self.pynput_keyboard.Key.f6,
                7: self.pynput_keyboard.Key.f7, 8: self.pynput_keyboard.Key.f8,
                9: self.pynput_keyboard.Key.f9, 10: self.pynput_keyboard.Key.f10,
                11: self.pynput_keyboard.Key.f11, 12: self.pynput_keyboard.Key.f12
            }
            return f_key_map.get(f_num) in self.pressed_keys
        
        # Special keys
        special_keys = {
            'tab': self.pynput_keyboard.Key.tab,
            'space': self.pynput_keyboard.Key.space,
            'enter': self.pynput_keyboard.Key.enter,
            'escape': self.pynput_keyboard.Key.esc,
            'backspace': self.pynput_keyboard.Key.backspace,
            'delete': self.pynput_keyboard.Key.delete,
            'up': self.pynput_keyboard.Key.up,
            'down': self.pynput_keyboard.Key.down,
            'left': self.pynput_keyboard.Key.left,
            'right': self.pynput_keyboard.Key.right
        }
        
        if main_key in special_keys:
            return special_keys[main_key] in self.pressed_keys
        
        # Mouse buttons
        if main_key == 'middle':
            return self.pynput_mouse.Button.middle in self.pressed_mouse
        elif main_key == 'mouse4':
            return self.pynput_mouse.Button.x1 in self.pressed_mouse
        elif main_key == 'mouse5':
            return self.pynput_mouse.Button.x2 in self.pressed_mouse
        
        # Regular keys (letters, numbers)
        if len(main_key) == 1:
            key_code = self.pynput_keyboard.KeyCode.from_char(main_key)
            return key_code in self.pressed_keys
        
        return False
    
    def _convert_for_keyboard_lib(self, hotkey: str) -> str:
        """Convert hotkey format for keyboard library"""
        # Handle mouse buttons specially
        if 'middle' in hotkey:
            return hotkey.replace('middle', 'middle mouse')
        elif 'mouse4' in hotkey:
            return hotkey.replace('mouse4', 'x1 mouse')
        elif 'mouse5' in hotkey:
            return hotkey.replace('mouse5', 'x2 mouse')
        
        return hotkey
    
    def _convert_for_win32(self, config: HotkeyConfig) -> tuple:
        """Convert hotkey config to Win32 virtual key codes"""
        try:
            import win32con
            from models.hotkey import ModifierKey
            
            # Calculate modifier flags
            mod_flags = 0
            for modifier in config.modifiers:
                if modifier == ModifierKey.CTRL:
                    mod_flags |= win32con.MOD_CONTROL
                elif modifier == ModifierKey.ALT:
                    mod_flags |= win32con.MOD_ALT
                elif modifier == ModifierKey.SHIFT:
                    mod_flags |= win32con.MOD_SHIFT
                elif modifier == ModifierKey.WIN:
                    mod_flags |= win32con.MOD_WIN
            
            # Get virtual key code
            vk_code = self._get_vk_code(config.main_key)
            
            return (vk_code, mod_flags) if vk_code else (None, None)
            
        except Exception:
            return (None, None)
    
    def _get_vk_code(self, key: str) -> Optional[int]:
        """Get Windows virtual key code for a key"""
        try:
            import win32con
            
            # Function keys
            if key.startswith('f') and key[1:].isdigit():
                f_num = int(key[1:])
                if 1 <= f_num <= 12:
                    return win32con.VK_F1 + (f_num - 1)
            
            # Special keys
            special_vk_map = {
                'space': win32con.VK_SPACE,
                'tab': win32con.VK_TAB,
                'enter': win32con.VK_RETURN,
                'escape': win32con.VK_ESCAPE,
                'backspace': win32con.VK_BACK,
                'delete': win32con.VK_DELETE,
                'up': win32con.VK_UP,
                'down': win32con.VK_DOWN,
                'left': win32con.VK_LEFT,
                'right': win32con.VK_RIGHT
            }
            
            if key in special_vk_map:
                return special_vk_map[key]
            
            # Letters and numbers
            if len(key) == 1:
                if key.isalpha():
                    return ord(key.upper())
                elif key.isdigit():
                    return ord(key)
            
            # Mouse buttons not supported by Win32 RegisterHotKey
            if key in ['middle', 'mouse4', 'mouse5']:
                return None
            
            return None
            
        except Exception:
            return None
    
    def _should_trigger(self) -> bool:
        """Check if enough time has passed since last trigger (debounce)"""
        current_time = time.time()
        if current_time - self.last_trigger_time >= self.min_trigger_interval:
            self.last_trigger_time = current_time
            return True
        return False
    
    def _trigger_callback(self):
        """Trigger the callback in a separate thread"""
        if self.callback:
            try:
                print(f"🎹 Hotkey triggered: {self.current_config.display_name}")
                threading.Thread(target=self.callback, daemon=True).start()
            except Exception as e:
                print(f"Error in hotkey callback: {e}")
    
    def stop_listening(self):
        """Stop listening for hotkeys"""
        self.is_listening = False
        
        # Stop Win32 thread
        if self.hotkey_thread:
            self.stop_thread = True
            self.hotkey_thread = None
        
        # Stop keyboard library
        if self.keyboard_available and self.keyboard:
            try:
                self.keyboard.unhook_all()
            except:
                pass
        
        # Stop pynput listeners
        if hasattr(self, 'key_listener') and self.key_listener:
            try:
                self.key_listener.stop()
                self.key_listener = None
            except:
                pass
        
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            try:
                self.mouse_listener.stop()
                self.mouse_listener = None
            except:
                pass
        
        self.active_method = None
        print("🔇 Hotkey listening stopped")
    
    def get_status(self) -> dict:
        """Get current status information"""
        return {
            'is_listening': self.is_listening,
            'active_method': self.active_method.value if self.active_method else None,
            'current_hotkey': self.current_config.display_name if self.current_config else None,
            'keyboard_available': self.keyboard_available,
            'pynput_available': self.pynput_available,
            'win32_available': self.windows_api is not None
        }