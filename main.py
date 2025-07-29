#!/usr/bin/env python3
"""
🎮 Dofus/Wakfu Window Cycler - Main Entry Point
Advanced window cycling tool specifically designed for Dofus and Wakfu games
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.platform_utils import check_platform_requirements, check_dependencies
from gui.main_window import WindowCyclerApp


def main():
    """Main application entry point"""
    try:
        print("🎮 Starting Dofus/Wakfu Window Cycler...")
        
        # Check platform compatibility
        if not check_platform_requirements():
            return 1
        
        # Check required dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            print("❌ Missing required dependencies:")
            for dep in missing_deps:
                print(f"   - {dep}")
            print("\n💡 Install them with:")
            print(f"   pip install {' '.join(missing_deps)}")
            return 1
        
        # Create and run the application
        app = WindowCyclerApp()
        app.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())