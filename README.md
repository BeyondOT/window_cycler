# 🎮 Dofus/Wakfu Window Cycler v2.0

**A professional, modular window cycling tool specifically designed for Dofus and Wakfu games with advanced hotkey support, profile management, and modern GUI.**

## ✨ Features

### 🎯 **Game-Specific Design**

- **Auto-detects** Dofus and Wakfu windows
- **Extracts character names** from window titles
- **Supports all versions** (Dofus Classic, Retro, Unity, Wakfu)
- **Multi-server support** for different game instances

### 🎹 **Advanced Hotkey System**

- **Mouse button support** (Mouse 4, Mouse 5, Middle Click)
- **Custom key combinations** (Ctrl+Mouse5, Alt+F3, etc.)
- **Live hotkey capture** - press keys to detect them automatically
- **Multiple fallback methods** for maximum compatibility
- **Triple-redundant system** (keyboard lib, Win32, pynput)

### 💾 **Professional Profile System**

- **Save/Load configurations** for different character setups
- **Import/Export profiles** to share with other players
- **Automatic window matching** by character names
- **Profile management** (rename, duplicate, delete)
- **Backup system** with automatic versioning

### 🖥️ **Modern GUI**

- **Clean, professional interface** with tooltips
- **Drag-and-drop style ordering** with auto-numbering
- **Real-time window detection** and validation
- **Status bar** with detailed feedback
- **Scrollable lists** for many windows

### 🔧 **Advanced Window Management**

- **Smart window activation** with multiple fallback methods
- **Invalid window cleanup** (removes closed windows automatically)
- **Cross-monitor support**
- **Minimized window handling** (restores when cycling)
- **Process validation** ensures windows are still alive

## 🚀 Quick Start

### Installation

1. **Install Python 3.8+** from [python.org](https://python.org/downloads/)

2. **Download the project** and extract to a folder

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### Basic Usage

1. **Launch your games** - Start Dofus/Wakfu with your characters
2. **Open the cycler** - Run `python main.py`
3. **Refresh windows** - Click "🔄 Refresh Windows"
4. **Select windows** - Check boxes for windows you want to cycle
5. **Configure hotkey** - Click "🔧 Change" to set your preferred hotkey
6. **Start cycling** - Click "▶️ Start Cycling"
7. **Cycle away!** - Press your hotkey to cycle through windows

## 📁 Project Structure

```
dofus_wakfu_cycler/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # This file
│
├── core/                       # Core functionality
│   ├── window_detector.py      # Game window detection
│   ├── window_cycler.py        # Cycling logic
│   ├── hotkey_manager.py       # Hotkey handling
│   └── config_manager.py       # Profile management
│
├── models/                     # Data structures
│   ├── game_window.py          # GameWindow class
│   ├── profile.py              # Profile classes
│   └── hotkey.py               # Hotkey configuration
│
├── gui/                        # User interface
│   ├── main_window.py          # Main application window
│   ├── hotkey_dialog.py        # Hotkey configuration dialog
│   ├── profile_dialog.py       # Profile management dialog
│   └── components/             # Reusable UI components
│       ├── window_list.py      # Window selection widget
│       └── status_bar.py       # Status bar widget
│
└── utils/                      # Utilities
    └── platform_utils.py       # Windows API wrapper
```

## 🎯 Advanced Features

### 🖱️ **Mouse Button Hotkeys**

Perfect for gaming - use side mouse buttons that don't interfere with gameplay:

- **Mouse 4** (side button)
- **Mouse 5** (other side button)
- **Middle Click** (mouse wheel)
- **Combinations** like Ctrl+Mouse4, Alt+Mouse5

### 📋 **Profile System**

- **Save different setups** for different activities (PvP, dungeon, farming)
- **Auto-match characters** when loading profiles
- **Export/Import** to share configurations with friends
- **Backup system** prevents data loss

### 🔄 **Smart Window Detection**

- **Character name extraction** from window titles
- **Game type detection** (Dofus vs Wakfu)
- **Process validation** ensures windows are still running
- **Multi-instance support** for different servers

### ⚡ **Performance Optimized**

- **Minimal CPU usage** when idle
- **Fast window switching** with multiple activation methods
- **Memory efficient** profile storage
- **Threaded operations** keep UI responsive

## 🎮 Usage Tips

### **For Dofus Players:**

- Works with Classic, Retro, and Unity versions
- Character names automatically detected from window titles
- Perfect for multi-character dungeon runs
- Save profiles for different team compositions

### **For Wakfu Players:**

- Full compatibility with current Wakfu client
- Character detection works with standard window titles
- Great for ecosystem management
- Multi-server character cycling

### **Recommended Hotkeys:**

- **Mouse 4** - Most convenient for gaming
- **Mouse 5** - Alternative side button
- **Ctrl+Space** - Doesn't conflict with games
- **F1/F2** - Dedicated function keys

## 🛠️ Building Executable

To create a standalone `.exe` file:

1. **Install PyInstaller:**

   ```bash
   pip install pyinstaller
   ```

2. **Run the build script:**

   ```bash
   python build_executable.py
   ```

3. **Find your executable in:** `dist/DofusWakfuCycler.exe`

## 🔧 Troubleshooting

### **"No game windows detected"**

- Make sure Dofus/Wakfu is running
- Try clicking "🔄 Refresh Windows"
- Check that games are in windowed mode (not fullscreen)

### **Hotkeys not working**

- Try running as Administrator (right-click → "Run as administrator")
- Try different hotkeys (F1, F2, Mouse buttons)
- Check if other applications are using the same hotkey

### **Window switching fails**

- Ensure games are in windowed mode
- Try different window activation methods
- Check that windows haven't been closed

### **Profile loading issues**

- Make sure character names match between sessions
- Check that the same games are running
- Try refreshing windows before loading profile

## 📊 Technical Details

### **Hotkey Methods (in order of priority):**

1. **Keyboard Library** - Fastest, most reliable when it works
2. **Win32 RegisterHotKey** - Most compatible, works system-wide
3. **Pynput** - Fallback method, supports mouse buttons

### **Window Activation Methods:**

1. Basic activation (SetForegroundWindow, BringWindowToTop)
2. Thread input attachment (advanced Windows technique)
3. Alt key trick (overcomes Windows focus restrictions)
4. Mouse click simulation (last resort)

### **Profile Storage:**

- JSON format for easy editing and backup
- Automatic backup creation when profiles are modified
- Configurable backup retention (default: 10 backups per profile)

## 🤝 Contributing

This project is designed to be easily extensible:

- **Add new games**: Extend `GameWindowDetector`
- **New hotkey methods**: Add to `HotkeyManager`
- **UI improvements**: Modify components in `gui/`
- **New features**: Core logic is modular and well-documented

## 📝 Version History

### **v2.0** - Complete Rewrite

- Modular architecture for better maintainability
- Advanced hotkey system with mouse support
- Professional profile management
- Modern GUI with tooltips and status feedback
- Comprehensive error handling and validation

### **v1.0** - Original AutoHotkey Version

- Basic window cycling functionality
- Simple hotkey support
- Single-file architecture

## 🎉 Enjoy!

Happy cycling through
