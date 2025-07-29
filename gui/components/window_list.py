"""
Window list widget for selecting and ordering game windows
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable, Dict

from models.game_window import GameWindow
from models.profile import Profile


class WindowListWidget(ttk.Frame):
    """Custom widget for displaying and managing game windows"""
    
    def __init__(self, parent, on_selection_changed: Optional[Callable] = None):
        super().__init__(parent)
        
        self.windows: List[GameWindow] = []
        self.window_vars: List[tk.BooleanVar] = []
        self.order_vars: List[tk.StringVar] = []
        self.on_selection_changed = on_selection_changed
        
        self._create_widget()
    
    def _create_widget(self):
        """Create the widget layout"""
        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Create scrollable area
        self._create_scrollable_area()
        
        # Create header and empty state
        self._create_header()
        self._show_empty_state()
    
    def _create_scrollable_area(self):
        """Create scrollable canvas area"""
        # Canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Mouse wheel scrolling
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """Bind mouse wheel scrolling"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind to canvas and all child widgets
        def bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            for child in widget.winfo_children():
                bind_to_mousewheel(child)
        
        bind_to_mousewheel(self.canvas)
    
    def _create_header(self):
        """Create the column headers"""
        self.header_frame = ttk.Frame(self.scrollable_frame)
        self.header_frame.pack(fill=tk.X, padx=5, pady=(5, 10))
        
        # Column headers
        ttk.Label(self.header_frame, text="Select", font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=0, padx=(10, 20), sticky=tk.W)
        ttk.Label(self.header_frame, text="Order", font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=1, padx=(0, 20), sticky=tk.W)
        ttk.Label(self.header_frame, text="Game", font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=2, padx=(0, 20), sticky=tk.W)
        ttk.Label(self.header_frame, text="Character/Window", font=('Segoe UI', 9, 'bold')).grid(
            row=0, column=3, padx=(0, 20), sticky=tk.W)
    
    def _show_empty_state(self):
        """Show empty state message"""
        self.empty_frame = ttk.Frame(self.scrollable_frame)
        self.empty_frame.pack(fill=tk.BOTH, expand=True, pady=50)
        
        empty_label = ttk.Label(self.empty_frame, 
                               text="No game windows detected.\n\nMake sure Dofus or Wakfu is running\nand click 'Refresh Windows'.",
                               font=('Segoe UI', 11), foreground='gray', justify=tk.CENTER)
        empty_label.pack(expand=True)
    
    def set_windows(self, windows: List[GameWindow]):
        """Set the list of windows to display"""
        self.windows = windows.copy()
        self._clear_window_entries()
        
        if not windows:
            self._show_empty_state()
            return
        
        # Hide empty state
        if hasattr(self, 'empty_frame'):
            self.empty_frame.destroy()
        
        # Create window entries
        self.window_vars = []
        self.order_vars = []
        
        for i, window in enumerate(windows):
            self._create_window_entry(window, i)
        
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _clear_window_entries(self):
        """Clear all window entries"""
        # Destroy all children except header
        for child in self.scrollable_frame.winfo_children():
            if child != self.header_frame:
                child.destroy()
        
        self.window_vars = []
        self.order_vars = []
    
    def _create_window_entry(self, window: GameWindow, index: int):
        """Create a single window entry"""
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Selection checkbox
        var = tk.BooleanVar()
        checkbox = ttk.Checkbutton(frame, variable=var, command=self._on_selection_change)
        checkbox.grid(row=0, column=0, padx=(10, 20))
        self.window_vars.append(var)
        
        # Order entry
        order_var = tk.StringVar()
        order_entry = ttk.Entry(frame, textvariable=order_var, width=5, 
                               justify=tk.CENTER, state=tk.DISABLED)
        order_entry.grid(row=0, column=1, padx=(0, 20))
        self.order_vars.append(order_var)
        
        # Enable/disable order entry based on checkbox
        def on_checkbox_change():
            if var.get():
                order_entry.config(state=tk.NORMAL)
                if not order_var.get():
                    # Auto-assign order number
                    self._auto_assign_order(index)
            else:
                order_entry.config(state=tk.DISABLED)
                order_var.set("")
            
            if self.on_selection_changed:
                self.on_selection_changed()
        
        var.trace('w', lambda *args: on_checkbox_change())
        order_var.trace('w', lambda *args: self._on_selection_change())
        
        # Game type with icon
        game_icon = "🎮" if window.game_type == "dofus" else "🏰" if window.game_type == "wakfu" else "⚡"
        game_text = f"{game_icon} {window.game_type.title()}"
        game_label = ttk.Label(frame, text=game_text, font=('Segoe UI', 9, 'bold'))
        game_label.grid(row=0, column=2, padx=(0, 20), sticky=tk.W)
        
        # Character/window name
        display_text = window.get_display_name()
        if len(display_text) > 60:
            display_text = display_text[:57] + "..."
        
        info_label = ttk.Label(frame, text=display_text, font=('Segoe UI', 9))
        info_label.grid(row=0, column=3, sticky=tk.W)
        
        # Add tooltip with full window information
        self._create_tooltip(info_label, self._get_window_tooltip(window))
    
    def _create_tooltip(self, widget, text: str):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, background="lightyellow", 
                             relief=tk.SOLID, borderwidth=1, font=('Segoe UI', 8),
                             wraplength=300)
            label.pack(padx=5, pady=5)
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def _get_window_tooltip(self, window: GameWindow) -> str:
        """Generate tooltip text for a window"""
        tooltip = f"Game: {window.game_type.title()}\n"
        tooltip += f"Character: {window.character_name}\n"
        tooltip += f"Window Title: {window.title}\n"
        tooltip += f"Process: {window.process_name} (PID: {window.process_id})\n"
        tooltip += f"Window Handle: {window.hwnd}"
        return tooltip
    
    def _auto_assign_order(self, index: int):
        """Auto-assign an order number to a window"""
        # Find the next available order number
        used_orders = set()
        for order_var in self.order_vars:
            if order_var.get().isdigit():
                used_orders.add(int(order_var.get()))
        
        next_order = 1
        while next_order in used_orders:
            next_order += 1
        
        self.order_vars[index].set(str(next_order))
    
    def _on_selection_change(self):
        """Handle selection changes"""
        if self.on_selection_changed:
            self.on_selection_changed()
    
    def get_selected_windows(self) -> List[GameWindow]:
        """Get list of selected windows"""
        selected = []
        for i, var in enumerate(self.window_vars):
            if var.get() and i < len(self.windows):
                selected.append(self.windows[i])
        return selected
    
    def get_selected_windows_with_order(self) -> List[GameWindow]:
        """Get selected windows with their order numbers set"""
        selected = []
        
        for i, (window_var, order_var) in enumerate(zip(self.window_vars, self.order_vars)):
            if window_var.get() and i < len(self.windows):
                try:
                    order = int(order_var.get())
                    if order > 0:
                        window = self.windows[i]
                        window.order = order
                        selected.append(window)
                except (ValueError, IndexError):
                    pass
        
        # Sort by order
        selected.sort(key=lambda w: w.order)
        return selected
    
    def clear_selection(self):
        """Clear all selections"""
        for var in self.window_vars:
            var.set(False)
        for var in self.order_vars:
            var.set("")
    
    def select_all(self):
        """Select all windows"""
        for var in self.window_vars:
            var.set(True)
        # Auto-assign orders will be triggered by the checkbox events
    
    def auto_assign_orders(self):
        """Auto-assign order numbers to all selected windows"""
        order = 1
        for i, var in enumerate(self.window_vars):
            if var.get():
                self.order_vars[i].set(str(order))
                order += 1
    
    def apply_profile(self, profile: Profile) -> int:
        """Apply a profile to the current window list"""
        # Clear current selection
        self.clear_selection()
        
        matched_count = 0
        
        # Try to match profile windows with current windows
        for profile_window in profile.windows:
            for i, current_window in enumerate(self.windows):
                # Match by character name first, then by title similarity
                if self._windows_match(profile_window, current_window):
                    self.window_vars[i].set(True)
                    self.order_vars[i].set(str(profile_window.order))
                    matched_count += 1
                    break
        
        return matched_count
    
    def _windows_match(self, profile_window, current_window: GameWindow) -> bool:
        """Check if a profile window matches a current window"""
        # Match by character name (preferred)
        if (hasattr(profile_window, 'character_name') and profile_window.character_name and 
            current_window.character_name and 
            profile_window.character_name.lower() in current_window.character_name.lower()):
            return True
        
        # Match by title similarity
        if hasattr(profile_window, 'title') and profile_window.title:
            if (profile_window.title.lower() in current_window.title.lower() or 
                current_window.title.lower() in profile_window.title.lower()):
                return True
        
        # Match by game type and partial name
        if (hasattr(profile_window, 'game_type') and 
            profile_window.game_type == current_window.game_type):
            # If same game type, check for any character name overlap
            if (hasattr(profile_window, 'character_name') and profile_window.character_name and
                current_window.character_name):
                # Fuzzy matching for character names
                profile_name = profile_window.character_name.lower().strip()
                current_name = current_window.character_name.lower().strip()
                
                # Check if one name contains the other
                if profile_name in current_name or current_name in profile_name:
                    return True
                
                # Check if names are similar (common prefixes/suffixes)
                if len(profile_name) > 3 and len(current_name) > 3:
                    if (profile_name.startswith(current_name[:3]) or 
                        current_name.startswith(profile_name[:3])):
                        return True
        
        return False
    
    def get_selection_summary(self) -> str:
        """Get a summary of the current selection"""
        selected = self.get_selected_windows_with_order()
        
        if not selected:
            return "No windows selected"
        
        summary = f"{len(selected)} windows selected: "
        names = [w.get_short_title(15) for w in selected[:3]]
        
        if len(selected) > 3:
            names.append(f"... and {len(selected) - 3} more")
        
        return summary + ", ".join(names)
    
    def validate_selection(self) -> List[str]:
        """Validate the current selection and return any errors"""
        errors = []
        selected = self.get_selected_windows()
        
        if not selected:
            errors.append("No windows selected")
            return errors
        
        # Check orders
        orders = []
        for i, (window_var, order_var) in enumerate(zip(self.window_vars, self.order_vars)):
            if window_var.get():
                order_text = order_var.get().strip()
                if not order_text:
                    errors.append(f"Window {i+1} is selected but has no order number")
                    continue
                
                try:
                    order = int(order_text)
                    if order <= 0:
                        errors.append(f"Window {i+1} has invalid order number: {order}")
                    else:
                        orders.append(order)
                except ValueError:
                    errors.append(f"Window {i+1} has non-numeric order: {order_text}")
        
        # Check for duplicate orders
        if len(orders) != len(set(orders)):
            errors.append("Duplicate order numbers found")
        
        return errors
    
    def get_window_at_index(self, index: int) -> Optional[GameWindow]:
        """Get window at specific index"""
        if 0 <= index < len(self.windows):
            return self.windows[index]
        return None
    
    def set_window_selected(self, index: int, selected: bool):
        """Set selection state for a specific window"""
        if 0 <= index < len(self.window_vars):
            self.window_vars[index].set(selected)
    
    def set_window_order(self, index: int, order: int):
        """Set order for a specific window"""
        if 0 <= index < len(self.order_vars):
            self.order_vars[index].set(str(order))
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the current window list"""
        total_windows = len(self.windows)
        selected_windows = len(self.get_selected_windows())
        
        game_counts = {}
        for window in self.windows:
            game_type = window.game_type
            game_counts[game_type] = game_counts.get(game_type, 0) + 1
        
        return {
            'total_windows': total_windows,
            'selected_windows': selected_windows,
            'dofus_windows': game_counts.get('dofus', 0),
            'wakfu_windows': game_counts.get('wakfu', 0),
            'unique_characters': len(set(w.character_name for w in self.windows if w.character_name))
        }
    
    def refresh_display(self):
        """Refresh the display without changing the window list"""
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def get_window_by_character(self, character_name: str) -> Optional[GameWindow]:
        """Find a window by character name"""
        for window in self.windows:
            if window.character_name.lower() == character_name.lower():
                return window
        return None
    
    def get_selected_character_names(self) -> List[str]:
        """Get list of selected character names"""
        selected_windows = self.get_selected_windows()
        return [w.character_name for w in selected_windows if w.character_name]
    
    def has_selection(self) -> bool:
        """Check if any windows are selected"""
        return any(var.get() for var in self.window_vars)
    
    def get_selection_count(self) -> int:
        """Get number of selected windows"""
        return sum(1 for var in self.window_vars if var.get())
    
    def sort_windows_by_character(self):
        """Sort windows by character name"""
        if not self.windows:
            return
        
        # Sort windows while preserving current selection
        selected_indices = [i for i, var in enumerate(self.window_vars) if var.get()]
        selected_orders = [self.order_vars[i].get() for i in selected_indices]
        
        # Sort windows by character name
        sorted_pairs = sorted(enumerate(self.windows), key=lambda x: x[1].character_name.lower())
        sorted_windows = [pair[1] for pair in sorted_pairs]
        old_to_new_index = {old_idx: new_idx for new_idx, (old_idx, _) in enumerate(sorted_pairs)}
        
        # Update windows list
        self.windows = sorted_windows
        
        # Recreate the display
        self.set_windows(self.windows)
        
        # Restore selection with new indices
        for old_idx, order in zip(selected_indices, selected_orders):
            if old_idx in old_to_new_index:
                new_idx = old_to_new_index[old_idx]
                if new_idx < len(self.window_vars):
                    self.window_vars[new_idx].set(True)
                    self.order_vars[new_idx].set(order)