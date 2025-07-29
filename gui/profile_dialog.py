"""
Profile management dialog for saving and loading window configurations
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Optional, Dict, Any
import time

from models.game_window import GameWindow
from models.profile import Profile, WindowProfile
from models.hotkey import HotkeyConfig
from core.config_manager import ConfigManager


class ProfileManagerDialog:
    """Dialog for managing profiles - save, load, delete, import, export"""
    
    def __init__(self, parent, config_manager: ConfigManager, 
                 current_selection: List[GameWindow] = None,
                 current_hotkey: HotkeyConfig = None):
        self.parent = parent
        self.config_manager = config_manager
        self.current_selection = current_selection or []
        self.current_hotkey = current_hotkey
        self.result: Optional[Dict[str, Any]] = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("💾 Profile Manager")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # Center dialog
        self._center_dialog()
        
        # Create UI
        self._create_ui()
        
        # Load profiles
        self._refresh_profile_list()
    
    def _center_dialog(self):
        """Center dialog on parent"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title and current selection info
        self._create_header(main_frame)
        
        # Profile list
        self._create_profile_list(main_frame)
        
        # Profile details
        self._create_profile_details(main_frame)
        
        # Action buttons
        self._create_action_buttons(main_frame)
        
        # Bottom buttons
        self._create_bottom_buttons(main_frame)
    
    def _create_header(self, parent):
        """Create header with title and current selection info"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(header_frame, text="💾 Profile Manager", 
                               font=('Segoe UI', 14, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Current selection info
        if self.current_selection:
            selection_text = f"Current selection: {len(self.current_selection)} windows"
            if self.current_hotkey:
                selection_text += f" | Hotkey: {self.current_hotkey.display_name}"
        else:
            selection_text = "No windows currently selected"
        
        selection_label = ttk.Label(header_frame, text=selection_text, 
                                   font=('Segoe UI', 9), foreground='gray')
        selection_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
    
    def _create_profile_list(self, parent):
        """Create profile list with scrollbar"""
        list_frame = ttk.LabelFrame(parent, text="📋 Saved Profiles", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create treeview for profiles
        columns = ('name', 'windows', 'hotkey', 'created')
        self.profile_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        self.profile_tree.heading('name', text='Profile Name')
        self.profile_tree.heading('windows', text='Windows')
        self.profile_tree.heading('hotkey', text='Hotkey')
        self.profile_tree.heading('created', text='Created')
        
        self.profile_tree.column('name', width=200)
        self.profile_tree.column('windows', width=80)
        self.profile_tree.column('hotkey', width=100)
        self.profile_tree.column('created', width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profile_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.profile_tree.xview)
        
        self.profile_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.profile_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind selection event
        self.profile_tree.bind('<<TreeviewSelect>>', self._on_profile_select)
        self.profile_tree.bind('<Double-1>', self._on_profile_double_click)
    
    def _create_profile_details(self, parent):
        """Create profile details section"""
        details_frame = ttk.LabelFrame(parent, text="📄 Profile Details", padding="10")
        details_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        details_frame.columnconfigure(1, weight=1)
        
        # Profile info
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.name_label = ttk.Label(details_frame, text="", font=('Segoe UI', 9, 'bold'))
        self.name_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(details_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.desc_label = ttk.Label(details_frame, text="", wraplength=400)
        self.desc_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(details_frame, text="Windows:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.windows_label = ttk.Label(details_frame, text="")
        self.windows_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(details_frame, text="Hotkey:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.hotkey_label = ttk.Label(details_frame, text="")
        self.hotkey_label.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(details_frame, text="Created:").grid(row=4, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.created_label = ttk.Label(details_frame, text="")
        self.created_label.grid(row=4, column=1, sticky=tk.W, pady=(5, 0))
    
    def _create_action_buttons(self, parent):
        """Create action buttons"""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Left side - Profile actions
        left_frame = ttk.Frame(action_frame)
        left_frame.pack(side=tk.LEFT)
        
        ttk.Button(left_frame, text="📥 Load Selected", 
                  command=self._load_profile).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(left_frame, text="🗑️ Delete Selected", 
                  command=self._delete_profile).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(left_frame, text="📝 Rename", 
                  command=self._rename_profile).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(left_frame, text="📋 Duplicate", 
                  command=self._duplicate_profile).pack(side=tk.LEFT)
        
        # Right side - Import/Export
        right_frame = ttk.Frame(action_frame)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="📤 Export", 
                  command=self._export_profile).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(right_frame, text="📥 Import", 
                  command=self._import_profile).pack(side=tk.LEFT)
    
    def _create_bottom_buttons(self, parent):
        """Create bottom buttons"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        # Left side - Save new profile
        if self.current_selection:
            ttk.Button(bottom_frame, text="💾 Save Current Selection", 
                      command=self._save_current_selection).pack(side=tk.LEFT)
        
        # Right side - Close button
        ttk.Button(bottom_frame, text="❌ Close", 
                  command=self._close).pack(side=tk.RIGHT)
    
    def _refresh_profile_list(self):
        """Refresh the profile list"""
        # Clear existing items
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        
        # Load profiles
        profiles_data = self.config_manager.load_profiles()
        
        # Add profiles to tree
        for name, profile_data in profiles_data.items():
            try:
                profile = Profile.from_dict(profile_data)
                
                # Format data for display
                windows_text = f"{len(profile.windows)} windows"
                hotkey_text = profile.hotkey or "Default"
                created_text = profile.created_at or "Unknown"
                
                # Insert into tree
                item_id = self.profile_tree.insert('', tk.END, values=(
                    name, windows_text, hotkey_text, created_text
                ))
                
                # Store profile data with item
                self.profile_tree.set(item_id, 'profile_data', profile_data)
                
            except Exception as e:
                print(f"Error loading profile {name}: {e}")
    
    def _on_profile_select(self, event):
        """Handle profile selection"""
        selection = self.profile_tree.selection()
        if not selection:
            self._clear_profile_details()
            return
        
        item_id = selection[0]
        profile_data = self.profile_tree.item(item_id, 'values')
        
        if not profile_data:
            return
        
        try:
            # Load full profile data
            name = profile_data[0]
            profiles = self.config_manager.load_profiles()
            
            if name in profiles:
                profile = Profile.from_dict(profiles[name])
                self._show_profile_details(profile)
        except Exception as e:
            print(f"Error showing profile details: {e}")
    
    def _on_profile_double_click(self, event):
        """Handle double-click on profile (load it)"""
        self._load_profile()
    
    def _show_profile_details(self, profile: Profile):
        """Show details for selected profile"""
        self.name_label.config(text=profile.name)
        self.desc_label.config(text=profile.description or "No description")
        
        # Format windows list
        if profile.windows:
            windows_text = f"{len(profile.windows)} windows: "
            window_names = [w.character_name or w.title[:20] for w in profile.windows[:3]]
            if len(profile.windows) > 3:
                window_names.append(f"... and {len(profile.windows) - 3} more")
            windows_text += ", ".join(window_names)
        else:
            windows_text = "No windows"
        
        self.windows_label.config(text=windows_text)
        self.hotkey_label.config(text=profile.hotkey or "Default")
        self.created_label.config(text=profile.created_at or "Unknown")
    
    def _clear_profile_details(self):
        """Clear profile details"""
        self.name_label.config(text="")
        self.desc_label.config(text="")
        self.windows_label.config(text="")
        self.hotkey_label.config(text="")
        self.created_label.config(text="")
    
    def _get_selected_profile_name(self) -> Optional[str]:
        """Get the name of the selected profile"""
        selection = self.profile_tree.selection()
        if not selection:
            return None
        
        item_id = selection[0]
        profile_data = self.profile_tree.item(item_id, 'values')
        return profile_data[0] if profile_data else None
    
    def _load_profile(self):
        """Load the selected profile"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("No Selection", "Please select a profile to load.", parent=self.dialog)
            return
        
        profile = self.config_manager.load_profile(profile_name)
        if not profile:
            messagebox.showerror("Error", f"Failed to load profile '{profile_name}'.", parent=self.dialog)
            return
        
        self.result = {'action': 'load', 'profile': profile}
        self.dialog.destroy()
    
    def _delete_profile(self):
        """Delete the selected profile"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("No Selection", "Please select a profile to delete.", parent=self.dialog)
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete profile '{profile_name}'?\n\nThis action cannot be undone.", 
                                  parent=self.dialog):
            return
        
        if self.config_manager.delete_profile(profile_name):
            messagebox.showinfo("Profile Deleted", f"Profile '{profile_name}' has been deleted.", parent=self.dialog)
            self._refresh_profile_list()
            self._clear_profile_details()
        else:
            messagebox.showerror("Error", f"Failed to delete profile '{profile_name}'.", parent=self.dialog)
    
    def _rename_profile(self):
        """Rename the selected profile"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("No Selection", "Please select a profile to rename.", parent=self.dialog)
            return
        
        # Get new name
        new_name = simpledialog.askstring("Rename Profile", 
                                         f"Enter new name for '{profile_name}':",
                                         initialvalue=profile_name,
                                         parent=self.dialog)
        
        if not new_name or new_name == profile_name:
            return
        
        if self.config_manager.rename_profile(profile_name, new_name):
            messagebox.showinfo("Profile Renamed", f"Profile renamed to '{new_name}'.", parent=self.dialog)
            self._refresh_profile_list()
        else:
            messagebox.showerror("Error", f"Failed to rename profile.", parent=self.dialog)
    
    def _duplicate_profile(self):
        """Duplicate the selected profile"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("No Selection", "Please select a profile to duplicate.", parent=self.dialog)
            return
        
        # Get new name
        new_name = simpledialog.askstring("Duplicate Profile", 
                                         f"Enter name for duplicate of '{profile_name}':",
                                         initialvalue=f"{profile_name}_copy",
                                         parent=self.dialog)
        
        if not new_name:
            return
        
        if self.config_manager.duplicate_profile(profile_name, new_name):
            messagebox.showinfo("Profile Duplicated", f"Profile duplicated as '{new_name}'.", parent=self.dialog)
            self._refresh_profile_list()
        else:
            messagebox.showerror("Error", f"Failed to duplicate profile.", parent=self.dialog)
    
    def _export_profile(self):
        """Export the selected profile"""
        profile_name = self._get_selected_profile_name()
        if not profile_name:
            messagebox.showwarning("No Selection", "Please select a profile to export.", parent=self.dialog)
            return
        
        # Choose export location
        filename = filedialog.asksaveasfilename(
            title="Export Profile",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialvalue=f"{profile_name}.json",
            parent=self.dialog
        )
        
        if not filename:
            return
        
        from pathlib import Path
        if self.config_manager.export_profile(profile_name, Path(filename)):
            messagebox.showinfo("Export Successful", f"Profile exported to:\n{filename}", parent=self.dialog)
        else:
            messagebox.showerror("Export Failed", f"Failed to export profile.", parent=self.dialog)
    
    def _import_profile(self):
        """Import a profile from file"""
        # Choose file to import
        filename = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.dialog
        )
        
        if not filename:
            return
        
        from pathlib import Path
        imported_name = self.config_manager.import_profile(Path(filename))
        
        if imported_name:
            messagebox.showinfo("Import Successful", f"Profile imported as '{imported_name}'.", parent=self.dialog)
            self._refresh_profile_list()
        else:
            messagebox.showerror("Import Failed", f"Failed to import profile.", parent=self.dialog)
    
    def _save_current_selection(self):
        """Save current window selection as new profile"""
        if not self.current_selection:
            messagebox.showwarning("No Selection", "No windows currently selected to save.", parent=self.dialog)
            return
        
        # Get profile name
        profile_name = simpledialog.askstring("Save Profile", 
                                             "Enter a name for this profile:",
                                             parent=self.dialog)
        
        if not profile_name:
            return
        
        # Create profile
        window_profiles = []
        for window in self.current_selection:
            window_profile = WindowProfile(
                title=window.title,
                character_name=window.character_name,
                game_type=window.game_type,
                order=window.order
            )
            window_profiles.append(window_profile)
        
        profile = Profile(
            name=profile_name,
            windows=window_profiles,
            hotkey=self.current_hotkey.raw_value if self.current_hotkey else "ctrl+tab",
            auto_detect=True,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        if self.config_manager.save_profile(profile):
            messagebox.showinfo("Profile Saved", f"Profile '{profile_name}' has been saved!", parent=self.dialog)
            self._refresh_profile_list()
        else:
            messagebox.showerror("Save Failed", f"Failed to save profile.", parent=self.dialog)
    
    def _close(self):
        """Close the dialog"""
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict[str, Any]]:
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result