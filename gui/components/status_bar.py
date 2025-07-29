"""
Status bar widget for displaying application status and progress
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional


class StatusBarWidget(ttk.Frame):
    """Custom status bar widget with message display and progress indication"""
    
    def __init__(self, parent):
        super().__init__(parent, relief=tk.SUNKEN, borderwidth=1)
        
        self.current_message = ""
        self.is_busy = False
        self._create_widget()
    
    def _create_widget(self):
        """Create the status bar layout"""
        # Configure grid weights
        self.columnconfigure(0, weight=1)
        
        # Main status label
        self.status_label = ttk.Label(self, text="Ready", anchor=tk.W, 
                                     font=('Segoe UI', 9))
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Progress bar (hidden by default)
        self.progress_bar = ttk.Progressbar(self, mode='indeterminate', length=100)
        self.progress_bar.grid(row=0, column=1, sticky=tk.E, padx=(5, 5))
        self.progress_bar.grid_remove()  # Hide initially
        
        # Additional info label (right side)
        self.info_label = ttk.Label(self, text="", anchor=tk.E, 
                                   font=('Segoe UI', 8), foreground='gray')
        self.info_label.grid(row=0, column=2, sticky=tk.E, padx=(5, 5))
    
    def set_message(self, message: str, show_progress: bool = False):
        """Set the main status message"""
        self.current_message = message
        self.status_label.config(text=message)
        
        if show_progress and not self.is_busy:
            self.show_progress()
        elif not show_progress and self.is_busy:
            self.hide_progress()
    
    def set_info(self, info: str):
        """Set additional info text (shown on the right)"""
        self.info_label.config(text=info)
    
    def show_progress(self):
        """Show progress bar with indeterminate animation"""
        if not self.is_busy:
            self.is_busy = True
            self.progress_bar.grid()
            self.progress_bar.start(10)  # Animation speed
    
    def hide_progress(self):
        """Hide progress bar"""
        if self.is_busy:
            self.is_busy = False
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
    
    def set_temporary_message(self, message: str, duration: float = 3.0):
        """Set a temporary message that reverts after duration"""
        original_message = self.current_message
        self.set_message(message)
        
        def revert_message():
            time.sleep(duration)
            if self.current_message == message:  # Only revert if message wasn't changed
                self.set_message(original_message)
        
        threading.Thread(target=revert_message, daemon=True).start()
    
    def set_success_message(self, message: str, duration: float = 3.0):
        """Set a success message with green color"""
        original_fg = self.status_label.cget('foreground')
        self.status_label.config(foreground='green')
        self.set_temporary_message(f"✅ {message}", duration)
        
        def revert_color():
            time.sleep(duration)
            self.status_label.config(foreground=original_fg)
        
        threading.Thread(target=revert_color, daemon=True).start()
    
    def set_error_message(self, message: str, duration: float = 5.0):
        """Set an error message with red color"""
        original_fg = self.status_label.cget('foreground')
        self.status_label.config(foreground='red')
        self.set_temporary_message(f"❌ {message}", duration)
        
        def revert_color():
            time.sleep(duration)
            self.status_label.config(foreground=original_fg)
        
        threading.Thread(target=revert_color, daemon=True).start()
    
    def set_warning_message(self, message: str, duration: float = 4.0):
        """Set a warning message with orange color"""
        original_fg = self.status_label.cget('foreground')
        self.status_label.config(foreground='orange')
        self.set_temporary_message(f"⚠️ {message}", duration)
        
        def revert_color():
            time.sleep(duration)
            self.status_label.config(foreground=original_fg)
        
        threading.Thread(target=revert_color, daemon=True).start()
    
    def clear(self):
        """Clear the status bar"""
        self.set_message("")
        self.set_info("")
        self.hide_progress()
    
    def get_current_message(self) -> str:
        """Get the current status message"""
        return self.current_message