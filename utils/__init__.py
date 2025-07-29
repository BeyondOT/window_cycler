"""
Utility functions and platform-specific code
"""

from .platform_utils import (
    check_platform_requirements,
    check_dependencies,
    get_app_data_dir,
    get_windows_api,
    WindowsAPI
)

__all__ = [
    'check_platform_requirements',
    'check_dependencies', 
    'get_app_data_dir',
    'get_windows_api',
    'WindowsAPI'
]