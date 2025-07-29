"""
Platform-specific utilities and compatibility checks
"""

import sys
import os
from typing import List, Optional


def check_platform_requirements() -> bool:
    """Check if the current platform is supported"""
    if sys.platform != "win32":
        print("❌ This application currently only supports Windows.")
        print("   Linux and Mac support coming soon!")
        return False
    return True


def check_dependencies() -> List[str]:
    """Check for required dependencies and return list of missing ones"""
    missing_deps = []
    
    # Check pywin32
    try:
        import win32gui, win32process, win32con, win32api
    except ImportError:
        missing_deps.append("pywin32")
    
    # Check psutil
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    # Check PIL/Pillow
    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing_deps.append("Pillow")
    
    # Check pynput
    try:
        import pynput
    except ImportError:
        missing_deps.append("pynput")
    
    # Check keyboard (optional)
    try:
        import keyboard
    except ImportError:
        # This is optional, so we don't add it to missing_deps
        pass
    
    return missing_deps


def get_app_data_dir() -> str:
    """Get the application data directory"""
    if sys.platform == "win32":
        app_data = os.path.expanduser("~/.dofus_wakfu_cycler")
    else:
        app_data = os.path.expanduser("~/.config/dofus_wakfu_cycler")
    
    os.makedirs(app_data, exist_ok=True)
    return app_data


def is_admin() -> bool:
    """Check if running with administrator privileges (Windows only)"""
    if sys.platform != "win32":
        return False
    
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def request_admin_privileges() -> bool:
    """Request administrator privileges (Windows only)"""
    if sys.platform != "win32":
        return False
    
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            # Re-run the program with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
    except:
        return False


def get_system_info() -> dict:
    """Get system information for debugging"""
    info = {
        'platform': sys.platform,
        'python_version': sys.version,
        'is_admin': is_admin() if sys.platform == "win32" else False,
        'app_data_dir': get_app_data_dir()
    }
    
    if sys.platform == "win32":
        try:
            import platform
            info['windows_version'] = platform.version()
            info['machine'] = platform.machine()
        except:
            pass
    
    return info


class WindowsAPI:
    """Windows API utilities wrapper"""
    
    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("WindowsAPI only available on Windows")
        
        import win32gui
        import win32process
        import win32con
        import win32api
        
        self.win32gui = win32gui
        self.win32process = win32process
        self.win32con = win32con
        self.win32api = win32api
    
    def enum_windows(self, callback):
        """Enumerate all windows"""
        return self.win32gui.EnumWindows(callback, [])
    
    def get_window_title(self, hwnd: int) -> str:
        """Get window title"""
        try:
            return self.win32gui.GetWindowText(hwnd)
        except:
            return ""
    
    def get_window_process_id(self, hwnd: int) -> Optional[int]:
        """Get process ID for window"""
        try:
            _, process_id = self.win32process.GetWindowThreadProcessId(hwnd)
            return process_id
        except:
            return None
    
    def is_window_visible(self, hwnd: int) -> bool:
        """Check if window is visible"""
        try:
            return bool(self.win32gui.IsWindowVisible(hwnd))
        except:
            return False
    
    def is_window_valid(self, hwnd: int) -> bool:
        """Check if window handle is valid"""
        try:
            return bool(self.win32gui.IsWindow(hwnd))
        except:
            return False
    
    def activate_window(self, hwnd: int) -> bool:
        """Activate a window with multiple fallback methods"""
        try:
            # Method 1: Check if minimized and restore
            try:
                placement = self.win32gui.GetWindowPlacement(hwnd)
                if placement[1] == self.win32con.SW_SHOWMINIMIZED:
                    self.win32gui.ShowWindow(hwnd, self.win32con.SW_RESTORE)
                    import time
                    time.sleep(0.1)
            except:
                pass
            
            # Method 2: Basic activation
            try:
                self.win32gui.SetForegroundWindow(hwnd)
                self.win32gui.BringWindowToTop(hwnd)
                self.win32gui.ShowWindow(hwnd, self.win32con.SW_SHOW)
            except:
                pass
            
            # Method 3: Advanced activation with thread attachment
            try:
                current_thread = self.win32api.GetCurrentThreadId()
                target_thread = self.win32process.GetWindowThreadProcessId(hwnd)[0]
                
                if current_thread != target_thread:
                    self.win32process.AttachThreadInput(current_thread, target_thread, True)
                    self.win32gui.SetForegroundWindow(hwnd)
                    self.win32gui.SetFocus(hwnd)
                    self.win32process.AttachThreadInput(current_thread, target_thread, False)
            except:
                pass
            
            # Verification
            try:
                import time
                time.sleep(0.05)
                foreground = self.win32gui.GetForegroundWindow()
                return foreground == hwnd
            except:
                return True  # Assume success if we can't verify
                
        except Exception as e:
            print(f"Window activation failed: {e}")
            return False


# Global Windows API instance (lazy-loaded)
_windows_api = None

def get_windows_api() -> Optional[WindowsAPI]:
    """Get the Windows API instance"""
    global _windows_api
    if _windows_api is None and sys.platform == "win32":
        try:
            _windows_api = WindowsAPI()
        except Exception as e:
            print(f"Failed to initialize Windows API: {e}")
    return _windows_api