"""
Hotkey configuration dialog with live capture and preset options
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Optional

from models.hotkey import HotkeyConfig, HotkeyValidator, KEYBOARD_PRESETS, MOUSE_PRESETS


class HotkeyConfigDialog:
    """Dialog for configuring hotkeys with multiple input methods"""
    
    def __init__(self, parent, current_hotkey: HotkeyConfig):
        self.parent = parent
        self.current_hotkey = current_hotkey
        self.result: Optional[HotkeyConfig] = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("🔧 Configure Hotkey")
        self.dialog.geometry("550x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center dialog
        self._center_dialog()
        
        # Create UI
        self._create_ui()
        
        # Focus dialog
        self.dialog.focus_set()
    
    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎹 Choose Your Cycling Hotkey", 
                               font=('Segoe UI', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Current hotkey display
        self._create_current_hotkey_section(main_frame)
        
        # Preset sections
        self._create_keyboard_presets(main_frame)
        self._create_mouse_presets(main_frame)
        
        # Custom input section
        self._create_custom_input_section(main_frame)
        
        # Live capture section
        self._create_capture_section(main_frame)
        
        # Bottom buttons
        self._create_buttons(main_frame)
    
    def _create_current_hotkey_section(self, parent):
        """Create current hotkey display section"""
        current_frame = ttk.LabelFrame(parent, text="Current Hotkey", padding="15")
        current_frame.pack(fill=tk.X, pady=(0, 20))
        
        current_text = f"Currently using: {self.current_hotkey.display_name}"
        current_label = ttk.Label(current_frame, text=current_text, 
                                 font=('Segoe UI', 12, 'bold'), foreground='blue')
        current_label.pack()
        
        # Show hotkey details
        details_text = f"Type: {self.current_hotkey.hotkey_type.value.title()}"
        if self.current_hotkey.modifiers:
            details_text += f" | Modifiers: {', '.join(m.value.title() for m in self.current_hotkey.modifiers)}"
        details_text += f" | Key: {self.current_hotkey.main_key}"
        
        details_label = ttk.Label(current_frame, text=details_text, 
                                 font=('Segoe UI', 9), foreground='gray')
        details_label.pack(pady=(5, 0))
    
    def _create_keyboard_presets(self, parent):
        """Create keyboard preset buttons"""
        keyboard_frame = ttk.LabelFrame(parent, text="⌨️ Keyboard Presets", padding="15")
        keyboard_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create grid of preset buttons
        for i, (display, value) in enumerate(KEYBOARD_PRESETS):
            row = i // 5
            col = i % 5
            
            btn = ttk.Button(keyboard_frame, text=display, width=12,
                           command=lambda v=value, d=display: self._set_preset_hotkey(v, d))
            btn.grid(row=row, column=col, padx=3, pady=3)
    
    def _create_mouse_presets(self, parent):
        """Create mouse preset buttons"""
        mouse_frame = ttk.LabelFrame(parent, text="🖱️ Mouse Button Presets", padding="15")
        mouse_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create grid of mouse preset buttons
        for i, (display, value) in enumerate(MOUSE_PRESETS):
            row = i // 5
            col = i % 5
            
            btn = ttk.Button(mouse_frame, text=display, width=12,
                           command=lambda v=value, d=display: self._set_preset_hotkey(v, d))
            btn.grid(row=row, column=col, padx=3, pady=3)
    
    def _create_custom_input_section(self, parent):
        """Create custom hotkey input section"""
        custom_frame = ttk.LabelFrame(parent, text="✏️ Custom Hotkey", padding="15")
        custom_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Instructions
        instructions = ttk.Label(custom_frame, 
                                text="Enter custom hotkey combination:",
                                font=('Segoe UI', 10))
        instructions.pack(anchor=tk.W)
        
        examples = ttk.Label(custom_frame, 
                            text="Examples: ctrl+j, alt+f5, shift+mouse4, ctrl+alt+x, f12",
                            font=('Segoe UI', 9), foreground='gray')
        examples.pack(anchor=tk.W, pady=(2, 10))
        
        # Input frame
        input_frame = ttk.Frame(custom_frame)
        input_frame.pack(fill=tk.X)
        
        self.custom_var = tk.StringVar(value=self.current_hotkey.raw_value)
        custom_entry = ttk.Entry(input_frame, textvariable=self.custom_var, 
                                font=('Segoe UI', 10), width=25)
        custom_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        test_btn = ttk.Button(input_frame, text="🧪 Test", 
                             command=self._test_custom_hotkey)
        test_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        set_btn = ttk.Button(input_frame, text="✅ Set Custom", 
                            command=self._set_custom_hotkey)
        set_btn.pack(side=tk.LEFT)
    
    def _create_capture_section(self, parent):
        """Create live hotkey capture section"""
        capture_frame = ttk.LabelFrame(parent, text="🎯 Live Hotkey Capture", padding="15")
        capture_frame.pack(fill=tk.X, pady=(0, 20))
        
        instructions = ttk.Label(capture_frame, 
                                text="Click the button below and press your desired hotkey combination:",
                                font=('Segoe UI', 10))
        instructions.pack(anchor=tk.W, pady=(0, 10))
        
        self.capture_button = ttk.Button(capture_frame, text="🎤 Click & Press Keys", 
                                        command=self._start_capture)
        self.capture_button.pack(pady=(0, 10))
        
        self.capture_result = ttk.Label(capture_frame, text="", 
                                       font=('Segoe UI', 10, 'bold'))
        self.capture_result.pack()
    
    def _create_buttons(self, parent):
        """Create bottom buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Left side - Reset button
        ttk.Button(button_frame, text="🔄 Reset to Default", 
                  command=self._reset_to_default).pack(side=tk.LEFT)
        
        # Right side - OK/Cancel buttons
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self._cancel).pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="✅ OK", 
                  command=self._ok).pack(side=tk.RIGHT, padx=(0, 10))
    
    def _set_preset_hotkey(self, hotkey_value: str, display_name: str):
        """Set a preset hotkey"""
        try:
            config = HotkeyConfig.parse(hotkey_value)
            self.result = config
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid preset hotkey: {e}", parent=self.dialog)
    
    def _test_custom_hotkey(self):
        """Test custom hotkey input"""
        hotkey_text = self.custom_var.get().strip()
        
        if not hotkey_text:
            messagebox.showwarning("Empty Input", "Please enter a hotkey combination to test.", 
                                 parent=self.dialog)
            return
        
        error = HotkeyValidator.get_validation_error(hotkey_text)
        
        if error:
            messagebox.showerror("Invalid Hotkey", f"❌ {error}\n\nValid examples:\n"
                               f"• ctrl+j\n• alt+mouse5\n• shift+f3\n• ctrl+alt+x", 
                               parent=self.dialog)
        else:
            messagebox.showinfo("Valid Hotkey", f"✅ '{hotkey_text}' is a valid hotkey format!", 
                              parent=self.dialog)
    
    def _set_custom_hotkey(self):
        """Set custom hotkey"""
        hotkey_text = self.custom_var.get().strip()
        
        if not hotkey_text:
            messagebox.showwarning("Empty Input", "Please enter a hotkey combination.", 
                                 parent=self.dialog)
            return
        
        error = HotkeyValidator.get_validation_error(hotkey_text)
        
        if error:
            messagebox.showerror("Invalid Hotkey", f"❌ {error}", parent=self.dialog)
            return
        
        try:
            config = HotkeyConfig.parse(hotkey_text)
            self.result = config
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse hotkey: {e}", parent=self.dialog)
    
    def _start_capture(self):
        """Start live hotkey capture"""
        self.capture_button.config(text="🎤 Press your hotkey now...", state=tk.DISABLED)
        self.capture_result.config(text="Waiting for input...", foreground="orange")
        
        # Start capture in background thread
        capture_thread = threading.Thread(target=self._capture_thread, daemon=True)
        capture_thread.start()
    
    def _capture_thread(self):
        """Background thread for hotkey capture"""
        try:
            # Import pynput for capture
            import pynput.keyboard as pynput_keyboard
            import pynput.mouse as pynput_mouse
            
            captured_keys = []
            pressed_keys = set()
            capture_timeout = 10.0  # 10 second timeout
            
            def on_press(key):
                pressed_keys.add(key)
            
            def on_release(key):
                if key in pressed_keys:
                    pressed_keys.remove(key)
                
                # If all keys released and we have a combination, stop
                if not pressed_keys and captured_keys:
                    return False
            
            def on_click(x, y, button, pressed):
                if pressed:
                    if button == pynput_mouse.Button.middle:
                        captured_keys.append('middle')
                    elif button == pynput_mouse.Button.x1:
                        captured_keys.append('mouse4')
                    elif button == pynput_mouse.Button.x2:
                        captured_keys.append('mouse5')
                    return False  # Stop on mouse click
            
            # Start listeners
            keyboard_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
            mouse_listener = pynput_mouse.Listener(on_click=on_click)
            
            keyboard_listener.start()
            mouse_listener.start()
            
            # Wait for capture with timeout
            start_time = time.time()
            while (keyboard_listener.running or mouse_listener.running) and (time.time() - start_time < capture_timeout):
                time.sleep(0.1)
                
                # Check for keyboard combination
                if pressed_keys and not captured_keys:
                    modifiers = []
                    main_key = None
                    
                    for key in pressed_keys:
                        if key == pynput_keyboard.Key.ctrl_l or key == pynput_keyboard.Key.ctrl_r:
                            modifiers.append('ctrl')
                        elif key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                            modifiers.append('alt')
                        elif key == pynput_keyboard.Key.shift_l or key == pynput_keyboard.Key.shift_r:
                            modifiers.append('shift')
                        elif hasattr(key, 'char') and key.char:
                            main_key = key.char.lower()
                        elif hasattr(key, 'name'):
                            main_key = key.name.lower()
                    
                    if main_key:
                        captured_keys = list(set(modifiers)) + [main_key]
            
            # Clean up listeners
            try:
                keyboard_listener.stop()
                mouse_listener.stop()
            except:
                pass
            
            # Update UI in main thread
            self.dialog.after(0, self._capture_complete, captured_keys)
            
        except Exception as e:
            self.dialog.after(0, self._capture_error, str(e))
    
    def _capture_complete(self, captured_keys):
        """Handle capture completion"""
        if captured_keys:
            hotkey_str = '+'.join(captured_keys)
            try:
                config = HotkeyConfig.parse(hotkey_str)
                display_str = config.display_name
                
                self.capture_result.config(text=f"Captured: {display_str}", foreground="green")
                self.custom_var.set(hotkey_str)
                
            except Exception as e:
                self.capture_result.config(text=f"Invalid combination: {e}", foreground="red")
        else:
            self.capture_result.config(text="No hotkey captured (timeout)", foreground="red")
        
        # Re-enable button
        self.capture_button.config(text="🎤 Click & Press Keys", state=tk.NORMAL)
    
    def _capture_error(self, error_msg):
        """Handle capture error"""
        self.capture_result.config(text=f"Capture failed: {error_msg}", foreground="red")
        self.capture_button.config(text="🎤 Click & Press Keys", state=tk.NORMAL)
    
    def _reset_to_default(self):
        """Reset to default hotkey"""
        try:
            default_config = HotkeyConfig.parse("ctrl+tab")
            self.result = default_config
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset: {e}", parent=self.dialog)
    
    def _ok(self):
        """OK button handler"""
        # Use current hotkey if no new one was set
        if self.result is None:
            self.result = self.current_hotkey
        self.dialog.destroy()
    
    def _cancel(self):
        """Cancel button handler"""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[HotkeyConfig]:
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result