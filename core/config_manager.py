"""
Configuration and profile management
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import shutil

from models.profile import Profile, WindowProfile
from utils.platform_utils import get_app_data_dir


class ConfigManager:
    """Handles saving and loading of profiles and application settings"""
    
    def __init__(self):
        self.config_dir = Path(get_app_data_dir())
        self.profiles_file = self.config_dir / "profiles.json"
        self.settings_file = self.config_dir / "settings.json"
        self.backup_dir = self.config_dir / "backups"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings
        self.default_settings = {
            'auto_save_profiles': True,
            'backup_profiles': True,
            'max_backups': 10,
            'window_geometry': '',
            'theme': 'default',
            'auto_refresh_interval': 5,  # seconds
            'show_tooltips': True,
            'confirm_deletions': True,
            'debug_mode': False
        }
    
    # ===============================================================================
    # PROFILE MANAGEMENT
    # ===============================================================================
    
    def save_profile(self, profile: Profile) -> bool:
        """Save a profile to disk"""
        try:
            # Validate profile
            errors = profile.validate()
            if errors:
                print(f"❌ Profile validation failed: {', '.join(errors)}")
                return False
            
            # Load existing profiles
            profiles = self.load_profiles()
            
            # Backup if profile already exists
            if profile.name in profiles and self.get_setting('backup_profiles', True):
                self._backup_profile(profile.name, profiles[profile.name])
            
            # Save profile
            profiles[profile.name] = profile.to_dict()
            
            # Write to file
            self._write_profiles(profiles)
            
            print(f"✅ Profile '{profile.name}' saved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save profile '{profile.name}': {e}")
            return False
    
    def load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load all profiles from disk"""
        if not self.profiles_file.exists():
            return {}
        
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            
            # Validate and migrate if needed
            return self._validate_and_migrate_profiles(profiles)
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"❌ Failed to load profiles: {e}")
            # Try to restore from backup
            return self._restore_from_backup()
        except Exception as e:
            print(f"❌ Unexpected error loading profiles: {e}")
            return {}
    
    def load_profile(self, profile_name: str) -> Optional[Profile]:
        """Load a specific profile by name"""
        profiles = self.load_profiles()
        
        if profile_name not in profiles:
            return None
        
        try:
            return Profile.from_dict(profiles[profile_name])
        except Exception as e:
            print(f"❌ Failed to load profile '{profile_name}': {e}")
            return None
    
    def delete_profile(self, profile_name: str) -> bool:
        """Delete a profile"""
        try:
            profiles = self.load_profiles()
            
            if profile_name not in profiles:
                return False
            
            # Backup before deletion if enabled
            if self.get_setting('backup_profiles', True):
                self._backup_profile(profile_name, profiles[profile_name])
            
            # Remove profile
            del profiles[profile_name]
            
            # Write updated profiles
            self._write_profiles(profiles)
            
            print(f"✅ Profile '{profile_name}' deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete profile '{profile_name}': {e}")
            return False
    
    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """Rename a profile"""
        if old_name == new_name:
            return True
        
        try:
            profiles = self.load_profiles()
            
            if old_name not in profiles:
                return False
            
            if new_name in profiles:
                print(f"❌ Profile '{new_name}' already exists")
                return False
            
            # Copy profile with new name
            profile_data = profiles[old_name].copy()
            profile_data['name'] = new_name
            profiles[new_name] = profile_data
            
            # Remove old profile
            del profiles[old_name]
            
            # Write updated profiles
            self._write_profiles(profiles)
            
            print(f"✅ Profile renamed from '{old_name}' to '{new_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to rename profile: {e}")
            return False
    
    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """Duplicate a profile with a new name"""
        try:
            profiles = self.load_profiles()
            
            if source_name not in profiles:
                return False
            
            if new_name in profiles:
                print(f"❌ Profile '{new_name}' already exists")
                return False
            
            # Copy profile data
            profile_data = profiles[source_name].copy()
            profile_data['name'] = new_name
            profile_data['created_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            profiles[new_name] = profile_data
            
            # Write updated profiles
            self._write_profiles(profiles)
            
            print(f"✅ Profile duplicated: '{source_name}' -> '{new_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to duplicate profile: {e}")
            return False
    
    def get_profile_names(self) -> List[str]:
        """Get list of all profile names"""
        profiles = self.load_profiles()
        return sorted(profiles.keys())
    
    def profile_exists(self, profile_name: str) -> bool:
        """Check if a profile exists"""
        profiles = self.load_profiles()
        return profile_name in profiles
    
    # ===============================================================================
    # SETTINGS MANAGEMENT
    # ===============================================================================
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save application settings"""
        try:
            # Merge with existing settings
            current_settings = self.load_settings()
            current_settings.update(settings)
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save settings: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        if not self.settings_file.exists():
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            result = self.default_settings.copy()
            result.update(settings)
            return result
            
        except Exception as e:
            print(f"❌ Failed to load settings: {e}")
            return self.default_settings.copy()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        settings = self.load_settings()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        return self.save_settings({key: value})
    
    # ===============================================================================
    # BACKUP AND RECOVERY
    # ===============================================================================
    
    def _backup_profile(self, profile_name: str, profile_data: Dict[str, Any]):
        """Create a backup of a profile"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{profile_name}_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump({profile_name: profile_data}, f, indent=2, ensure_ascii=False)
            
            # Clean up old backups
            self._cleanup_old_backups(profile_name)
            
        except Exception as e:
            print(f"⚠️ Failed to backup profile '{profile_name}': {e}")
    
    def _cleanup_old_backups(self, profile_name: str):
        """Remove old backup files, keeping only the most recent ones"""
        try:
            max_backups = self.get_setting('max_backups', 10)
            pattern = f"{profile_name}_*.json"
            
            # Get all backup files for this profile
            backup_files = list(self.backup_dir.glob(pattern))
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_file in backup_files[max_backups:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"⚠️ Failed to cleanup backups: {e}")
    
    def _restore_from_backup(self) -> Dict[str, Dict[str, Any]]:
        """Attempt to restore profiles from backup"""
        try:
            backup_files = list(self.backup_dir.glob("*.json"))
            if not backup_files:
                return {}
            
            # Use the most recent backup
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            print(f"🔄 Restored profiles from backup: {latest_backup.name}")
            return backup_data
            
        except Exception as e:
            print(f"❌ Failed to restore from backup: {e}")
            return {}
    
    def create_full_backup(self) -> bool:
        """Create a full backup of all profiles and settings"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"full_backup_{timestamp}.json"
            
            backup_data = {
                'profiles': self.load_profiles(),
                'settings': self.load_settings(),
                'backup_time': timestamp,
                'version': '1.0'
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Full backup created: {backup_file.name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create full backup: {e}")
            return False
    
    # ===============================================================================
    # IMPORT/EXPORT
    # ===============================================================================
    
    def export_profile(self, profile_name: str, export_path: Path) -> bool:
        """Export a profile to a file"""
        try:
            profile = self.load_profile(profile_name)
            if not profile:
                return False
            
            export_data = {
                'profile': profile.to_dict(),
                'export_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                'version': '1.0'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to export profile: {e}")
            return False
    
    def import_profile(self, import_path: Path, overwrite: bool = False) -> Optional[str]:
        """Import a profile from a file"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'profile' not in import_data:
                print("❌ Invalid profile file format")
                return None
            
            profile = Profile.from_dict(import_data['profile'])
            
            # Check if profile already exists
            if self.profile_exists(profile.name) and not overwrite:
                # Generate unique name
                base_name = profile.name
                counter = 1
                while self.profile_exists(f"{base_name}_{counter}"):
                    counter += 1
                profile.name = f"{base_name}_{counter}"
            
            # Save imported profile
            if self.save_profile(profile):
                return profile.name
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to import profile: {e}")
            return None
    
    # ===============================================================================
    # UTILITY METHODS
    # ===============================================================================
    
    def _write_profiles(self, profiles: Dict[str, Dict[str, Any]]):
        """Write profiles to disk with error handling"""
        # Create temporary file first
        temp_file = self.profiles_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(self.profiles_file)
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _validate_and_migrate_profiles(self, profiles: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Validate and migrate profiles to current format"""
        validated_profiles = {}
        
        for name, profile_data in profiles.items():
            try:
                # Try to create Profile object to validate
                profile = Profile.from_dict(profile_data)
                validated_profiles[name] = profile.to_dict()
                
            except Exception as e:
                print(f"⚠️ Skipping invalid profile '{name}': {e}")
                continue
        
        return validated_profiles
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about storage usage"""
        try:
            info = {
                'config_dir': str(self.config_dir),
                'profiles_file_size': self.profiles_file.stat().st_size if self.profiles_file.exists() else 0,
                'settings_file_size': self.settings_file.stat().st_size if self.settings_file.exists() else 0,
                'backup_count': len(list(self.backup_dir.glob('*.json'))),
                'backup_dir_size': sum(f.stat().st_size for f in self.backup_dir.glob('*.json')),
                'total_profiles': len(self.load_profiles())
            }
            
            return info
            
        except Exception as e:
            print(f"❌ Failed to get storage info: {e}")
            return {}
    
    def cleanup_storage(self) -> bool:
        """Clean up old backups and optimize storage"""
        try:
            # Clean up all old backups
            for profile_name in self.get_profile_names():
                self._cleanup_old_backups(profile_name)
            
            print("✅ Storage cleanup completed")
            return True
            
        except Exception as e:
            print(f"❌ Storage cleanup failed: {e}")
            return False