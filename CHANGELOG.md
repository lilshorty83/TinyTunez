# Changelog

All notable changes to TinyTunez will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-08

### Added
- Keyboard shortcuts for media controls:
  - Z = Previous song
  - X = Play
  - C = Pause
  - V = Stop
  - B = Next song
  - S = Toggle shuffle
  - Up arrow = Volume up (5% increments)
  - Down arrow = Volume down (5% increments)

### Fixed
- App startup delay by using cached metadata instead of re-reading ID3 tags for all songs
- Visualization delay on first played song by optimizing audio loading and time update intervals
- Time display delay by reducing update interval from 1000ms to 100ms

### Changed
- Optimized audio loading for visualization by limiting to first 60 seconds instead of entire file
- Improved visualization bar initialization timing for faster startup

## [1.1.0] - 2026-05-06

### Added
- Winamp-style shuffle navigation:
  - Previous button at start of shuffle history does nothing
  - Next button moves forward in shuffle history, picking random song only at the end
  - Shuffle history tracking for proper back/forward navigation
  - Removed peek state logic for simpler, more predictable behavior

### Fixed
- Listbox widget invalidation error during folder addition
- Duplicate treeview during folder addition
- Crash after folder addition in dark theme
- Custom dialog theme colors
- Peaks reset to bottom when song stops
- Visualization bars display immediately on startup with current style/color
- Previous button repeating same song in shuffle mode
- Next button navigation in shuffle history
- Various audio loading warnings

### Changed
- Updated .gitignore to exclude user-specific files:
  - viz_multi.py
  - winamp_optimized.json
  - shuffle_state.json
  - audio_output_driver_config.txt
  - innosetup.exe
  - installer/
  - TinyTunez.iss
  - *.code-workspace
  - screenshots/

## [1.0.0] - 2026-05-06

### Initial Release
- Basic music player functionality
- Playlist management
- Audio visualization
- Shuffle mode
- Lyrics support
- Theme support (dark, peach)
