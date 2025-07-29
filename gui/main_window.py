"""
Main application window and GUI controller
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import List, Optional

from models.game_window import GameWindow
from models.profile import Profile, WindowProfile
from models.hotkey import HotkeyConfig
from core.window_detector import GameWindowDetector
from core.window_cycler import WindowCycler  
from core.config_manager import ConfigManager
from gui.hotkey_dialog import HotkeyConfigDialog
from gui.profile_dialog import ProfileManagerDialog
from gui.components.window_list import WindowListWidget
from gui.components.status_bar import StatusBarWidget


class WindowCyclerApp:
    """Main application window and controller"""
    
    def __init__(self):
        # Initialize core components
        self.detector = GameWindowDetector()
        self.cycler = WindowCycler()
        self.config_manager = ConfigManager()
        
        # GUI state
        self.detected_windows: List[GameWindow] = []
        self.current_hotkey = HotkeyConfig.parse("ctrl+tab")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("🎮 Dofus/Wakfu Window Cycler")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Load settings
        self._load_settings()
        
        # Create GUI
        self._create_gui()
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Initial window detection
        self.refresh_windows()
    
    def _load_settings(self):
        """Load application settings"""
        settings = self.config_manager.load_settings()
        
        # Apply window geometry if saved
        if settings.get('window_geometry'):
            try:
                self.root.geometry(settings['window_geometry'])
            except:
                pass
    
    def _save_settings(self):
        """Save application settings"""
        settings = {
            'window_geometry': self.root.geometry(),
        }
        self.config_manager.save_settings(settings)
    
    def _create_gui(self):
        """Create the main GUI interface"""
        # Configure styles
        self._configure_styles()
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Window list gets extra space
        
        # Create GUI sections
        self._create_header(main_frame)
        self._create_toolbar(main_frame)
        self._create_window_list(main_frame)
        self._create_controls(main_frame)
        self._create_status_bar(main_frame)
    
    def _configure_styles(self):
        """Configure TTK styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom button styles
        style.configure('Accent.TButton', font=('Segoe UI', 9, 'bold'))
        style.configure('Success.TButton', background='#28a745')
        style.configure('Danger.TButton', background='#dc3545')
    
    def _create_header(self, parent):
        """Create the application header"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="🎮 Dofus/Wakfu Window Cycler", 
                               font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Version/Info
        info_label = ttk.Label(header_frame, text="v2.0 - Enhanced Edition", 
                              font=('Segoe UI', 9), foreground='gray')
        info_label.grid(row=0, column=2, sticky=tk.E)
        
        # Subtitle
        subtitle = ttk.Label(header_frame, 
                            text="Select game windows, configure hotkeys, and cycle efficiently through your characters",
                            font=('Segoe UI', 10))
        subtitle.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
    
    def _create_toolbar(self, parent):
        """Create the main toolbar"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Left side buttons
        left_frame = ttk.Frame(toolbar_frame)
        left_frame.pack(side=tk.LEFT)
        
        ttk.Button(left_frame, text="🔄 Refresh Windows", 
                  command=self.refresh_windows).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(left_frame, text="💾 Manage Profiles", 
                  command=self.show_profile_manager).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(left_frame, text="⚙️ Settings", 
                  command=self.show_settings).pack(side=tk.LEFT)
        
        # Right side - statistics
        right_frame = ttk.Frame(toolbar_frame)
        right_frame.pack(side=tk.RIGHT)
        
        self.stats_label = ttk.Label(right_frame, text="", font=('Segoe UI', 9))
        self.stats_label.pack(side=tk.RIGHT)
    
    def _create_window_list(self, parent):
        """Create the window selection list"""
        list_frame = ttk.LabelFrame(parent, text="🪟 Detected Game Windows", padding="10")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create window list widget
        self.window_list = WindowListWidget(list_frame, on_selection_changed=self._on_window_selection_changed)
        self.window_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _create_controls(self, parent):
        """Create the control panel"""
        control_frame = ttk.LabelFrame(parent, text="🎹 Cycling Controls", padding="10")
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(2, weight=1)
        
        # Hotkey configuration
        ttk.Label(control_frame, text="Hotkey:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.hotkey_var = tk.StringVar(value=self.current_hotkey.display_name)
        self.hotkey_display = ttk.Entry(control_frame, textvariable=self.hotkey_var, 
                                       width=20, state="readonly")
        self.hotkey_display.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(control_frame, text="🔧 Change", 
                  command=self.show_hotkey_dialog).grid(row=0, column=2, sticky=tk.W, padx=(0, 20))
        
        # Control buttons
        self.start_button = ttk.Button(control_frame, text="▶️ Start Cycling", 
                                      command=self.start_cycling, style='Success.TButton')
        self.start_button.grid(row=0, column=3, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="⏹️ Stop", 
                                     command=self.stop_cycling, state=tk.DISABLED, 
                                     style='Danger.TButton')
        self.stop_button.grid(row=0, column=4)
        
        # Quick actions
        ttk.Button(control_frame, text="🧹 Clear Selection", 
                  command=self.clear_selection).grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        ttk.Button(control_frame, text="☑️ Select All", 
                  command=self.select_all_windows).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        ttk.Button(control_frame, text="🔢 Auto Order", 
                  command=self.auto_order_windows).grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
    
    def _create_status_bar(self, parent):
        """Create the status bar"""
        self.status_bar = StatusBarWidget(parent)
        self.status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.status_bar.set_message("Ready - Refresh windows to begin")
    
    def _setup_callbacks(self):
        """Set up event callbacks"""
        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Cycler callbacks
        self.cycler.on_window_activated = self._on_window_activated
        self.cycler.on_window_removed = self._on_window_removed
        self.cycler.on_cycling_stopped = self._on_cycling_stopped
    
    # ===============================================================================
    # WINDOW MANAGEMENT
    # ===============================================================================
    
    def refresh_windows(self):
        """Refresh the list of detected game windows"""
        try:
            # Show loading in status
            self.status_bar.set_message("🔍 Scanning for game windows...")
            self.root.update()
            
            # Detect windows
            self.detected_windows = self.detector.get_all_game_windows()
            
            # Update display
            self.window_list.set_windows(self.detected_windows)
            
            # Update statistics
            self._update_statistics()
            
            # Update status
            if self.detected_windows:
                self.status_bar.set_message(f"Found {len(self.detected_windows)} game windows")
            else:
                self.status_bar.set_message("No Dofus/Wakfu windows detected - make sure games are running")
            
        except Exception as e:
            self.status_bar.set_message(f"Error scanning windows: {e}")
            messagebox.showerror("Error", f"Failed to scan for game windows:\n{e}")
    
    def _update_statistics(self):
        """Update the statistics display"""
        if not self.detected_windows:
            self.stats_label.config(text="")
            return
        
        stats = self.detector.get_game_statistics()
        stats_text = f"Total: {stats['total_windows']} | "
        stats_text += f"Dofus: {stats['dofus_windows']} | "
        stats_text += f"Wakfu: {stats['wakfu_windows']} | "
        stats_text += f"Characters: {stats['unique_characters']}"
        
        self.stats_label.config(text=stats_text)
    
    def _on_window_selection_changed(self):
        """Handle window selection changes"""
        selected_count = len(self.window_list.get_selected_windows())
        
        # Update start button state
        if selected_count > 0:
            self.start_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.DISABLED)
        
        # Update status
        if selected_count > 0:
            self.status_bar.set_message(f"{selected_count} windows selected for cycling")
        else:
            self.status_bar.set_message("Select windows to enable cycling")
    
    # ===============================================================================
    # CYCLING CONTROL
    # ===============================================================================
    
    def start_cycling(self):
        """Start window cycling"""
        try:
            # Get selected windows
            selected_windows = self.window_list.get_selected_windows_with_order()
            
            if not selected_windows:
                messagebox.showwarning("No Selection", "Please select at least one window to cycle through.")
                return
            
            # Validate order uniqueness
            orders = [w.order for w in selected_windows]
            if len(orders) != len(set(orders)):
                messagebox.showerror("Invalid Order", "Window order numbers must be unique!")
                return
            
            # Set up cycling
            if not self.cycler.set_windows(selected_windows):
                messagebox.showerror("Setup Failed", "Failed to set up window cycling.")
                return
            
            # Set hotkey
            if not self.cycler.set_hotkey(self.current_hotkey):
                messagebox.showerror("Hotkey Failed", "Failed to set up hotkey. Try running as Administrator.")
                return
            
            # Start cycling
            if not self.cycler.start_cycling():
                messagebox.showerror("Start Failed", "Failed to start cycling system.")
                return
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Show success message
            messagebox.showinfo("Cycling Started", 
                               f"Window cycling is now active!\n\n"
                               f"• Selected {len(selected_windows)} windows\n"
                               f"• Press {self.current_hotkey.display_name} to cycle\n"
                               f"• Click 'Stop' to disable")
            
            self.status_bar.set_message(f"Cycling active - Press {self.current_hotkey.display_name} to cycle")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start cycling:\n{e}")
    
    def stop_cycling(self):
        """Stop window cycling"""
        try:
            self.cycler.stop_cycling()
            
            # Update UI
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.status_bar.set_message("Cycling stopped")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop cycling:\n{e}")
    
    def _on_window_activated(self, window: GameWindow):
        """Handle window activation event"""
        self.status_bar.set_message(f"Activated: {window.get_display_name()}")
    
    def _on_window_removed(self, window: GameWindow):
        """Handle window removal event"""
        self.status_bar.set_message(f"Removed invalid window: {window.get_display_name()}")
        # Refresh window list to reflect changes
        threading.Timer(1.0, self.refresh_windows).start()
    
    def _on_cycling_stopped(self):
        """Handle cycling stopped event"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    # ===============================================================================
    # SELECTION HELPERS
    # ===============================================================================
    
    def clear_selection(self):
        """Clear all window selections"""
        self.window_list.clear_selection()
        self.status_bar.set_message("Selection cleared")
    
    def select_all_windows(self):
        """Select all detected windows"""
        self.window_list.select_all()
        self.status_bar.set_message("All windows selected")
    
    def auto_order_windows(self):
        """Automatically assign order numbers to selected windows"""
        self.window_list.auto_assign_orders()
        self.status_bar.set_message("Order numbers assigned automatically")
    
    # ===============================================================================
    # DIALOG MANAGEMENT
    # ===============================================================================
    
    def show_hotkey_dialog(self):
        """Show hotkey configuration dialog"""
        dialog = HotkeyConfigDialog(self.root, self.current_hotkey)
        new_hotkey = dialog.show()
        
        if new_hotkey:
            self.current_hotkey = new_hotkey
            self.hotkey_var.set(new_hotkey.display_name)
            self.status_bar.set_message(f"Hotkey changed to: {new_hotkey.display_name}")
    
    def show_profile_manager(self):
        """Show profile management dialog"""
        # Get current selection for saving
        selected_windows = self.window_list.get_selected_windows_with_order()
        
        dialog = ProfileManagerDialog(self.root, self.config_manager, 
                                    current_selection=selected_windows,
                                    current_hotkey=self.current_hotkey)
        result = dialog.show()
        
        if result and result.get('action') == 'load':
            self._load_profile(result['profile'])
    
    def _load_profile(self, profile: Profile):
        """Load a profile and apply it to current windows"""
        try:
            # Try to match profile windows with current windows
            matched_count = self.window_list.apply_profile(profile)
            
            # Update hotkey
            if profile.hotkey:
                try:
                    self.current_hotkey = HotkeyConfig.parse(profile.hotkey)
                    self.hotkey_var.set(self.current_hotkey.display_name)
                except:
                    pass  # Keep current hotkey if parsing fails
            
            # Show result
            total_windows = len(profile.windows)
            if matched_count == total_windows:
                self.status_bar.set_message(f"Profile '{profile.name}' loaded successfully")
                messagebox.showinfo("Profile Loaded", 
                                   f"Profile loaded successfully!\n{matched_count} windows matched and configured.")
            else:
                self.status_bar.set_message(f"Profile partially loaded - {matched_count}/{total_windows} windows matched")
                messagebox.showwarning("Partial Match", 
                                      f"Profile partially loaded.\n"
                                      f"Matched {matched_count} out of {total_windows} windows.\n"
                                      f"Some windows may not be currently running.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile:\n{e}")
    
    def show_settings(self):
        """Show application settings dialog"""
        # TODO: Implement settings dialog
        messagebox.showinfo("Settings", "Settings dialog coming soon!")
    
    # ===============================================================================
    # APPLICATION LIFECYCLE
    # ===============================================================================
    
    def _on_closing(self):
        """Handle application closing"""
        try:
            # Stop cycling if active
            if self.cycler.is_cycling_active():
                self.cycler.stop_cycling()
            
            # Save settings
            self._save_settings()
            
            # Destroy window
            self.root.destroy()
            
        except Exception:
            # Force quit if there's an error
            self.root.quit()
    
    def run(self):
        """Start the application"""
        try:
            # Center window on screen
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f'{width}x{height}+{x}+{y}')
            
            # Start the GUI event loop
            print("🚀 Application started successfully")
            self.root.mainloop()
            
        except Exception as e:
            print(f"Application error: {e}")
            raise
    
    def get_cycling_status(self) -> dict:
        """Get current cycling status for debugging"""
        return {
            'is_active': self.cycler.is_cycling_active(),
            'window_count': self.cycler.get_window_count(),
            'current_window': str(self.cycler.get_current_window()) if self.cycler.get_current_window() else None,
            'hotkey': self.current_hotkey.display_name,
            'statistics': self.cycler.get_statistics()
        }