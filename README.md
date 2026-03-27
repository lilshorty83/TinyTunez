# TinyTunez Music Player

A modern, feature-rich music player for Windows with beautiful themes, lyrics display, and intuitive controls built with Python.

## 🎵 Features

- **🎨 Beautiful Themes**: Switch between Dark and Peach themes with persistent settings
- **🎵 High-Quality Audio**: MPV and pygame audio engines for optimal playback
- **📝 Smart Lyrics**: Automatic lyrics fetching from LRCLib with manual search options
- **🎼 Playlist Management**: Add songs/folders, save playlists, shuffle mode
- **🎛️ Full Control**: Play, pause, stop, next, previous, volume controls
- **🖼️ Album Art**: Automatic album artwork display
- **📊 Visualizations**: Real-time audio visualization
- **⌨️ Keyboard Shortcuts**: Efficient navigation and control
- **💾 Persistent Settings**: Your preferences are saved between sessions

## 📸 Screenshots

*Coming soon - Beautiful dark and peach theme interfaces*

## 🚀 Windows Installation

### Option 1: Python Installation (Recommended for developers)

1. **Install Python 3.7+**
   - Download from [python.org](https://python.org)
   - During installation, check "Add Python to PATH"

2. **Download TinyTunez**
   - Extract the ZIP file to your desired location
   - Open Command Prompt or PowerShell in that folder

3. **Install Dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run TinyTunez**
   ```cmd
   python tinytunez.py
   ```

### Option 2: Executable (Coming Soon)

- Download the `.exe` file
- Double-click to run
- No installation required!

## 🎮 Usage Guide

### Adding Music
- **File → Add Songs**: Select individual MP3, WAV, OGG, or FLAC files
- **File → Add Folder**: Add entire music folders (supports subfolders)
- **Drag & Drop**: Drag files or folders directly onto the playlist

### Playing Music
- **Double-click** any song in the playlist to start playing
- Use **control buttons**: ⏮️ Previous, ▶️ Play, ⏸️ Pause, ⏹️ Stop, ⏭️ Next
- **Volume Control**: Click mute button or drag volume slider

### Lyrics Features
- **Automatic Fetching**: Lyrics appear automatically when available
- **Manual Search**: Right-click song → Search LRCLib/AZLyrics/Genius
- **Edit Lyrics**: Right-click → Edit Lyrics to modify or add lyrics
- **Storage Options**: Centralized or album-specific lyrics storage

### Themes & Customization
- **Theme Switching**: View → Dark Theme / Peach Theme
- **Persistent Settings**: Your theme choice is saved automatically
- **Beautiful UI**: Modern, clean interface with smooth transitions

### Keyboard Shortcuts
- **Space**: Play/Pause
- **→**: Next Track
- **←**: Previous Track
- **↑/↓**: Volume Up/Down
- **M**: Mute/Unmute
- **Ctrl+F**: Search/Filter playlist
- **Ctrl+O**: Open file dialog
- **Escape**: Close dialogs

## 📁 Supported Formats

- **Audio**: MP3, WAV, OGG, FLAC, M4A
- **Playlists**: JSON format (auto-saved)
- **Lyrics**: LRC, TXT formats

## ⚙️ Settings & Configuration

Settings are automatically saved in `settings.json`:
- **Theme Preference**: Dark or Peach theme
- **Lyrics Storage**: Centralized, album folders, or hybrid
- **Lyrics Preference**: Synced first, plain text only, or synced only
- **UI Debug Mode**: Enable tooltips for development
- **Window Position**: Remembered between sessions

## 🔧 Requirements

### Minimum Requirements
- **Windows 7, 8, 10, or 11**
- **Python 3.7+** (for source installation)
- **RAM**: 256MB minimum
- **Storage**: 50MB for application

### Python Dependencies
```txt
pygame>=2.0.0
requests>=2.25.0
beautifulsoup4>=4.9.0
pillow>=8.0.0
lrclib>=1.0.0
matplotlib>=3.3.0
numpy>=1.20.0
```

## 📁 File Structure

```
TinyTunez/
├── tinytunez.py          # Main application
├── peach_theme.py        # Peach theme configuration
├── requirements.txt      # Python dependencies
├── assets/               # Icons and images
├── settings.json         # User settings (auto-created)
├── playlist.json         # Current playlist (auto-created)
├── audio_cache/          # Audio analysis cache (auto-created)
└── cover_cache/          # Album art cache (auto-created)
```

## 🎯 Tips & Tricks

### Performance
- **Large Libraries**: Use folder-based organization for better performance
- **Album Art**: Place `cover.jpg` in album folders for automatic artwork
- **Lyrics**: Place `.lrc` files with songs for offline lyrics

### Troubleshooting
- **No Sound**: Check volume settings and try different audio engines
- **Missing Lyrics**: Use manual search or add lyrics manually
- **Performance Issues**: Clear audio cache if it grows too large

### Advanced Features
- **Karaoke Mode**: Synced lyrics highlight in real-time
- **Visualization**: Real-time frequency analysis during playback
- **Shuffle Mode**: Random playback with position memory

## 🔄 Updates & Support

### Version History
- **v3.0**: Peach theme, persistent settings, improved lyrics
- **v2.0**: Audio visualization, album art, keyboard shortcuts
- **v1.0**: Basic music player functionality

### Getting Help
- **Issues**: Report bugs on GitHub
- **Features**: Request new features in discussions
- **Community**: Join our Discord server

## 🛠️ Development

### Building from Source
```bash
git clone https://github.com/yourusername/tinytunez.git
cd tinytunez
pip install -r requirements.txt
python tinytunez.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **LRCLib** for lyrics API
- **MPV** for high-quality audio playback
- **Tkinter** for the GUI framework
- **pygame** for audio fallback support

---

**Made with ❤️ for music lovers on Windows**
