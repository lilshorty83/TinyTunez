import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
import os
import threading
import time
import subprocess
import platform
from tkinter import font as tkfont
from PIL import Image, ImageTk
import mutagen
import json
import pygame
import math
import numpy as np
import librosa

# Import peach theme
try:
    from peach_theme import PEACH_THEME, PEACH_TTK_STYLES, apply_peach_theme
    PEACH_THEME_AVAILABLE = True
except ImportError:
    PEACH_THEME_AVAILABLE = False
    print("Warning: Peach theme not available")

# Add the directory containing the script to the PATH environment variable
# This ensures python-mpv can find the DLLs in the script's local directory
os.environ["PATH"] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ["PATH"]

# Try to import mpv, but don't fail if it's not available
try:
    import mpv
    MPV_AVAILABLE = True
except (ImportError, OSError) as e:
    MPV_AVAILABLE = False
    print(f"MPV not available: {e}")
    mpv = None

# Try to import sounddevice for audio device detection
try:
    import sounddevice
    SOUNDDEVICE_AVAILABLE = True
    print("SoundDevice library available for audio device detection")
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("SoundDevice not available - install with: pip install sounddevice")
    sounddevice = None

# Check both locations
locations = ["C:\\mpv", "C:\\Users\\dana_\\TinyTunez"]
mpv_dlls_found = False

for location in locations:
    if os.path.exists(location):
        dlls = [f for f in os.listdir(location) if f.endswith('.dll')]
        required_dlls = [f for f in dlls if 'mpv' in f.lower()]
        if required_dlls:
            mpv_dlls_found = True
            break

if not mpv_dlls_found:
    print("Warning: MPV DLLs not found in expected locations")
else:
    pass
import matplotlib.pyplot as plt
from datetime import datetime
import requests
from pathlib import Path
try:
    import lrclib
    LRC_AVAILABLE = True
except ImportError:
    LRC_AVAILABLE = False
    print("LrcLib not available, will use web search fallback")

class ImageButton(tk.Button):
    def __init__(self, master, image_path, **kwargs):
        # Load and resize image
        try:
            original_image = Image.open(image_path)
            # Resize to appropriate button size
            image = original_image.resize((32, 32), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            
            # Mark this as an ImageButton
            self.is_image_button = True
            
            # Default styling for image buttons
            default_style = {
                'image': self.photo,
                'bg': '#161b22',
                'relief': tk.FLAT,
                'border': 0,
                'cursor': 'hand2',
                'activebackground': '#21262d'
            }
            default_style.update(kwargs)
            super().__init__(master, **default_style)
            
            # Store reference to prevent garbage collection
            self.image_ref = self.photo
            
        except Exception as e:
            # Fallback to text button if image fails to load
            default_style = {
                'bg': '#4a9eff',
                'fg': 'white',
                'font': ('Segoe UI', 10, 'bold'),
                'border': 0,
                'relief': tk.FLAT,
                'cursor': 'hand2',
                'activebackground': '#3d8ce6',
                'activeforeground': 'white'
            }
            default_style.update(kwargs)
            super().__init__(master, **default_style)

class ModernFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        default_style = {
            'bg': '#1e1e1e',
            'relief': tk.FLAT,
            'bd': 0
        }
        default_style.update(kwargs)
        super().__init__(master, **default_style)

class ModernLabel(tk.Label):
    def __init__(self, master, **kwargs):
        default_style = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'font': ('Segoe UI', 10)
        }
        default_style.update(kwargs)
        super().__init__(master, **default_style)

class TinyTunez:
    def __init__(self, root):
        self.root = root
        self.root.title("TinyTunez Music Player")
        
        # Calculate center position immediately
        width = 1100
        height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Set centered geometry immediately
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg='#0d1117')
        self.root.minsize(900, 550)
        
        # Apply global dark scrollbar styling (disabled - reverting to simple approach)
        self.setup_global_scrollbar_style()
        
        # Store original dark mode colors for theme restoration
        self.original_dark_colors = {
            'treeview_bg': '#0d1117',
            'treeview_fg': '#f0f6fc',
            'treeview_selected': '#1f6feb',
            'treeview_heading_bg': '#21262d',
            'treeview_heading_fg': '#f0f6fc',
            'scrollbar_bg': '#30363d',
            'scrollbar_trough': '#21262d',
            'scrollbar_border': '#30363d',
            'scrollbar_arrow': '#8b949e',
            # Add more original colors for complete restoration
            'root_bg': '#0d1117',
            'frame_bg': '#0d1117',
            'info_card_bg': '#161b22',
            'album_frame_bg': '#21262d',
            'progress_frame_bg': '#161b22',
            'progress_bg': '#21262d',
            'progress_fill': '#1f6feb',
            'lyrics_frame_bg': '#0d1117',
            'song_title_fg': '#f0f6fc',
            'song_length_fg': '#4a9eff',
            'current_time_fg': '#f0f6fc',
            'current_time_bg': '#161b22',
            'title_fg': '#4a9eff',
            'subtitle_fg': '#8b949e',
        }
        
        # Player state
        self.current_song = None
        self.current_song_path = None  # Initialize current song path for lyrics folder access
        self.is_playing = False
        self.is_paused = False
        self.is_muted = False
        self.is_shuffle = self.load_shuffle_state()  # Load shuffle state from file
        self.volume = 0.7
        self.playlist = []
        self.playlist_metadata = []  # Store metadata for each song
        self.current_index = 0
        self.lyrics = ""
        self.play_process = None
        self.current_time = 0
        self.total_time = 0
        self.visualization_running = False
        
        # Add flag to prevent time override after seeking
        self.just_seeked = False
        self.seek_time = 0
        self.seek_offset = 0  # Track manual seek offset
        self.current_sound = None  # Store current sound for better seeking
        
        # Karaoke lyrics system
        self.lyrics_lines = []  # List of (time_ms, text) tuples
        self.current_lyrics = ""  # Raw LRC text
        self.current_line_index = -1  # Current highlighted line
        self.lyrics_timer = None  # Timer for karaoke updates
        
        # Star cache for lyrics
        self.star_cache_file = "star_cache.json"
        self.star_cache = self.load_star_cache()
        
        # Debounced playlist save timer
        self.playlist_save_timer = None
        
        # Initialize shuffle history
        self.shuffle_history = []  # Track played songs in shuffle mode
        self.shuffle_history_index = -1  # Current position in shuffle history
        
        # Scrolling variables for song title
        self.scroll_text = ""
        self.scroll_position = 0
        self.scroll_direction = 1
        self.scroll_enabled = False
        self.scroll_pause_counter = 0
        self.scroll_speed = 200  # milliseconds between scroll updates (slower)
        
        # Last played song tracking
        self.last_played_file = "last_played.json"
        self.last_played_song = self.load_last_played_song()
        
        # Album cover cache
        self.cover_cache_dir = "cover_cache"
        self.cover_cache_file = "cover_cache.json"
        self.cover_cache = self.load_cover_cache()
        self.ensure_cover_cache_dir()
        
        # Search filtering
        self.filtered_indices = []  # Store mapping of filtered items to original indices
        
        # Auto-play control
        self.auto_play_enabled = False  # Disable auto-play on startup
        self.has_manually_played = False  # Track if user has manually played a song
        
        # Current lyrics tracking for editing
        self.current_lyrics_artist = ""
        self.current_lyrics_title = ""
        self.current_lyrics_content = ""
        self.current_lyrics_is_synced = False
        
        # Asset paths
        self.assets_dir = "assets"
        self.playlist_file = "playlist.json"
        self.settings_file = "settings.json"
        
        # Settings
        self.settings = self.load_settings()
        self.custom_lyrics_folder = self.settings.get('lyrics_folder', None)
        
        # Load and apply saved theme
        saved_theme = self.settings.get('theme', 'dark')  # Default to dark theme
        if saved_theme == 'peach' and PEACH_THEME_AVAILABLE:
            self.current_theme = 'peach'
            # Apply peach theme after UI is fully initialized
            self.root.after(100, self.apply_peach_theme)
        else:
            self.current_theme = 'dark'
            # Apply dark theme (default)
            self.root.after(100, self.apply_dark_theme)
        
        # Load star icon (after assets_dir is defined)
        self.star_icon = None
        self.star_empty = None
        self.load_star_icons()
        
        # Audio analysis for visualization
        self.audio_data = []
        self.audio_thread = None
        self.analyzing_audio = False
        self.current_audio_samples = None
        self.audio_sample_rate = 44100  # Default sample rate
        self.audio_duration = None
        self.sample_position = 0
        
        # Audio device tracking
        self.current_audio_device = None  # Will be set to first available device
        self.audio_device_menu = None  # Reference to device menu for updates
        
        # Load saved audio device preference
        self.load_audio_device_preference()
        
        # Lyrics font size tracking
        self.lyrics_font_size = 11  # Default font size
        self.load_lyrics_font_size_preference()
        
        # Initialize visualization components early to prevent first-start freeze
        self.bar_levels = [0] * 32
        self.bar_peaks = [0] * 32
        self.visualization_running = False
        self.viz_bars = []  # Store bar canvas items
        self.viz_peaks = []  # Store peak canvas items
        
        # Initialize pygame for visualization and audio
        try:
            pygame.init()
            
            # Initialize pygame mixer first (always needed for fallback)
            try:
                pygame.mixer.init()
            except Exception as e:
                pass
            
            # Try to initialize mpv for audio, fall back to pygame mixer
            self.use_pygame_fallback = True  # Default to fallback
            if MPV_AVAILABLE and mpv:
                try:
                    # Initialize MPV with saved audio device or default
                    if hasattr(self, 'current_audio_device') and self.current_audio_device:
                        print(f"Initializing MPV with saved device: {self.current_audio_device}")
                        if self.current_audio_device == 'auto':
                            self.player = mpv.MPV(
                                ytdl=False, 
                                vo='null',  # No video output
                                ao='wasapi'  # Windows Audio Session API
                            )
                        else:
                            # Use the saved device
                            self.player = mpv.MPV(
                                ytdl=False, 
                                vo='null',  # No video output
                                ao='wasapi',  # Windows Audio Session API
                                audio_device=self.current_audio_device
                            )
                    else:
                        # Default initialization - no device saved
                        print("Initializing MPV with default device")
                        self.player = mpv.MPV(
                            ytdl=False, 
                            vo='null',  # No video output
                            ao='wasapi'  # Windows Audio Session API
                        )
                    
                    self.player.volume = 70  # Set initial volume
                    
                    # Set some additional options for better playback
                    self.player.keep_open = 'no'  # Don't keep open when finished
                    self.player.loop = 'no'  # Don't loop by default
                    
                    self.use_pygame_fallback = False
                    device_used = getattr(self, 'current_audio_device', 'default')
                    print(f"MPV initialized successfully with device: {device_used}")
                except Exception as e:
                    print(f"Failed to initialize MPV with saved device: {e}")
                    self.use_pygame_fallback = True
            else:
                pass
            
        except Exception as e:
            self.use_pygame_fallback = True
        
        # Initialize player usage counter
        self.player_usage_count = 0
        self.max_player_uses = 50  # Reinitialize after 50 play/stop cycles
        
        # Create GUI first
        self.create_widgets()
        
        # Load saved playlist after GUI is created
        self.load_playlist()
        
        # Update shuffle status after all widgets are created
        self.root.after(100, self.update_shuffle_status)
        
        # Display last played song after everything is loaded
        self.root.after(300, self.display_last_played_song)
        
        # Apply UI debugging if it was previously enabled
        if self.settings.get('ui_debug_enabled', False):
            self.root.after(400, self.enable_ui_debug_tooltips)
        
        # Window is already centered during initialization, no need to delay
    
    def setup_global_scrollbar_style(self):
        """Setup global dark scrollbar styling for consistent appearance"""
        try:
            style = ttk.Style()
            current_theme = style.theme_use()
            
            # Apply dark scrollbar styling to current theme (no theme switching)
            style.configure(
                'TScrollbar',
                background='#30363d',
                troughcolor='#21262d',
                bordercolor='#30363d',
                arrowcolor='#8b949e',
                lightcolor='#40474e',  # Lighter shade for 3D effect
                darkcolor='#262c32',  # Darker shade for 3D effect
                relief='raised'  # Restore 3D beveled appearance
            )
            
            style.configure(
                'Vertical.TScrollbar',
                background='#30363d',
                troughcolor='#21262d',
                bordercolor='#30363d',
                arrowcolor='#8b949e',
                lightcolor='#40474e',  # Lighter shade for 3D effect
                darkcolor='#262c32',  # Darker shade for 3D effect
                relief='raised'  # Restore 3D beveled appearance
            )
            
            style.configure(
                'Horizontal.TScrollbar',
                background='#30363d',
                troughcolor='#21262d',
                bordercolor='#30363d',
                arrowcolor='#8b949e',
                lightcolor='#40474e',  # Lighter shade for 3D effect
                darkcolor='#262c32',  # Darker shade for 3D effect
                relief='raised'  # Restore 3D beveled appearance
            )
            
            # Remove any hover/active states that might cause white highlights
            style.map('TScrollbar', 
                     background=[('active', '#30363d'), ('!active', '#30363d')])
            style.map('Vertical.TScrollbar', 
                     background=[('active', '#30363d'), ('!active', '#30363d')])
            style.map('Horizontal.TScrollbar', 
                     background=[('active', '#30363d'), ('!active', '#30363d')])
            
            # Also configure all possible scrollbar variations
            for scrollbar_type in ['TScrollbar', 'Vertical.TScrollbar', 'Horizontal.TScrollbar']:
                style.configure(scrollbar_type,
                    background='#30363d',
                    troughcolor='#21262d',
                    bordercolor='#30363d',
                    arrowcolor='#8b949e',
                    lightcolor='#40474e',  # Lighter shade for 3D effect
                    darkcolor='#262c32',  # Darker shade for 3D effect
                    relief='raised'  # Restore 3D beveled appearance
                )
                # Remove hover effects
                style.map(scrollbar_type, 
                    background=[('active', '#30363d'), ('!active', '#30363d')],
                    arrowcolor=[('active', '#8b949e'), ('!active', '#8b949e')]
                )
            
            # Force immediate style refresh
            style.configure('TScrollbar', background='#30363d')
            style.configure('Vertical.TScrollbar', background='#30363d')
            
            # Schedule a delayed refresh to ensure all scrollbars get the style
            self.root.after(100, self.force_scrollbar_refresh)
        except Exception as e:
            print(f"Error setting up scrollbar style: {e}")
    
    def force_scrollbar_refresh(self):
        """Force refresh all scrollbar styles to ensure consistency"""
        # Skip if peach theme is active
        current_theme = getattr(self, 'current_theme', 'dark')
        if current_theme == 'peach':
            return
            
        try:
            style = ttk.Style()
            
            # Comprehensive scrollbar styling
            scrollbar_configs = {
                'TScrollbar': {
                    'background': '#30363d',
                    'troughcolor': '#21262d',
                    'bordercolor': '#30363d',
                    'arrowcolor': '#8b949e',
                    'lightcolor': '#40474e',  # Lighter shade for 3D effect
                    'darkcolor': '#262c32',  # Darker shade for 3D effect
                    'relief': 'raised'  # Restore 3D beveled appearance
                },
                'Vertical.TScrollbar': {
                    'background': '#30363d',
                    'troughcolor': '#21262d',
                    'bordercolor': '#30363d',
                    'arrowcolor': '#8b949e',
                    'lightcolor': '#40474e',  # Lighter shade for 3D effect
                    'darkcolor': '#262c32',  # Darker shade for 3D effect
                    'relief': 'raised'  # Restore 3D beveled appearance
                },
                'Horizontal.TScrollbar': {
                    'background': '#30363d',
                    'troughcolor': '#21262d',
                    'bordercolor': '#30363d',
                    'arrowcolor': '#8b949e',
                    'lightcolor': '#40474e',  # Lighter shade for 3D effect
                    'darkcolor': '#262c32',  # Darker shade for 3D effect
                    'relief': 'raised'  # Restore 3D beveled appearance
                }
            }
            
            # Apply configurations
            for scrollbar_type, config in scrollbar_configs.items():
                style.configure(scrollbar_type, **config)
                # Remove hover/active states
                style.map(scrollbar_type, 
                    background=[('active', '#30363d'), ('!active', '#30363d'), ('pressed', '#30363d'), ('hover', '#30363d')],
                    arrowcolor=[('active', '#8b949e'), ('!active', '#8b949e'), ('pressed', '#8b949e'), ('hover', '#8b949e')]
                )
            
            # Schedule another refresh to catch any missed scrollbars
            self.root.after(50, self.force_scrollbar_refresh_final)
            
        except Exception as e:
            print(f"Error refreshing scrollbar styles: {e}")
    
    def force_scrollbar_refresh_final(self):
        """Final scrollbar refresh to catch any remaining issues"""
        # Skip if peach theme is active
        current_theme = getattr(self, 'current_theme', 'dark')
        if current_theme == 'peach':
            return
            
        try:
            style = ttk.Style()
            
            # One more comprehensive pass
            for scrollbar_type in ['TScrollbar', 'Vertical.TScrollbar', 'Horizontal.TScrollbar']:
                style.configure(scrollbar_type,
                    background='#30363d',
                    troughcolor='#21262d',
                    bordercolor='#30363d',
                    arrowcolor='#8b949e',
                    lightcolor='#40474e',  # Lighter shade for 3D effect
                    darkcolor='#262c32',  # Darker shade for 3D effect
                    relief='raised'  # Restore 3D beveled appearance
                )
                # Force all states to dark colors
                style.map(scrollbar_type, 
                    background=[('active', '#30363d'), ('!active', '#30363d'), ('pressed', '#30363d'), ('hover', '#30363d'), ('focus', '#30363d'), ('disabled', '#30363d')],
                    arrowcolor=[('active', '#8b949e'), ('!active', '#8b949e'), ('pressed', '#8b949e'), ('hover', '#8b949e'), ('focus', '#8b949e'), ('disabled', '#8b949e')]
                )
            
        except Exception as e:
            pass
    
    def create_widgets(self):
        # Header with title - aligned with main container
        frame_header_main = ModernFrame(self.root, bg='#0d1117', height=80, name='header_frame')
        frame_header_main.pack(fill=tk.X, padx=10, pady=(10, 0))  # Same padding as main_container
        frame_header_main.pack_propagate(False)
        
        # Store reference for theme updates
        self.title_frame = frame_header_main
        
        # Title with music icon
        try:
            music_icon = ImageButton(frame_header_main, os.path.join(self.assets_dir, "music.png"), bg='#0d1117')
            music_icon.pack(side=tk.LEFT, pady=20, padx=(10, 10))
        except:
            # Fallback to text icon
            header_icon_label = ModernLabel(frame_header_main, text="🎵", font=('Segoe UI', 28), bg='#0d1117', fg='#4a9eff', name='header_icon_label')
            header_icon_label.pack(side=tk.LEFT, pady=20, padx=(0, 10))
        
        app_title_label = ModernLabel(
            frame_header_main, 
            text="TinyTunez", 
            font=('Segoe UI', 28, 'bold'),
            bg='#0d1117',
            fg='#4a9eff',
            name='app_title_label'
        )
        app_title_label.pack(side=tk.LEFT, pady=20)
        
        app_subtitle_label = ModernLabel(
            frame_header_main, 
            text="Music Player with Lyrics", 
            font=('Segoe UI', 12),
            bg='#0d1117',
            fg='#8b949e',
            name='app_subtitle_label'
        )
        app_subtitle_label.pack(side=tk.LEFT, pady=25, padx=(10, 0))
        
        # Menu Bar
        self.create_menu_bar()
        
        # Main container with padding
        frame_main_container = ModernFrame(self.root, bg='#0d1117', name='main_frame')
        frame_main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side (Controls + Playlist) - more compact
        frame_left_panel = ModernFrame(frame_main_container, name='left_panel')
        frame_left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        frame_left_panel.pack_propagate(False)
        frame_left_panel.config(width=550)  # Increased from 500 to 550 for more control space
        
        # Store reference for theme updates
        self.left_frame = frame_left_panel
        
        # Song Information Card
        self.create_song_info_card(frame_left_panel)
        
        # Player Controls
        self.create_player_controls(frame_left_panel)
        
        # Playlist
        self.create_playlist(frame_left_panel)
        
        # Right side (Lyrics)
        self.create_lyrics_window(frame_main_container)
        
    def create_song_info_card(self, parent):
        # Song Information Card with modern styling
        frame_song_info_card = ModernFrame(parent, bg='#161b22', relief=tk.FLAT, bd=0, height=140, name='song_info_frame')
        frame_song_info_card.pack(fill=tk.X, pady=(0, 0))
        frame_song_info_card.pack_propagate(False)
        
        # Store reference for theme updates
        self.info_card = frame_song_info_card
        
        # Add subtle border effect
        frame_song_info_border = ModernFrame(frame_song_info_card, bg='#30363d', height=2, name='info_border_frame')
        frame_song_info_border.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Album art placeholder - smaller for compact layout
        frame_album_art = ModernFrame(frame_song_info_card, bg='#21262d', width=60, height=60, name='album_frame')
        frame_album_art.pack(side=tk.LEFT, padx=10, pady=10)
        frame_album_art.pack_propagate(False)
        
        # Store reference for theme updates
        self.album_frame = frame_album_art
        
        # Try to load placeholder image
        try:
            placeholder_img = Image.open(os.path.join(self.assets_dir, "transparent_placeholder.png"))
            if placeholder_img.size == (1, 1):  # Check if it's the tiny placeholder
                raise Exception("Use text fallback")
            photo = ImageTk.PhotoImage(placeholder_img)
            label_album_img = tk.Label(frame_album_art, image=photo, bg='#21262d', name='album_art_label')
            label_album_img.image = photo  # Keep reference
            label_album_img.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            # Store reference for theme updates
            self.album_img_label = label_album_img
        except:
            # Music icon in album frame
            label_album_music_icon = ModernLabel(frame_album_art, text="🎵", font=('Segoe UI', 32), bg='#21262d', name='album_icon_label')
            label_album_music_icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            # Store reference for theme updates
            self.album_music_icon = label_album_music_icon
        
        # Song info with time and visualization - reduced padding
        frame_song_info_content = ModernFrame(frame_song_info_card, bg='#161b22', name='info_content_frame')
        frame_song_info_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=2)
        
        # Top row: Song title and length
        frame_song_title_row = ModernFrame(frame_song_info_content, bg='#161b22', name='title_row_frame')
        frame_song_title_row.pack(fill=tk.X, pady=(2, 0))
        
        self.song_title_label = ModernLabel(
            frame_song_title_row, 
            text="No song playing", 
            font=('Segoe UI', 16, 'bold'),
            bg='#161b22',
            fg='#f0f6fc',
            anchor=tk.W,
            name='song_title_label'
        )
        self.song_title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.song_length_label = ModernLabel(
            frame_song_title_row, 
            text="0:00", 
            font=('Segoe UI', 14, 'bold'),
            bg='#161b22',
            fg='#4a9eff',
            anchor=tk.E,
            name='song_length_label'
        )
        self.song_length_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Artist label (now hidden/repurposed)
        self.song_artist_label = ModernLabel(
            frame_song_info_content, 
            text="", 
            font=('Segoe UI', 11),
            bg='#161b22',
            fg='#8b949e',
            anchor=tk.W,
            name='song_artist_label'
        )
        # Keep the label but don't pack it so it's hidden
        
        # Time display and visualization frame
        frame_time_visualization = ModernFrame(frame_song_info_content, bg='#161b22', name='time_viz_frame')
        frame_time_visualization.pack(fill=tk.X, pady=(10, 0))
        
        # Current time display (like Winamp)
        frame_current_time = ModernFrame(frame_time_visualization, bg='#21262d', name='current_time_frame')
        frame_current_time.pack(side=tk.LEFT, padx=(0, 10))
        
        self.current_time_label = ModernLabel(
            frame_current_time, 
            text="0:00", 
            font=('Courier New', 24, 'bold'),
            bg='#21262d',
            fg='#ffffff',
            width=6,
            name='current_time_label'
        )
        self.current_time_label.pack(padx=10, pady=5)
        
        # Visualization canvas (simpler and faster)
        frame_visualization = ModernFrame(frame_time_visualization, bg='#21262d', name='viz_frame')
        frame_visualization.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.visualization_canvas = tk.Canvas(
            frame_visualization,
            bg='#000000',
            highlightthickness=0,
            height=30,
            name='visualization_canvas'
        )
        self.visualization_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Progress bar placeholder
        frame_progress_bar = ModernFrame(frame_song_info_content, bg='#161b22', name='progress_frame')
        frame_progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Store reference for theme updates
        self.progress_frame = frame_progress_bar
        
        self.progress_bg = ModernFrame(frame_progress_bar, bg='#21262d', height=12, name='progress_bg')
        self.progress_bg.pack(fill=tk.X)
        
        self.progress_fill = ModernFrame(self.progress_bg, bg='#4a9eff', height=12, width=0, name='progress_fill')
        self.progress_fill.place(x=0, y=0)
        
        # Bind click events for seeking (Winamp-style) - prevent event bubbling
        self.progress_bg.bind('<Button-1>', lambda e: self.on_progress_click(e) or "break")
        self.progress_bg.bind('<B1-Motion>', lambda e: self.on_progress_drag(e) or "break")
        self.progress_bg.bind('<ButtonRelease-1>', lambda e: self.on_progress_release(e) or "break")
        self.progress_fill.bind('<Button-1>', lambda e: self.on_progress_click(e) or "break")
        self.progress_fill.bind('<B1-Motion>', lambda e: self.on_progress_drag(e) or "break")
        self.progress_fill.bind('<ButtonRelease-1>', lambda e: self.on_progress_release(e) or "break")
    
    def on_progress_click(self, event):
        """Handle click on progress bar to seek to position (Winamp-style)."""
        # Don't handle click if we're already dragging
        if getattr(self, 'seek_pending', False):
            return
            
        if not self.current_song or not self.is_playing and not self.is_paused:
            return
        
        # Get and cache the progress bar width
        progress_bg = event.widget
        if hasattr(progress_bg, 'winfo_width'):
            bar_width = progress_bg.winfo_width()
            if bar_width <= 0:
                return
            
            # Cache the bar width for consistent calculations
            self.progress_bar_width = bar_width
            
            # Calculate click position as percentage
            click_x = event.x
            # Ensure click_x is within bounds
            click_x = max(0, min(click_x, bar_width))
            percentage = max(0, min(1, click_x / bar_width))
            
            # Store target position but don't seek yet (Winamp-style)
            self.seek_target = percentage * self.total_time
            self.seek_pending = True
            
            # Update visual progress immediately for feedback
            self.current_time = self.seek_target
            self.update_progress_display()
    
    def on_progress_drag(self, event):
        """Handle dragging on progress bar to seek (Winamp-style)."""
        if not self.current_song or not self.is_playing and not self.is_paused:
            return
        
        # Use cached bar width for consistency
        if not hasattr(self, 'progress_bar_width') or self.progress_bar_width <= 0:
            # Fallback: get current width and cache it
            progress_bg = event.widget
            if hasattr(progress_bg, 'winfo_width'):
                bar_width = progress_bg.winfo_width()
                if bar_width <= 0:
                    return
                self.progress_bar_width = bar_width
            else:
                return
        
        bar_width = self.progress_bar_width
        
        # Calculate drag position as percentage
        drag_x = event.x
        # Ensure drag_x is within bounds
        drag_x = max(0, min(drag_x, bar_width))
        percentage = max(0, min(1, drag_x / bar_width))
        
        # Update target position but don't seek yet (Winamp-style)
        self.seek_target = percentage * self.total_time
        self.seek_pending = True
        
        # Update visual progress immediately for feedback
        self.current_time = self.seek_target
        self.update_progress_display()
    
    def on_progress_release(self, event):
        """Handle releasing mouse on progress bar - actually seek now (Winamp-style)."""
        if hasattr(self, 'seek_pending') and self.seek_pending and hasattr(self, 'seek_target'):
            # Convert target time back to percentage for seeking
            percentage = self.seek_target / self.total_time
            self.seek_to_position(percentage)
            self.seek_pending = False
    
    def seek_to_position(self, percentage):
        """Seek to a specific position in the current song using mpv."""
        try:
            if self.current_song and hasattr(self, 'total_time') and self.total_time > 0:
                # Calculate target time in seconds
                target_time = percentage * self.total_time
                
                # Clamp target time to valid range (0.1s to 0.9s before end)
                target_time = max(0.1, min(target_time, self.total_time - 0.5))
                
                # Use mpv for real audio seeking
                if self.is_playing or self.is_paused:
                    try:
                        if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                            # Seek to the actual position in the audio using mpv
                            self.player.seek(target_time, reference='absolute')
                            
                            # Update current time to match seeked position
                            self.current_time = target_time
                            
                            # Update display immediately
                            self.update_progress_display()
                            
                        else:
                            # Fallback to pygame mixer (visual only)
                            self.current_time = target_time
                            self.update_progress_display()
                            
                    except Exception as e:
                        # Silently handle seeking errors (like seeking beyond song end)
                        if "Error running mpv command" not in str(e):
                            print(f"SEEK_ERROR: {e}")
                        # Fallback to visual seek
                        self.current_time = target_time
                        self.update_progress_display()
                        
        except Exception as e:
            print(f"SEEK_ERROR: {e}")
    
    def update_progress_display(self):
        """Update the progress bar display."""
        try:
            if hasattr(self, 'total_time') and self.total_time > 0:
                # Calculate percentage
                percentage = self.current_time / self.total_time
                percentage = max(0.0, min(1.0, percentage))
                
                # Update progress bar
                if hasattr(self, 'progress_fill') and hasattr(self, 'progress_bg'):
                    # Get the background width
                    self.progress_bg.update_idletasks()
                    bar_width = self.progress_bg.winfo_width()
                    if bar_width > 0:
                        fill_width = int(bar_width * percentage)
                        self.progress_fill.config(width=fill_width)
        except Exception as e:
            print(f"PROGRESS_ERROR: {e}")
    
    def format_time(self, seconds):
        """Format time in seconds to MM:SS format."""
        if seconds < 0:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def create_menu_bar(self):
        menubar = Menu(self.root, bg='#0d1117', fg='#f0f6fc', 
                      activebackground='#21262d', activeforeground='#4a9eff',
                      borderwidth=0, font=('Segoe UI', 10))
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = Menu(menubar, tearoff=0, bg='#161b22', fg='#f0f6fc',
                        activebackground='#21262d', activeforeground='#4a9eff',
                        font=('Segoe UI', 10))
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="🎵 Add Songs", command=self.add_songs)
        file_menu.add_command(label="📁 Add Folder", command=self.add_folder)
        file_menu.add_separator()
        file_menu.add_command(label="📂 Open Lyrics Folder", command=self.open_lyrics_folder)
        file_menu.add_command(label="⚙️ Settings", command=self.show_settings_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Exit", command=self.root.quit)
        
        # Themes Menu
        themes_menu = Menu(menubar, tearoff=0, bg='#161b22', fg='#f0f6fc',
                          activebackground='#21262d', activeforeground='#4a9eff',
                          font=('Segoe UI', 10))
        menubar.add_cascade(label="🎨 Themes", menu=themes_menu)
        themes_menu.add_command(label="🌙 Default", command=self.apply_dark_theme)
        if PEACH_THEME_AVAILABLE:
            themes_menu.add_command(label="🍑 Peach Theme", command=self.apply_peach_theme)
        themes_menu.add_command(label="☀️ Light Mode", command=lambda: None)  # Placeholder
        themes_menu.add_separator()
        themes_menu.add_command(label="🎨 Custom Theme...", command=lambda: None)  # Placeholder
        themes_menu.add_separator()
        themes_menu.add_command(label="⚙️ Theme Settings", command=lambda: None)  # Placeholder
        
        # Audio Menu
        audio_menu = Menu(menubar, tearoff=0, bg='#161b22', fg='#f0f6fc',
                         activebackground='#21262d', activeforeground='#4a9eff',
                         font=('Segoe UI', 10))
        menubar.add_cascade(label="🔊 Audio", menu=audio_menu)
        
        # Audio device submenu
        device_menu = Menu(audio_menu, tearoff=0, bg='#161b22', fg='#f0f6fc',
                          activebackground='#21262d', activeforeground='#4a9eff',
                          font=('Segoe UI', 10))
        audio_menu.add_cascade(label="🎧 Audio Device", menu=device_menu)
        
        # Store reference for updating checkmarks
        self.audio_device_menu = device_menu
        
        # Populate device menu dynamically
        self.populate_audio_device_menu(device_menu)
        
        audio_menu.add_separator()
        audio_menu.add_command(label="🔄 Refresh Devices", command=self.refresh_audio_devices)
        audio_menu.add_command(label="🔊 Test Device", command=self.show_device_test_dialog)
        audio_menu.add_command(label="🎵 Test MPV Devices", command=self.test_mpv_devices)
        audio_menu.add_separator()
        audio_menu.add_command(label="📝 Lyrics Font Size", command=self.show_font_size_dialog)
        
        # Help Menu
        help_menu = Menu(menubar, tearoff=0, bg='#161b22', fg='#f0f6fc',
                        activebackground='#21262d', activeforeground='#4a9eff',
                        font=('Segoe UI', 10))
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="ℹ️ About", command=self.show_about)
        
    def populate_audio_device_menu(self, device_menu):
        """Populate the audio device menu with available devices"""
        try:
            # Clear existing menu items
            device_menu.delete(0, 'end')
            
            # Get audio devices
            devices = self.get_audio_device_list_for_menu()
            
            # Add devices to menu with checkmarks
            for device in devices:
                device_name = device['name']
                device_desc = device['description']
                
                # Add checkmark if this is the current device
                checkmark = "✓ " if device_name == self.current_audio_device else ""
                
                # Create a command that switches to this device
                def switch_to_device(dev=device_name):
                    self.switch_audio_device(dev)
                    # Update checkmarks after switching
                    self.update_audio_device_checkmarks()
                
                device_menu.add_command(
                    label=f"{checkmark}{device_desc}", 
                    command=switch_to_device
                )
            
            print(f"Added {len(devices)} devices to audio menu")
            
        except Exception as e:
            print(f"Error populating audio device menu: {e}")
    
    def update_audio_device_checkmarks(self):
        """Update the checkmarks in the audio device menu"""
        if not self.audio_device_menu:
            return
        
        try:
            # Get current menu items
            devices = self.get_audio_device_list_for_menu()
            
            # Clear and rebuild menu with updated checkmarks
            self.audio_device_menu.delete(0, 'end')
            
            for device in devices:
                device_name = device['name']
                device_desc = device['description']
                
                # Add checkmark if this is the current device
                checkmark = "✓ " if device_name == self.current_audio_device else ""
                
                # Create a command that switches to this device
                def switch_to_device(dev=device_name):
                    self.switch_audio_device(dev)
                    self.update_audio_device_checkmarks()
                
                self.audio_device_menu.add_command(
                    label=f"{checkmark}{device_desc}", 
                    command=switch_to_device
                )
            
        except Exception as e:
            print(f"Error updating audio device checkmarks: {e}")
    
    def switch_audio_device(self, device_name):
        """Switch to a different audio device without changing the current song"""
        try:
            print(f"\n=== Switching to audio device: {device_name} ===")
            
            # Update current device tracking
            self.current_audio_device = device_name
            print(f"Current device set to: {device_name}")
            
            # Save the preference
            self.save_audio_device_preference()
            
            # Check if a song is currently playing
            song_was_playing = hasattr(self, 'is_playing') and self.is_playing and hasattr(self, 'current_song') and self.current_song
            
            # Save the current position if a song is playing
            current_position = None
            if song_was_playing:
                try:
                    if self.player and self.use_pygame_fallback == False:
                        current_position = self.player.time_pos
                        print(f"Current position: {current_position}")
                except Exception as e:
                    print(f"Could not get current position: {e}")
            
            # Handle different device types
            if device_name.startswith('sounddevice/'):
                # Extract device ID from sounddevice format
                device_id = device_name.replace('sounddevice/', '')
                try:
                    device_id = int(device_id)
                    print(f"Switching to SoundDevice ID: {device_id}")
                    
                    # Get the device name from sounddevice and try to find matching MPV device
                    if SOUNDDEVICE_AVAILABLE:
                        devices = sounddevice.query_devices()
                        if device_id < len(devices):
                            device_name_for_mpv = devices[device_id]['name']
                            print(f"Device name from SoundDevice: {device_name_for_mpv}")
                            
                            # Try to find matching MPV device by name
                            mpv_devices = self.detect_mpv_audio_devices()
                            matching_mpv_device = None
                            
                            for mpv_device in mpv_devices:
                                if device_name_for_mpv in mpv_device['description']:
                                    matching_mpv_device = mpv_device['name']
                                    print(f"Found matching MPV device: {matching_mpv_device}")
                                    break
                            
                            if matching_mpv_device:
                                self.reinitialize_mpv_with_device_name(matching_mpv_device)
                            else:
                                print("No matching MPV device found, using TV speakers")
                                tv_device = 'wasapi/{7f21c2ab-ae95-4bbb-aa98-9c593d04d4cf}'
                                self.reinitialize_mpv_with_device_name(tv_device)
                                self.current_audio_device = tv_device
                        else:
                            print("Invalid device ID")
                            return
                except ValueError:
                    print("Invalid device ID format")
                    return
            elif device_name.startswith('wasapi/') or device_name == 'openal':
                # Direct MPV device name
                print(f"Using direct MPV device name: {device_name}")
                self.reinitialize_mpv_with_device_name(device_name)
            else:
                # Fallback to TV speakers
                print(f"Unknown device format, falling back to TV speakers")
                tv_device = 'wasapi/{7f21c2ab-ae95-4bbb-aa98-9c593d04d4cf}'
                self.reinitialize_mpv_with_device_name(tv_device)
                self.current_audio_device = tv_device
            
            # Update checkmarks after successful switch
            self.root.after(100, self.update_audio_device_checkmarks)
            
            # Resume the same song at the same position if it was playing
            if song_was_playing and self.current_song:
                print(f"Resuming same song: {self.current_song}")
                if current_position and current_position > 0:
                    # Resume playing and seek to saved position
                    self.root.after(500, lambda: self.resume_song_at_position(current_position))
                else:
                    # Just resume playing from start
                    self.root.after(500, self.resume_current_song)
            
            return True
            
        except Exception as e:
            print(f"Error switching audio device: {e}")
            return False
    
    def reinitialize_mpv_with_device_name(self, device_name):
        """Reinitialize MPV player with a specific device name"""
        try:
            print(f"Reinitializing MPV with device: {device_name}")
            
            # Cleanup existing player
            if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                try:
                    self.player.terminate()
                except:
                    pass
            
            # Reinitialize MPV with new device
            if MPV_AVAILABLE and mpv:
                try:
                    if device_name == 'auto':
                        self.player = mpv.MPV(
                            ytdl=False, 
                            vo='null',  # No video output
                            ao='wasapi'  # Windows Audio Session API
                        )
                    else:
                        # Try to use the device name with WASAPI
                        self.player = mpv.MPV(
                            ytdl=False, 
                            vo='null',  # No video output
                            ao='wasapi',  # Windows Audio Session API
                            audio_device=device_name
                        )
                    
                    self.player.volume = 70  # Set initial volume
                    self.player.keep_open = 'no'
                    self.player.loop = 'no'
                    
                    self.use_pygame_fallback = False
                    print(f"MPV reinitialized with device: {device_name}")
                    
                    # Restart audio analysis if a song is currently playing
                    if hasattr(self, 'is_playing') and self.is_playing and hasattr(self, 'current_song') and self.current_song:
                        print("Restarting audio analysis after device switch")
                        self.root.after(100, self.restart_audio_analysis)
                    
                except Exception as e:
                    print(f"Failed to reinitialize MPV with device {device_name}: {e}")
                    # Fallback to auto
                    self.player = mpv.MPV(
                        ytdl=False, 
                        vo='null',  # No video output
                        ao='wasapi'  # Windows Audio Session API
                    )
                    self.player.volume = 70
                    self.use_pygame_fallback = False
                    print("MPV reinitialized with default device")
            
        except Exception as e:
            print(f"Error reinitializing MPV: {e}")
    
    def load_lyrics_font_size_preference(self):
        """Load the saved lyrics font size preference"""
        try:
            config_file = 'lyrics_font_config.txt'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_size = f.read().strip()
                    if saved_size and saved_size.isdigit():
                        self.lyrics_font_size = int(saved_size)
                        print(f"Loaded saved lyrics font size: {self.lyrics_font_size}")
                    else:
                        print("No valid saved font size found, using default")
        except Exception as e:
            print(f"Error loading lyrics font size preference: {e}")
    
    def save_lyrics_font_size_preference(self):
        """Save the current lyrics font size preference"""
        try:
            config_file = 'lyrics_font_config.txt'
            with open(config_file, 'w') as f:
                f.write(str(self.lyrics_font_size))
            print(f"Saved lyrics font size preference: {self.lyrics_font_size}")
        except Exception as e:
            print(f"Error saving lyrics font size preference: {e}")
    
    def update_lyrics_font_size(self, new_size):
        """Update the lyrics font size and refresh the display"""
        try:
            self.lyrics_font_size = new_size
            self.save_lyrics_font_size_preference()
            
            # Update the lyrics text widget font
            if hasattr(self, 'lyrics_text'):
                self.lyrics_text.config(font=('Segoe UI', self.lyrics_font_size))
                
                # Update the current line highlighting font for synced lyrics
                if hasattr(self, 'lyrics_text'):
                    self.lyrics_text.tag_config("current", background="#FFB366", foreground="#000000", 
                                              font=('Segoe UI', self.lyrics_font_size, 'bold'))
                
                print(f"Updated lyrics font size to: {self.lyrics_font_size}")
                
                # Refresh the display without re-processing lyrics content
                # Just update the font without calling update_lyrics_display
                if hasattr(self, 'current_lyrics_content') and self.current_lyrics_content:
                    # Get the current displayed text to preserve it
                    current_displayed_text = self.lyrics_text.get("1.0", tk.END).strip()
                    
                    # If we have synced lyrics active, don't disturb it
                    if hasattr(self, 'lyrics_lines') and self.lyrics_lines:
                        # Synced lyrics are active, just update fonts
                        pass
                    else:
                        # Plain text lyrics - just update font without content changes
                        pass
            
        except Exception as e:
            print(f"Error updating lyrics font size: {e}")
    
    def show_font_size_dialog(self):
        """Show a dialog to adjust lyrics font size"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Lyrics Font Size")
        dialog.geometry("400x300")
        dialog.configure(bg='#21262d')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Title
        title_label = tk.Label(dialog, text="Adjust Lyrics Font Size", 
                              font=('Segoe UI', 12, 'bold'), 
                              bg='#21262d', fg='#f0f6fc')
        title_label.pack(pady=20)
        
        # Current size display
        size_frame = tk.Frame(dialog, bg='#21262d')
        size_frame.pack(pady=10)
        
        tk.Label(size_frame, text="Current Size:", 
                font=('Segoe UI', 10), 
                bg='#21262d', fg='#8b949e').pack(side=tk.LEFT, padx=5)
        
        size_label = tk.Label(size_frame, text=str(self.lyrics_font_size), 
                             font=('Segoe UI', 14, 'bold'), 
                             bg='#21262d', fg='#58a6ff')
        size_label.pack(side=tk.LEFT)
        
        # Slider for font size
        slider_frame = tk.Frame(dialog, bg='#21262d')
        slider_frame.pack(pady=20, padx=20, fill=tk.X)
        
        font_slider = tk.Scale(slider_frame, from_=8, to=24, orient=tk.HORIZONTAL,
                              bg='#21262d', fg='#f0f6fc', troughcolor='#30363d',
                              activebackground='#58a6ff', highlightthickness=0,
                              command=lambda v: size_label.config(text=str(int(float(v)))))
        font_slider.set(self.lyrics_font_size)
        font_slider.pack(fill=tk.X)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#21262d')
        button_frame.pack(pady=20)
        
        def apply_font_size():
            new_size = int(font_slider.get())
            self.update_lyrics_font_size(new_size)
            dialog.destroy()
        
        tk.Button(button_frame, text="Apply", command=apply_font_size,
                 bg='#238636', fg='white', font=('Segoe UI', 10),
                 activebackground='#2ea043', activeforeground='white',
                 borderwidth=0, padx=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg='#da3633', fg='white', font=('Segoe UI', 10),
                 activebackground='#f85149', activeforeground='white',
                 borderwidth=0, padx=20).pack(side=tk.LEFT, padx=5)
    
    def load_audio_device_preference(self):
        """Load the saved audio device preference"""
        try:
            config_file = 'audio_device_config.txt'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_device = f.read().strip()
                    if saved_device:
                        self.current_audio_device = saved_device
                        print(f"Loaded saved audio device: {saved_device}")
                    else:
                        print("No saved audio device found, will use default")
                        self.current_audio_device = None
            else:
                print("No audio device config file, will use default")
                self.current_audio_device = None
        except Exception as e:
            print(f"Error loading audio device preference: {e}")
            self.current_audio_device = None
    
    def resume_song_at_position(self, position):
        """Resume the current song at a specific position"""
        try:
            print(f"Resuming song at position: {position}")
            if self.player and not self.use_pygame_fallback:
                # Reload the song first
                self.player.play(self.current_song)
                # Wait a bit then seek to the saved position
                self.root.after(500, lambda: self.seek_to_position(position / self.total_time))
        except Exception as e:
            print(f"Error resuming song at position: {e}")
    
    def restart_audio_analysis(self):
        """Restart audio analysis after device switch"""
        try:
            # Stop current analysis
            self.stop_audio_analysis()
            
            # Restart analysis if song is playing
            if hasattr(self, 'is_playing') and self.is_playing:
                self.start_audio_analysis()
                print("Audio analysis restarted successfully")
        except Exception as e:
            print(f"Error restarting audio analysis: {e}")
    
    def restart_song_with_device(self, position):
        """Restart the current song at a specific position"""
        try:
            if self.current_song:
                print(f"Restarting song: {self.current_song}")
                self.play_selected_song()
                
                # Seek to the saved position after a short delay
                if position and position > 0:
                    self.root.after(500, lambda: self.seek_to_position(position / self.total_time))
                    
        except Exception as e:
            print(f"Error restarting song: {e}")
    
    def detect_mpv_audio_devices(self):
        """Detect audio devices that MPV can actually use"""
        if not MPV_AVAILABLE or not mpv:
            print("MPV not available for device detection")
            return []
        
        try:
            print("Detecting MPV-compatible audio devices...")
            
            # Create a temporary MPV instance to query devices
            temp_player = mpv.MPV(ytdl=False, vo='null', ao='wasapi')
            
            try:
                # Try to get device list - this might not work on all MPV versions
                devices = temp_player.audio_device_list
                print(f"MPV detected {len(devices)} devices:")
                
                mpv_devices = []
                for device in devices:
                    device_info = {
                        'name': device['name'],
                        'description': device.get('description', device['name'])
                    }
                    # Only add devices that are not 'auto'
                    if device['name'] != 'auto':
                        mpv_devices.append(device_info)
                        print(f"  MPV Device: {device['name']} - {device.get('description', 'No description')}")
                    else:
                        print(f"  Skipping auto device: {device['name']}")
                
                temp_player.terminate()
                print(f"Filtered to {len(mpv_devices)} usable MPV devices")
                return mpv_devices
                
            except Exception as e:
                print(f"MPV device detection failed: {e}")
                temp_player.terminate()
                
                # Fallback: try common device names that might work (no auto)
                fallback_devices = [
                    {'name': 'wasapi/{7f21c2ab-ae95-4bbb-aa98-9c593d04d4cf}', 'description': 'NS-L42Q-10A (NVIDIA High Definition Audio) - TV SPEAKERS'},
                    {'name': 'wasapi/{d09eb373-46c6-4b52-b5e5-62bf7db4f27f}', 'description': 'Speakers (Realtek(R) Audio)'},
                    {'name': 'wasapi/{0757638a-c393-4a30-a4a7-8cbf05bb8951}', 'description': 'MSI G244F E2 (NVIDIA High Definition Audio)'},
                ]
                
                print("Using fallback MPV device list:")
                for device in fallback_devices:
                    print(f"  {device['name']} - {device['description']}")
                
                return fallback_devices
                
        except Exception as e:
            print(f"Error creating MPV for device detection: {e}")
            return []
    
    def test_audio_output_device(self, device_id):
        """Test a specific audio device by playing a short test tone"""
        if not SOUNDDEVICE_AVAILABLE:
            print("SoundDevice not available for testing")
            return
        
        try:
            print(f"\n🔊 Testing audio device ID {device_id}...")
            
            # Get device info
            devices = sounddevice.query_devices()
            if device_id >= len(devices):
                print(f"Invalid device ID: {device_id}")
                return
            
            device = devices[device_id]
            print(f"Device: {device['name']}")
            print(f"Host API: {sounddevice.query_hostapis()[device['hostapi']]['name']}")
            print("🎵 Playing test tone... (listen for sound)")
            
            # Generate a simple test tone (440 Hz for 2 seconds)
            sample_rate = int(device['default_samplerate'])
            duration = 2  # seconds
            frequency = 440  # Hz (A4 note)
            
            # Generate sine wave
            import numpy as np
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = 0.3 * np.sin(frequency * t * 2 * np.pi)
            
            # Make stereo if device supports it
            if device['max_output_channels'] >= 2:
                tone = np.column_stack((tone, tone))
            
            # Play the tone
            sounddevice.play(tone, samplerate=sample_rate, device=device_id)
            sounddevice.wait()
            
            print("✅ Test completed!")
            
        except Exception as e:
            print(f"❌ Error testing device {device_id}: {e}")
    
    def show_device_test_dialog(self):
        """Show a dialog to test audio devices"""
        if not SOUNDDEVICE_AVAILABLE:
            from tkinter import messagebox
            messagebox.showerror("Error", "SoundDevice library not available. Install with: pip install sounddevice")
            return
        
        # Create a simple dialog
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Test Audio Devices")
        dialog.geometry("400x300")
        dialog.configure(bg='#161b22')
        
        tk.Label(dialog, text="Select a device to test:", bg='#161b22', fg='#f0f6fc', 
                font=('Segoe UI', 12)).pack(pady=10)
        
        # Get devices
        devices = self.detect_audio_devices_sounddevice()
        
        if not devices:
            tk.Label(dialog, text="No audio devices found!", bg='#161b22', fg='#ff6b6b',
                    font=('Segoe UI', 10)).pack(pady=20)
            return
        
        # Create device list
        device_var = tk.StringVar()
        device_list = ttk.Combobox(dialog, textvariable=device_var, width=50)
        device_list['values'] = [f"{d['id']}: {d['name']}" for d in devices]
        device_list.pack(pady=10, padx=20)
        
        if devices:
            device_list.current(0)  # Select first device
        
        def test_selected():
            selected = device_var.get()
            if selected:
                device_id = int(selected.split(':')[0])
                self.test_audio_output_device(device_id)
                messagebox.showinfo("Test", f"Test completed for device {device_id}!\n\nDid you hear the test tone?")
        
        tk.Button(dialog, text="🔊 Test Device", command=test_selected,
                 bg='#238636', fg='white', font=('Segoe UI', 10),
                 padx=20, pady=10).pack(pady=20)
        
        tk.Button(dialog, text="Close", command=dialog.destroy,
                 bg='#da3633', fg='white', font=('Segoe UI', 10),
                 padx=20, pady=5).pack()
        
        # Add instructions
        instructions = """
💡 Instructions:
1. Select a device from the list
2. Click 'Test Device' 
3. Listen for the test tone
4. Try different NS-L42Q-10A devices to find your TV

📺 Look for devices with:
- Windows DirectSound or Windows WASAPI
- 2+ channels (stereo)
- 48000 Hz sample rate
        """
        tk.Label(dialog, text=instructions, bg='#161b22', fg='#8b949e',
                font=('Segoe UI', 9), justify=tk.LEFT).pack(pady=10, padx=20)
    
    def test_mpv_devices(self):
        """Test MPV device detection and try playing through MPV"""
        try:
            print("\n🎵 Testing MPV Audio Devices...")
            
            # Detect MPV devices
            mpv_devices = self.detect_mpv_audio_devices()
            
            if not mpv_devices:
                print("No MPV devices detected!")
                return
            
            # Try to test each MPV device with a short audio file
            print("Testing MPV device switching...")
            
            for device in mpv_devices:
                device_name = device['name']
                description = device['description']
                
                print(f"\n🎵 Testing MPV device: {device_name}")
                print(f"   Description: {description}")
                
                try:
                    # Create a temporary MPV instance with this device
                    test_player = mpv.MPV(
                        ytdl=False, 
                        vo='null', 
                        ao='wasapi',
                        audio_device=device_name if device_name != 'auto' else None
                    )
                    
                    print(f"   ✅ MPV initialized successfully with {device_name}")
                    
                    # Try to set volume
                    test_player.volume = 50
                    
                    # Note: We can't easily play a test tone with MPV without a file
                    # But we can confirm the device was accepted
                    print(f"   ✅ Device {device_name} is accepted by MPV")
                    
                    test_player.terminate()
                    
                except Exception as e:
                    print(f"   ❌ Failed to initialize MPV with {device_name}: {e}")
            
            print("\n💡 If a device shows 'accepted by MPV', try selecting it from Audio → Audio Device")
            print("💡 Then play a song to see if it comes out your TV speakers!")
            
        except Exception as e:
            print(f"Error testing MPV devices: {e}")
    
    def refresh_audio_devices(self):
        """Refresh the audio device list and update menu"""
        try:
            print("Refreshing audio devices...")
            
            # Re-detect devices
            if SOUNDDEVICE_AVAILABLE:
                devices = self.detect_audio_devices_sounddevice()
                print(f"Detected {len(devices)} audio devices")
            
            # Update the menu (need to find the device menu first)
            # For simplicity, we'll just show a message
            from tkinter import messagebox
            messagebox.showinfo("Audio Devices", f"Audio device list refreshed!\n\nDetected {len(devices) if SOUNDDEVICE_AVAILABLE else 0} devices.\n\nCheck the Audio → Audio Device menu for updated options.")
            
        except Exception as e:
            print(f"Error refreshing audio devices: {e}")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to refresh audio devices: {e}")

    def create_player_controls(self, parent):
        frame_player_controls = ModernFrame(parent, bg='#161b22', name='player_controls_frame')
        frame_player_controls.pack(fill=tk.X, pady=(0, 0))
        frame_player_controls.pack_propagate(False)
        frame_player_controls.config(width=540, height=70)  # Increased to match 550px left frame
        
        # Control buttons and volume in same row
        frame_control_buttons = ModernFrame(frame_player_controls, bg='#161b22', name='controls_frame')
        frame_control_buttons.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Control buttons with custom icons
        try:
            # Previous button frame (vertical layout)
            frame_btn_previous = ModernFrame(frame_control_buttons, bg='#161b22', name='prev_btn_frame')
            frame_btn_previous.pack(side=tk.LEFT, padx=4)  # Reduced from 8 to 4
            
            self.prev_btn = ImageButton(
                frame_btn_previous, 
                os.path.join(self.assets_dir, "back-button.png"),
                command=self.previous_song
            )
            self.prev_btn.pack(side=tk.TOP, pady=(0, 1))
            
            # Previous label below button
            label_btn_previous = ModernLabel(
                frame_btn_previous,
                text="Previous",
                font=('Segoe UI', 8),
                bg='#161b22',
                fg='#8b949e',
                name='prev_btn_label'
            )
            label_btn_previous.pack(side=tk.TOP, pady=(0, 0))
            
            # Play button frame (vertical layout)
            frame_btn_play = ModernFrame(frame_control_buttons, bg='#161b22', name='play_btn_frame')
            frame_btn_play.pack(side=tk.LEFT, padx=4)  # Reduced from 8 to 4
            
            self.play_btn = ImageButton(
                frame_btn_play, 
                os.path.join(self.assets_dir, "btn_play.png"),
                command=self.play_song
            )
            self.play_btn.pack(side=tk.TOP, pady=(0, 1))
            
            # Play label below button
            label_btn_play = ModernLabel(
                frame_btn_play,
                text="Play",
                font=('Segoe UI', 8),
                bg='#161b22',
                fg='#8b949e',
                name='play_btn_label'
            )
            label_btn_play.pack(side=tk.TOP, pady=(0, 0))
            
            # Pause button frame (vertical layout)
            frame_btn_pause = ModernFrame(frame_control_buttons, bg='#161b22', name='pause_btn_frame')
            frame_btn_pause.pack(side=tk.LEFT, padx=4)  # Reduced from 8 to 4
            
            self.pause_btn = ImageButton(
                frame_btn_pause, 
                os.path.join(self.assets_dir, "btn_pause.png"),
                command=self.pause_song
            )
            self.pause_btn.pack(side=tk.TOP, pady=(0, 1))
            
            # Pause label below button
            label_btn_pause = ModernLabel(
                frame_btn_pause,
                text="Pause",
                font=('Segoe UI', 8),
                bg='#161b22',
                fg='#8b949e',
                name='pause_btn_label'
            )
            label_btn_pause.pack(side=tk.TOP, pady=(0, 0))
            
            # Stop button frame (vertical layout)
            frame_btn_stop = ModernFrame(frame_control_buttons, bg='#161b22', name='stop_btn_frame')
            frame_btn_stop.pack(side=tk.LEFT, padx=4)  # Reduced from 8 to 4
            
            self.stop_btn = ImageButton(
                frame_btn_stop, 
                os.path.join(self.assets_dir, "btn_stop.png"),
                command=self.stop_song
            )
            self.stop_btn.pack(side=tk.TOP, pady=(0, 1))
            
            # Stop label below button
            label_btn_stop = ModernLabel(
                frame_btn_stop,
                text="Stop",
                font=('Segoe UI', 8),
                bg='#161b22',
                fg='#8b949e',
                name='stop_btn_label'
            )
            label_btn_stop.pack(side=tk.TOP, pady=(0, 0))
            
            # Next button frame (vertical layout)
            frame_btn_next = ModernFrame(frame_control_buttons, bg='#161b22', name='next_btn_frame')
            frame_btn_next.pack(side=tk.LEFT, padx=4)  # Reduced from 8 to 4
            
            self.next_btn = ImageButton(
                frame_btn_next, 
                os.path.join(self.assets_dir, "next-button.png"),
                command=self.next_song
            )
            self.next_btn.pack(side=tk.TOP, pady=(0, 1))
            
            # Next label below button
            label_btn_next = ModernLabel(
                frame_btn_next,
                text="Next",
                font=('Segoe UI', 8),
                bg='#161b22',
                fg='#8b949e',
                name='next_btn_label'
            )
            label_btn_next.pack(side=tk.TOP, pady=(0, 0))
            
            # Create a frame for shuffle button and status (vertical layout)
            frame_btn_shuffle = ModernFrame(frame_control_buttons, bg='#161b22', name='shuffle_btn_frame')
            frame_btn_shuffle.pack(side=tk.LEFT, padx=4, pady=0)  # Reduced from 8 to 4  # Remove vertical padding
            
            # Shuffle button in its own frame
            self.shuffle_btn = ImageButton(
                frame_btn_shuffle, 
                os.path.join(self.assets_dir, "shuffle.png"),
                command=self.toggle_shuffle
            )
            self.shuffle_btn.pack(side=tk.TOP, pady=(0, 1))  # Reduce padding
            
            # Shuffle status label below shuffle button
            self.shuffle_status_label = ModernLabel(
                frame_btn_shuffle,
                text="Shuffle: OFF",
                font=('Segoe UI', 9),
                bg='#161b22',
                fg='#8b949e',
                name='shuffle_status_label'
            )
            self.shuffle_status_label.pack(side=tk.TOP, pady=(0, 0))  # Remove padding
            
        except Exception as e:
            # Fallback to text buttons if images fail
            button_config = {
                'font': ('Segoe UI', 10, 'bold'),
                'width': 8,
                'height': 1,
                'cursor': 'hand2',
                'bg': '#30363d',
                'activebackground': '#21262d',
                'fg': 'white',
                'relief': tk.RAISED
            }
            
            self.prev_btn = tk.Button(frame_control_buttons, text="⏮", command=self.previous_song, **button_config)
            self.prev_btn.pack(side=tk.LEFT, padx=5)
            
            self.play_btn = tk.Button(frame_control_buttons, text="▶", command=self.play_song, **button_config)
            self.play_btn.pack(side=tk.LEFT, padx=5)
            
            self.pause_btn = tk.Button(frame_control_buttons, text="⏸", command=self.pause_song, **button_config)
            self.pause_btn.pack(side=tk.LEFT, padx=5)
            
            self.stop_btn = tk.Button(frame_control_buttons, text="⏹", command=self.stop_song, **button_config)
            self.stop_btn.pack(side=tk.LEFT, padx=5)
            
            self.next_btn = tk.Button(frame_control_buttons, text="⏭", command=self.next_song, **button_config)
            self.next_btn.pack(side=tk.LEFT, padx=5)
            
            self.shuffle_btn = tk.Button(frame_control_buttons, text="🔀", command=self.toggle_shuffle, **button_config)
            self.shuffle_btn.pack(side=tk.LEFT, padx=5)
        
        # Volume controls on right side in same row
        frame_volume_controls = ModernFrame(frame_player_controls, bg='#161b22', name='volume_frame')
        frame_volume_controls.pack(side=tk.RIGHT, padx=(10, 3), pady=5)  # Reduced right padding from 10 to 3px
        
        try:
            # Mute button
            self.mute_btn = ImageButton(
                frame_volume_controls, 
                os.path.join(self.assets_dir, "btn_mute.png"),
                command=self.toggle_mute
            )
            self.mute_btn.pack(side=tk.LEFT, padx=(0, 10))
        except:
            self.mute_btn = tk.Button(frame_volume_controls, text="🔊", command=self.toggle_mute, 
                                     bg='#30363d', fg='white', font=('Segoe UI', 10),
                                     cursor='hand2', relief=tk.RAISED)
            self.mute_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Modern volume slider
        self.volume_slider = tk.Scale(
            frame_volume_controls, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL,
            command=self.set_volume,
            bg='#21262d',
            fg='#4a9eff',
            troughcolor='#30363d',
            activebackground='#4a9eff',
            highlightthickness=1,      # Add border
            highlightbackground='#4A6984',  # Better contrast border color
            borderwidth=0,              # No additional border
            length=150,
            showvalue=False,
            name='volume_slider'
        )
        self.volume_slider.set(70)
        self.volume_slider.pack(side=tk.LEFT)
        
        # Volume percentage label
        self.volume_label = ModernLabel(frame_volume_controls, text="70%", font=('Segoe UI', 9), bg='#161b22', fg='#8b949e', width=5, anchor='center', name='volume_label')  # Width 5 chars for "100%", centered
        self.volume_label.pack(side=tk.LEFT, padx=(5, 0))
        
    def create_playlist(self, parent):
        frame_playlist_main = ModernFrame(parent, bg='#161b22', name='playlist_frame')
        frame_playlist_main.pack(fill=tk.BOTH, expand=True)
        
        # Playlist header
        frame_playlist_header = ModernFrame(frame_playlist_main, bg='#21262d', height=40, name='playlist_header_frame')
        frame_playlist_header.pack(fill=tk.X)
        frame_playlist_header.pack_propagate(False)
        
        label_playlist_header = ModernLabel(
            frame_playlist_header, 
            text="📋 Playlist", 
            font=('Segoe UI', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            name='playlist_header_label'
        )
        label_playlist_header.pack(side=tk.LEFT, padx=8, pady=8)
        
        # Search box
        frame_playlist_search = ModernFrame(frame_playlist_header, bg='#21262d', name='search_frame')
        frame_playlist_search.pack(side=tk.LEFT, padx=8, pady=8, fill=tk.X, expand=True)
        
        # Search entry with modern styling
        self.search_var = tk.StringVar()
        # Don't bind trace yet - will do it after treeview is created
        
        # Create a frame for search entry with inline clear button
        frame_search_entry = ModernFrame(frame_playlist_search, bg='#0d1117', relief=tk.FLAT, highlightthickness=1, highlightbackground='#30363d', highlightcolor='#1f6feb', name='search_entry_frame')
        frame_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0, pady=0)
        
        self.search_entry = tk.Entry(
            frame_search_entry,
            textvariable=self.search_var,
            font=('Segoe UI', 10),
            bg='#0d1117',
            fg='#f0f6fc',
            insertbackground='#4a9eff',
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            name='search_entry'
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0)
        
        # Inline clear button inside the search box (circular using Canvas)
        self.clear_search_canvas = tk.Canvas(
            frame_search_entry,
            width=16,
            height=16,
            bg='#0d1117',
            highlightthickness=0,
            bd=0
        )
        self.clear_search_canvas.place(relx=1.0, rely=0.5, anchor='e', x=-8, y=-1)
        
        # Draw circular background
        self.clear_search_canvas.create_oval(2, 2, 14, 14, fill='#30363d', outline='#30363d')
        # Draw X symbol
        self.clear_search_canvas.create_text(8, 8, text="✕", font=('Segoe UI', 8, 'bold'), fill='#f0f6fc')
        
        # Bind events
        self.clear_search_canvas.bind('<Button-1>', self.clear_search)
        self.clear_search_canvas.bind('<Enter>', self.on_clear_button_enter)
        self.clear_search_canvas.bind('<Leave>', self.on_clear_button_leave)
        
        # Initially hide clear button
        self.clear_search_canvas.place_forget()
        
        # Add placeholder text
        self.search_entry.insert(0, "🔍 Search artist or song...")
        self.search_entry.bind('<FocusIn>', self.on_search_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_search_focus_out)
        
        # Bind text change to show/hide clear button
        self.search_var.trace('w', self.update_clear_button_visibility)
        
        # Playlist control buttons
        frame_playlist_controls = ModernFrame(frame_playlist_header, bg='#21262d', name='playlist_buttons_frame')
        frame_playlist_controls.pack(side=tk.RIGHT, padx=8, pady=8)
        
        small_button_style = {
            'font': ('Segoe UI', 9),
            'bg': '#30363d',
            'activebackground': '#21262d',
            'width': 8,
            'height': 1,
            'cursor': 'hand2',
            'fg': 'white',
            'relief': tk.RAISED
        }
        
        tk.Button(frame_playlist_controls, text="Clear", command=self.clear_playlist, **small_button_style).pack(side=tk.RIGHT, padx=2)
        tk.Button(frame_playlist_controls, text="Remove", command=self.remove_from_playlist, **small_button_style).pack(side=tk.RIGHT, padx=2)
        tk.Button(frame_playlist_controls, text="Edit", command=self.edit_playlist, **small_button_style).pack(side=tk.RIGHT, padx=2)
        
        # Playlist listbox with modern styling using Treeview for columns
        frame_playlist_listbox = ModernFrame(frame_playlist_main, bg='#0d1117', name='playlist_listbox_frame')
        frame_playlist_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for column layout
        self.playlist_treeview = ttk.Treeview(
            frame_playlist_listbox,
            columns=('star', 'position', 'name', 'length'),
            show='headings',
            height=15,
            name='playlist_treeview'
        )
        
        # Configure columns - adjusted for 400px frame width
        self.playlist_treeview.column('star', width=20, anchor='center')  # Star column
        self.playlist_treeview.column('position', width=40, anchor='center')  # Reduced from 50
        self.playlist_treeview.column('name', width=250, anchor='w')  # Reduced from 400
        self.playlist_treeview.column('length', width=60, anchor='center')  # Reduced from 80
        
        # Configure headings
        self.playlist_treeview.heading('star', text='')  # Empty heading for star
        self.playlist_treeview.heading('position', text='#')
        self.playlist_treeview.heading('name', text='Song')
        self.playlist_treeview.heading('length', text='Length')
        
        # Style the treeview
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            'Custom.Treeview',
            background='#0d1117',
            foreground='#f0f6fc',
            fieldbackground='#0d1117',
            borderwidth=0,
            font=('Segoe UI', 10)
        )
        self.playlist_treeview.configure(style='Custom.Treeview')
        
        # Bind right-click for context menu
        self.playlist_treeview.bind('<Button-3>', self.show_playlist_context_menu)
        
        # Bind single-click for lyrics fetching
        self.playlist_treeview.bind('<ButtonRelease-1>', self.on_playlist_single_click)
        
        style.configure(
            'Custom.Treeview.Heading',
            background='#21262d',
            foreground='#8b949e',
            font=('Segoe UI', 10, 'bold')
        )
        style.map(
            'Custom.Treeview',
            'Treeview',
            background=[('selected', '#1f6feb')],
            foreground=[('selected', '#ffffff')]
        )
        
        self.playlist_treeview.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.playlist_treeview.bind('<Double-1>', self.on_playlist_double_click)
        
        # Scrollbar - simple approach
        scrollbar_playlist = ttk.Scrollbar(frame_playlist_listbox, orient=tk.VERTICAL, command=self.playlist_treeview.yview)
        scrollbar_playlist.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_treeview.config(yscrollcommand=scrollbar_playlist.set)
        
        # Now bind the search trace since treeview is created
        if hasattr(self, 'search_var'):
            self.search_var.trace('w', self.filter_playlist)
        
    def create_lyrics_window(self, parent):
        frame_lyrics_main = ModernFrame(parent, bg='#161b22', width=450, name='lyrics_frame')  # Increased from 400 to 450
        frame_lyrics_main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        frame_lyrics_main.pack_propagate(False)
        
        # Lyrics header
        frame_lyrics_header = ModernFrame(frame_lyrics_main, bg='#21262d', height=40, name='lyrics_header_frame')
        frame_lyrics_header.pack(fill=tk.X)
        frame_lyrics_header.pack_propagate(False)
        
        label_lyrics_header = ModernLabel(
            frame_lyrics_header, 
            text="📝 Lyrics", 
            font=('Segoe UI', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc',
            name='lyrics_header_label'
        )
        label_lyrics_header.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Status indicator
        self.lyrics_status_label = ModernLabel(
            frame_lyrics_header,
            text="",
            font=('Segoe UI', 10),
            bg='#21262d',
            fg='#8b949e',
            name='lyrics_status_label'
        )
        self.lyrics_status_label.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Edit lyrics button
        self.edit_lyrics_btn = tk.Button(
            frame_lyrics_header,
            text="✏️ Edit",
            font=('Segoe UI', 9),
            bg='#30363d',
            fg='#f0f6fc',
            activebackground='#58a6ff',
            activeforeground='white',
            relief=tk.RAISED,
            cursor='hand2',
            command=self.edit_current_lyrics,
            padx=8,
            pady=4
        )
        self.edit_lyrics_btn.pack(side=tk.RIGHT, padx=5, pady=8)  # Reduced padding from 15px to 5px
        # Initially disable edit button until lyrics are loaded
        self.edit_lyrics_btn.config(state=tk.DISABLED)
        
        # Open lyrics folder button
        self.open_lyrics_folder_btn = tk.Button(
            frame_lyrics_header,
            text="📂 Open Folder",
            font=('Segoe UI', 9),
            bg='#238636',
            fg='white',
            activebackground='#2ea043',
            activeforeground='white',
            relief=tk.RAISED,
            cursor='hand2',
            command=self.open_lyrics_folder,
            padx=8,
            pady=4
        )
        self.open_lyrics_folder_btn.pack(side=tk.RIGHT, padx=(0, 0), pady=8)
        
        # Lyrics text area with modern styling
        frame_lyrics_text = ModernFrame(frame_lyrics_main, bg='#0d1117', name='lyrics_text_frame')
        frame_lyrics_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Store reference for theme updates
        self.lyrics_text_frame = frame_lyrics_text
        
        # Create lyrics text widget
        self.lyrics_text = tk.Text(
    frame_lyrics_text,
    bg='#0d1117',
    fg='#f0f6fc',
    font=('Segoe UI', self.lyrics_font_size),
    wrap=tk.WORD,
    state=tk.DISABLED,
    borderwidth=0,
    highlightthickness=0,
    relief=tk.FLAT,
    insertbackground='#4a9eff',
    selectbackground='#1f6feb',
    selectforeground='#ffffff',
    name='lyrics_text'
)
        # Create smart scrollbar (initially hidden)
        self.lyrics_scrollbar = ttk.Scrollbar(frame_lyrics_text, orient=tk.VERTICAL, command=self.lyrics_text.yview)
        self.lyrics_text.config(yscrollcommand=self.lyrics_scrollbar.set)
        
        # Use grid layout for better control
        self.lyrics_text.grid(row=0, column=0, sticky='nsew')
        self.lyrics_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Configure grid weights
        frame_lyrics_text.grid_rowconfigure(0, weight=1)
        frame_lyrics_text.grid_columnconfigure(0, weight=1)
        frame_lyrics_text.grid_columnconfigure(1, weight=0)
        
        # Initially hide scrollbar
        self.lyrics_scrollbar.grid_remove()
        
    def get_song_metadata(self, file_path):
        """Extract metadata from audio file"""
        filename = os.path.basename(file_path)
        
        try:
            # Try to get metadata using mutagen
            audio = mutagen.File(file_path)
            if audio is not None:
                # Get title and artist
                title = "Unknown Title"
                artist = "Unknown Artist"
                
                if hasattr(audio, 'get'):
                    # Try different metadata keys for various formats
                    title_keys = ['TIT2', 'TITLE', '\xa9nam', 'TITLE']  # ID3, Vorbis, MP4
                    artist_keys = ['TPE1', 'TPE2', 'ARTIST', '\xa9ART', 'ARTIST']  # ID3, Vorbis, MP4
                    
                    # Extract title
                    for key in title_keys:
                        if key in audio and audio[key]:
                            title_value = audio[key]
                            if isinstance(title_value, list):
                                title = str(title_value[0])
                            else:
                                title = str(title_value)
                            # Clean up the title - remove extra whitespace and quotes
                            title = title.strip().strip('"\'')
                            if title and title != "Unknown Title":
                                break
                    
                    # Extract artist
                    for key in artist_keys:
                        if key in audio and audio[key]:
                            artist_value = audio[key]
                            if isinstance(artist_value, list):
                                artist = str(artist_value[0])
                            else:
                                artist = str(artist_value)
                            # Clean up the artist - remove extra whitespace and quotes
                            artist = artist.strip().strip('"\'')
                            if artist and artist != "Unknown Artist":
                                break
                
                # Get duration
                duration = getattr(audio, 'info', None)
                length = "0:00"
                if duration and hasattr(duration, 'length'):
                    seconds = int(duration.length)
                    minutes = seconds // 60
                    seconds = seconds % 60
                    length = f"{minutes}:{seconds:02d}"
                
                # If we still have unknown values, try to parse from filename as fallback
                if title == "Unknown Title" or artist == "Unknown Artist":
                    name_without_ext = os.path.splitext(filename)[0]
                    # Try to parse "Artist - Title" format
                    if ' - ' in name_without_ext:
                        parts = name_without_ext.split(' - ', 1)
                        if len(parts) == 2:
                            # Remove track numbers from the beginning (e.g., "03 - ")
                            artist_part = parts[0].strip()
                            title_part = parts[1].strip()
                            
                            # Remove leading numbers from artist part if it looks like a track number
                            if artist_part and artist_part[0].isdigit():
                                artist_part = ' - '.join(artist_part.split(' - ')[1:]) if ' - ' in artist_part else artist_part
                                artist_part = artist_part.lstrip('0123456789. ').strip()
                            
                            if title == "Unknown Title" and title_part:
                                title = title_part
                            if artist == "Unknown Artist" and artist_part:
                                artist = artist_part
                    else:
                        # Single filename without separator, use as title
                        if title == "Unknown Title":
                            # Remove track numbers from beginning
                            clean_name = name_without_ext.lstrip('0123456789. ').strip()
                            title = clean_name
                
                return {
                    'title': title,
                    'artist': artist,
                    'display_name': f"{artist} - {title}",
                    'length': length
                }
        except Exception as e:
            pass
        
        # Fallback to filename parsing
        name_without_ext = os.path.splitext(filename)[0]
        title = name_without_ext
        artist = "Unknown Artist"
        
        # Try to parse "Artist - Title" format from filename
        if ' - ' in name_without_ext:
            parts = name_without_ext.split(' - ', 1)
            if len(parts) == 2:
                artist_part = parts[0].strip()
                title_part = parts[1].strip()
                
                # Remove track numbers from the beginning
                if artist_part and artist_part[0].isdigit():
                    artist_part = ' - '.join(artist_part.split(' - ')[1:]) if ' - ' in artist_part else artist_part
                    artist_part = artist_part.lstrip('0123456789. ').strip()
                
                artist = artist_part if artist_part else "Unknown Artist"
                title = title_part if title_part else name_without_ext
        else:
            # Remove track numbers from single filename
            title = name_without_ext.lstrip('0123456789. ').strip()
        
        return {
            'title': title,
            'artist': artist,
            'display_name': f"{artist} - {title}",
            'length': "0:00"
        }
    
    def refresh_current_song_metadata(self):
        """Refresh metadata for the current song and update display"""
        if hasattr(self, 'current_song') and self.current_song:
            # Re-read metadata with the improved extraction
            new_metadata = self.get_song_metadata(self.current_song)
            
            # Update playlist metadata if this song is in the playlist
            for i, song_path in enumerate(self.playlist):
                if song_path == self.current_song:
                    self.playlist_metadata[i] = new_metadata
                    break
            
            # Update the song title label immediately
            if hasattr(self, 'song_title_label'):
                self.song_title_label.config(text=new_metadata.get('display_name', os.path.basename(self.current_song)))
            
            # Update the playlist treeview if needed
            self.update_playlist_item_display(self.current_song, new_metadata)
            
            print(f"Refreshed metadata: {new_metadata.get('display_name', 'Unknown')}")
    
    def update_playlist_item_display(self, song_path, new_metadata):
        """Update a specific item in the playlist treeview with new metadata"""
        try:
            # Find the item in the treeview
            for item in self.playlist_treeview.get_children():
                tags = self.playlist_treeview.item(item, 'tags')
                for tag in tags:
                    if tag.startswith('index_'):
                        try:
                            index = int(tag.split('_')[1])
                            if index < len(self.playlist) and self.playlist[index] == song_path:
                                # Update the item values
                                position = index + 1
                                star_text = '⭐' if self.check_cached_lyrics(new_metadata['artist'], new_metadata['title']) else ''
                                
                                self.playlist_treeview.item(item, values=(
                                    star_text,  # star column
                                    position,  # position
                                    new_metadata['display_name'],  # updated song name
                                    new_metadata.get('length', '0:00')  # duration
                                ))
                                break
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            pass
    
    def scroll_song_title(self):
        """Scroll the song title like Winamp - back and forth"""
        if not self.scroll_enabled or not self.scroll_text:
            return
        
        # Estimate if text needs scrolling
        text_length = len(self.scroll_text)
        max_display_chars = 30  # Maximum characters that fit in the fixed width
        
        if text_length <= max_display_chars:
            # Text fits, no need to scroll
            self.song_title_label.config(text=self.scroll_text)
            self.root.after(1000, self.scroll_song_title)
            return
        
        # Handle pausing at ends - check this BEFORE updating position
        if self.scroll_pause_counter > 0:
            self.scroll_pause_counter -= 1
            # Keep displaying the same text while pausing
            display_text = self.scroll_text[self.scroll_position:self.scroll_position + max_display_chars]
            if len(display_text) < max_display_chars:
                display_text = display_text.ljust(max_display_chars)
            self.song_title_label.config(text=display_text)
            self.root.after(self.scroll_speed, self.scroll_song_title)
            return
        
        # Calculate scroll limits
        max_scroll = text_length - max_display_chars
        
        # Winamp-style back and forth scrolling
        if self.scroll_direction == 1:
            # Scrolling to the right (text moves left)
            if self.scroll_position >= max_scroll:
                # Reached the end, pause and reverse
                self.scroll_pause_counter = 18  # Pause for 18 cycles (3.6 seconds)
                self.scroll_direction = -1
                # Don't update position this cycle, just pause
            else:
                self.scroll_position += 1
        else:
            # Scrolling to the left (text moves right)
            if self.scroll_position <= 0:
                # Reached the start, pause and reverse
                self.scroll_pause_counter = 18  # Pause for 18 cycles (3.6 seconds)
                self.scroll_direction = 1
                # Don't update position this cycle, just pause
            else:
                self.scroll_position -= 1
        
        # Display the current portion of text
        display_text = self.scroll_text[self.scroll_position:self.scroll_position + max_display_chars]
        
        # Ensure we always have the right number of characters
        if len(display_text) < max_display_chars:
            display_text = display_text.ljust(max_display_chars)
        
        self.song_title_label.config(text=display_text)
        
        # Schedule next scroll
        self.root.after(self.scroll_speed, self.scroll_song_title)
    
    def start_scrolling(self, text):
        """Start scrolling the song title"""
        self.scroll_text = text
        self.scroll_position = 0
        self.scroll_direction = 1
        self.scroll_enabled = True
        self.scroll_song_title()
    
    def stop_scrolling(self):
        """Stop scrolling the song title"""
        self.scroll_enabled = False
        self.scroll_text = ""
    
    def on_search_focus_in(self, event):
        """Handle search box focus in - clear placeholder."""
        if self.search_entry.get() == "🔍 Search artist or song...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg='#f0f6fc')
    
    def on_search_focus_out(self, event):
        """Handle search box focus out - restore placeholder if empty."""
        if not self.search_entry.get():
            self.search_entry.insert(0, "🔍 Search artist or song...")
            self.search_entry.config(fg='#8b949e')
    
    def clear_search(self, event=None):
        """Clear the search box and reset the playlist view."""
        self.search_var.set("")
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, "🔍 Search artist or song...")
        self.search_entry.config(fg='#8b949e')
        # Hide clear button after clearing
        self.clear_search_canvas.place_forget()
        # Focus back to search entry
        self.search_entry.focus_set()
    
    def update_clear_button_visibility(self, *args):
        """Show or hide clear button based on search content."""
        search_text = self.search_var.get()
        # Show clear button if there's text and it's not just the placeholder
        if search_text and search_text != "🔍 Search artist or song...":
            self.clear_search_canvas.place(relx=1.0, rely=0.5, anchor='e', x=-8, y=-1)
        else:
            self.clear_search_canvas.place_forget()
    
    def on_clear_button_enter(self, event):
        """Handle clear button hover enter."""
        # Redraw with hover color
        self.clear_search_canvas.delete("all")
        self.clear_search_canvas.create_oval(2, 2, 14, 14, fill='#58a6ff', outline='#58a6ff')
        self.clear_search_canvas.create_text(8, 8, text="✕", font=('Segoe UI', 8, 'bold'), fill='#ffffff')
    
    def on_clear_button_leave(self, event):
        """Handle clear button hover leave."""
        # Redraw with normal color
        self.clear_search_canvas.delete("all")
        self.clear_search_canvas.create_oval(2, 2, 14, 14, fill='#30363d', outline='#30363d')
        self.clear_search_canvas.create_text(8, 8, text="✕", font=('Segoe UI', 8, 'bold'), fill='#f0f6fc')
    
    def load_star_icons(self):
        """Load star icons from assets folder."""
        try:
            from PIL import Image, ImageTk
            
            star_path = os.path.join(self.assets_dir, "star_yellow.png")
            if os.path.exists(star_path):
                # Load and resize star icon to 16x16 like old version
                star_image = Image.open(star_path)
                star_image = star_image.resize((16, 16), Image.Resampling.LANCZOS)
                self.star_icon = ImageTk.PhotoImage(star_image)
                # Star icon loaded successfully
            else:
                # Star icon not found, using fallback
                # Fallback to text star
                self.star_icon = None
            
            # Create empty placeholder (transparent 16x16)
            empty_image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            self.star_empty = ImageTk.PhotoImage(empty_image)
            
        except ImportError:
            # PIL not available, using text stars
            self.star_icon = None
            self.star_empty = None
        except Exception as e:
            # Error loading star icons
            self.star_icon = None
            self.star_empty = None
    
    def load_star_cache(self):
        """Load star cache from file."""
        try:
            if os.path.exists(self.star_cache_file):
                with open(self.star_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    return cache
            else:
                # Star cache file not found
                return {}
        except Exception as e:
            # Error loading star cache
            return {}
    
    def detect_audio_devices_sounddevice(self):
        """Detect audio devices using sounddevice library"""
        if not SOUNDDEVICE_AVAILABLE:
            print("SoundDevice not available for audio device detection")
            return []
        
        try:
            print("Detecting audio devices with SoundDevice...")
            
            # Get all audio devices
            devices = sounddevice.query_devices()
            
            # Get default output device info
            default_output = sounddevice.default.device[1]  # [1] is output device
            
            # Filter for output devices only
            output_devices = []
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:  # This is an output device
                    # Safely get sample rate
                    sample_rate = getattr(device, 'default_samplerate', 44100)
                    if sample_rate is None:
                        sample_rate = 44100
                    
                    device_info = {
                        'id': i,
                        'name': device['name'],
                        'hostapi': device['hostapi'],
                        'max_output_channels': device['max_output_channels'],
                        'default_output': (i == default_output),
                        'hostapi_name': sounddevice.query_hostapis()[device['hostapi']]['name'],
                        'default_samplerate': sample_rate
                    }
                    output_devices.append(device_info)
                    
                    # Mark if this is a default device
                    default_marker = " [DEFAULT]" if device_info['default_output'] else ""
                    
                    print(f"🔊 Device {i}: {device['name']}{default_marker}")
                    print(f"   Host API: {device_info['hostapi_name']}")
                    print(f"   Channels: {device['max_output_channels']}")
                    print(f"   Sample Rate: {sample_rate} Hz")
                    print()
            
            print(f"Found {len(output_devices)} audio output devices")
            
            # Special help for NVIDIA devices
            nvidia_devices = [d for d in output_devices if 'NVIDIA' in d['name'] and 'NS-L42Q-10A' in d['name']]
            if nvidia_devices:
                print("📺 Found NVIDIA TV devices:")
                for device in nvidia_devices:
                    print(f"   ID {device['id']}: {device['name']} ({device['hostapi_name']})")
                    print(f"      Channels: {device['max_output_channels']}, Sample Rate: {device['default_samplerate']} Hz")
                print()
                print("💡 Tip: Try the one with 'Windows WASAPI' first (usually ID 17)")
                print()
            
            return output_devices
            
        except Exception as e:
            print(f"Error detecting audio devices with SoundDevice: {e}")
            return []
    
    def get_audio_device_list_for_menu(self):
        """Get audio devices formatted for the menu"""
        devices = []
        
        if SOUNDDEVICE_AVAILABLE and MPV_AVAILABLE:
            try:
                # Use MPV's device list since those are the names MPV actually understands
                mpv_devices = self.detect_mpv_audio_devices()
                
                if mpv_devices:
                    # Add MPV devices to menu, but exclude 'auto'
                    for device in mpv_devices:
                        if device['name'] != 'auto':  # Skip auto device
                            devices.append({
                                'name': device['name'],
                                'description': device['description']
                            })
                    print(f"Added {len(devices)} MPV devices to audio menu")
                else:
                    # Fallback to sounddevice if MPV detection fails
                    detected_devices = self.detect_audio_devices_sounddevice()
                    
                    # Add detected devices (no default option)
                    for device in detected_devices:
                        # Create a safe name for the device
                        safe_name = device['name'].replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
                        devices.append({
                            'name': f"sounddevice/{device['id']}",
                            'description': f"{device['id']}: {device['name']}"
                        })
                    print(f"Added {len(devices)} sounddevice devices to audio menu")
                    
            except Exception as e:
                print(f"Error getting device list: {e}")
                # Fallback to hardcoded list (no auto)
                devices = [
                    {'name': 'wasapi/{7f21c2ab-ae95-4bbb-aa98-9c593d04d4cf}', 'description': 'NS-L42Q-10A (NVIDIA High Definition Audio) - TV SPEAKERS'},
                    {'name': 'wasapi/{d09eb373-46c6-4b52-b5e5-62bf7db4f27f}', 'description': 'Speakers (Realtek(R) Audio)'},
                    {'name': 'wasapi/{0757638a-c393-4a30-a4a7-8cbf05bb8951}', 'description': 'MSI G244F E2 (NVIDIA High Definition Audio)'},
                ]
                print("Using hardcoded MPV device list with TV speakers")
        else:
            # Fallback to hardcoded list (no auto)
            devices = [
                {'name': 'wasapi/{7f21c2ab-ae95-4bbb-aa98-9c593d04d4cf}', 'description': 'NS-L42Q-10A (NVIDIA High Definition Audio) - TV SPEAKERS'},
                {'name': 'wasapi/{d09eb373-46c6-4b52-b5e5-62bf7db4f27f}', 'description': 'Speakers (Realtek(R) Audio)'},
                {'name': 'wasapi/{0757638a-c393-4a30-a4a7-8cbf05bb8951}', 'description': 'MSI G244F E2 (NVIDIA High Definition Audio)'},
            ]
            print("Using fallback audio device list")
        
        return devices

    def validate_star_cache(self):
        """Validate star cache against actual lyrics files after playlist is loaded."""
        try:
            if not self.star_cache:
                return
            
            # Validate cache entries against actual lyrics files
            validated_cache = {}
            for song_key, has_lyrics in self.star_cache.items():
                if has_lyrics:  # Only check entries that should have lyrics
                    # Parse artist and title from song key
                    if ' - ' in song_key:
                        artist, title = song_key.split(' - ', 1)
                        # Check if lyrics actually exist for this song in any playlist location
                        if self.check_lyrics_exist_in_playlist(artist, title):
                            validated_cache[song_key] = True
            
            if len(validated_cache) != len(self.star_cache):
                self.star_cache = validated_cache
                self.save_star_cache()
                # Refresh playlist to show updated stars
                if hasattr(self, 'search_var'):
                    self.filter_playlist()
        except Exception as e:
            pass
    
    def check_lyrics_exist_in_playlist(self, artist, title):
        """Check if lyrics exist for a song across all possible storage locations."""
        try:
            # Check all songs in the playlist to find matching artist/title
            for song_path, metadata in zip(self.playlist, self.playlist_metadata):
                if metadata and 'artist' in metadata and 'title' in metadata:
                    if metadata['artist'] == artist and metadata['title'] == title:
                        # Found matching song, check for lyrics files in multiple locations
                        
                        # 1. Check song's own folder (album storage)
                        song_dir = os.path.dirname(song_path)
                        lrc_file = os.path.join(song_dir, f"{artist} - {title}.lrc")
                        txt_file = os.path.join(song_dir, f"{artist} - {title}.txt")
                        
                        if os.path.exists(lrc_file) or os.path.exists(txt_file):
                            return True
                        
                        return False
            return False
        except:
            return False
    
    def save_star_cache(self):
        """Save star cache to file."""
        try:
            with open(self.star_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.star_cache, f, indent=2)
            # Star cache saved successfully
        except Exception as e:
            # Error saving star cache
            pass
    
    def debounced_save_playlist(self):
        """Save playlist with debouncing to reduce frequent file operations."""
        if self.playlist_save_timer:
            self.root.after_cancel(self.playlist_save_timer)
        self.playlist_save_timer = self.root.after(2000, self.save_playlist)  # Save after 2 seconds of inactivity
    
    def load_last_played_song(self):
        """Load the last played song information."""
        try:
            if os.path.exists(self.last_played_file):
                with open(self.last_played_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('last_played', {})
            else:
                return {}
        except Exception as e:
            print(f"Error loading last played song: {e}")
            return {}
    
    def save_last_played_song(self, song_path, metadata):
        """Save the current playing song information."""
        try:
            data = {
                'last_played': {
                    'song_path': song_path,
                    'metadata': metadata,
                    'timestamp': time.time()
                }
            }
            with open(self.last_played_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving last played song: {e}")
    
    def display_last_played_song(self):
        """Display the last played song information in the song info area."""
        if self.last_played_song and 'song_path' in self.last_played_song:
            song_path = self.last_played_song['song_path']
            metadata = self.last_played_song.get('metadata', {})
            
            # Check if the song file still exists
            if os.path.exists(song_path):
                # Set the current song so play button will play this song
                self.current_song = song_path
                
                # Display the song info
                display_name = metadata.get('display_name', os.path.basename(song_path))
                self.song_title_label.config(text=display_name)
                self.song_artist_label.config(text="Last Played")
                
                # Start scrolling for the last played song title
                self.start_scrolling(display_name)
                
                # Load and display the album cover for the last played song
                self.display_album_cover(song_path)
                
                # Set current song path for last played song but don't auto-fetch lyrics
                self.current_song_path = song_path  # Set current song path for last played song
                # Don't auto-fetch lyrics for last played song - let user click to load them
                
                print(f"Displayed last played song: {display_name}")
            else:
                print(f"Last played song file not found: {song_path}")
                # Clear the display if file doesn't exist
                self.song_title_label.config(text="No Song Playing")
                self.song_artist_label.config(text="")
                # Display default album icon
                self.show_default_album_icon()
    
    def load_cover_cache(self):
        try:
            if os.path.exists(self.cover_cache_file):
                with open(self.cover_cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    return cache
            else:
                return {}
        except Exception as e:
            return {}
    
    def save_cover_cache(self):
        """Save album cover cache to file."""
        try:
            with open(self.cover_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cover_cache, f, indent=2)
        except Exception as e:
            pass
    
    def get_cover_cache_path(self, song_path):
        """Get the cached cover image path for a song."""
        # Create a unique filename based on the song path
        import hashlib
        song_hash = hashlib.md5(song_path.encode('utf-8')).hexdigest()
        return os.path.join(self.cover_cache_dir, f"{song_hash}.jpg")
    
    def ensure_cover_cache_dir(self):
        """Ensure the cover cache directory exists."""
        if not os.path.exists(self.cover_cache_dir):
            os.makedirs(self.cover_cache_dir)
    
    def extract_album_cover(self, song_path):
        """Extract album cover from audio file metadata."""
        try:
            # Check if cover is already cached
            cached_path = self.get_cover_cache_path(song_path)
            if os.path.exists(cached_path):
                return cached_path
            
            # Extract cover from audio file
            audio = mutagen.File(song_path)
            if audio is None:
                return None
            
            # Look for album art in various formats
            artwork = None
            
            # Check for MP3 (ID3 tags)
            if hasattr(audio, 'tags') and audio.tags:
                # APIC is the standard tag for cover art
                for key in audio.tags.keys():
                    if key.startswith('APIC:'):
                        artwork = audio.tags[key]
                        break
                
                # Also check common alternative keys
                if not artwork:
                    for key in ['Cover Art', 'CoverArt', 'Artwork']:
                        if key in audio.tags:
                            artwork = audio.tags[key]
                            break
            
            # Check for FLAC/M4A/OGG formats
            if not artwork and hasattr(audio, 'pictures'):
                if audio.pictures:
                    artwork = audio.pictures[0]  # Take the first picture
            
            # Check for M4A specific metadata
            if not artwork and hasattr(audio, 'info'):
                # Some M4A files store artwork in 'covr' field
                if 'covr' in audio:
                    artwork = audio['covr'][0] if isinstance(audio['covr'], list) else audio['covr']
            
            if artwork:
                # Get the image data
                if hasattr(artwork, 'data'):
                    image_data = artwork.data
                elif hasattr(artwork, 'image'):
                    image_data = artwork.image
                elif hasattr(artwork, 'value'):
                    image_data = artwork.value
                else:
                    # If artwork is already bytes
                    image_data = artwork if isinstance(artwork, bytes) else None
                
                if image_data:
                    # Save the image to cache
                    from PIL import Image
                    import io
                    
                    # Open image from bytes
                    img = Image.open(io.BytesIO(image_data))
                    
                    # Convert to RGB if necessary and resize to reasonable size
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Resize to a reasonable size for display (max 300x300)
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    
                    # Save as JPEG
                    img.save(cached_path, 'JPEG', quality=85)
                    
                    # Update cache metadata
                    self.cover_cache[song_path] = cached_path
                    self.save_cover_cache()
                    
                    return cached_path
            
            return None
            
        except Exception as e:
            print(f"Error extracting album cover from {song_path}: {e}")
            return None
    
    def display_album_cover(self, song_path):
        """Display album cover in the song info card."""
        try:
            # Extract or get cached album cover
            cover_path = self.extract_album_cover(song_path)
            
            if cover_path and os.path.exists(cover_path):
                # Load and display the cover image
                try:
                    from PIL import Image, ImageTk
                    
                    # Open and resize image to fit the album frame
                    img = Image.open(cover_path)
                    img_size = 60  # Match the album frame size
                    img = img.resize((img_size, img_size), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Clear existing content and display cover
                    for widget in self.album_frame.winfo_children():
                        widget.destroy()
                    
                    img_label = tk.Label(self.album_frame, image=photo, bg='#21262d', name='album_art_label')
                    img_label.image = photo  # Keep reference
                    img_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                    
                    # Store reference for theme updates
                    self.album_img_label = img_label
                    
                except Exception as e:
                    print(f"Error displaying album cover: {e}")
                    self.show_default_album_icon()
            else:
                # No cover available, show default icon
                self.show_default_album_icon()
                
        except Exception as e:
            print(f"Error in display_album_cover: {e}")
            self.show_default_album_icon()
    
    def show_default_album_icon(self):
        """Show the default music icon when no album cover is available."""
        # Clear existing content
        for widget in self.album_frame.winfo_children():
            widget.destroy()
        
        # Show music icon
        music_icon = ModernLabel(self.album_frame, text="🎵", font=('Segoe UI', 32), bg='#21262d', name='label_album_music_icon')
        music_icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.album_music_icon = music_icon
    
    def load_settings(self):
        """Load settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default settings
                return {
                    'lyrics_folder': None,
                    'lyrics_preference': 'synced_first',  # New setting: synced_first, synced_only, plain_only
                    'theme': 'dark',
                    'volume': 0.7
                }
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}
    
    def save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_lyrics_folder(self):
        """Get the base lyrics folder path."""
        if self.custom_lyrics_folder:
            return self.custom_lyrics_folder
        
        # Default to current directory
        return str(Path.cwd())
    
    def choose_lyrics_folder(self):
        """Open dialog to choose lyrics folder."""
        folder_path = filedialog.askdirectory(
            title="Choose Lyrics Folder",
            initialdir=self.get_lyrics_folder() if self.custom_lyrics_folder else os.path.expanduser("~")
        )
        if folder_path:
            self.custom_lyrics_folder = folder_path
            self.settings['lyrics_folder'] = folder_path
            self.save_settings()
            messagebox.showinfo("Settings Updated", f"Lyrics folder set to:\n{folder_path}")
            
            # Refresh lyrics display if current song has lyrics
            if self.current_song:
                self.refresh_current_lyrics()
    
    def refresh_current_lyrics(self):
        """Refresh lyrics for current song from new folder."""
        if self.current_song and self.playlist_metadata:
            metadata = self.playlist_metadata[self.current_index] if self.current_index < len(self.playlist_metadata) else None
            if metadata and 'artist' in metadata and 'title' in metadata:
                # Try to load lyrics from new location
                local_lyrics, source = self.load_local_lyrics(metadata['artist'], metadata['title'])
                if local_lyrics:
                    if source == "Local LRC":
                        self.display_synced_lyrics(local_lyrics, source)
                    else:
                        self.update_lyrics_display(local_lyrics)
                        self.stop_karaoke_timer()
                    self.update_lyrics_status(f"-- Loaded ({source})")
                else:
                    # Clear display if no lyrics found
                    self.update_lyrics_display("No lyrics found in new location")
                    self.update_lyrics_status("-- Not Found")
    
    def apply_peach_settings_dialog(self, dialog):
        """Apply peach theme to Settings dialog"""
        if not PEACH_THEME_AVAILABLE:
            return
        
        theme = PEACH_THEME
        try:
            # Apply peach theme to dialog background
            dialog.configure(bg='#FFE0CC')  # Light peach background
            
            # Apply peach theme to notebook tabs
            style = ttk.Style()
            style.configure('TNotebook', background='#FFE0CC', borderwidth=0)
            style.configure('TNotebook.Tab', background='#FFB366', foreground=theme['text_on_primary'], padding=[20, 10])
            style.map('TNotebook.Tab', background=[('selected', '#FFB366')], foreground=[('selected', theme['text_on_primary'])])
            
            # Apply peach theme to all widgets in the dialog
            self.apply_peach_settings_children(dialog, theme)
            
        except Exception as e:
            print(f"Error applying peach theme to Settings dialog: {e}")
    
    def apply_peach_settings_children(self, parent, theme):
        """Apply peach theme to all children in Settings dialog"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Dialog background
                if widget_class == 'Toplevel':
                    widget.configure(bg='#FFE0CC')  # Light peach background
                
                # Title label
                elif widget_class == 'Label' and 'settings' in str(widget.cget('text')).lower():
                    widget.configure(bg='#FFE0CC', fg=theme['text_primary'])
                
                # Other labels
                elif widget_class == 'Label':
                    label_text = str(widget.cget('text')).lower()
                    widget_name = getattr(widget, '_name', '')
                    # Check for folder path display label (contains path-like text but NOT description text)
                    if (('lyrics_folder_path' in widget_name or 
                        ('\\' in label_text or '/' in label_text) and 
                        ('tinytunez' in label_text.lower() or 'lyrics' in label_text)) and
                        'this folder will contain' not in label_text and
                        'synced_lyrics' not in label_text and
                        'plain_txt_lyrics' not in label_text):
                        widget.configure(bg='white', fg=theme['text_primary'])
                    else:
                        widget.configure(bg='#FFE0CC', fg=theme['text_secondary'])
                
                # Notebook (tabs)
                elif widget_class == 'Notebook':
                    # Notebook styling is handled in the main function
                    # Recursively apply to children (tab content)
                    self.apply_peach_settings_children(widget, theme)
                
                # Tab frames
                elif widget_class == 'Frame':
                    widget.configure(bg='#FFE0CC')  # Light peach background
                    # Recursively apply to children
                    self.apply_peach_settings_children(widget, theme)
                
                # ModernFrames
                elif widget_class == 'TFrame' or (hasattr(widget, '__class__') and widget.__class__.__name__ == 'ModernFrame'):
                    widget.configure(bg='#FFE0CC')  # Light peach background
                    # Recursively apply to children
                    self.apply_peach_settings_children(widget, theme)
                
                # Radio buttons
                elif widget_class == 'Radiobutton':
                    widget.configure(
                        bg='#FFE0CC',
                        fg=theme['text_primary'],
                        selectcolor='white',
                        activebackground='#FFE0CC',
                        activeforeground=theme['text_primary']
                    )
                
                # Checkbuttons
                elif widget_class == 'Checkbutton':
                    widget.configure(
                        bg='#FFE0CC',
                        fg=theme['text_primary'],
                        selectcolor='white',
                        activebackground='#FFE0CC',
                        activeforeground=theme['text_primary']
                    )
                
                # Buttons
                elif widget_class == 'Button':
                    if 'Close' in widget.cget('text'):
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    else:
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    
                    # Recursively apply to other children
                else:
                    self.apply_peach_settings_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach theme to Settings dialog children: {e}")
    
    def restore_dark_settings_dialog(self, dialog):
        """Restore dark theme to Settings dialog"""
        try:
            # Restore dark theme to dialog background
            dialog.configure(bg='#0d1117')
            
            # Restore dark theme to notebook tabs
            style = ttk.Style()
            style.configure('TNotebook', background='#0d1117', borderwidth=0)
            style.configure('TNotebook.Tab', background='#21262d', foreground='#f0f6fc', padding=[20, 10])
            style.map('TNotebook.Tab', background=[('selected', '#30363d')], foreground=[('selected', '#ffffff')])
            
            # Restore dark theme to all widgets in the dialog
            self.restore_dark_settings_children(dialog)
            
        except Exception as e:
            print(f"Error restoring dark theme to Settings dialog: {e}")
    
    def restore_dark_settings_children(self, parent):
        """Restore dark theme to all children in Settings dialog"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Dialog background
                if widget_class == 'Toplevel':
                    widget.configure(bg='#0d1117')
                
                # Title label
                elif widget_class == 'Label' and 'settings' in str(widget.cget('text')).lower():
                    widget.configure(bg='#0d1117', fg='#f0f6fc')
                
                # Other labels
                elif widget_class == 'Label':
                    label_text = str(widget.cget('text')).lower()
                    widget_name = getattr(widget, '_name', '')
                    # Check for folder path display label (contains path-like text but NOT description text)
                    if (('lyrics_folder_path' in widget_name or 
                        ('\\' in label_text or '/' in label_text) and 
                        ('tinytunez' in label_text.lower() or 'lyrics' in label_text)) and
                        'this folder will contain' not in label_text and
                        'synced_lyrics' not in label_text and
                        'plain_txt_lyrics' not in label_text):
                        widget.configure(bg='#161b22', fg='#8b949e')
                    else:
                        widget.configure(bg='#161b22', fg='#8b949e')
                
                # Notebook (tabs)
                elif widget_class == 'Notebook':
                    # Notebook styling is handled in the main function
                    # Recursively apply to children (tab content)
                    self.restore_dark_settings_children(widget)
                
                # Tab frames
                elif widget_class == 'Frame':
                    widget.configure(bg='#161b22')
                    # Recursively apply to children
                    self.restore_dark_settings_children(widget)
                
                # ModernFrames
                elif widget_class == 'TFrame' or (hasattr(widget, '__class__') and widget.__class__.__name__ == 'ModernFrame'):
                    widget.configure(bg='#161b22')
                    # Recursively apply to children
                    self.restore_dark_settings_children(widget)
                
                # Radio buttons
                elif widget_class == 'Radiobutton':
                    widget.configure(
                        bg='#161b22',
                        fg='#f0f6fc',
                        selectcolor='#21262d',
                        activebackground='#161b22',
                        activeforeground='#f0f6fc'
                    )
                
                # Checkbuttons
                elif widget_class == 'Checkbutton':
                    widget.configure(
                        bg='#21262d',
                        fg='#f0f6fc',
                        selectcolor='#21262d',
                        activebackground='#21262d',
                        activeforeground='#f0f6fc'
                    )
                
                # Buttons
                elif widget_class == 'Button':
                    if 'Close' in widget.cget('text'):
                        widget.configure(bg='#da3633', fg='white', activebackground='#b91c1c')
                    else:
                        widget.configure(bg='#1f6feb', fg='white', activebackground='#2c7fdb')
                
                # Recursively apply to other children
                else:
                    self.restore_dark_settings_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark theme to Settings dialog children: {e}")
    
    def update_all_settings_dialogs_theme(self):
        """Update theme for all open Settings dialogs"""
        try:
            # Find all Toplevel windows that might be settings dialogs
            for widget in self.root.winfo_children():
                if widget.winfo_class() == 'Toplevel':
                    widget_title = widget.title() if hasattr(widget, 'title') else ''
                    if 'Settings' in widget_title:
                        if hasattr(self, 'current_theme') and self.current_theme == 'peach':
                            self.apply_peach_settings_dialog(widget)
                        else:
                            self.restore_dark_settings_dialog(widget)
                        print(f"Updated Settings dialog theme to {self.current_theme}")
        except Exception as e:
            print(f"Error updating Settings dialogs theme: {e}")
    
    def show_settings_dialog(self):
        """Show settings dialog with tabs."""
        window_settings_main = tk.Toplevel(self.root)
        window_settings_main.title("TinyTunez Settings")
        window_settings_main.geometry("630x710")
        window_settings_main.configure(bg='#0d1117')
        window_settings_main.transient(self.root)
        window_settings_main.grab_set()
        
        # Bind UI debugging events to this window
        self.bind_window_events(window_settings_main)
        
        # Title
        label_settings_title = tk.Label(
            window_settings_main,
            text="TinyTunez Settings",
            font=('Segoe UI', 16, 'bold'),
            bg='#0d1117',
            fg='#f0f6fc'
        )
        label_settings_title.pack(pady=15)
        
        # Create notebook for tabs
        from tkinter import ttk
        notebook_settings = ttk.Notebook(window_settings_main)
        notebook_settings.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        # Style the notebook for dark theme
        style = ttk.Style()
        style.configure('TNotebook', background='#0d1117', borderwidth=0)
        style.configure('TNotebook.Tab', background='#21262d', foreground='#f0f6fc', padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', '#30363d')], foreground=[('selected', '#ffffff')])
        
        # Tab 1: Lyrics Settings
        tab_lyrics_settings = tk.Frame(notebook_settings, bg='#161b22')
        notebook_settings.add(tab_lyrics_settings, text="🎵 Lyrics")
        
        # Lyrics preference section
        frame_lyrics_preference = tk.Frame(tab_lyrics_settings, bg='#161b22')
        frame_lyrics_preference.pack(fill=tk.X, padx=15, pady=15)
        
        label_lyrics_preference_title = tk.Label(
            frame_lyrics_preference,
            text="Lyrics Preference:",
            font=('Segoe UI', 12),
            bg='#161b22',
            fg='#8b949e'
        )
        label_lyrics_preference_title.pack(anchor=tk.W)
        
        # Get current preference
        current_preference = self.settings.get('lyrics_preference', 'synced_first')
        
        # Radio buttons for lyrics preference
        preference_var = tk.StringVar(value=current_preference)
        
        def on_preference_change():
            self.settings['lyrics_preference'] = preference_var.get()
            self.save_settings()
        
        # Option 1: Synced lyrics first (default)
        rb_preference_synced_first = tk.Radiobutton(
            frame_lyrics_preference,
            text="🎵 Download synced lyrics first, fallback to plain text if none found",
            variable=preference_var,
            value='synced_first',
            font=('Segoe UI', 10),
            bg='#161b22',
            fg='#f0f6fc',
            selectcolor='#21262d',
            activebackground='#161b22',
            activeforeground='#f0f6fc',
            command=on_preference_change
        )
        rb_preference_synced_first.pack(anchor=tk.W, pady=5)
        
        # Option 2: Strictly synced
        rb_preference_synced_only = tk.Radiobutton(
            frame_lyrics_preference,
            text="⏱️ Strictly synced lyrics only (no plain text searching/downloading)",
            variable=preference_var,
            value='synced_only',
            font=('Segoe UI', 10),
            bg='#161b22',
            fg='#f0f6fc',
            selectcolor='#21262d',
            activebackground='#161b22',
            activeforeground='#f0f6fc',
            command=on_preference_change
        )
        rb_preference_synced_only.pack(anchor=tk.W, pady=5)
        
        # Option 3: Strictly plain text
        rb_preference_plain_only = tk.Radiobutton(
            frame_lyrics_preference,
            text="📄 Strictly plain text only (no synced lyrics searching/downloading)",
            variable=preference_var,
            value='plain_only',
            font=('Segoe UI', 10),
            bg='#161b22',
            fg='#f0f6fc',
            selectcolor='#21262d',
            activebackground='#161b22',
            activeforeground='#f0f6fc',
            command=on_preference_change
        )
        rb_preference_plain_only.pack(anchor=tk.W, pady=5)
        
        # Tab 2: Audio Settings (placeholder for future audio settings)
        tab_audio_settings = tk.Frame(notebook_settings, bg='#161b22')
        notebook_settings.add(tab_audio_settings, text="🔊 Audio")
        
        # Placeholder for audio settings
        label_audio_placeholder = tk.Label(
            tab_audio_settings,
            text="Audio settings will be added here in future updates:\n\n- Volume normalization\n- Audio quality settings\n- Output device selection\n- Equalizer settings",
            font=('Segoe UI', 11),
            bg='#161b22',
            fg='#8b949e',
            justify=tk.CENTER
        )
        label_audio_placeholder.pack(expand=True, pady=50)
        
        # Tab 3: Interface Settings (placeholder for future interface settings)
        tab_interface_settings = tk.Frame(notebook_settings, bg='#161b22')
        notebook_settings.add(tab_interface_settings, text="🎨 Interface")
        
        # Placeholder for interface settings
        label_interface_placeholder = tk.Label(
            tab_interface_settings,
            text="Interface settings will be added here in future updates:\n\n- Theme selection\n- Font size settings\n- Window behavior\n- Visualization options",
            font=('Segoe UI', 11),
            bg='#161b22',
            fg='#8b949e',
            justify=tk.CENTER
        )
        label_interface_placeholder.pack(expand=True, pady=50)
        
        # Tab 4: Advanced Settings
        tab_advanced_settings = tk.Frame(notebook_settings, bg='#161b22')
        notebook_settings.add(tab_advanced_settings, text="⚙️ Advanced")
        
        # UI Debugging Section
        frame_ui_debugging = ModernFrame(tab_advanced_settings, bg='#21262d')
        frame_ui_debugging.pack(fill=tk.X, padx=20, pady=10)
        
        label_ui_debugging_title = tk.Label(
            frame_ui_debugging,
            text="🔍 UI Debugging",
            font=('Segoe UI', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc'
        )
        label_ui_debugging_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        label_ui_debugging_desc = tk.Label(
            frame_ui_debugging,
            text="Enable UI debugging tooltips to inspect widget information",
            font=('Segoe UI', 10),
            bg='#21262d',
            fg='#8b949e'
        )
        label_ui_debugging_desc.pack(anchor=tk.W, padx=15, pady=(0, 10))
        
        # UI Debugging Toggle
        self.ui_debug_var = tk.BooleanVar(value=self.settings.get('ui_debug_enabled', False))
        checkbox_ui_debugging = tk.Checkbutton(
            frame_ui_debugging,
            text="Enable UI Debugging Tooltips",
            variable=self.ui_debug_var,
            font=('Segoe UI', 10),
            bg='#21262d',
            fg='#f0f6fc',
            selectcolor='#21262d',
            activebackground='#21262d',
            activeforeground='#f0f6fc',
            command=self.toggle_ui_debug
        )
        checkbox_ui_debugging.pack(anchor=tk.W, padx=15, pady=(0, 15))
        
        # Additional debug options placeholder
        frame_additional_debug = ModernFrame(tab_advanced_settings, bg='#21262d')
        frame_additional_debug.pack(fill=tk.X, padx=20, pady=10)
        
        label_additional_debug_title = tk.Label(
            frame_additional_debug,
            text="🔧 Additional Debug Options",
            font=('Segoe UI', 12, 'bold'),
            bg='#21262d',
            fg='#f0f6fc'
        )
        label_additional_debug_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        label_additional_debug_placeholder = tk.Label(
            frame_additional_debug,
            text="More debug options coming soon:\n\n- Console logging levels\n- Performance monitoring\n- Memory usage tracking\n- Network request debugging",
            font=('Segoe UI', 10),
            bg='#21262d',
            fg='#8b949e',
            justify=tk.LEFT
        )
        label_additional_debug_placeholder.pack(anchor=tk.W, padx=15, pady=(0, 15))
        
        # Close button
        btn_settings_close = tk.Button(
            window_settings_main,
            text="Close",
            command=window_settings_main.destroy,
            bg='#da3633',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.RAISED,
            cursor='hand2',
            padx=25,
            pady=5
        )
        btn_settings_close.pack(pady=(0, 8))
        
        # Apply appropriate theme to the dialog immediately after all widgets are created
        if hasattr(self, 'current_theme') and self.current_theme == 'peach':
            self.apply_peach_settings_dialog(window_settings_main)
    
    def toggle_ui_debug(self):
        """Toggle UI debugging tooltips on/off."""
        enabled = self.ui_debug_var.get()
        self.settings['ui_debug_enabled'] = enabled
        self.save_settings()
        
        if enabled:
            self.enable_ui_debug_tooltips()
        else:
            self.disable_ui_debug_tooltips()

    def enable_ui_debug_tooltips(self):
        """Enable UI debugging tooltips for all widgets."""
        if not hasattr(self, 'ui_tooltip'):
            self.ui_tooltip = None
        
        # Bind events to all existing widgets
        self.bind_widget_events(self.root)
        
        # Also bind to any existing toplevel windows
        for widget in self.root.winfo_children():
            if widget.winfo_class() == 'Toplevel':
                self.bind_widget_events(widget)

    def disable_ui_debug_tooltips(self):
        """Disable UI debugging tooltips."""
        if hasattr(self, 'ui_tooltip') and self.ui_tooltip:
            self.ui_tooltip.destroy()
            self.ui_tooltip = None
        
        # Unbind events from all widgets
        self.unbind_widget_events(self.root)

    def bind_widget_events(self, widget):
        """Recursively bind debug events to widget and all children."""
        if widget.winfo_class() in ['Toplevel', 'Frame', 'Label', 'Button', 'Entry', 'Text', 
                                   'Listbox', 'Canvas', 'Scale', 'Scrollbar', 'Checkbutton', 
                                   'Radiobutton', 'Menubutton', 'Spinbox']:
            widget.bind('<Enter>', self.on_widget_enter)
            widget.bind('<Leave>', self.on_widget_leave)
            widget.bind('<Motion>', self.on_widget_motion)
        
        # Recursively bind to children
        for child in widget.winfo_children():
            self.bind_widget_events(child)

    def bind_window_events(self, window):
        """Bind debug events to a new window and all its children."""
        if self.settings.get('ui_debug_enabled', False):
            self.bind_widget_events(window)
        
        # Also reapply scrollbar styles to ensure consistency in new windows
        # Skip if peach theme is active to prevent overriding peach scrollbars
        current_theme = getattr(self, 'current_theme', 'dark')
        if current_theme != 'peach':
            self.apply_scrollbar_styles_to_window(window)
        else:
            pass
    
    def apply_scrollbar_styles_to_window(self, window):
        """Apply scrollbar styles to all scrollbars in a window."""
        try:
            import tkinter.ttk as ttk
            style = ttk.Style()
            
            # Apply comprehensive scrollbar styling
            scrollbar_configs = {
                'TScrollbar': {
                    'background': '#30363d',
                    'troughcolor': '#21262d',
                    'bordercolor': '#30363d',
                    'arrowcolor': '#8b949e',
                    'lightcolor': '#40474e',  # Lighter shade for 3D effect
                    'darkcolor': '#262c32',  # Darker shade for 3D effect
                    'relief': 'raised'  # Restore 3D beveled appearance
                },
                'Vertical.TScrollbar': {
                    'background': '#30363d',
                    'troughcolor': '#21262d',
                    'bordercolor': '#30363d',
                    'arrowcolor': '#8b949e',
                    'lightcolor': '#40474e',  # Lighter shade for 3D effect
                    'darkcolor': '#262c32',  # Darker shade for 3D effect
                    'relief': 'raised'  # Restore 3D beveled appearance
                },
                'Horizontal.TScrollbar': {
                    'background': '#30363d',
                    'troughcolor': '#21262d',
                    'bordercolor': '#30363d',
                    'arrowcolor': '#8b949e',
                    'lightcolor': '#40474e',  # Lighter shade for 3D effect
                    'darkcolor': '#262c32',  # Darker shade for 3D effect
                    'relief': 'raised'  # Restore 3D beveled appearance
                }
            }
            
            # Apply configurations
            for scrollbar_type, config in scrollbar_configs.items():
                style.configure(scrollbar_type, **config)
                # Remove all hover/active states
                style.map(scrollbar_type, 
                    background=[('active', '#30363d'), ('!active', '#30363d'), ('pressed', '#30363d'), ('hover', '#30363d'), ('focus', '#30363d'), ('disabled', '#30363d')],
                    arrowcolor=[('active', '#8b949e'), ('!active', '#8b949e'), ('pressed', '#8b949e'), ('hover', '#8b949e'), ('focus', '#8b949e'), ('disabled', '#8b949e')]
                )
            
            # Schedule a refresh for this window
            window.after(100, lambda: self.force_scrollbar_refresh())
            
        except Exception as e:
            print(f"Error applying scrollbar styles to window: {e}")

    def unbind_widget_events(self, widget):
        """Recursively unbind debug events from widget and all children."""
        try:
            widget.unbind('<Enter>')
            widget.unbind('<Leave>')
            widget.unbind('<Motion>')
        except:
            pass
        
        # Recursively unbind from children
        for child in widget.winfo_children():
            self.unbind_widget_events(child)

    def on_widget_enter(self, event):
        """Handle mouse enter on widget."""
        if not self.settings.get('ui_debug_enabled', False):
            return
        
        widget = event.widget
        self.show_ui_tooltip(widget, event.x_root, event.y_root)

    def on_widget_leave(self, event):
        """Handle mouse leave from widget."""
        if hasattr(self, 'ui_tooltip') and self.ui_tooltip:
            self.ui_tooltip.destroy()
            self.ui_tooltip = None

    def on_widget_motion(self, event):
        """Handle mouse motion on widget."""
        if not self.settings.get('ui_debug_enabled', False):
            return
        
        widget = event.widget
        if hasattr(self, 'ui_tooltip') and self.ui_tooltip:
            self.show_ui_tooltip(widget, event.x_root, event.y_root)

    def show_ui_tooltip(self, widget, x, y):
        """Show UI debugging tooltip with widget information."""
        if hasattr(self, 'ui_tooltip') and self.ui_tooltip:
            self.ui_tooltip.destroy()
        
        # Create tooltip window
        self.ui_tooltip = tk.Toplevel(self.root)
        self.ui_tooltip.wm_overrideredirect(True)
        self.ui_tooltip.wm_geometry(f"+{x+10}+{y+10}")
        
        # Get widget information
        info = self.get_widget_info(widget)
        
        # Create tooltip content
        tooltip_frame = tk.Frame(self.ui_tooltip, bg='#1e2127', relief=tk.SOLID, borderwidth=1)
        tooltip_frame.pack()
        
        tooltip_text = tk.Text(
            tooltip_frame,
            bg='#1e2127',
            fg='#f0f6fc',
            font=('Consolas', 9),
            relief=tk.FLAT,
            padx=8,
            pady=6,
            width=40,
            height=len(info.split('\n'))
        )
        tooltip_text.pack()
        tooltip_text.insert('1.0', info)
        tooltip_text.config(state=tk.DISABLED)

    def get_widget_info(self, widget):
        """Get detailed information about a widget."""
        try:
            widget_class = widget.winfo_class()
            widget_name = getattr(widget, '_name', 'unnamed')
            
            # Special handling for container frames - check for interesting children
            if widget_class == 'Frame':
                children_info = self.get_frame_children_info(widget)
                if children_info:
                    return children_info
            
            # Get colors
            bg = widget.cget('bg') if hasattr(widget, 'cget') and 'bg' in widget.keys() else 'N/A'
            fg = widget.cget('fg') if hasattr(widget, 'cget') and 'fg' in widget.keys() else 'N/A'
            
            # Get font info
            font_info = 'N/A'
            if hasattr(widget, 'cget') and 'font' in widget.keys():
                font = widget.cget('font')
                if isinstance(font, tuple):
                    font_info = f"{font[0]} {font[1]}"
                else:
                    font_info = str(font)
            
            # Get dimensions
            width = widget.winfo_width()
            height = widget.winfo_height()
            x = widget.winfo_x()
            y = widget.winfo_y()
            
            # Get text/content
            content = 'N/A'
            if hasattr(widget, 'cget'):
                if 'text' in widget.keys():
                    text = widget.cget('text')
                    if text and len(str(text)) > 20:
                        content = str(text)[:20] + "..."
                    else:
                        content = str(text)
                elif widget_class == 'Text':
                    content = f"[Text widget: {widget.index('end-1c').split('.')[0]} lines]"
                elif widget_class == 'Treeview':
                    # Get Treeview specific info
                    try:
                        # Get column information
                        columns = widget.cget('columns')
                        if columns:
                            column_info = []
                            for col in columns:
                                heading = widget.heading(col, 'text')
                                width = widget.column(col, 'width')
                                column_info.append(f"{heading}({width}px)")
                            content = f"Columns: {', '.join(column_info)}"
                        
                        # Get item count
                        items = len(widget.get_children())
                        if items > 0:
                            content += f" | Items: {items}"
                            
                    except Exception as e:
                        content = f"[Treeview: Error getting info - {str(e)}]"
            
            # Get parent chain
            parent_chain = self.get_parent_chain(widget)
            
            # Get additional widget-specific info
            extra_info = ""
            if widget_class == 'Treeview':
                try:
                    # Get treeview-specific settings
                    show_headings = widget.cget('show') == 'tree headings'
                    select_mode = widget.cget('selectmode')
                    extra_info = f"\nShow Headings: {show_headings}\nSelect Mode: {select_mode}"
                except:
                    pass
            elif widget_class == 'Canvas':
                try:
                    # Get canvas-specific info
                    scroll_region = widget.cget('scrollregion')
                    if scroll_region:
                        extra_info = f"\nScroll Region: {scroll_region}"
                except:
                    pass
            elif widget_class == 'Scrollbar':
                try:
                    # Get scrollbar-specific info
                    orient = widget.cget('orient')
                    command = widget.cget('command')
                    extra_info = f"\nOrientation: {orient}\nCommand: {command}"
                except:
                    pass
            
            info = f"""Widget: {widget_class}
Name: {widget_name}
Parent Chain: {parent_chain}
BG: {bg} | FG: {fg}
Font: {font_info}
Size: {width}x{height}
Position: ({x}, {y})
Content: {content}{extra_info}"""
            
            return info
            
        except Exception as e:
            return f"Error getting widget info: {str(e)}"
    
    def get_parent_chain(self, widget):
        """Get the parent chain of a widget as a readable string."""
        try:
            chain = []
            current = widget
            
            while current and current.winfo_name() != 'root':
                widget_class = current.winfo_class()
                
                # Try to get the name we set via the name parameter
                try:
                    # Use winfo_name() which should return the name we set
                    widget_name = current.winfo_name()
                    
                    # Check if it looks like a descriptive name (not auto-generated)
                    if (widget_name and 
                        not widget_name.startswith('!') and 
                        not widget_name.isdigit() and
                        widget_name != 'frame' and
                        widget_name != 'label' and
                        widget_name != 'button'):
                        display_name = widget_name
                    else:
                        display_name = widget_class
                except Exception as e:
                    display_name = widget_class
                
                chain.append(display_name)
                
                # Get parent widget object from the parent path
                try:
                    parent_path = current.winfo_parent()
                    if parent_path:
                        # Find the parent widget by traversing from root
                        current = current.nametowidget(parent_path)
                    else:
                        break
                except (tk.TclError, AttributeError):
                    # If we can't get the parent widget, break the loop
                    break
                
                # Prevent infinite loops
                if len(chain) > 20:
                    break
            
            # Reverse to show from root to current widget
            chain.reverse()
            
            # Join with arrows
            return " → ".join(chain[-5:]) if len(chain) > 5 else " → ".join(chain)
            
        except Exception as e:
            return f"Error getting parent chain: {str(e)}"

    def get_frame_children_info(self, frame):
        """Get information about interesting child widgets in a frame."""
        try:
            children = frame.winfo_children()
            interesting_children = []
            
            for child in children:
                child_class = child.winfo_class()
                child_name = getattr(child, '_name', 'unnamed')
                
                # Look for specific widget types
                if child_class == 'Treeview':
                    # Get Treeview info
                    try:
                        columns = child.cget('columns')
                        column_info = []
                        if columns:
                            for col in columns:
                                heading = child.heading(col, 'text')
                                width = child.column(col, 'width')
                                column_info.append(f"{heading}({width}px)")
                        
                        items = len(child.get_children())
                        show_headings = child.cget('show') == 'tree headings'
                        select_mode = child.cget('selectmode')
                        
                        # Get style information
                        style_info = ""
                        try:
                            import tkinter.ttk as ttk
                            style = ttk.Style()
                            treeview_style = child.cget('style') if 'style' in child.keys() else 'Treeview'
                            
                            # Get heading style
                            heading_style = style.configure(f'{treeview_style}.Heading')
                            if heading_style:
                                style_info += f"\nHeading BG: {heading_style.get('background', 'N/A')}"
                                style_info += f"\nHeading FG: {heading_style.get('foreground', 'N/A')}"
                                heading_font = heading_style.get('font', 'N/A')
                                if isinstance(heading_font, tuple):
                                    style_info += f"\nHeading Font: {heading_font[0]} {heading_font[1]}"
                                else:
                                    style_info += f"\nHeading Font: {heading_font}"
                            
                            # Get treeview style
                            treeview_config = style.configure(treeview_style)
                            if treeview_config:
                                style_info += f"\nTreeview BG: {treeview_config.get('background', 'N/A')}"
                                style_info += f"\nTreeview FG: {treeview_config.get('foreground', 'N/A')}"
                            
                            # Get selection colors
                            treeview_map = style.map(treeview_style)
                            if treeview_map and 'Treeview' in treeview_map:
                                for state, colors in treeview_map['Treeview']:
                                    if 'background' in colors:
                                        style_info += f"\nSelected BG: {colors['background']}"
                                    if 'foreground' in colors:
                                        style_info += f"\nSelected FG: {colors['foreground']}"
                        except Exception as style_error:
                            style_info = f"\nStyle Error: {str(style_error)}"
                        
                        return f"""Container Frame: Frame
Name: {child_name}
Contains: Treeview Widget
Columns: {', '.join(column_info)}
Items: {items}
Show Headings: {show_headings}
Select Mode: {select_mode}
Style: {treeview_style}{style_info}
Frame Size: {frame.winfo_width()}x{frame.winfo_height()}
Treeview Size: {child.winfo_width()}x{child.winfo_height()}
Selection Highlight: {self.get_treeview_selection_color()}"""
                    except Exception as e:
                        return f"Container Frame with Treeview (Error: {str(e)})"
                
                elif child_class == 'Scrollbar':
                    try:
                        orient = child.cget('orient')
                        return f"""Container Frame: Frame
Name: {child_name}
Contains: Scrollbar
Orientation: {orient}
Frame Size: {frame.winfo_width()}x{frame.winfo_height()}
Scrollbar Size: {child.winfo_width()}x{child.winfo_height()}"""
                    except:
                        return "Container Frame with Scrollbar"
                
                elif child_class == 'Canvas':
                    try:
                        scroll_region = child.cget('scrollregion')
                        return f"""Container Frame: Frame
Name: {child_name}
Contains: Canvas Widget
Scroll Region: {scroll_region}
Frame Size: {frame.winfo_width()}x{frame.winfo_height()}
Canvas Size: {child.winfo_width()}x{child.winfo_height()}"""
                    except:
                        return "Container Frame with Canvas"
            
            # If no interesting children found, return None to use normal frame info
            return None
            
        except Exception as e:
            return None

    def get_treeview_selection_color(self):
        """Get the current treeview selection highlight color"""
        try:
            style = ttk.Style()
            style_map = style.map('Custom.Treeview', 'background')
            selection_color = '#1f6feb'  # Default fallback
            
            if style_map:
                for state, color in style_map:
                    if state == 'selected':
                        selection_color = color
                        break
            
            return selection_color
        except:
            return "#1f6feb"

    def update_star_cache(self, artist, title, has_lyrics=True):
        song_key = f"{artist} - {title}"
        if has_lyrics:
            self.star_cache[song_key] = True
        else:
            self.star_cache.pop(song_key, None)
        self.save_star_cache()
    
    def check_cached_lyrics(self, artist, title):
        """Check if lyrics are cached for this song in album folders."""
        try:
            # Check album folders for all songs in playlist
            for song_path, metadata in zip(self.playlist, self.playlist_metadata):
                if metadata and 'artist' in metadata and 'title' in metadata:
                    if metadata['artist'] == artist and metadata['title'] == title:
                        # Check song's own folder
                        song_dir = os.path.dirname(song_path)
                        lrc_file = os.path.join(song_dir, f"{artist} - {title}.lrc")
                        txt_file = os.path.join(song_dir, f"{artist} - {title}.txt")
                        
                        if os.path.exists(lrc_file) or os.path.exists(txt_file):
                            # Update cache
                            self.update_star_cache(artist, title, has_lyrics=True)
                            return True
                        break
                
            return False
        except Exception as e:
            return False
    
    def update_star_for_song(self, artist, title, has_lyrics=True):
        """Update the star icon for a specific song in the playlist."""
        try:
            # Find the song in the playlist and update its star
            for i, metadata in enumerate(self.playlist_metadata):
                if metadata and 'artist' in metadata and 'title' in metadata:
                    if metadata['artist'] == artist and metadata['title'] == title:
                        # Find the treeview item for this song
                        for item in self.playlist_treeview.get_children():
                            values = self.playlist_treeview.item(item, 'values')
                            if len(values) >= 3 and values[2] == f"{artist} - {title}":
                                # Update the star icon
                                star_icon = "⭐" if has_lyrics else ""
                                new_values = list(values)
                                new_values[0] = star_icon
                                self.playlist_treeview.item(item, values=new_values)
                                break
                        break
        except Exception as e:
            print(f"Error updating star: {e}")
    
    def filter_playlist(self, *args):
        """Filter playlist based on search query."""
        # Check if search_var and playlist_treeview exist (might not during initialization)
        if not hasattr(self, 'search_var') or not hasattr(self, 'playlist_treeview'):
            return
            
        search_term = self.search_var.get().lower()
        
        # Clear current selection
        existing_items = self.playlist_treeview.get_children()
        for item in existing_items:
            self.playlist_treeview.delete(item)
        
        # Store mapping of displayed items to original indices
        self.filtered_indices = []  # Clear previous mapping
        
        # Filter and repopulate playlist
        for i, (song_path, metadata) in enumerate(zip(self.playlist, self.playlist_metadata)):
            song_name = os.path.basename(song_path)
            
            # Get display name from metadata or filename
            if metadata and 'title' in metadata and 'artist' in metadata:
                display_name = f"{metadata['artist']} - {metadata['title']}"
            else:
                # Remove .mp3 extension for display
                display_name = song_name[:-4] if song_name.lower().endswith('.mp3') else song_name
            
            # Apply search filter
            if search_term and search_term != "🔍 search artist or song...":
                if search_term not in display_name.lower():
                    continue
            
            # Store the original index for this filtered item
            self.filtered_indices.append(i)
            
            # Check if song has cached lyrics
            has_lyrics = self.check_cached_lyrics(metadata['artist'], metadata['title']) if metadata and 'artist' in metadata and 'title' in metadata else False
            
            # Processing song for playlist
            
            # Insert filtered item with correct column structure
            position = i + 1  # Show original position
            
            # Use regular star without coloring (Treeview tags affect entire row)
            if has_lyrics:
                star_text = '⭐'  # Back to regular star
            else:
                star_text = ''
            
            # Insert with text star and store original index in tags
            item_id = self.playlist_treeview.insert('', 'end', values=(
                star_text,  # star column with star
                position,  # position
                display_name,  # song name
                metadata.get('length', '0:00')  # duration (using 'length' field)
            ), tags=(f"index_{i}",))  # Store original index in tags
        
        # Restore selection if possible
        if self.current_index < len(self.playlist):
            try:
                # Find the item in the filtered view that matches current_index
                for item in self.playlist_treeview.get_children():
                    tags = self.playlist_treeview.item(item, 'tags')
                    for tag in tags:
                        if tag.startswith('index_') and int(tag.split('_')[1]) == self.current_index:
                            self.playlist_treeview.selection_set(item)
                            self.playlist_treeview.see(item)
                            # Re-apply peach theme if active to prevent color reversion
                            if hasattr(self, 'current_theme') and self.current_theme == 'peach':
                                self.apply_peach_theme()
                            break
            except:
                pass
    
    def load_playlist(self):
        try:
            if os.path.exists(self.playlist_file):
                with open(self.playlist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.playlist = data.get('songs', [])
                    self.playlist_metadata = data.get('metadata', [])
                    self.current_index = data.get('current_index', 0)
                    
                    # Verify files still exist
                    valid_songs = []
                    valid_metadata = []
                    for i, song_path in enumerate(self.playlist):
                        if os.path.exists(song_path):
                            valid_songs.append(song_path)
                            # Always re-read metadata to get updated information
                            metadata = self.get_song_metadata(song_path)
                            valid_metadata.append(metadata)
                    
                    self.playlist = valid_songs
                    self.playlist_metadata = valid_metadata
                    
                    print(f"Loaded {len(self.playlist)} songs from playlist")
                    
                    # Populate treeview with search capability (only if search box exists)
                    if hasattr(self, 'search_var'):
                        self.filter_playlist()
                    else:
                        # Fallback: populate treeview directly
                        for i, metadata in enumerate(self.playlist_metadata):
                            position = i + 1
                            
                            # Check if song has cached lyrics
                            has_lyrics = self.check_cached_lyrics(metadata['artist'], metadata['title']) if metadata and 'artist' in metadata and 'title' in metadata else False
                            
                            position = i + 1
                            
                            # Use regular star without coloring (Treeview tags affect entire row)
                            if has_lyrics:
                                star_text = '⭐'  # Back to regular star
                            else:
                                star_text = ''
                            
                            # Insert with text star and store original index in tags
                            item_id = self.playlist_treeview.insert('', 'end', values=(
                                star_text,  # star column with star
                                position,  # position
                                metadata['display_name'],  # song name
                                metadata.get('length', '0:00')  # duration (using 'length' field)
                            ), tags=(f"index_{i}",))  # Store original index in tags
                            
                            # Added star for song with lyrics
            else:
                print("No saved playlist found")
                if hasattr(self, 'search_var'):
                    self.filter_playlist()
        except Exception as e:
            print(f"Error loading playlist: {e}")
            self.playlist = []
            self.playlist_metadata = []
            if hasattr(self, 'search_var'):
                self.filter_playlist()
        
        # Scroll to top of playlist after loading
        if hasattr(self, 'playlist_treeview'):
            # Get the first item in the treeview
            children = self.playlist_treeview.get_children()
            if children:
                # Try to restore the saved selection first
                if self.current_index < len(self.playlist):
                    try:
                        # Find the item in the filtered view that matches current_index
                        found_item = None
                        for item in self.playlist_treeview.get_children():
                            tags = self.playlist_treeview.item(item, 'tags')
                            for tag in tags:
                                if tag.startswith('index_') and int(tag.split('_')[1]) == self.current_index:
                                    found_item = item
                                    break
                            if found_item:
                                break
                        
                        if found_item:
                            self.playlist_treeview.see(found_item)
                            self.playlist_treeview.selection_clear()
                            self.playlist_treeview.selection_set(found_item)
                        else:
                            # If no matching item found, select first item
                            first_item = children[0]
                            self.playlist_treeview.see(first_item)
                            self.playlist_treeview.selection_clear()
                            self.playlist_treeview.selection_set(first_item)
                    except:
                        # If restoring selection fails, default to first item
                        first_item = children[0]
                        self.playlist_treeview.see(first_item)
                        self.playlist_treeview.selection_clear()
                        self.playlist_treeview.selection_set(first_item)
                else:
                    # If current_index is invalid, select first item
                    first_item = children[0]
                    self.playlist_treeview.see(first_item)
                    self.playlist_treeview.selection_clear()
                    self.playlist_treeview.selection_set(first_item)
        
        # Validate star cache after playlist is fully loaded
        if self.playlist and self.playlist_metadata:
            self.validate_star_cache()
    
    def save_playlist(self):
        """Save playlist to JSON file"""
        try:
            data = {
                'songs': self.playlist,
                'metadata': self.playlist_metadata,
                'current_index': self.current_index
            }
            with open(self.playlist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(self.playlist)} songs to playlist")
        except Exception as e:
            print(f"Error saving playlist: {e}")
    
    def add_songs(self):
        files = filedialog.askopenfilenames(
            title="Select Music Files",
            filetypes=[("Music Files", "*.mp3 *.wav *.ogg *.flac"), ("All Files", "*.*")]
        )
        for file in files:
            self.playlist.append(file)
            metadata = self.get_song_metadata(file)
            self.playlist_metadata.append(metadata)
            # Add to treeview with columns
            position = len(self.playlist)
            self.playlist_treeview.insert('', 'end', values=(
                '',  # star column (empty for now)
                position,  # position
                metadata['display_name'],  # song name
                metadata['length']  # length
            ))
        
        # Save playlist after adding songs
        self.debounced_save_playlist()
            
    def add_folder(self):
        """Add multiple folders of songs to the playlist with multi-select interface."""
        self.show_folder_selection_dialog()
    
    def apply_peach_folder_selection_dialog(self, dialog):
        """Apply peach theme to Select Music Folders dialog"""
        if not PEACH_THEME_AVAILABLE:
            return
        
        theme = PEACH_THEME
        try:
            # Apply peach theme to dialog background
            dialog.configure(bg='#FFE0CC')  # Light peach background
            
            # Apply peach theme to all widgets in the dialog
            self.apply_peach_folder_selection_children(dialog, theme)
            
        except Exception as e:
            print(f"Error applying peach theme to Select Music Folders dialog: {e}")
    
    def apply_peach_folder_selection_children(self, parent, theme):
        """Apply peach theme to all children in Select Music Folders dialog"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Dialog background
                if widget_class == 'Toplevel':
                    widget.configure(bg='#FFE0CC')  # Light peach background
                
                # Labels
                elif widget_class == 'Label':
                    if 'header' in widget_name:
                        widget.configure(bg='#FFE0CC', fg=theme['text_primary'])
                    elif 'instructions' in widget_name:
                        widget.configure(bg='#FFE0CC', fg=theme['text_secondary'])
                    else:
                        widget.configure(bg='white', fg=theme['text_primary'])
                
                # ModernFrames
                elif widget_class == 'TFrame' or (hasattr(widget, '__class__') and widget.__class__.__name__ == 'ModernFrame'):
                    widget.configure(bg='#FFE0CC')  # Light peach background
                    # Recursively apply to children
                    self.apply_peach_folder_selection_children(widget, theme)
                
                # Regular Frames
                elif widget_class == 'Frame':
                    widget.configure(bg='#FFE0CC')  # Light peach background
                    # Recursively apply to children
                    self.apply_peach_folder_selection_children(widget, theme)
                
                # Listbox
                elif widget_class == 'Listbox':
                    widget.configure(
                        bg='white',  # White background
                        fg=theme['input_fg'], 
                        selectbackground=theme['primary'],
                        selectforeground=theme['text_on_primary']
                    )
                
                # Buttons
                elif widget_class == 'Button':
                    if 'Select Parent Directory' in widget.cget('text'):
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    elif 'Select All' in widget.cget('text'):
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    elif 'Clear Selection' in widget.cget('text'):
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    elif 'Add to Playlist' in widget.cget('text'):
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    elif 'Cancel' in widget.cget('text'):
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    else:
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                    
                    # Recursively apply to other children
                else:
                    self.apply_peach_folder_selection_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach theme to Select Music Folders dialog children: {e}")
    
    def restore_dark_folder_selection_dialog(self, dialog):
        """Restore dark theme to Select Music Folders dialog"""
        try:
            # Restore dark theme to dialog background
            dialog.configure(bg='#0d1117')
            
            # Restore dark theme to all widgets in the dialog
            self.restore_dark_folder_selection_children(dialog)
            
        except Exception as e:
            print(f"Error restoring dark theme to Select Music Folders dialog: {e}")
    
    def restore_dark_folder_selection_children(self, parent):
        """Restore dark theme to all children in Select Music Folders dialog"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Dialog background
                if widget_class == 'Toplevel':
                    widget.configure(bg='#0d1117')
                
                # Labels
                elif widget_class == 'Label':
                    if 'header' in widget_name:
                        widget.configure(bg='#161b22', fg='#f0f6fc')
                    elif 'instructions' in widget_name:
                        widget.configure(bg='#0d1117', fg='#8b949e')
                    else:
                        widget.configure(bg='#161b22', fg='#8b949e')
                
                # ModernFrames
                elif widget_class == 'TFrame' or (hasattr(widget, '__class__') and widget.__class__.__name__ == 'ModernFrame'):
                    widget.configure(bg='#161b22')
                    # Recursively apply to children
                    self.restore_dark_folder_selection_children(widget)
                
                # Regular Frames
                elif widget_class == 'Frame':
                    widget.configure(bg='#161b22')
                    # Recursively apply to children
                    self.restore_dark_folder_selection_children(widget)
                
                # Listbox
                elif widget_class == 'Listbox':
                    widget.configure(
                        bg='#21262d', 
                        fg='#f0f6fc', 
                        selectbackground='#1f6feb',
                        selectforeground='#ffffff'
                    )
                
                # Buttons
                elif widget_class == 'Button':
                    if 'Select Parent Directory' in widget.cget('text'):
                        widget.configure(bg='#1f6feb', fg='white', activebackground='#2c7fdb')
                    elif 'Select All' in widget.cget('text'):
                        widget.configure(bg='#1f6feb', fg='white', activebackground='#2c7fdb')
                    elif 'Clear Selection' in widget.cget('text'):
                        widget.configure(bg='#6f7780', fg='white', activebackground='#5a6168')
                    elif 'Add to Playlist' in widget.cget('text'):
                        widget.configure(bg='#238636', fg='white', activebackground='#2ea043')
                    elif 'Cancel' in widget.cget('text'):
                        widget.configure(bg='#6f7780', fg='white', activebackground='#5a6168')
                    else:
                        widget.configure(bg='#1f6feb', fg='white', activebackground='#2c7fdb')
                
                # Recursively apply to other children
                else:
                    self.restore_dark_folder_selection_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark theme to Select Music Folders dialog children: {e}")
    
    def update_all_folder_selection_dialogs_theme(self):
        """Update theme for all open Select Music Folders dialogs"""
        try:
            # Find all Toplevel windows that might be folder selection dialogs
            for widget in self.root.winfo_children():
                if widget.winfo_class() == 'Toplevel':
                    widget_title = widget.title() if hasattr(widget, 'title') else ''
                    if 'Select Music Folders' in widget_title:
                        if hasattr(self, 'current_theme') and self.current_theme == 'peach':
                            self.apply_peach_folder_selection_dialog(widget)
                        else:
                            self.restore_dark_folder_selection_dialog(widget)
                        print(f"Updated Select Music Folders dialog theme to {self.current_theme}")
        except Exception as e:
            print(f"Error updating Select Music Folders dialogs theme: {e}")
    
    def show_folder_selection_dialog(self):
        """Show a dialog for selecting multiple folders."""
        window_folder_selection = tk.Toplevel(self.root)
        window_folder_selection.title("Select Music Folders")
        window_folder_selection.geometry("700x500")
        window_folder_selection.configure(bg='#0d1117')
        window_folder_selection.transient(self.root)
        window_folder_selection.grab_set()
        
        # Bind UI debugging events to this window
        self.bind_window_events(window_folder_selection)
        
        # Store selected folders and current directory
        selected_folders = []
        current_directory = None
        
        # Header
        frame_folder_selection_header = ModernFrame(window_folder_selection, bg='#161b22', height=50)
        frame_folder_selection_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        frame_folder_selection_header.pack_propagate(False)
        
        label_folder_selection_header = ModernLabel(
            frame_folder_selection_header,
            text="📁 Select Music Folders to Add",
            font=('Segoe UI', 12, 'bold'),
            bg='#161b22',
            fg='#f0f6fc',
            name='folder_header_label'
        )
        label_folder_selection_header.pack(expand=True)
        
        # Directory selection frame
        frame_directory_selection = ModernFrame(window_folder_selection, bg='#161b22', height=60)
        frame_directory_selection.pack(fill=tk.X, padx=10, pady=5)
        frame_directory_selection.pack_propagate(False)
        
        # Current directory label
        label_current_directory = ModernLabel(
            frame_directory_selection,
            text="📂 No directory selected",
            font=('Segoe UI', 10),
            bg='#161b22',
            fg='#8b949e',
            name='current_dir_label'
        )
        label_current_directory.pack(side=tk.LEFT, padx=10, pady=10)
        
        def select_parent_directory():
            nonlocal current_directory
            parent_dir = filedialog.askdirectory(title="Select Parent Directory")
            if parent_dir:
                current_directory = parent_dir
                label_current_directory.config(text=f"📂 {parent_dir}")
                load_folders_from_directory()
        
        def load_folders_from_directory():
            """Load all subfolders from the selected directory into the listbox."""
            if not current_directory:
                return
            
            # Clear existing items
            folder_listbox.delete(0, tk.END)
            
            # Load subfolders
            try:
                folders = []
                for item in os.listdir(current_directory):
                    item_path = os.path.join(current_directory, item)
                    if os.path.isdir(item_path) and not item.startswith('.'):
                        folders.append(item)
                
                # Sort folders alphabetically
                folders.sort()
                
                # Add to listbox
                for folder in folders:
                    folder_listbox.insert(tk.END, folder)
                
                # Update status
                label_folder_status.config(text=f"📁 Found {len(folders)} folders in {os.path.basename(current_directory)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load folders:\n{str(e)}")
        
        # Select directory button
        btn_select_parent_dir = tk.Button(
            frame_directory_selection,
            text="📂 Select Parent Directory",
            command=select_parent_directory,
            bg='#1f6feb',
            fg='white',
            font=('Segoe UI', 10),
            cursor='hand2',
            relief=tk.RAISED
        )
        btn_select_parent_dir.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Main content frame
        frame_folder_content = ModernFrame(window_folder_selection, bg='#161b22')
        frame_folder_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Listbox with scrollbar
        frame_folder_listbox = ModernFrame(frame_folder_content, bg='#161b22')
        frame_folder_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Create listbox
        folder_listbox = tk.Listbox(
            frame_folder_listbox,
            bg='#21262d',
            fg='#f0f6fc',
            selectbackground='#1f6feb',
            selectforeground='#ffffff',
            font=('Segoe UI', 10),
            borderwidth=0,
            highlightthickness=0,
            selectmode=tk.MULTIPLE,  # Enable multi-select
            exportselection=False
        )
        
        # Scrollbar
        scrollbar_folder_list = ttk.Scrollbar(frame_folder_listbox, orient=tk.VERTICAL, command=folder_listbox.yview)
        folder_listbox.config(yscrollcommand=scrollbar_folder_list.set)
        
        folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_folder_list.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status label
        label_folder_status = ModernLabel(
            frame_folder_content,
            text="📁 Please select a parent directory to load folders",
            font=('Segoe UI', 9),
            bg='#161b22',
            fg='#8b949e',
            name='folder_status_label'
        )
        label_folder_status.pack(pady=5)
        
        # Buttons frame
        frame_folder_buttons = ModernFrame(window_folder_selection, bg='#161b22', height=50)
        frame_folder_buttons.pack(fill=tk.X, padx=10, pady=(5, 10))
        frame_folder_buttons.pack_propagate(False)
        
        # Button functions
        def select_all():
            folder_listbox.selection_set(0, tk.END)
        
        def clear_selection():
            folder_listbox.selection_clear(0, tk.END)
        
        def add_folders_to_playlist():
            selected_indices = folder_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select at least one folder.")
                return
            
            if not current_directory:
                messagebox.showwarning("No Directory", "Please select a parent directory first.")
                return
            
            # Create progress dialog for large selections
            if len(selected_indices) > 50:
                progress_window = tk.Toplevel(window_folder_selection)
                progress_window.title("Processing Folders...")
                progress_window.geometry("400x150")
                progress_window.resizable(False, False)
                progress_window.transient(window_folder_selection)
                progress_window.grab_set()
                
                # Center the progress dialog
                progress_window.update_idletasks()
                x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
                y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
                progress_window.geometry(f"400x150+{x}+{y}")
                
                tk.Label(progress_window, text=f"Processing {len(selected_indices)} folders...", 
                        font=('Segoe UI', 12)).pack(pady=20)
                
                progress_var = tk.DoubleVar()
                progress_bar = ttk.Progressbar(progress_window, variable=progress_var, 
                                            maximum=len(selected_indices), length=350)
                progress_bar.pack(pady=10)
                
                status_label = tk.Label(progress_window, text="Starting...", font=('Segoe UI', 10))
                status_label.pack(pady=5)
                
                # Update GUI to show progress dialog
                progress_window.update()
            else:
                progress_window = None
                progress_var = None
                status_label = None
            
            total_songs = 0
            try:
                for i, index in enumerate(selected_indices):
                    # Update progress
                    if progress_window:
                        progress_var.set(i + 1)
                        folder_name = folder_listbox.get(index)
                        status_label.config(text=f"Processing: {folder_name} ({i+1}/{len(selected_indices)})")
                        progress_window.update()
                    
                    # Process folder
                    folder_name = folder_listbox.get(index)
                    folder_path = os.path.join(current_directory, folder_name)
                    songs_added = self.scan_music_folder(folder_path, show_progress=False)
                    total_songs += songs_added
                    
                    # Small delay to prevent freezing with very large selections
                    if progress_window and i % 10 == 0:
                        progress_window.update_idletasks()
                
                # Show success message
                if progress_window:
                    progress_window.destroy()
                
                messagebox.showinfo("Success", f"Added {total_songs} songs from {len(selected_indices)} folder(s).")
                window_folder_selection.destroy()
                
            except Exception as e:
                if progress_window:
                    progress_window.destroy()
                messagebox.showerror("Error", f"Error processing folders: {str(e)}")
        
        def cancel():
            window_folder_selection.destroy()
        
        # Keyboard shortcuts
        def handle_key(event):
            if event.state & 0x4:  # Ctrl key
                if event.keysym.lower() == 'a':
                    select_all()
                    return "break"
            elif event.keysym == 'Escape':
                cancel()
                return "break"
        
        # Bind to both dialog and listbox
        window_folder_selection.bind('<Control-a>', handle_key)
        window_folder_selection.bind('<Control-A>', handle_key)
        window_folder_selection.bind('<Escape>', handle_key)
        folder_listbox.bind('<Control-a>', handle_key)
        folder_listbox.bind('<Control-A>', handle_key)
        folder_listbox.bind('<Escape>', handle_key)
        
        # Enhanced selection handling for Shift+Click
        def handle_shift_click(event):
            clicked_index = folder_listbox.nearest(event.y)
            if clicked_index == -1:
                return
            
            # Get current selection
            current_selection = folder_listbox.curselection()
            
            if current_selection:
                # Use the most recently selected item as the anchor
                anchor_index = current_selection[-1]
                
                # Clear current selection first
                folder_listbox.selection_clear(0, tk.END)
                
                # Select range from anchor to clicked index
                if clicked_index >= anchor_index:
                    folder_listbox.selection_set(anchor_index, clicked_index)
                else:
                    folder_listbox.selection_set(clicked_index, anchor_index)
            else:
                # No current selection, just select the clicked item
                folder_listbox.selection_set(clicked_index)
        
        # Bind Shift+Click
        folder_listbox.bind('<Shift-Button-1>', handle_shift_click)
        
        # Debug click handler - but don't interfere with Ctrl+Click
        def handle_click(event):
            # Don't return "break" to allow default Ctrl+Click behavior to work
            pass
        
        folder_listbox.bind('<Button-1>', handle_click)
        
        # Custom Ctrl+Click handler for proper multi-select
        def handle_ctrl_click(event):
            clicked_index = folder_listbox.nearest(event.y)
            if clicked_index == -1:
                return
            
            # Check if this item is already selected
            current_selection = folder_listbox.curselection()
            if clicked_index in current_selection:
                # Deselect this item
                folder_listbox.selection_clear(clicked_index)
            else:
                # Select this item
                folder_listbox.selection_set(clicked_index)
            
            return "break"  # Prevent default behavior
        
        folder_listbox.bind('<Control-Button-1>', handle_ctrl_click)
        
        # Buttons
        btn_select_all_folders = tk.Button(
            frame_folder_buttons,
            text="🔽 Select All (Ctrl+A)",
            command=select_all,
            bg='#1f6feb',
            fg='white',
            font=('Segoe UI', 10),
            cursor='hand2',
            relief=tk.RAISED
        )
        btn_select_all_folders.pack(side=tk.LEFT, padx=5)
        
        btn_clear_folder_selection = tk.Button(
            frame_folder_buttons,
            text="🔼 Clear Selection",
            command=clear_selection,
            bg='#6f7780',
            fg='white',
            font=('Segoe UI', 10),
            cursor='hand2',
            relief=tk.RAISED
        )
        btn_clear_folder_selection.pack(side=tk.LEFT, padx=5)
        
        # Right side buttons
        btn_add_folders_to_playlist = tk.Button(
            frame_folder_buttons,
            text="✅ Add to Playlist",
            command=add_folders_to_playlist,
            bg='#238636',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            relief=tk.RAISED
        )
        btn_add_folders_to_playlist.pack(side=tk.RIGHT, padx=5)
        
        btn_cancel_folder_selection = tk.Button(
            frame_folder_buttons,
            text="❌ Cancel",
            command=cancel,
            bg='#6f7780',
            fg='white',
            font=('Segoe UI', 10),
            cursor='hand2',
            relief=tk.RAISED
        )
        btn_cancel_folder_selection.pack(side=tk.RIGHT, padx=5)
        
        # Instructions
        instructions = ModernLabel(
            window_folder_selection,
            text="Instructions: 1) Click 'Select Parent Directory' to choose a folder\n" +
                 "2) Select folders from the list below using shortcuts: Ctrl+A (Select All), Ctrl+Click (multi-select), Shift+Click (range select)\n" +
                 "3) Click 'Add to Playlist' to add all songs from selected folders",
            font=('Segoe UI', 9),
            bg='#0d1117',
            fg='#8b949e',
            name='folder_instructions_label'
        )
        instructions.pack(pady=(0, 5))
        
        # Center dialog
        window_folder_selection.update_idletasks()
        x = (window_folder_selection.winfo_screenwidth() // 2) - (window_folder_selection.winfo_width() // 2)
        y = (window_folder_selection.winfo_screenheight() // 2) - (window_folder_selection.winfo_height() // 2)
        window_folder_selection.geometry(f"+{x}+{y}")
        
        # Apply appropriate theme to the dialog immediately after all widgets are created
        if hasattr(self, 'current_theme') and self.current_theme == 'peach':
            self.apply_peach_folder_selection_dialog(window_folder_selection)
        
        window_folder_selection.wait_window()
    
    def open_lyrics_folder(self):
        """Open the album folder for the current song in the system file explorer."""
        try:
            # If we have a current song, try to open the album folder
            if hasattr(self, 'current_song_path') and self.current_song_path:
                album_path = self.get_album_lyrics_path(self.current_song_path)
                if album_path and os.path.exists(album_path):
                    # Open the album folder
                    if platform.system() == "Windows":
                        os.startfile(album_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", album_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", album_path])
                    return
                else:
                    messagebox.showinfo("Lyrics Folder", f"Album folder not found:\n{album_path}")
            else:
                messagebox.showinfo("Lyrics Folder", "No song currently selected. Please select a song first.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open album folder:\n{str(e)}")
    
    def scan_music_folder(self, folder_path, show_progress=True):
        """Scan a music folder and add songs to playlist. Returns count of songs added."""
        songs_added = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    file_path = os.path.join(root, file)
                    self.playlist.append(file_path)
                    metadata = self.get_song_metadata(file_path)
                    self.playlist_metadata.append(metadata)
                    # Don't add to treeview directly - let filter_playlist handle it
                    songs_added += 1
        
        # Save playlist after adding folder
        self.debounced_save_playlist()
        
        # Update treeview to show newly added songs
        if hasattr(self, 'search_var'):
            self.filter_playlist()
        
        return songs_added
                        
    def clear_playlist(self):
        """Clear the entire playlist and save the empty state."""
        self.playlist.clear()
        self.playlist_metadata.clear()
        self.current_index = 0  # Reset current index
        self.playlist_treeview.delete(*self.playlist_treeview.get_children())
        self.stop_song()
        # Save cleared playlist immediately
        self.save_playlist()
        
        # Also clear the treeview display to prevent duplicates
        if hasattr(self, 'search_var'):
            self.filter_playlist()
        
    def remove_from_playlist(self):
        selection = self.playlist_treeview.selection()
        if selection:
            # Get the selected item
            item = selection[0]
            # Get the index from the treeview
            index = self.playlist_treeview.index(item)
            # Remove from lists
            del self.playlist[index]
            del self.playlist_metadata[index]
            # Remove from treeview
            self.playlist_treeview.delete(item)
            # Renumber remaining items
            self.update_playlist_display()
            # Save playlist after removing
            self.debounced_save_playlist()
            
    def update_playlist_display(self):
        """Update playlist display with correct numbering"""
        # Clear treeview
        self.playlist_treeview.delete(*self.playlist_treeview.get_children())
        # Re-add all items with correct numbering and stars
        for i, metadata in enumerate(self.playlist_metadata):
            position = i + 1
            
            # Check if this song has cached lyrics (star)
            star_icon = ""
            if metadata and 'artist' in metadata and 'title' in metadata:
                song_key = f"{metadata['artist']} - {metadata['title']}"
                if song_key in self.star_cache:
                    star_icon = "⭐"
            
            self.playlist_treeview.insert('', 'end', values=(
                star_icon,  # star column
                position,  # position
                metadata['display_name'],  # song name
                metadata['length']  # length
            ))
    
    def populate_playlist_from_loaded_data(self):
        """Populate treeview with loaded playlist data"""
        for i, metadata in enumerate(self.playlist_metadata):
            position = i + 1
            
            # Check if this song has cached lyrics (star)
            star_icon = ""
            if metadata and 'artist' in metadata and 'title' in metadata:
                song_key = f"{metadata['artist']} - {metadata['title']}"
                if song_key in self.star_cache:
                    star_icon = "⭐"
            
            self.playlist_treeview.insert('', 'end', values=(
                star_icon,  # star column
                position,  # position
                metadata['display_name'],  # song name
                metadata['length']  # length
            ))
    
    def edit_playlist(self):
        messagebox.showinfo("Edit Playlist", "Playlist editing feature coming soon!")
        
    def on_playlist_single_click(self, event):
        """Handle single click on playlist items - fetch lyrics only if not playing."""
        # Don't handle playlist clicks during seeking
        if getattr(self, 'seek_pending', False):
            return
            
        # Handle single click on playlist items
        selection = self.playlist_treeview.selection()
        if selection:
            # Get the selected item
            item = selection[0]
            
            # Get the values from the treeview (star, position, name, duration)
            values = self.playlist_treeview.item(item, 'values')
            if len(values) >= 3:
                display_name = values[2]  # Song name is in the third column
                # Selected display name for processing
                
                # Find the matching song in the original playlist
                song_path = None
                song_index = -1
                
                for i, metadata in enumerate(self.playlist_metadata):
                    # Check if this metadata matches the display name
                    if metadata and 'title' in metadata and 'artist' in metadata:
                        metadata_name = f"{metadata['artist']} - {metadata['title']}"
                    else:
                        # Fallback to filename
                        song_name = os.path.basename(self.playlist[i])
                        metadata_name = song_name[:-4] if song_name.lower().endswith('.mp3') else song_name
                    
                    if metadata_name == display_name:
                        song_path = self.playlist[i]
                        song_index = i
                        break
                
                if song_path:
                    # Found matching song
                    # Update current index to match the selected song
                    self.current_index = song_index
                    self.current_song_path = os.path.normpath(song_path)  # Normalize path separators
                    self.current_song = song_path  # Update current_song for play button logic
                    # Save the current selection to playlist file
                    self.save_playlist()
                    # Display album cover for the clicked song
                    self.display_album_cover(song_path)
                    
                    # Only fetch lyrics if not playing
                    if not self.is_playing or self.is_paused:
                        try:
                            # Fetch lyrics for clicked song
                            self.fetch_lyrics(song_path)
                        except Exception as e:
                            # Error fetching lyrics
                            pass
                else:
                    # Could not find matching song
                    pass
            else:
                # Invalid item values
                pass
        else:
            # No selection found
            pass
    
    def on_playlist_double_click(self, event):
        """Handle double click on playlist items - play song."""
        # Don't handle playlist clicks during seeking
        if getattr(self, 'seek_pending', False):
            return
            
        selection = self.playlist_treeview.selection()
        if selection:
            # Get the selected item
            item = selection[0]
            
            # Get the original index from tags
            tags = self.playlist_treeview.item(item, 'tags')
            song_index = -1
            
            for tag in tags:
                if tag.startswith('index_'):
                    try:
                        song_index = int(tag.split('_')[1])
                        break
                    except (ValueError, IndexError):
                        continue
            
            if song_index >= 0 and song_index < len(self.playlist):
                # Update current index to match the selected song
                old_index = self.current_index
                self.current_index = song_index
                
                # Enable auto-play for this explicit user action
                self.auto_play_enabled = True
                self.has_manually_played = True  # Mark that user has manually played
                self.play_selected_song()
                self.auto_play_enabled = False  # Disable again after playing
            else:
                # Fallback to the old method if original_index not found
                values = self.playlist_treeview.item(item, 'values')
                if len(values) >= 3:
                    display_name = values[2]  # Song name is in the third column
                    
                    # Find the matching song in the original playlist
                    song_index = -1
                    
                    for i, metadata in enumerate(self.playlist_metadata):
                        # Check if this metadata matches the display name
                        if metadata and 'title' in metadata and 'artist' in metadata:
                            metadata_name = f"{metadata['artist']} - {metadata['title']}"
                        else:
                            # Fallback to filename
                            song_name = os.path.basename(self.playlist[i])
                            metadata_name = song_name[:-4] if song_name.lower().endswith('.mp3') else song_name
                        
                        if metadata_name == display_name:
                            song_index = i
                            break
                    
                    if song_index >= 0:
                        # Update current index to match the selected song
                        self.current_index = song_index
                        # Enable auto-play for this explicit user action
                        self.auto_play_enabled = True
                        self.has_manually_played = True  # Mark that user has manually played
                        self.play_selected_song()
                        self.auto_play_enabled = False  # Disable again after playing
            
    def show_playlist_context_menu(self, event):
        """Show context menu when right-clicking on playlist items."""
        # Get the item under the cursor
        item = self.playlist_treeview.identify_row(event.y)
        if not item:
            return
        
        # Select the item
        self.playlist_treeview.selection_set(item)
        
        # Get the values from the treeview (star, position, name, duration)
        values = self.playlist_treeview.item(item, 'values')
        if len(values) < 3:
            return
            
        display_name = values[2]  # Song name is in the third column
        
        # Find the matching song in the original playlist
        song_path = None
        metadata = None
        
        for i, song_metadata in enumerate(self.playlist_metadata):
            # Check if this metadata matches the display name
            if song_metadata and 'title' in song_metadata and 'artist' in song_metadata:
                metadata_name = f"{song_metadata['artist']} - {song_metadata['title']}"
            else:
                # Fallback to filename
                song_name = os.path.basename(self.playlist[i])
                metadata_name = song_name[:-4] if song_name.lower().endswith('.mp3') else song_name
            
            if metadata_name == display_name:
                song_path = self.playlist[i]
                metadata = song_metadata
                break
        
        if not song_path or not metadata:
            return
            
        artist = metadata['artist']
        title = metadata['title']
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0, bg='#161b22', fg='#f0f6fc',
                             activebackground='#21262d', activeforeground='#4a9eff',
                             font=('Segoe UI', 10))
        
        # Add lyrics options
        context_menu.add_command(label="🔍 Search LRCLib", 
                               command=lambda: self.search_lrclib_manual(artist, title))
        context_menu.add_command(label="🔍 Search AZLyrics", 
                               command=lambda: self.search_lyrics_website(artist, title, "azlyrics"))
        context_menu.add_command(label="🔍 Search Genius", 
                               command=lambda: self.search_lyrics_website(artist, title, "genius"))
        context_menu.add_command(label="📝 Add Lyrics Manually", 
                               command=lambda: self.show_lyrics_dialog(artist, title))
        
        context_menu.add_separator()
        context_menu.add_command(label="▶️ Play Song", 
                               command=lambda: self.play_selected_song_at_index(index))
        
        # Show the menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def search_lrclib_manual(self, artist, title):
        """Open LRCLib website in browser with search query."""
        try:
            import webbrowser
            # Create LRCLib search URL - use the correct format
            query = f"{artist} {title}".replace(' ', '+')
            url = f"https://lrclib.net/search/{query}"
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening LRCLib: {e}")
            messagebox.showerror("Error", f"Could not open LRCLib:\n{e}")
    
    def search_lyrics_website(self, artist, title, source):
        """Search for lyrics on specified website."""
        # This will open the website with search parameters
        if source == "azlyrics":
            # AZLyrics search URL format - new format with proper search endpoint
            search_query = f"{artist}+-+{title}".replace(' ', '+').lower()
            # Use the new search format with the hash parameter
            url = f"https://www.azlyrics.com/search/?q={search_query}&x=9cd5e9d2f84d9498c7bb93c29ca2769cb1a0ee25cd4ddb7a9b9e206570a75b70"
        elif source == "genius":
            # Genius search URL format
            search_query = f"{artist} {title}".replace(' ', '+')
            url = f"https://genius.com/search?q={search_query}"
        
        # Open in default browser
        import webbrowser
        webbrowser.open(url)
        
        # Show message to user
        self.update_lyrics_display(f"Searching {source.title()} for:\n\n{artist} - {title}\n\n"
                                 f"Copy the lyrics and then right-click the song again and select 'Add Lyrics Manually'.")
    
    def show_lyrics_dialog(self, artist, title):
        """Show dialog for manual lyrics input."""
        window_lyrics_input = tk.Toplevel(self.root)
        window_lyrics_input.title(f"Add Lyrics - {artist} - {title}")
        window_lyrics_input.geometry("600x650")  # Increased height from 600 to 650
        window_lyrics_input.configure(bg='#0d1117')
        window_lyrics_input.transient(self.root)
        window_lyrics_input.grab_set()
        
        # Bind UI debugging events to this window
        self.bind_window_events(window_lyrics_input)
        
        # Title
        label_lyrics_input_title = tk.Label(window_lyrics_input, text=f"Add lyrics for: {artist} - {title}",
                              font=('Segoe UI', 12, 'bold'), bg='#0d1117', fg='#f0f6fc')
        label_lyrics_input_title.pack(pady=10)
        
        # Instructions
        label_lyrics_input_instructions = tk.Label(window_lyrics_input, text="Paste lyrics below (or type them manually):",
                               font=('Segoe UI', 10), bg='#0d1117', fg='#8b949e')
        label_lyrics_input_instructions.pack(pady=5)
        
        # Text area frame with scrollbar
        frame_lyrics_input_text = tk.Frame(window_lyrics_input, bg='#0d1117')
        frame_lyrics_input_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Text area for lyrics
        lyrics_text = tk.Text(frame_lyrics_input_text, bg='#161b22', fg='#f0f6fc', font=('Segoe UI', 11),
                            wrap=tk.WORD, borderwidth=0, highlightthickness=0,
                            insertbackground='#4a9eff', selectbackground='#1f6feb')
        
        # Scrollbar for text area
        scrollbar_lyrics_input = ttk.Scrollbar(frame_lyrics_input_text, orient=tk.VERTICAL, command=lyrics_text.yview)
        lyrics_text.config(yscrollcommand=scrollbar_lyrics_input.set)
        
        # Use grid layout for text and scrollbar
        lyrics_text.grid(row=0, column=0, sticky='nsew')
        scrollbar_lyrics_input.grid(row=0, column=1, sticky='ns')
        
        # Configure grid weights
        frame_lyrics_input_text.grid_rowconfigure(0, weight=1)
        frame_lyrics_input_text.grid_columnconfigure(0, weight=1)
        frame_lyrics_input_text.grid_columnconfigure(1, weight=0)
        
        # Initially hide scrollbar
        scrollbar_lyrics_input.grid_remove()
        
        # Function to show/hide scrollbar based on content
        def update_scrollbar_visibility():
            try:
                # Update the text widget to ensure accurate measurements
                lyrics_text.update_idletasks()
                
                # Get the total lines and visible height
                total_lines = int(lyrics_text.index('end-1c').split('.')[0])
                visible_height = lyrics_text.winfo_height()
                
                # Check if content exceeds visible area
                if total_lines == 0:
                    # No content - hide scrollbar
                    scrollbar_lyrics_input.grid_remove()
                else:
                    # Check if we need scrolling (more than ~20 lines or content height)
                    bbox = lyrics_text.bbox(f"{total_lines}.0")
                    if bbox:
                        content_height = bbox[1] + bbox[3]  # y position + height
                        if content_height > visible_height * 0.9:  # 90% of visible height
                            scrollbar_lyrics_input.grid()
                        else:
                            scrollbar_lyrics_input.grid_remove()
                    else:
                        # Fallback - show if more than 20 lines
                        if total_lines > 20:
                            scrollbar_lyrics_input.grid()
                        else:
                            scrollbar_lyrics_input.grid_remove()
            except:
                # Hide scrollbar on error
                scrollbar_lyrics_input.grid_remove()
        
        # Bind to text changes to update scrollbar visibility
        def on_text_change(*args):
            window_lyrics_input.after(100, update_scrollbar_visibility)  # Delay to ensure text is updated
        
        lyrics_text.bind('<KeyRelease>', on_text_change)
        lyrics_text.bind('<ButtonRelease-1>', on_text_change)
        
        # Buttons frame with more padding
        frame_lyrics_input_buttons = tk.Frame(window_lyrics_input, bg='#0d1117')
        frame_lyrics_input_buttons.pack(fill=tk.X, padx=20, pady=(10, 20))  # Increased bottom padding
        
        def save_lyrics():
            lyrics = lyrics_text.get("1.0", tk.END).strip()
            if lyrics:
                # Create clean filename for save dialog
                filename = f"{artist} - {title}.txt"
                filename_clean = filename.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                
                # Determine default folder - use song's folder
                if hasattr(self, 'current_song') and self.current_song:
                    default_folder = Path(self.current_song).parent
                else:
                    # No current song, use desktop as fallback
                    default_folder = Path.home() / "Desktop"
                
                default_folder.mkdir(parents=True, exist_ok=True)
                
                # Show save dialog
                save_path = filedialog.asksaveasfilename(
                    title="Save Lyrics",
                    initialfile=filename_clean,
                    initialdir=str(default_folder),
                    filetypes=[
                        ("Text Files (*.txt)", "*.txt"),
                        ("All Files", "*.*")
                    ]
                )
                
                if save_path:  # User didn't cancel
                    # Save to selected location
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(lyrics)
                    
                    # Update lyrics tracking for editing
                    self.current_lyrics_artist = artist
                    self.current_lyrics_title = title
                    self.current_lyrics_content = lyrics
                    self.current_lyrics_is_synced = False
                    
                    # Enable edit button
                    if hasattr(self, 'edit_lyrics_btn'):
                        self.edit_lyrics_btn.config(state=tk.NORMAL)
                    
                    self.update_lyrics_display(lyrics, artist, title)
                    window_lyrics_input.destroy()
        
        def cancel_dialog():
            window_lyrics_input.destroy()
        
        # Buttons with better spacing
        btn_save_lyrics_input = tk.Button(frame_lyrics_input_buttons, text="Save Lyrics", command=save_lyrics,
                           bg='#238636', fg='white', font=('Segoe UI', 10, 'bold'),
                           cursor='hand2', relief=tk.RAISED, padx=25, pady=8)  # Increased padding
        btn_save_lyrics_input.pack(side=tk.RIGHT, padx=(10, 0))  # Added left padding
        
        btn_cancel_lyrics_input = tk.Button(frame_lyrics_input_buttons, text="Cancel", command=cancel_dialog,
                             bg='#da3633', fg='white', font=('Segoe UI', 10, 'bold'),
                             cursor='hand2', relief=tk.RAISED, padx=25, pady=8)  # Increased padding
        btn_cancel_lyrics_input.pack(side=tk.RIGHT)
    
    def open_song_folder(self):
        """Open the folder containing the current song in file explorer"""
        if hasattr(self, 'current_song') and self.current_song:
            try:
                import subprocess
                import platform
                
                song_path = Path(self.current_song)
                folder_path = str(song_path.parent)
                
                if platform.system() == "Windows":
                    # On Windows, open the folder and select the file
                    subprocess.run(f'explorer /select,"{song_path}"', shell=True)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", "-R", str(song_path)])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
                    
                print(f"Opened folder: {folder_path}")
            except Exception as e:
                print(f"Error opening folder: {e}")
                # Fallback: try to open just the folder
                try:
                    import webbrowser
                    folder_path = str(Path(self.current_song).parent)
                    webbrowser.open(f"file:///{folder_path}")
                except Exception as e2:
                    print(f"Fallback also failed: {e2}")
    
    def parse_lrc_timestamps(self, lrc_text):
        """Parse LRC format into list of (time_ms, text) tuples."""
        import re
        
        lines = []
        has_valid_timestamps = False
        
        for line in lrc_text.split('\n'):
            # Skip metadata lines
            if re.match(r'\[ar:|\[ti:|\[al:|\[offset:]', line):
                continue
            
            # Find timestamp and text
            match = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)', line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                hundredths = int(match.group(3))
                text = match.group(4).strip()
                
                # Convert to milliseconds
                time_ms = (minutes * 60 + seconds) * 1000 + hundredths * 10
                
                if text:  # Only add non-empty lines
                    lines.append((time_ms, text))
                    has_valid_timestamps = True
        
        result = sorted(lines)  # Sort by time
        
        # If no valid timestamps found, return empty list to indicate plain text
        if not has_valid_timestamps:
            return []
        
        return result
    
    def convert_lrc_to_plain(self, lrc_text):
        """Convert LRC format to plain text by removing timestamps."""
        import re
        
        lines = lrc_text.split('\n')
        plain_lines = []
        
        for line in lines:
            # Remove timestamps like [00:12.34]
            plain_line = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', line)
            
            # Remove metadata tags
            plain_line = re.sub(r'\[ar:.*?\]|\[ti:.*?\]|\[al:.*?\]|\[offset:.*?\]', '', plain_line)
            
            plain_line = plain_line.strip()
            
            if plain_line:
                plain_lines.append(plain_line)
        
        return '\n'.join(plain_lines)
    
    def update_lyrics_status(self, status):
        """Update the lyrics status indicator."""
        if hasattr(self, 'lyrics_status_label'):
            self.lyrics_status_label.config(text=status)
    
    def update_lyrics_display(self, lyrics_text, artist=None, title=None, preserve_sync_content=False):
        """Update the lyrics display area with smart scrollbar."""
        # Track current lyrics for editing
        # Use provided artist/title, or fallback to current_song metadata
        if artist and title:
            self.current_lyrics_artist = artist
            self.current_lyrics_title = title
            # Only overwrite content if not preserving sync content
            if not preserve_sync_content:
                self.current_lyrics_content = lyrics_text
                self.current_lyrics_is_synced = False
            # Enable edit button
            if hasattr(self, 'edit_lyrics_btn'):
                self.edit_lyrics_btn.config(state=tk.NORMAL)
        elif hasattr(self, 'current_song') and self.current_song:
            metadata = self.get_song_metadata(self.current_song)
            if metadata and 'artist' in metadata and 'title' in metadata:
                self.current_lyrics_artist = metadata['artist']
                self.current_lyrics_title = metadata['title']
                # Only overwrite content if not preserving sync content
                if not preserve_sync_content:
                    self.current_lyrics_content = lyrics_text
                    self.current_lyrics_is_synced = False
                # Enable edit button
                if hasattr(self, 'edit_lyrics_btn'):
                    self.edit_lyrics_btn.config(state=tk.NORMAL)
        
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete("1.0", tk.END)
        self.lyrics_text.insert("1.0", lyrics_text)
        self.lyrics_text.config(state=tk.DISABLED)
        
        # Check if scrollbar is needed
        self.update_scrollbar_visibility()
    
    def update_scrollbar_visibility(self):
        """Show/hide scrollbar based on content size."""
        try:
            # Update the text widget to ensure accurate measurements
            self.lyrics_text.update_idletasks()
            
            # Get the total lines and visible lines
            total_lines = int(self.lyrics_text.index('end-1c').split('.')[0])
            visible_height = self.lyrics_text.winfo_height()
            
            # Calculate if scrolling is needed
            if total_lines == 0:
                # No content - hide scrollbar
                self.lyrics_scrollbar.grid_remove()
            else:
                # Check if content exceeds visible area
                bbox = self.lyrics_text.bbox(f"{total_lines}.0")
                if bbox:
                    content_height = bbox[1] + bbox[3]  # y position + height
                    if content_height > visible_height:
                        # Show scrollbar
                        self.lyrics_scrollbar.grid()
                    else:
                        # Hide scrollbar
                        self.lyrics_scrollbar.grid_remove()
                else:
                    # Fallback - show if more than 15 lines
                    if total_lines > 15:
                        self.lyrics_scrollbar.grid()
                    else:
                        self.lyrics_scrollbar.grid_remove()
                        
        except Exception as e:
            print(f"Scrollbar visibility error: {e}")
            # Hide scrollbar on error
            self.lyrics_scrollbar.grid_remove()
    
    def start_karaoke_timer(self):
        """Start the karaoke highlighting timer."""
        if self.lyrics_timer:
            self.root.after_cancel(self.lyrics_timer)
        self.lyrics_timer = self.root.after(25, self.update_lyrics_highlight)  # Update every 25ms for ultra-precise timing
    
    def stop_karaoke_timer(self):
        """Stop the karaoke highlighting timer."""
        if self.lyrics_timer:
            self.root.after_cancel(self.lyrics_timer)
            self.lyrics_timer = None
    
    def update_lyrics_highlight(self):
        """Update lyrics highlighting based on current playback time with precise timing"""
        if not self.lyrics_lines:
            return
        
        try:
            # Get current playback time with precise timing
            if self.current_song_path and hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                try:
                    # Get precise position from MPV
                    current_time = self.player.time_pos
                    if current_time is None:
                        current_time = 0
                    current_time_ms = int(current_time * 1000)
                    
                except Exception as e:
                    # Fallback to our own timing if MPV fails
                    if self.start_time:
                        current_time_ms = int((time.time() - self.start_time) * 1000)
                    else:
                        current_time_ms = 0
            
            # Apply timing offset if calibrated
            adjusted_time_ms = current_time_ms
            if hasattr(self, 'lyrics_time_offset'):
                adjusted_time_ms = current_time_ms - self.lyrics_time_offset
            
            # Add preview offset so lyrics highlight slightly before the actual timestamp
            # This gives users time to read and sing along
            preview_offset = 200  # Highlight 200ms before timestamp
            adjusted_time_ms += preview_offset
            
            # Find the current line - use precise timing without compensation
            new_line_index = -1
            for i, (time_ms, text) in enumerate(self.lyrics_lines):
                # Highlight exactly when current time reaches the timestamp
                if adjusted_time_ms >= time_ms:
                    new_line_index = i
                else:
                    break
            
            # Auto-calibrate timing offset on a stable line (not the very first ones)
            if new_line_index >= 0 and new_line_index < 8 and not hasattr(self, 'offset_calibrated'):
                # Only add calibration data when the line changes (not on every timer tick)
                if new_line_index != self.current_line_index:
                    # Calculate the offset needed for this line
                    expected_time = self.lyrics_lines[new_line_index][0]
                    actual_time = current_time_ms
                    calculated_offset = actual_time - expected_time
                    
                    # Store calibration data points for better accuracy
                    if not hasattr(self, 'calibration_data'):
                        self.calibration_data = []
                    
                    # Only add data points that are reasonable (filter out noise)
                    if abs(calculated_offset) < 2000:  # Only accept offsets within 2 seconds
                        self.calibration_data.append((expected_time, actual_time, calculated_offset))
                    
                    # Only calibrate if we're past the initial loading phase (after 3 seconds)
                    # and we have a few good data points from more stable timing
                    if expected_time > 3000 and len(self.calibration_data) >= 3 and len(self.calibration_data) <= 5:
                        # Calculate average offset from a few reliable data points
                        offsets = [data[2] for data in self.calibration_data]
                        avg_offset = sum(offsets) / len(offsets)
                        
                        self.lyrics_time_offset = avg_offset
                        self.offset_calibrated = True
                        adjusted_time_ms = current_time_ms - self.lyrics_time_offset
                    elif expected_time >= 15000:
                        # If we're past 15 seconds without calibration, use the most recent reasonable offset
                        if hasattr(self, 'calibration_data') and self.calibration_data:
                            # Use the most recent offset as fallback
                            last_offset = self.calibration_data[-1][2]
                            self.lyrics_time_offset = last_offset
                            self.offset_calibrated = True
                        else:
                            self.offset_calibrated = True
                            self.lyrics_time_offset = 0
            
            # Apply initial startup compensation if not calibrated yet
            elif not hasattr(self, 'offset_calibrated') and current_time_ms > 1000:
                # If we're 1+ seconds into the song but haven't calibrated yet,
                # apply a temporary compensation for the startup delay
                # This prevents the lyrics from being too far behind during the early lines
                startup_compensation = 600  # 600ms typical startup delay
                self.lyrics_time_offset = startup_compensation
                adjusted_time_ms = current_time_ms - self.lyrics_time_offset
            
            # Update if line changed
            if new_line_index != self.current_line_index and new_line_index >= 0:
                # Prevent large jumps by limiting to one line at a time for smooth progression
                if self.current_line_index >= 0 and abs(new_line_index - self.current_line_index) > 1:
                    # Too big a jump - only move one line in the right direction
                    if new_line_index > self.current_line_index:
                        new_line_index = self.current_line_index + 1
                    else:
                        new_line_index = self.current_line_index - 1
                
                self.current_line_index = new_line_index
                self.highlight_current_line()
            
        except Exception as e:
            print(f"Error updating lyrics highlight: {e}")
        
        # Schedule next update with more frequent checks for better accuracy
        if self.is_playing and not self.is_paused:
            self.lyrics_timer = self.root.after(25, self.update_lyrics_highlight)  # Update every 25ms for even better timing
                
    def highlight_current_line(self):
        """Highlight the current lyrics line and scroll when it reaches 2/3 threshold."""
        if not self.lyrics_lines or self.current_line_index < 0:
            return
        
        try:
            # Get all lyrics text
            all_lines = [text for _, text in self.lyrics_lines]
            full_text = '\n'.join(all_lines)
            
            # Update display with highlighting
            self.lyrics_text.config(state=tk.NORMAL)
            
            # Only update text if it has changed (reduces flicker)
            current_content = self.lyrics_text.get("1.0", tk.END).rstrip('\n')
            if current_content != full_text:
                self.lyrics_text.delete("1.0", tk.END)
                self.lyrics_text.insert("1.0", full_text)
            
            # Remove previous highlighting
            self.lyrics_text.tag_remove("current", "1.0", tk.END)
            
            # Highlight current line
            start_line = f"{self.current_line_index + 1}.0"
            end_line = f"{self.current_line_index + 2}.0"
            
            # Add highlighting tag
            self.lyrics_text.tag_add("current", start_line, end_line)
            self.lyrics_text.tag_config("current", background="#FFB366", foreground="#000000", font=('Segoe UI', self.lyrics_font_size, 'bold'))
            
            # Smart scrolling based on visible line position
            self.lyrics_text.update_idletasks()  # Ensure widget is updated
            
            # Get the line number
            line_num = self.current_line_index + 1
            total_lines = len(all_lines)
            
            # You counted 27 visible lines, so 2/3 threshold is around line 18
            visible_lines = 27
            scroll_threshold = visible_lines * 2 // 3  # 2/3 of visible lines (around line 18)
            
            # Strategy: Let current line progress naturally, only scroll when it reaches 2/3 threshold
            if line_num <= scroll_threshold:
                # Early to mid part - just make current line visible, no special positioning
                self.lyrics_text.see(f"{line_num}.0")
                
                # Only log first few lines and when reaching threshold
                if line_num <= 3 or line_num == scroll_threshold:
                    pass
            else:
                # Current line has passed 2/3 threshold, scroll less frequently for fast songs
                # Only scroll every 10 lines instead of every line to reduce scrolling movement
                
                # Simple scrolling: only scroll when highlight reaches line 25 (near bottom)
                if line_num == 25:  # Scroll exactly when highlight reaches line 25
                    # Scroll to put current line at position 20 (show 7 future lines)
                    target_position = 20
                    scroll_to_line = line_num - target_position
                    
                    # Don't scroll if we're near the end
                    if scroll_to_line > total_lines - visible_lines:
                        self.lyrics_text.see(f"{line_num}.0")
                    else:
                        # Scroll to position
                        scroll_fraction = scroll_to_line / max(1, total_lines - visible_lines)
                        self.lyrics_text.yview_moveto(scroll_fraction)
                else:
                    # Don't scroll, just make current line visible
                    self.lyrics_text.see(f"{line_num}.0")
                    if line_num % 5 == 0:  # Log every 5th line for debugging
                        pass
                    else:
                        # Fallback to see() if content is shorter than visible area
                        self.lyrics_text.see(f"{line_num}.0")
            
            self.lyrics_text.config(state=tk.DISABLED)
            
            # Update scrollbar visibility after highlighting
            self.update_scrollbar_visibility()
            
        except Exception as e:
            print(f"Highlight display error: {e}")
    
    def display_synced_lyrics(self, lyrics_text, source, artist=None, title=None):
        """Display synced lyrics with karaoke highlighting."""
        # Track current lyrics for editing
        # Use provided artist/title, or fallback to current_song metadata
        if artist and title:
            self.current_lyrics_artist = artist
            self.current_lyrics_title = title
        elif hasattr(self, 'current_song') and self.current_song:
            metadata = self.get_song_metadata(self.current_song)
            if metadata and 'artist' in metadata and 'title' in metadata:
                self.current_lyrics_artist = metadata['artist']
                self.current_lyrics_title = metadata['title']
            else:
                return
        else:
            return
        
        self.current_lyrics_content = lyrics_text
        self.current_lyrics_is_synced = True
        
        # Enable edit button
        if hasattr(self, 'edit_lyrics_btn'):
            self.edit_lyrics_btn.config(state=tk.NORMAL)
        
        # Parse LRC timestamps
        self.lyrics_lines = self.parse_lrc_timestamps(lyrics_text)
        
        if self.lyrics_lines:  # Valid synced lyrics found
            # Display all synced lyrics immediately
            all_lyrics_text = '\n'.join([text for _, text in self.lyrics_lines])
            
            self.lyrics_header = f"Synced lyrics ({source}):\n\n"
            self.update_lyrics_display(self.lyrics_header + all_lyrics_text, artist, title, preserve_sync_content=True)
            
            self.current_lyrics = lyrics_text
            self.current_line_index = -1
            
            # Start time-sync timer for highlighting
            if self.is_playing and not self.is_paused:
                self.start_karaoke_timer()
            
            # Highlight first line immediately
            self.current_line_index = 0
            self.highlight_current_line()
        else:  # No timestamps, treat as plain text
            self.update_lyrics_display(f"Lyrics ({source}):\n\n{lyrics_text}")
            self.stop_karaoke_timer()
            self.lyrics_lines = []
            self.current_lyrics = ""
    
    def play_selected_song_at_index(self, index):
        """Play the song at the specified index."""
        # Don't allow song changes during seeking
        if getattr(self, 'seek_pending', False):
            return
            
        if 0 <= index < len(self.playlist):
            self.current_index = index
            self.play_selected_song()
    
    def fetch_lyrics(self, song_path):
        """Fetch lyrics for the current song automatically."""
        # Fetch lyrics for current song
        try:
            # Get song metadata
            metadata = self.get_song_metadata(song_path)
            # Metadata extracted successfully
            artist = metadata['artist']
            title = metadata['title']
            
            # Debug info for troubleshooting
            
            # Loading lyrics display
            self.update_lyrics_status("-- Searching...")
            
            # Try to load local lyrics first
            # Try loading local lyrics
            local_lyrics, source = self.load_local_lyrics(artist, title, song_path)
            # Local lyrics result received
            if local_lyrics:
                # Found local lyrics, displaying
                # Check if lyrics are synced (LRC format) or plain text
                if source == "Local LRC":
                    self.display_synced_lyrics(local_lyrics, source, artist, title)
                    # Update star cache for local LRC files
                    self.update_star_cache(artist, title, has_lyrics=True)
                    self.update_star_for_song(artist, title, has_lyrics=True)
                else:
                    self.update_lyrics_display(local_lyrics, artist, title)
                    self.stop_karaoke_timer()  # Stop karaoke for plain text
                    # Update star cache for local TXT files
                    self.update_star_cache(artist, title, has_lyrics=True)
                    self.update_star_for_song(artist, title, has_lyrics=True)
                self.update_lyrics_status(f"-- Loaded ({source})")
                return
            
            # No local lyrics found, searching APIs
            # Show loading message
            self.update_lyrics_display(f"Searching for lyrics:\n\n{artist} - {title}\n\nPlease wait...", artist, title)
            self.update_lyrics_status("-- Downloading...")
            
            # Clear previous lyrics tracking if no lyrics found yet
            self.current_lyrics_artist = ""
            self.current_lyrics_title = ""
            self.current_lyrics_content = ""
            self.current_lyrics_is_synced = False
            # Keep edit button enabled so user can add lyrics manually
            if hasattr(self, 'edit_lyrics_btn'):
                self.edit_lyrics_btn.config(state=tk.NORMAL)
            
            # Try to fetch lyrics automatically
            def auto_fetch_lyrics():
                # Starting auto-fetch lyrics
                lyrics, source = self.get_lyrics_from_api(artist, title, song_path)
                # API result received
                if lyrics:
                    # Cache downloaded lyrics and display immediately
                    # Caching and displaying lyrics
                    self.cache_lyrics(artist, title, lyrics, song_path)
                    self.update_lyrics_status(f"-- Loaded ({source})")
                else:
                    # Show fallback message
                    # No lyrics found from APIs
                    self.update_lyrics_display(f"No lyrics found for:\n\n{artist} - {title}\n\n"
                                             f"Right-click the song and select:\n"
                                             f"• 🔍 Search LRCLib\n"
                                             f"• 🔍 Search AZLyrics\n"
                                             f"• 🔍 Search Genius\n"
                                             f"• 📝 Add Lyrics Manually")
                    self.update_lyrics_status("-- Not Found")
                    # Clear lyrics tracking when no lyrics found
                    self.current_lyrics_artist = ""
                    self.current_lyrics_title = ""
                    self.current_lyrics_content = ""
                    self.current_lyrics_is_synced = False
                    # Keep edit button enabled so user can add lyrics manually
                    if hasattr(self, 'edit_lyrics_btn'):
                        self.edit_lyrics_btn.config(state=tk.NORMAL)
                    self.stop_karaoke_timer()  # Stop karaoke when no lyrics
            
            # Run in background thread
            # Starting background thread
            threading.Thread(target=auto_fetch_lyrics, daemon=True).start()
            # Background thread started
            
        except Exception as e:
            # Error fetching lyrics
            self.update_lyrics_display("Error loading lyrics")
            self.update_lyrics_status("-- Error")
        
        # Fetch lyrics completed
    
    def get_lyrics_from_api(self, artist, title, song_path=None):
        """Get lyrics from LrcLib and lyrics.ovh based on user preference."""
        print(f"Searching lyrics for {artist} - {title}")
        print(f"LrcLib available: {LRC_AVAILABLE}")
        
        # Get user preference
        preference = self.settings.get('lyrics_preference', 'synced_first')
        
        if preference == 'plain_only':
            # Search LrcLib for plain text only, skip synced lyrics
            if LRC_AVAILABLE:
                try:
                    api = lrclib.LrcLibAPI(user_agent="TinyTunes/1.0")
                    
                    # Get duration from file metadata if available, otherwise use default
                    duration = 180  # Default 3 minutes
                    try:
                        # Try to get duration from the current song file first
                        if song_path:
                            audio_file = mutagen.File(song_path)
                            if audio_file is not None and hasattr(audio_file, 'info'):
                                duration = int(audio_file.info.length)
                        else:
                            # Fallback: search through playlist for matching file
                            if self.playlist:
                                music_folder = Path(self.playlist[0]).parent
                                song_files = list(music_folder.rglob('*.mp3'))
                                
                                for song_file in song_files:
                                    try:
                                        audio_file = mutagen.File(song_file)
                                        if audio_file is not None and hasattr(audio_file, 'info'):
                                            # Check if this file matches our artist/title
                                            file_artist = audio_file.get('artist', [''])[0] if hasattr(audio_file, 'get') else ""
                                            file_title = audio_file.get('title', [''])[0] if hasattr(audio_file, 'get') else ""
                                            
                                            # Try exact match first
                                            if file_artist == artist and file_title == title:
                                                duration = int(audio_file.info.length)
                                                break
                                            # Try filename match as fallback
                                            else:
                                                filename = song_file.stem
                                                expected_filename = f"{artist} - {title}"
                                                if filename.replace('_', ' ') == expected_filename:
                                                    duration = int(audio_file.info.length)
                                                    break
                                    except:
                                        continue
                    except:
                        pass
                    
                    # Ensure duration is between 1-3600 seconds
                    duration = min(max(duration, 1), 3600)
                    
                    print(f"Searching LRCLib for plain lyrics: {artist} - {title} (duration: {duration}s)")
                    
                    # Try multiple search variations for better results
                    search_variations = [
                        (title, artist),  # Original
                        (title.split('(')[0].strip(), artist),  # Without parenthetical info
                        (title.replace('(Phones Re-Edit)', '').strip(), artist),  # Specific case
                        (title.replace('(Re-Edit)', '').strip(), artist),  # Generic re-edit
                    ]
                    
                    for search_title, search_artist in search_variations:
                        if search_title and search_artist:
                            print(f"Trying plain lyrics search: {search_artist} - {search_title}")
                            try:
                                lyrics = api.get_lyrics(
                                    track_name=search_title,
                                    artist_name=search_artist,
                                    album_name="",  # Empty string
                                    duration=duration
                                )
                                
                                if lyrics and lyrics.plain_lyrics:
                                    print(f"Found plain lyrics with variation: {search_artist} - {search_title}")
                                    break
                            except Exception as e:
                                print(f"Plain lyrics search failed for {search_artist} - {search_title}: {e}")
                                continue
                    else:
                        # If all variations failed, try the original one last time
                        print(f"Trying original plain lyrics search as fallback: {artist} - {title}")
                        lyrics = api.get_lyrics(
                            track_name=title,
                            artist_name=artist,
                            album_name="",  # Empty string
                            duration=duration
                        )
                    
                    # Validate the returned lyrics to ensure they match our song
                    if lyrics and lyrics.plain_lyrics:
                        return lyrics.plain_lyrics, "LrcLib"
                    elif lyrics and lyrics.plain_lyrics:
                        # Don't return invalid lyrics, continue to next source
                        pass
                        
                except Exception as e:
                    error_msg = str(e)
                    if "404" in error_msg:
                        pass
                    else:
                        print(f"LrcLib error: {e}")
            
            # Fallback disabled - using LrcLib only
            return None, None
        
        # For 'synced_first' and 'synced_only', try LrcLib
        if LRC_AVAILABLE:
            try:
                api = lrclib.LrcLibAPI(user_agent="TinyTunes/1.0")
                
                # Get duration from file metadata if available, otherwise use default
                duration = 180  # Default 3 minutes
                try:
                    # Try to get duration from the current song file first
                    if song_path:
                        audio_file = mutagen.File(song_path)
                        if audio_file is not None and hasattr(audio_file, 'info'):
                            duration = int(audio_file.info.length)
                    else:
                        # Fallback: search through playlist for matching file
                        # We need to find the file path for this artist/title combination
                        if self.playlist:
                            music_folder = Path(self.playlist[0]).parent
                            song_files = list(music_folder.rglob('*.mp3'))
                            
                            for song_file in song_files:
                                try:
                                    audio_file = mutagen.File(song_file)
                                    if audio_file is not None and hasattr(audio_file, 'info'):
                                        # Check if this file matches our artist/title
                                        file_artist = audio_file.get('artist', [''])[0] if hasattr(audio_file, 'get') else ""
                                        file_title = audio_file.get('title', [''])[0] if hasattr(audio_file, 'get') else ""
                                        
                                        # Try exact match first
                                        if file_artist == artist and file_title == title:
                                            duration = int(audio_file.info.length)
                                            break
                                        # Try filename match as fallback
                                        else:
                                            filename = song_file.stem
                                            expected_filename = f"{artist} - {title}"
                                            if filename.replace('_', ' ') == expected_filename:
                                                duration = int(audio_file.info.length)
                                                break
                                except:
                                    continue
                except:
                    pass
                
                # Ensure duration is between 1-3600 seconds
                duration = min(max(duration, 1), 3600)
                
                print(f"Searching LRCLib for: {artist} - {title} (duration: {duration}s)")
                
                # Try multiple search variations for better results
                search_variations = [
                    (title, artist),  # Original
                    (title.split('(')[0].strip(), artist),  # Without parenthetical info
                    (title.replace('(Phones Re-Edit)', '').strip(), artist),  # Specific case
                    (title.replace('(Re-Edit)', '').strip(), artist),  # Generic re-edit
                ]
                
                for search_title, search_artist in search_variations:
                    if search_title and search_artist:
                        print(f"Trying search: {search_artist} - {search_title}")
                        try:
                            lyrics = api.get_lyrics(
                                track_name=search_title,
                                artist_name=search_artist,
                                album_name="",  # Empty string
                                duration=duration
                            )
                            
                            if lyrics and (lyrics.synced_lyrics or lyrics.plain_lyrics):
                                print(f"Found lyrics with variation: {search_artist} - {search_title}")
                                break
                        except Exception as e:
                            print(f"Search failed for {search_artist} - {search_title}: {e}")
                            continue
                else:
                    # If all variations failed, try the original one last time
                    print(f"Trying original search as fallback: {artist} - {title}")
                    lyrics = api.get_lyrics(
                        track_name=title,
                        artist_name=artist,
                        album_name="",  # Empty string
                        duration=duration
                    )
                
                if lyrics and (lyrics.synced_lyrics or lyrics.plain_lyrics):
                    # Return lyrics without validation
                    # Priority 1: Synced lyrics from LrcLib (for synced_first and synced_only)
                    if lyrics.synced_lyrics:
                        result_lyrics = lyrics.synced_lyrics
                        
                        # Cache the result like old version
                        self.cache_lyrics(artist, title, result_lyrics, song_path)
                        
                        # Display with karaoke for synced lyrics
                        self.display_synced_lyrics(result_lyrics, "LrcLib", artist, title)
                        return result_lyrics, "LrcLib"
                    
                    # Priority 2: Plain lyrics from LrcLib (only if preference allows)
                    elif lyrics.plain_lyrics and preference != 'synced_only':
                        result_lyrics = lyrics.plain_lyrics
                        
                        # Return lyrics without validation
                        self.cache_lyrics(artist, title, result_lyrics, song_path)
                        
                        # Display as plain text
                        self.update_lyrics_display(result_lyrics)
                        self.stop_karaoke_timer()  # Stop karaoke for plain text
                        return True, "LrcLib (plain)"
                    elif lyrics.plain_lyrics and preference == 'synced_only':
                        pass
                    else:
                        pass
                else:
                    pass
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    pass
                else:
                    print(f"LrcLib error: {e}")
        
        # Fallback disabled - using LrcLib only
        return None, None
    
    def cache_lyrics(self, artist, title, lyrics, song_path=None):
        """Cache downloaded lyrics based on user storage preference."""
        try:
            # Ensure lyrics is a string, not a boolean or None
            if not isinstance(lyrics, str):
                return
            
            # Check if lyrics are synced (have timestamps) or plain text
            is_synced = self.is_synced_lyrics(lyrics)
            
            # Create clean filename for file system
            filename_clean = f"{artist} - {title}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # Store in album folder
            if song_path:
                album_path = Path(self.get_album_lyrics_path(song_path))
                if album_path:
                    if is_synced:
                        cache_file = album_path / f"{filename_clean}.lrc"
                    else:
                        cache_file = album_path / f"{filename_clean}.txt"
                    
                    cache_file.write_text(lyrics, encoding='utf-8')
                else:
                    pass
            else:
                pass
            
            # Update star for this song
            self.update_star_for_song(artist, title, has_lyrics=True)
            # Update star cache
            self.update_star_cache(artist, title, has_lyrics=True)
            
        except Exception as e:
            print(f"Cache error: {e}")
    
    def is_synced_lyrics(self, lyrics):
        """Check if lyrics contain timestamps (LRC format)."""
        import re
        
        # Ensure lyrics is a string, not a boolean or None
        if not isinstance(lyrics, str):
            return False
        
        # Look for timestamp pattern [mm:ss.xx] or [mm:ss]
        timestamp_pattern = r'\[\d{2}:\d{2}(?:\.\d{2})?\]'
        return bool(re.search(timestamp_pattern, lyrics))
    
    def save_plain_txt_lyrics(self, artist, title, lyrics, song_path=None):
        """Save manual lyrics as individual files in the song's album folder."""
        import os
        import json
        from pathlib import Path
        
        # Create clean filename
        filename = f"{artist} - {title}"
        filename_clean = filename.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        
        # Save lyrics file in the song's album folder
        if song_path:
            album_path = Path(self.get_album_lyrics_path(song_path))
            if album_path:
                lyrics_file = album_path / f"{filename_clean}.txt"
                lyrics_file.write_text(lyrics, encoding='utf-8')
                return str(lyrics_file)
        
        return None
    
    def get_album_lyrics_path(self, song_path):
        """Get the album folder path for storing lyrics next to the song file."""
        try:
            song_dir = Path(song_path).parent
            return str(song_dir)
        except:
            return None
    
    def get_lyrics_storage_paths(self, artist, title, song_path=None):
        """Get all possible lyrics storage paths - album folders only."""
        paths = []
        
        # Create clean filename for file system
        filename_clean = f"{artist} - {title}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        
        # Only check album folders
        if song_path:
            album_path = self.get_album_lyrics_path(song_path)
            if album_path:
                paths.append({
                    'lrc': Path(album_path) / f"{filename_clean}.lrc",
                    'txt': Path(album_path) / f"{filename_clean}.txt",
                    'type': 'album'
                })
        
        return paths
    
    def load_local_lyrics(self, artist, title, song_path=None):
        """Load lyrics from local cache (both TXT and LRC files) based on user preference."""
        import json
        from pathlib import Path
        
        # Get user preference
        preference = self.settings.get('lyrics_preference', 'synced_first')
        
        # Get all possible storage paths
        paths = self.get_lyrics_storage_paths(artist, title, song_path)
        
        if preference == 'synced_only':
            # Only load synced lyrics
            for path_set in paths:
                lrc_file = path_set['lrc']
                if lrc_file.exists():
                    content = lrc_file.read_text(encoding='utf-8')
                    return content, "Local LRC"
            
            return None, None
                
        elif preference == 'plain_only':
            # Only load plain text lyrics
            for path_set in paths:
                txt_file = path_set['txt']
                if txt_file.exists():
                    content = txt_file.read_text(encoding='utf-8')
                    return content, "Local TXT"
            
            return None, None
                
        else:  # 'synced_first' (default)
            # Try synced lyrics first, then plain text as fallback
            for path_set in paths:
                lrc_file = path_set['lrc']
                if lrc_file.exists():
                    content = lrc_file.read_text(encoding='utf-8')
                    return content, "Local LRC"
            
            # Fallback to plain text
            for path_set in paths:
                txt_file = path_set['txt']
                if txt_file.exists():
                    content = txt_file.read_text(encoding='utf-8')
                    return content, "Local TXT"
                
        return None, None
    
    def play_selected_song(self):
        # Don't allow song changes during seeking
        if getattr(self, 'seek_pending', False):
            return
        
        # Check if auto-play should be allowed
        if not self.auto_play_enabled:
            if not self.has_manually_played:
                return
            else:
                pass
            
        if self.current_index < len(self.playlist):
            self.current_song = song_path = self.playlist[self.current_index]
            self.current_song_path = os.path.normpath(song_path)  # Normalize path separators
            metadata = self.playlist_metadata[self.current_index]
            song_name = os.path.basename(song_path)
            
            # Highlight current song in playlist
            self.highlight_current_song()
            
            # Refresh metadata to ensure we have the latest ID3 tag information
            self.refresh_current_song_metadata()
            
            # Update song info immediately using metadata
            metadata = self.playlist_metadata[self.current_index]
            song_display_name = metadata.get('display_name', os.path.basename(song_path))
            
            # Start scrolling with the properly formatted song name
            self.start_scrolling(song_display_name)
            
            # Display album cover for the playing song
            self.display_album_cover(song_path)
            
            # Extract and display song length immediately
            try:
                audio_file = mutagen.File(song_path)
                if audio_file is not None and hasattr(audio_file, 'info'):
                    length_seconds = int(audio_file.info.length)
                    minutes = length_seconds // 60
                    seconds = length_seconds % 60
                    self.total_time = length_seconds
                    self.song_length_label.config(text=f"({minutes}:{seconds:02d})")
                else:
                    # Fallback to metadata
                    metadata = self.get_song_metadata(song_path)
                    if 'length' in metadata:
                        time_parts = metadata['length'].split(':')
                        self.total_time = int(time_parts[0]) * 60 + int(time_parts[1])
                    else:
                        self.total_time = 0
            except:
                self.total_time = 0
            
            self.current_time = 0
            self.update_time_display()
            
            # Reset karaoke state for new song
            self.stop_karaoke_timer()
            self.current_line_index = -1
            self.lyrics_lines = []
            self.current_lyrics = ""
            # Reset timing calibration for new song
            if hasattr(self, 'lyrics_time_offset'):
                delattr(self, 'lyrics_time_offset')
            if hasattr(self, 'offset_calibrated'):
                delattr(self, 'offset_calibrated')
            
            # Auto-load lyrics for the new song
            self.fetch_lyrics(song_path)
            
            # Preload audio analysis when song is selected (not when played)
            def preload_audio_analysis():
                self.load_audio_for_analysis(self.current_song)
                # Start visualization immediately even before analysis completes
                self.start_visualization()
                # Start analysis in background
                self.start_audio_analysis()
            
            threading.Thread(target=preload_audio_analysis, daemon=True).start()
            
            # Load and play the song using mpv or pygame mixer fallback
            try:
                # Increment usage counter and check if reinitialization is needed
                self.player_usage_count += 1
                if self.player_usage_count >= self.max_player_uses:
                    print(f"Player usage count reached {self.player_usage_count}, reinitializing...")
                    self.reinitialize_player()
                    self.player_usage_count = 0  # Reset counter after reinitialization
                
                # Stop any currently playing song and clean up resources
                self.cleanup_player_resources()
                
                # Load and play the song
                if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                    # Use MPV for real seeking
                    self.player.play(self.current_song)
                    self.player.volume = int(self.volume * 100)
                    
                    # Check if MPV is actually playing and reinitialize if needed
                    def check_mpv_status():
                        try:
                            if hasattr(self.player, 'time_pos'):
                                pos = self.player.time_pos
                                if pos is not None and pos > 0:
                                    pass  # MPV is playing successfully
                                else:
                                    # MPV position is 0 or None - might not be playing
                                    if not self.is_paused and self.is_playing:
                                        # Try to restart once
                                        try:
                                            self.player.play(self.current_song)
                                        except:
                                            # If restart fails, reinitialize player
                                            print("MPV restart failed, reinitializing player...")
                                            self.reinitialize_player()
                                            # Try playing again with new player
                                            if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                                                try:
                                                    self.player.play(self.current_song)
                                                    self.player.volume = int(self.volume * 100)
                                                except:
                                                    pass
                        except Exception as e:
                            print(f"Error checking MPV status: {e}")
                            # If status check fails, reinitialize player
                            if not self.is_paused and self.is_playing:
                                self.reinitialize_player()
                                if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                                    try:
                                        self.player.play(self.current_song)
                                        self.player.volume = int(self.volume * 100)
                                    except:
                                        pass
                    
                    # Check status after a short delay
                    self.root.after(1000, check_mpv_status)
                    
                else:
                    # Fallback to pygame mixer
                    pygame.mixer.music.load(self.current_song)
                    pygame.mixer.music.play()
                    pygame.mixer.music.set_volume(self.volume)
                
                # Set playing state BEFORE starting analysis
                self.is_playing = True
                self.is_paused = False
                
                # Save the last played song
                self.save_last_played_song(song_path, metadata)
                
                # Start time tracking
                self.start_time_tracking()
                
                # Start audio analysis for visualization
                self.start_audio_analysis()
                
                # Start karaoke timer if synced lyrics are loaded
                if hasattr(self, 'lyrics_lines') and self.lyrics_lines:
                    self.start_karaoke_timer()
                
                print(f"Now playing: {os.path.basename(self.current_song)}")
                
            except Exception as e:
                print(f"Error playing song: {e}")
                self.is_playing = False
                self.is_paused = False
                # Try to cleanup on error
                self.cleanup_player_resources()
            
    def reinitialize_player(self):
        """Reinitialize the MPV player if it gets into a bad state"""
        try:
            # Cleanup existing player
            if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                try:
                    self.player.stop()
                    del self.player
                except:
                    pass
            
            # Reinitialize MPV if available
            if MPV_AVAILABLE and mpv:
                try:
                    # Initialize MPV with better Windows audio settings
                    self.player = mpv.MPV(
                        ytdl=False, 
                        vo='null',  # No video output
                        ao='wasapi'  # Windows Audio Session API
                    )
                    self.player.volume = int(self.volume * 100) if hasattr(self, 'volume') else 70
                    
                    # Set some additional options for better playback
                    self.player.keep_open = 'no'  # Don't keep open when finished
                    self.player.loop = 'no'  # Don't loop by default
                    
                    self.use_pygame_fallback = False
                    print("MPV player reinitialized successfully")
                except Exception as e:
                    print(f"Failed to reinitialize MPV: {e}")
                    self.use_pygame_fallback = True
            else:
                self.use_pygame_fallback = True
                
        except Exception as e:
            print(f"Error reinitializing player: {e}")
            self.use_pygame_fallback = True
    
    def stop_time_tracking(self):
        """Stop the time tracking timer"""
        if hasattr(self, 'time_update_job') and self.time_update_job:
            self.root.after_cancel(self.time_update_job)
            self.time_update_job = None
    
    def cleanup_player_resources(self):
        """Clean up player resources to prevent memory leaks and state issues"""
        try:
            # Stop all timers and threads first
            self.stop_karaoke_timer()
            self.stop_audio_analysis()
            self.stop_time_tracking()
            # Don't stop scrolling here - it should continue for the new song
            
            # Stop and cleanup MPV player
            if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                try:
                    self.player.stop()
                    # Give MPV a moment to cleanup
                    self.root.after(100, lambda: None)
                except:
                    pass
            else:
                # Stop pygame mixer
                try:
                    import pygame.mixer
                    pygame.mixer.music.stop()
                except:
                    pass
            
            # Clear audio data
            if hasattr(self, 'audio_data'):
                self.audio_data.clear()
                
            # Reset visualization state
            self.visualization_running = False
            
        except Exception as e:
            pass  # Silently handle cleanup errors
    
    def play_song(self):
        # PRIORITY 1: Resume from pause if we're paused - this should be checked BEFORE treeview selection
        if self.is_paused:
            # Resume from pause - don't change the current song
            try:
                if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                    self.player.pause = False  # Unpause with mpv
                else:
                    import pygame.mixer
                    pygame.mixer.music.unpause()
                self.is_paused = False
                self.is_playing = True
                
                # Clear previous synced lyrics state before reloading
                self.stop_karaoke_timer()
                self.lyrics_lines = []
                
                # Reload lyrics to ensure we have the latest version
                if hasattr(self, 'current_song') and self.current_song:
                    self.fetch_lyrics(self.current_song)
                
                # Start karaoke timer only if the newly loaded lyrics are synced
                if self.lyrics_lines and self.current_lyrics_is_synced:
                    self.start_karaoke_timer()
                self.start_visualization()
                self.start_audio_analysis()
            except Exception as e:
                pass
            return
        
        # PRIORITY 2: If not paused, check if we have a loaded song (like last played song) first
        # This takes priority over treeview selection for Winamp-like behavior
        if hasattr(self, 'current_song') and self.current_song and not self.is_playing:
            # We have a loaded song (like from last played) - play it regardless of selection
            # Find the index of this song in the playlist
            try:
                song_index = self.playlist.index(self.current_song)
                self.current_index = song_index
                
                # Highlight this song in the treeview
                self.highlight_current_song()
                
                # Start playing the loaded song
                # Enable auto-play for this explicit user action
                self.auto_play_enabled = True
                self.has_manually_played = True  # Mark that user has manually played
                self.play_selected_song()
                self.auto_play_enabled = False  # Disable again after playing
                return
            except ValueError:
                # Song not found in playlist, just play it directly
                # Enable auto-play for this explicit user action
                self.auto_play_enabled = True
                self.has_manually_played = True  # Mark that user has manually played
                self.play_selected_song()
                self.auto_play_enabled = False  # Disable again after playing
                return
        
        # PRIORITY 3: If not paused and no loaded song, then check treeview selection for new song selection
        selection = self.playlist_treeview.selection()
        
        if selection:
            item = selection[0]
            
            # Get the original index from tags (same logic as double-click)
            tags = self.playlist_treeview.item(item, 'tags')
            song_index = -1
            
            for tag in tags:
                if tag.startswith('index_'):
                    try:
                        song_index = int(tag.split('_')[1])
                        break
                    except (ValueError, IndexError):
                        continue
            
            if song_index >= 0 and song_index < len(self.playlist):
                # Only change song if it's different from current song
                if song_index != self.current_index:
                    self.current_index = song_index
                    
                    # Update current song when getting from selection
                    if self.current_index < len(self.playlist):
                        self.current_song = self.playlist[self.current_index]
                    
                    # Start playing the selected song
                    # Enable auto-play for this explicit user action
                    self.auto_play_enabled = True
                    self.has_manually_played = True  # Mark that user has manually played
                    self.play_selected_song()
                    self.auto_play_enabled = False  # Disable again after playing
                else:
                    # Same song selected - just resume if paused or restart if stopped
                    if self.is_paused:
                        # Resume the current song
                        try:
                            if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                                self.player.pause = False  # Unpause with mpv
                            else:
                                import pygame.mixer
                                pygame.mixer.music.unpause()
                            self.is_paused = False
                            self.is_playing = True
                            # Start karaoke timer if synced lyrics are loaded
                            if self.lyrics_lines:
                                self.start_karaoke_timer()
                            self.start_visualization()
                            self.start_audio_analysis()
                        except:
                            pass
                    elif not self.is_playing:
                        # Restart the current song
                        # Enable auto-play for this explicit user action
                        self.auto_play_enabled = True
                        self.has_manually_played = True  # Mark that user has manually played
                        self.play_selected_song()
                        self.auto_play_enabled = False  # Disable again after playing
            else:
                # Fallback to treeview index (less reliable)
                treeview_index = self.playlist_treeview.index(item)
                if treeview_index != self.current_index:
                    self.current_index = treeview_index
                    
                    # Update current song when getting from selection
                    if self.current_index < len(self.playlist):
                        self.current_song = self.playlist[self.current_index]
                    
                    # Start playing the selected song
                    # Enable auto-play for this explicit user action
                    self.auto_play_enabled = True
                    self.has_manually_played = True  # Mark that user has manually played
                    self.play_selected_song()
                    self.auto_play_enabled = False  # Disable again after playing
                else:
                    pass
            
    def pause_song(self):
        if self.is_playing and not self.is_paused:
            # Pause playback
            try:
                if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                    self.player.pause = True  # Pause with mpv
                else:
                    import pygame.mixer
                    pygame.mixer.music.pause()
                self.is_paused = True
                # Stop karaoke timer when paused
                self.stop_karaoke_timer()
                # Stop audio analysis to prevent jittering
                self.stop_audio_analysis()
                # Stop time tracking to prevent updates while paused
                self.stop_time_tracking()
                # Clear audio data to freeze visualization
                if hasattr(self, 'audio_data'):
                    self.audio_data.clear()
            except Exception as e:
                print(f"Error pausing song: {e}")
                # If pause fails, try to stop and cleanup
                self.cleanup_player_resources()
                self.is_playing = False
                self.is_paused = False
    
    def stop_song(self):
        if self.is_playing:
            # Increment usage counter and check if reinitialization is needed
            self.player_usage_count += 1
            if self.player_usage_count >= self.max_player_uses:
                print(f"Player usage count reached {self.player_usage_count}, reinitializing...")
                self.reinitialize_player()
                self.player_usage_count = 0  # Reset counter after reinitialization
            
            # Use the new cleanup method for consistent resource management
            self.cleanup_player_resources()
            
            # Set state flags
            self.is_playing = False
            self.is_paused = False
            self.current_time = 0
            self.update_time_display()
            
            # Stop scrolling when song stops
            self.stop_scrolling()
            
            # Keep song info but update status to show it's stopped
            if self.current_song:
                # Use the current metadata instead of filename
                if self.current_index < len(self.playlist_metadata):
                    metadata = self.playlist_metadata[self.current_index]
                    song_display_name = metadata.get('display_name', os.path.basename(self.current_song))
                else:
                    # Fallback to filename if metadata not available
                    song_display_name = os.path.basename(self.current_song)
                    if song_display_name.lower().endswith('.mp3'):
                        song_display_name = song_display_name[:-4]
                
                self.song_title_label.config(text=song_display_name)
                # Update artist label to show stopped status
                self.song_artist_label.config(text="Stopped")
                # Keep the album cover visible when stopped
                # Don't call show_default_album_icon()
            else:
                self.song_title_label.config(text="No song playing")
                self.song_length_label.config(text="(0:00)")
                self.current_time_label.config(text="0:00")
                self.show_default_album_icon()
        
            # Clear visualization
            self.visualization_canvas.delete("all")
            # Clean up visualization items to prevent memory leaks
            if hasattr(self, 'viz_bars'):
                self.viz_bars.clear()
            if hasattr(self, 'viz_peaks'):
                self.viz_peaks.clear()
        
            # Reset progress bar
            self.progress_fill.config(width=0)
        
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete(1.0, tk.END)
        self.lyrics_text.config(state=tk.DISABLED)
        
    def previous_song(self):
        # Don't allow song changes during seeking
        if getattr(self, 'seek_pending', False):
            return
        
        if self.is_shuffle and self.shuffle_history:
            # In shuffle mode, go to previous song in shuffle history
            if self.shuffle_history_index > 0:
                self.shuffle_history_index -= 1
                self.current_index = self.shuffle_history[self.shuffle_history_index]
                self.play_selected_song()
            elif self.shuffle_history_index == 0:
                # If we're at the first song in history, just replay it
                self.play_selected_song()
        else:
            # Normal mode - go to previous song in playlist
            if self.current_index > 0:
                self.current_index -= 1
                self.play_selected_song()
            
    def next_song(self):
        # Don't allow song changes during seeking
        if getattr(self, 'seek_pending', False):
            return
            
        if self.is_shuffle and self.playlist:
            # Random song in shuffle mode
            import random
            self.current_index = random.randint(0, len(self.playlist) - 1)
            
            # Add to shuffle history
            self.shuffle_history.append(self.current_index)
            self.shuffle_history_index = len(self.shuffle_history) - 1
            
            # Limit history size to prevent memory issues
            if len(self.shuffle_history) > 100:
                self.shuffle_history.pop(0)
                self.shuffle_history_index -= 1
            
            self.play_selected_song()
        elif self.current_index < len(self.playlist) - 1:
            # Next song in normal mode
            self.current_index += 1
            self.play_selected_song()
    
    def toggle_shuffle(self):
        """Toggle shuffle mode on/off"""
        self.is_shuffle = not self.is_shuffle
        
        # Clear shuffle history when turning off shuffle
        if not self.is_shuffle:
            self.shuffle_history = []
            self.shuffle_history_index = -1
        
        # Save shuffle state to file
        self.save_shuffle_state()
        
        # Update shuffle status text
        self.update_shuffle_status()
        
        if self.is_shuffle:
            print("Shuffle mode ON")
        else:
            print("Shuffle mode OFF")
    
    def load_shuffle_state(self):
        """Load shuffle state from file"""
        try:
            with open('shuffle_state.json', 'r') as f:
                data = json.load(f)
                shuffle_state = data.get('is_shuffle', False)
                return shuffle_state
        except Exception as e:
            return False
    
    def save_shuffle_state(self):
        """Save shuffle state to file"""
        try:
            with open('shuffle_state.json', 'w') as f:
                json.dump({'is_shuffle': self.is_shuffle}, f)
                print(f"Saved shuffle state: {self.is_shuffle}")
        except Exception as e:
            print(f"Error saving shuffle state: {e}")
    
    def update_shuffle_status(self):
        """Update the shuffle status text display"""
        if hasattr(self, 'shuffle_status_label'):
            if self.is_shuffle:
                self.shuffle_status_label.config(text="Shuffle: ON", fg='#00ff00')  # Bright green when on
            else:
                self.shuffle_status_label.config(text="Shuffle: OFF", fg='#8b949e')  # Gray when off
    
    def highlight_current_song(self):
        """Highlight the currently playing song in the playlist"""
        if hasattr(self, 'playlist_treeview') and self.playlist:
            # Clear all previous highlights by removing tags
            for item in self.playlist_treeview.get_children():
                self.playlist_treeview.item(item, tags=())
            
            # Highlight current song with tag
            if self.current_index < len(self.playlist_treeview.get_children()):
                current_item = self.playlist_treeview.get_children()[self.current_index]
                self.playlist_treeview.item(current_item, tags=('current_song',))
                
                # Configure tag for highlighting - use peach color if peach theme is active
                if hasattr(self, 'current_theme') and self.current_theme == 'peach':
                    # Use a darker peach for playing song to distinguish from regular selection
                    self.playlist_treeview.tag_configure('current_song', background='#FF9933')
                else:
                    # Default dark theme color
                    self.playlist_treeview.tag_configure('current_song', background='#2d333b')
                
                # Auto-scroll to current song
                self.playlist_treeview.see(current_item)
            
    def update_time_display(self):
        """Update the current time display using mpv position"""
        try:
            # Only update time if we're not in the middle of seeking
            if not getattr(self, 'seek_pending', False):
                if self.is_playing and not self.is_paused:
                    # Get actual position from mpv
                    try:
                        if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                            # Get position from mpv
                            time_pos = self.player.time_pos
                            if time_pos is not None and time_pos >= 0:
                                # Only update if significantly different (prevents jitter)
                                if abs(self.current_time - time_pos) > 0.1:
                                    self.current_time = time_pos
                        else:
                            # Fallback to pygame mixer
                            pos_ms = pygame.mixer.music.get_pos()
                            if pos_ms >= 0:
                                pygame_time = pos_ms // 1000
                                # Only update if significantly different
                                if abs(self.current_time - pygame_time) > 0.1:
                                    self.current_time = pygame_time
                    except:
                        pass
        except:
            pass
        
        minutes = int(self.current_time // 60)
        seconds = int(self.current_time % 60)
        self.current_time_label.config(text=f"{minutes}:{seconds:02d}")
        
        # Update progress bar using our new method
        self.update_progress_display()
    
    def start_time_tracking(self):
        """Start tracking playback time"""
        def update_time():
            if self.is_playing and not self.is_paused:
                # Don't update time during seeking
                if getattr(self, 'seek_pending', False):
                    self.root.after(100, update_time)
                    return
                
                # Get actual position from pygame mixer
                try:
                    pos_ms = pygame.mixer.music.get_pos()
                    if pos_ms >= 0:
                        self.current_time = pos_ms // 1000  # Convert to seconds
                    else:
                        # If get_pos() returns -1, song ended
                        self.current_time = self.total_time + 1
                except:
                    pass
                
                # Update display
                self.update_time_display()
                
                # Check if song ended
                if self.current_time >= self.total_time:
                    # Song ended, play next
                    self.next_song()
                else:
                    # Continue tracking
                    self.root.after(1000, update_time)  # Update every second
            elif self.is_playing and self.is_paused:
                # If paused, check again in a second
                self.root.after(1000, update_time)
        
        self.root.after(1000, update_time)
    
    def load_audio_for_analysis(self, audio_file):
        """Load audio file for real-time analysis using librosa (optimized for speed)"""
        # Check if audio is already loaded for this file
        if self.current_audio_samples is not None and hasattr(self, 'current_audio_file') and self.current_audio_file == audio_file:
            print(f"Audio already loaded for {audio_file}, skipping reload")
            return
        
        try:
            # Load audio file using librosa for analysis
            self.current_audio_samples, self.audio_sample_rate = librosa.load(audio_file, sr=22050, mono=True)
            self.audio_duration = len(self.current_audio_samples) / self.audio_sample_rate
            self.current_audio_file = audio_file
            print(f"Audio loaded for analysis: {self.audio_duration:.2f}s at {self.audio_sample_rate}Hz")
            
            # Always load with pygame mixer for visualization (even with MPV)
            try:
                pygame.mixer.music.load(audio_file)
            except Exception as e:
                print(f"Pygame mixer load failed: {e}")
                    
        except Exception as e:
            print(f"Error loading audio for analysis: {e}")
            self.current_audio_samples = None
            self.audio_sample_rate = 22050
            self.audio_duration = 0
    
    def start_audio_analysis(self):
        """Start thread to analyze real audio data for visualization"""
        print(f"Starting audio analysis - samples available: {self.current_audio_samples is not None}")
        if self.current_audio_samples is None:
            # Try to load audio again
            if hasattr(self, 'current_song') and self.current_song:
                self.load_audio_for_analysis(self.current_song)
                if self.current_audio_samples is not None:
                    print("Audio reload successful, starting analysis")
                else:
                    return
            else:
                return
        
        if self.analyzing_audio:
            print("Analysis already running, stopping first...")
            self.stop_audio_analysis()
            
        self.analyzing_audio = True
        self.audio_thread = threading.Thread(target=self.analyze_real_audio, daemon=True)
        self.audio_thread.start()
        print("Audio analysis thread started")
    
    def analyze_real_audio(self):
        """Analyze real audio data for visualization using pydub samples with beat detection"""
        # Use raw audio samples for real-time analysis like the working example
        
        while self.analyzing_audio and self.is_playing:
            if self.is_playing and not self.is_paused and self.current_audio_samples is not None:
                try:
                    # Try to get position from the active audio source
                    try:
                        if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', True):
                            # Get position from MPV for accurate sync
                            time_pos = self.player.time_pos
                            if time_pos is not None and time_pos >= 0:
                                current_time = time_pos
                            else:
                                current_time = self.current_time
                        else:
                            # Fallback to pygame mixer
                            pos_ms = pygame.mixer.music.get_pos()
                            if pos_ms >= 0:
                                current_time = pos_ms / 1000.0
                            else:
                                current_time = self.current_time
                    except:
                        current_time = self.current_time  # Fallback to our time tracking
                    
                    # Only analyze if we have valid time and audio
                    if 0 <= current_time < self.audio_duration:
                        # Calculate sample position with better sync
                        self.sample_position = int(current_time * self.audio_sample_rate)
                        
                        # Use overlapping windows for smoother analysis (like Web Audio API)
                        window_size = 1024  # Smaller window for better responsiveness
                        hop_size = 512  # 50% overlap
                        
                        # Extract multiple windows around current position for better analysis
                        windows_to_analyze = 3
                        all_freq_bands = []
                        
                        for w in range(windows_to_analyze):
                            window_offset = (w - windows_to_analyze // 2) * hop_size
                            start_sample = max(0, self.sample_position + window_offset - window_size // 2)
                            end_sample = min(len(self.current_audio_samples), self.sample_position + window_offset + window_size // 2)
                            
                            if end_sample > start_sample and (end_sample - start_sample) >= window_size:
                                # Extract audio window
                                audio_window = self.current_audio_samples[start_sample:end_sample]
                                
                                # Pad if necessary to get exact window size
                                if len(audio_window) < window_size:
                                    audio_window = np.pad(audio_window, (0, window_size - len(audio_window)), 'constant')
                                
                                # Apply window function (Hanning) to reduce spectral leakage
                                window_function = np.hanning(window_size)
                                audio_window = audio_window * window_function
                                
                                # Apply FFT (like Web Audio API)
                                fft_result = np.fft.fft(audio_window[:window_size])
                                magnitude = np.abs(fft_result[:window_size // 2])
                                
                                # Convert to 32 frequency bands (like Winamp)
                                freq_bands = self.fft_to_frequency_bands(magnitude, self.audio_sample_rate)
                                
                                # Normalize to 0-1 range
                                if np.max(freq_bands) > 0:
                                    freq_bands = freq_bands / np.max(freq_bands)
                                
                                freq_bands = np.clip(freq_bands, 0, 1)
                                all_freq_bands.append(freq_bands)
                        
                        # Average across windows for smoothness but keep responsiveness
                        if all_freq_bands:
                            freq_bands = np.mean(all_freq_bands, axis=0)
                            
                            # Apply beat detection enhancement
                            freq_bands = self.enhance_beat_response(freq_bands)
                            
                            self.audio_data = freq_bands.tolist()
                            
                            # Debug: Check if we're getting data
                            if len(self.audio_data) > 0:
                                max_amplitude = max(self.audio_data)
                                if max_amplitude > 0.01:  # Only print occasionally if there's actual signal
                                    if not hasattr(self, 'viz_debug_counter'):
                                        self.viz_debug_counter = 0
                                self.viz_debug_counter += 1
                    
                except Exception as e:
                    print(f"Error in audio analysis: {e}")
            
            time.sleep(0.016)  # Update 60 times per second for responsive visualization
    
    def enhance_beat_response(self, freq_bands):
        """Enhance beat response for better visual impact"""
        # Boost bass frequencies for better beat response
        bass_boost = 1.3
        mid_boost = 1.1
        high_boost = 1.0
        
        enhanced_bands = freq_bands.copy()
        
        for i in range(32):
            if i < 8:  # Bass frequencies
                enhanced_bands[i] = min(1.0, freq_bands[i] * bass_boost)
            elif i < 20:  # Mid frequencies
                enhanced_bands[i] = min(1.0, freq_bands[i] * mid_boost)
            else:  # High frequencies
                enhanced_bands[i] = min(1.0, freq_bands[i] * high_boost)
        
        return enhanced_bands
    
    def fft_to_frequency_bands(self, magnitude, sample_rate):
        """Convert FFT magnitude to 32 frequency bands like Winamp"""
        # Create 32 logarithmic frequency bands (like Winamp)
        bands = np.zeros(32)
        
        # Define frequency ranges for each band (logarithmic scale)
        min_freq = 20  # 20 Hz (bottom of human hearing)
        max_freq = sample_rate // 2  # Nyquist frequency
        
        # Generate frequency bins for FFT correctly
        freq_bins = np.linspace(0, sample_rate // 2, len(magnitude))
        
        for i in range(32):
            # Calculate frequency range for this band
            log_min = np.log10(min_freq)
            log_max = np.log10(max_freq)
            band_log_min = log_min + (log_max - log_min) * i / 32
            band_log_max = log_min + (log_max - log_min) * (i + 1) / 32
            band_min = 10 ** band_log_min
            band_max = 10 ** band_log_max
            
            # Find frequency bins in this range
            band_mask = (freq_bins >= band_min) & (freq_bins <= band_max)
            
            if np.any(band_mask):
                # Average magnitude in this frequency band
                bands[i] = np.mean(magnitude[band_mask])
            else:
                # If no bins in range, use nearest bin
                if band_min < freq_bins[0]:
                    bands[i] = magnitude[0]
                elif band_max > freq_bins[-1]:
                    bands[i] = magnitude[-1]
                else:
                    # Find closest bin
                    closest_idx = np.argmin(np.abs(freq_bins - band_min))
                    bands[i] = magnitude[closest_idx]
        
        return bands
    
    def stop_audio_analysis(self):
        """Stop the audio analysis thread"""
        self.analyzing_audio = False
        # Don't set visualization_running to False here - let the stop_song method handle that
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)  # Wait for thread to finish
    
    def start_visualization(self):
        """Start the audio visualization"""
        self.visualization_running = True
        if hasattr(self, 'visualization_canvas'):
            pass  # Canvas exists, ready for visualization
        self.animate_visualization()
    def animate_visualization(self):
        """Create Winamp-style visualization with many bars and peak effects"""
        if not self.visualization_running:
            return
        
        # Check if visualization canvas exists
        if not hasattr(self, 'visualization_canvas'):
            return
        
        # Get canvas dimensions
        width = self.visualization_canvas.winfo_width()
        height = self.visualization_canvas.winfo_height()
        
        if width <= 1:  # Canvas not yet rendered
            self.root.after(200, self.animate_visualization)
            return
        
        # Winamp-style setup
        num_bars = 32  # Winamp typically has 32+ bars
        bar_spacing = 1
        bar_width = max(1, (width - (num_bars + 1) * bar_spacing) // num_bars)
        
        # Initialize peak holders and canvas items
        if not hasattr(self, 'bar_peaks'):
            self.bar_peaks = [0] * num_bars
        if not hasattr(self, 'bar_levels'):
            self.bar_levels = [0] * num_bars
        if not hasattr(self, 'viz_bars') or len(self.viz_bars) != num_bars:
            # Clear existing items if they exist
            if hasattr(self, 'viz_bars'):
                for bar in self.viz_bars:
                    self.visualization_canvas.delete(bar)
                self.viz_bars.clear()
            if hasattr(self, 'viz_peaks'):
                for peak in self.viz_peaks:
                    self.visualization_canvas.delete(peak)
                self.viz_peaks.clear()
            
            # Create canvas items once and reuse them
            self.viz_bars = []
            self.viz_peaks = []
            for i in range(num_bars):
                x1 = i * (bar_width + bar_spacing) + bar_spacing
                x2 = x1 + bar_width
                # Create bar item (will be updated with coords)
                bar = self.visualization_canvas.create_rectangle(
                    x1, height, x2, height,
                    fill="#00ff00", outline=""
                )
                self.viz_bars.append(bar)
                # Create peak item
                peak = self.visualization_canvas.create_rectangle(
                    x1, height, x2, height,
                    fill="#ffff00", outline=""
                )
                self.viz_peaks.append(peak)
        
        # Ensure arrays have correct size
        if len(self.bar_peaks) != num_bars:
            self.bar_peaks = [0] * num_bars
        if len(self.bar_levels) != num_bars:
            self.bar_levels = [0] * num_bars
        
        # Use real audio data if available, otherwise show placeholder animation
        if self.audio_data and len(self.audio_data) >= num_bars and not self.is_paused:
            # Use actual audio analysis data - very responsive transitions
            for i in range(num_bars):
                amplitude = self.audio_data[i]
                target_level = amplitude * height * 0.95
                # Very responsive transitions (20% old, 80% new)
                self.bar_levels[i] = self.bar_levels[i] * 0.2 + target_level * 0.8
                
                # Peak effect - responsive decay for beat following
                if self.bar_levels[i] > self.bar_peaks[i]:
                    self.bar_peaks[i] = self.bar_levels[i]
                else:
                    self.bar_peaks[i] = max(0, self.bar_peaks[i] - height * 0.06)  # Faster decay
        else:
            # When no data yet, show a gentle "waiting" animation
            import time
            wait_time = time.time()
            for i in range(num_bars):
                # Gentle wave animation while waiting for audio data
                wave = (math.sin(wait_time * 2 + i * 0.2) + 1) * 0.1  # Small gentle wave
                target_level = wave * height * 0.3  # 30% max height
                self.bar_levels[i] = self.bar_levels[i] * 0.9 + target_level * 0.1  # Very smooth transition
                
                # Gentle peak effect
                if self.bar_levels[i] > self.bar_peaks[i]:
                    self.bar_peaks[i] = self.bar_levels[i]
                else:
                    self.bar_peaks[i] = max(0, self.bar_peaks[i] - height * 0.01)  # Very slow decay
        
        # Update existing canvas items instead of recreating them
        for i in range(min(num_bars, len(self.viz_bars), len(self.viz_peaks))):
            # Calculate positions
            x1 = i * (bar_width + bar_spacing) + bar_spacing
            x2 = x1 + bar_width
            
            # Update main bar
            bar_height = int(self.bar_levels[i])
            if bar_height > 0:
                # Update bar coordinates and color
                self.visualization_canvas.coords(
                    self.viz_bars[i],
                    x1, height - bar_height, x2, height
                )
                # Simple green color (no gradient for performance)
                intensity = min(1.0, bar_height / (height * 0.8))
                green_val = int(100 + 155 * intensity)  # Range from dark to bright green
                color = f"#00{green_val:02x}00"
                self.visualization_canvas.itemconfig(self.viz_bars[i], fill=color)
            else:
                # Hide bar if no height
                self.visualization_canvas.coords(
                    self.viz_bars[i],
                    x1, height, x2, height
                )
                self.visualization_canvas.itemconfig(self.viz_bars[i], fill="#003300")
            
            # Update peak indicator
            if self.bar_peaks[i] > 2:
                peak_y = height - int(self.bar_peaks[i])
                self.visualization_canvas.coords(
                    self.viz_peaks[i],
                    x1, peak_y, x2, peak_y + 1
                )
                self.visualization_canvas.itemconfig(self.viz_peaks[i], fill="#ffff00")
            else:
                # Hide peak if too small
                self.visualization_canvas.coords(
                    self.viz_peaks[i],
                    x1, height, x2, height
                )
                self.visualization_canvas.itemconfig(self.viz_peaks[i], fill="#000000")
        
        # Update at reasonable speed for performance (reduced from 30 to 20 FPS)
        if self.visualization_running:
            self.root.after(50, self.animate_visualization)  # 20 FPS for better performance
    
    def toggle_mute(self):
        if self.is_muted:
            try:
                if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                    self.player.volume = int(self.volume * 100)
                else:
                    import pygame.mixer
                    pygame.mixer.music.set_volume(self.volume)
            except:
                pass
            self.mute_btn.config(text="🔊")
            self.is_muted = False
        else:
            try:
                if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                    self.player.volume = 0
                else:
                    import pygame.mixer
                    pygame.mixer.music.set_volume(0)
            except:
                pass
            self.mute_btn.config(text="🔇")
            self.is_muted = True
            
    def set_volume(self, value):
        self.volume = float(value) / 100
        self.volume_label.config(text=f"{int(float(value))}%")
        # Set volume if music is playing
        if self.is_playing or self.is_paused:
            if not self.is_muted:
                try:
                    if hasattr(self, 'player') and not getattr(self, 'use_pygame_fallback', False):
                        self.player.volume = int(float(value))
                    else:
                        import pygame.mixer
                        pygame.mixer.music.set_volume(self.volume)
                except:
                    pass
            
    def toggle_lyrics(self):
        pass
        
    def toggle_playlist(self):
        pass
    
    def show_lyrics_context_menu(self, event):
        """Show context menu for lyrics area."""
        # Only show context menu if lyrics are loaded
        if not self.current_lyrics_artist or not self.current_lyrics_title:
            return
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0, bg='#21262d', fg='#f0f6fc',
                             activebackground='#58a6ff', activeforeground='white',
                             font=('Segoe UI', 10))
        
        # Add edit lyrics option
        context_menu.add_command(label="✏️ Edit Lyrics", command=self.edit_current_lyrics)
        
        # Add separator
        context_menu.add_separator()
        
        # Add copy lyrics option
        context_menu.add_command(label="📋 Copy Lyrics", command=self.copy_current_lyrics)
        
        # Show the menu at cursor position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def copy_current_lyrics(self):
        """Copy current lyrics to clipboard."""
        if self.current_lyrics_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_lyrics_content)
            # Show brief feedback
            if hasattr(self, 'lyrics_status_label'):
                self.lyrics_status_label.config(text="Copied to clipboard!")
                self.root.after(2000, lambda: self.lyrics_status_label.config(text=""))
        
    def maintain_peach_scrollbars(self):
        """Maintain peach theme scrollbar styling if peach theme is active"""
        if hasattr(self, 'current_theme') and self.current_theme == 'peach' and PEACH_THEME_AVAILABLE:
            theme = PEACH_THEME
            style = ttk.Style()
            
            # Re-apply peach theme to scrollbar with comprehensive configuration
            scrollbar_configs = {
                'TScrollbar': {
                    'background': theme['scrollbar_thumb'],
                    'troughcolor': theme['scrollbar_bg'],
                    'bordercolor': theme['scrollbar_bg'],
                    'arrowcolor': theme['text_secondary'],
                    'lightcolor': theme['primary_light'],
                    'darkcolor': theme['primary_dark'],
                    'relief': 'raised'
                },
                'Vertical.TScrollbar': {
                    'background': theme['scrollbar_thumb'],
                    'troughcolor': theme['scrollbar_bg'],
                    'bordercolor': theme['scrollbar_bg'],
                    'arrowcolor': theme['text_secondary'],
                    'lightcolor': theme['primary_light'],
                    'darkcolor': theme['primary_dark'],
                    'relief': 'raised'
                },
                'Horizontal.TScrollbar': {
                    'background': theme['scrollbar_thumb'],
                    'troughcolor': theme['scrollbar_bg'],
                    'bordercolor': theme['scrollbar_bg'],
                    'arrowcolor': theme['text_secondary'],
                    'lightcolor': theme['primary_light'],
                    'darkcolor': theme['primary_dark'],
                    'relief': 'raised'
                }
            }
            
            # Apply configurations
            for scrollbar_type, config in scrollbar_configs.items():
                style.configure(scrollbar_type, **config)
                # Configure hover states
                style.map(scrollbar_type, 
                    background=[
                        ('active', theme['scrollbar_thumb']),
                        ('!active', theme['scrollbar_thumb']),
                        ('pressed', theme['primary_dark']),
                        ('hover', theme['scrollbar_hover'])
                    ],
                    arrowcolor=[
                        ('active', theme['text_secondary']),
                        ('!active', theme['text_secondary']),
                        ('pressed', theme['text_primary']),
                        ('hover', theme['text_primary'])
                    ]
                )

    def update_all_edit_lyrics_dialogs_theme(self):
        """Update theme for all open Edit Lyrics dialogs"""
        try:
            # Find all Toplevel windows with the Edit Lyrics dialog name
            for widget in self.root.winfo_children():
                if widget.winfo_class() == 'Toplevel':
                    widget_name = getattr(widget, '_name', '')
                    if 'window_edit_lyrics' in widget_name:
                        if hasattr(self, 'current_theme') and self.current_theme == 'peach':
                            self.apply_peach_edit_lyrics_dialog(widget)
                        else:
                            self.restore_dark_edit_lyrics_dialog(widget)
        except Exception as e:
            print(f"Error updating Edit Lyrics dialogs theme: {e}")
    
    def apply_peach_edit_lyrics_dialog(self, dialog):
        """Apply peach theme to Edit Lyrics dialog"""
        if not PEACH_THEME_AVAILABLE:
            return
        
        theme = PEACH_THEME
        try:
            # Apply peach theme to dialog background
            dialog.configure(bg='#FFE0CC')  # Light peach background
            
            # Apply peach theme to all widgets in the dialog
            self.apply_peach_edit_lyrics_children(dialog, theme)
            
        except Exception as e:
            print(f"Error applying peach theme to Edit Lyrics dialog: {e}")
    
    def apply_peach_edit_lyrics_children(self, parent, theme):
        """Apply peach theme to all children in Edit Lyrics dialog"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Dialog background
                if widget_class == 'Toplevel':
                    widget.configure(bg='#FFE0CC')  # Light peach background
                
                # Labels
                elif widget_class == 'Label':
                    if widget_name in ['edit_title_label', 'edit_file_info_label', 'edit_instructions_label']:
                        widget.configure(bg='#FFE0CC', fg=theme['text_primary'] if 'title' in widget_name else theme['text_secondary'])
                    else:
                        widget.configure(bg='#FFE0CC', fg=theme['text_secondary'])
                
                # Frames
                elif widget_class == 'Frame':
                    if widget_name == 'frame_edit_lyrics_text':  # Text frame
                        widget.configure(bg=theme['input_border'])
                    elif widget_name == 'frame_edit_lyrics_buttons':  # Button frame
                        widget.configure(bg='#FFE0CC')  # Light peach background
                    else:  # Other frames
                        widget.configure(bg='#FFE0CC')  # Light peach background
                    # Recursively apply to children
                    self.apply_peach_edit_lyrics_children(widget, theme)
                
                # Text widget
                elif widget_class == 'Text':
                    widget.configure(
                        bg='white',  # White background
                        fg=theme['input_fg'], 
                        insertbackground=theme['text_primary'],
                        selectbackground=theme['primary'],
                        selectforeground=theme['text_on_primary']
                    )
                
                # Buttons
                elif widget_class == 'Button':
                    if 'save' in widget_name or 'cancel' in widget_name:
                        widget.configure(
                            bg='#FFB366',  # Peach button color
                            fg=theme['text_on_primary'],
                            activebackground=theme['primary_dark'],
                            activeforeground=theme['text_on_primary']
                        )
                
                # Recursively apply to other children
                else:
                    self.apply_peach_edit_lyrics_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach theme to Edit Lyrics dialog children: {e}")
    
    def restore_dark_edit_lyrics_dialog(self, dialog):
        """Restore dark theme to Edit Lyrics dialog"""
        try:
            # Restore dark theme to dialog background
            dialog.configure(bg='#0d1117')
            
            # Restore dark theme to all widgets in the dialog
            self.restore_dark_edit_lyrics_children(dialog)
            
        except Exception as e:
            print(f"Error restoring dark theme to Edit Lyrics dialog: {e}")
    
    def restore_dark_edit_lyrics_children(self, parent):
        """Restore dark theme to all children in Edit Lyrics dialog"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Dialog background
                if widget_class == 'Toplevel':
                    widget.configure(bg='#0d1117')
                
                # Labels
                elif widget_class == 'Label':
                    if 'title' in widget_name:
                        widget.configure(bg='#0d1117', fg='#f0f6fc')
                    else:
                        widget.configure(bg='#0d1117', fg='#8b949e')
                
                # Frames
                elif widget_class == 'Frame':
                    if 'text' in widget_name:  # Text frame
                        widget.configure(bg='#21262d')
                    else:  # Button frame
                        widget.configure(bg='#0d1117')
                    # Recursively apply to children
                    self.restore_dark_edit_lyrics_children(widget)
                
                # Text widget
                elif widget_class == 'Text':
                    widget.configure(
                        bg='#0d1117', 
                        fg='#f0f6fc', 
                        insertbackground='#4a9eff',
                        selectbackground='#1f6feb',
                        selectforeground='#ffffff'
                    )
                
                # Buttons
                elif widget_class == 'Button':
                    if 'save' in widget_name:
                        widget.configure(
                            bg='#238636',  # Green
                            fg='white',
                            activebackground='#2ea043',
                            activeforeground='white'
                        )
                    elif 'cancel' in widget_name:
                        widget.configure(
                            bg='#da3633',  # Red
                            fg='white',
                            activebackground='#b91c1c',
                            activeforeground='white'
                        )
                
                # Recursively apply to other children
                else:
                    self.restore_dark_edit_lyrics_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark theme to Edit Lyrics dialog children: {e}")
    
    def edit_current_lyrics(self):
        """Open a dialog to edit the current lyrics or add new lyrics."""
        # Try to get current song info from multiple sources
        artist = ""
        title = ""
        
        # Method 1: Use tracked lyrics info if available
        if self.current_lyrics_artist and self.current_lyrics_title:
            artist = self.current_lyrics_artist
            title = self.current_lyrics_title
        
        # Method 2: Use current_song if available
        elif hasattr(self, 'current_song') and self.current_song:
            metadata = self.get_song_metadata(self.current_song)
            if metadata and 'artist' in metadata and 'title' in metadata:
                artist = metadata['artist']
                title = metadata['title']
        
        # Method 3: Use currently selected song in playlist
        if not artist or not title:
            selection = self.playlist_treeview.selection()
            if selection:
                item = selection[0]
                # Get the original index from tags
                tags = self.playlist_treeview.item(item, 'tags')
                song_index = -1
                for tag in tags:
                    if tag.startswith('index_'):
                        try:
                            song_index = int(tag.split('_')[1])
                            break
                        except (ValueError, IndexError):
                            continue
                
                if song_index >= 0 and song_index < len(self.playlist):
                    song_path = self.playlist[song_index]
                    metadata = self.get_song_metadata(song_path)
                    if metadata and 'artist' in metadata and 'title' in metadata:
                        artist = metadata['artist']
                        title = metadata['title']
        
        # If still no song info, show error
        if not artist or not title:
            messagebox.showinfo("No Song Info", "No song information available for adding lyrics.\n\nPlease select a song in the playlist first.")
            return
        
        # Set the tracking variables for future use
        self.current_lyrics_artist = artist
        self.current_lyrics_title = title
        
        # Check if song is playing and suggest pausing
        if self.is_playing and not self.is_paused:
            result = messagebox.askyesno("Song Playing", 
                "The song is currently playing. It's recommended to pause before editing lyrics.\n\nPause the song now?")
            if result:
                self.pause_song()
        
        # Determine if we're editing existing lyrics or adding new ones
        is_editing = bool(self.current_lyrics_content)
        
        # Preserve the sync state - if we lose it, detect from content
        original_sync_state = self.current_lyrics_is_synced
        
        # If editing existing lyrics, check if it's LRC format by examining content
        if is_editing and self.current_lyrics_content:
            # Check if content contains LRC timestamps (multiple possible patterns)
            import re
            # Try multiple LRC timestamp patterns:
            # [mm:ss.xx] - standard LRC format
            # [mm:ss] - simplified LRC format
            # [mm:ss:xxx] - millisecond format
            lrc_patterns = [
                re.compile(r'\[\d{2}:\d{2}\.\d{2}\]'),  # [00:12.34]
                re.compile(r'\[\d{2}:\d{2}\]'),        # [00:12]
                re.compile(r'\[\d{2}:\d{2}:\d{2}\]'),  # [00:12:34]
                re.compile(r'\[\d{1,2}:\d{2}\.\d{2}\]'), # [0:12.34] or [12:34.56]
                re.compile(r'\[\d{1,2}:\d{2}\]'),       # [0:12] or [12:34]
            ]
            
            # Check if any pattern matches
            detected_sync = any(pattern.search(self.current_lyrics_content) for pattern in lrc_patterns)
            
            # Use detected sync state, but prefer original if it was True
            self.current_lyrics_is_synced = original_sync_state or detected_sync
            
            # Debug output
            if self.current_lyrics_is_synced:
                pass
            else:
                pass
        
        dialog_title = f"Edit Lyrics: {self.current_lyrics_artist} - {self.current_lyrics_title}" if is_editing else f"Add Lyrics: {self.current_lyrics_artist} - {self.current_lyrics_title}"
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root, name='window_edit_lyrics')
        dialog.title(dialog_title)
        dialog.geometry("600x500")
        dialog.configure(bg='#0d1117')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Maintain peach theme scrollbar styling if needed
        self.maintain_peach_scrollbars()
        
        # Bind UI debugging events to this window
        self.bind_window_events(dialog)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Title
        title_text = f"Editing: {self.current_lyrics_artist} - {self.current_lyrics_title}" if is_editing else f"Adding lyrics for: {self.current_lyrics_artist} - {self.current_lyrics_title}"
        title_label = tk.Label(
            dialog,
            text=title_text,
            font=('Segoe UI', 12, 'bold'),
            bg='#0d1117',
            fg='#f0f6fc',
            name='edit_title_label'
        )
        title_label.pack(pady=(20, 10))
        
        # File type info (for editing) or instructions (for adding)
        if is_editing:
            file_type = "LRC (Synced)" if self.current_lyrics_is_synced else "TXT (Plain Text)"
            file_ext = ".lrc" if self.current_lyrics_is_synced else ".txt"
            filename = f"{self.current_lyrics_artist} - {self.current_lyrics_title}{file_ext}"
            
            info_label = tk.Label(
                dialog,
                text=f"File Type: {file_type}\nFilename: {filename}",
                font=('Segoe UI', 10),
                bg='#0d1117',
                fg='#8b949e',
                name='edit_file_info_label'
            )
            info_label.pack(pady=(0, 10))
        else:
            info_label = tk.Label(
                dialog,
                text="Paste the lyrics you copied from Genius, AZLyrics, or type them manually.\n\nLyrics will be saved as plain text (.txt) file.",
                font=('Segoe UI', 10),
                bg='#0d1117',
                fg='#8b949e',
                justify=tk.LEFT,
                name='edit_instructions_label'
            )
            info_label.pack(pady=(0, 10))
        
        # Lyrics text area
        text_frame = tk.Frame(dialog, bg='#21262d', relief=tk.SUNKEN, bd=2, name='frame_edit_lyrics_text')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        lyrics_text = tk.Text(
            text_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Consolas', 11),  # Monospace font for better editing
            wrap=tk.WORD,
            padx=10,
            pady=10,
            insertbackground='#4a9eff',  # Bright blue insert cursor
            insertwidth=2,  # Make cursor more visible
            selectbackground='#1f6feb',
            selectforeground='#ffffff',
            name='text_edit_lyrics'
        )
        lyrics_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(lyrics_text, orient=tk.VERTICAL, command=lyrics_text.yview, name='scrollbar_edit_lyrics')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        lyrics_text.config(yscrollcommand=scrollbar.set)
        
        # Load existing lyrics or set placeholder
        if is_editing:
            lyrics_text.insert("1.0", self.current_lyrics_content)
        else:
            placeholder_text = f"[Verse 1]\nYour lyrics here...\n\n[Chorus]\nMore lyrics here...\n\n{self.current_lyrics_artist} - {self.current_lyrics_title}"
            lyrics_text.insert("1.0", placeholder_text)
            # Select all text for easy replacement
            lyrics_text.tag_add(tk.SEL, "1.0", tk.END)
        
        lyrics_text.focus_set()
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#0d1117', name='frame_edit_lyrics_buttons')
        button_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        def save_edited_lyrics():
            edited_lyrics = lyrics_text.get("1.0", tk.END).strip()
            if edited_lyrics:
                # Check if it's synced lyrics (has timestamps) or plain text
                is_synced = self.is_synced_lyrics(edited_lyrics)
                
                # Show save dialog
                file_ext = ".lrc" if is_synced else ".txt"
                default_filename = f"{self.current_lyrics_artist} - {self.current_lyrics_title}{file_ext}"
                
                # Determine default folder - use song's folder
                if hasattr(self, 'current_song') and self.current_song:
                    song_folder = Path(self.current_song).parent
                    default_folder = song_folder
                else:
                    # No current song, use desktop as fallback
                    default_folder = Path.home() / "Desktop"
                
                default_folder.mkdir(parents=True, exist_ok=True)
                
                # Show save dialog
                save_path = filedialog.asksaveasfilename(
                    title="Save Lyrics",
                    initialfile=default_filename,
                    initialdir=str(default_folder),
                    filetypes=[
                        (f"Lyrics Files (*{file_ext})", f"*{file_ext}"),
                        ("All Files", "*.*")
                    ]
                )
                
                if save_path:  # User didn't cancel
                    # Save to selected location
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(edited_lyrics)
                    
                    # Update tracking variables
                    self.current_lyrics_content = edited_lyrics
                    self.current_lyrics_is_synced = is_synced
                    
                    # Update the display immediately
                    if is_synced:
                        self.display_synced_lyrics(edited_lyrics, "Local LRC", self.current_lyrics_artist, self.current_lyrics_title)
                    else:
                        self.update_lyrics_display(edited_lyrics, self.current_lyrics_artist, self.current_lyrics_title)
                    
                    # Update status immediately
                    source_type = "Local LRC" if is_synced else "Local TXT"
                    self.update_lyrics_status(f"-- Loaded ({source_type})")
                    
                    # Add star to the song immediately
                    self.update_star_for_song(self.current_lyrics_artist, self.current_lyrics_title, has_lyrics=True)
                    self.update_star_cache(self.current_lyrics_artist, self.current_lyrics_title, has_lyrics=True)
                    
                    # Enable edit button
                    if hasattr(self, 'edit_lyrics_btn'):
                        self.edit_lyrics_btn.config(state=tk.NORMAL)
                    
                    messagebox.showinfo("Success", f"Lyrics saved successfully!\n\nLocation: {save_path}")
                    dialog.destroy()
                    # Maintain peach scrollbars when dialog closes
                    self.root.after(50, self.maintain_peach_scrollbars)
            else:
                messagebox.showwarning("Empty Lyrics", "Lyrics cannot be empty!")
        
        def cancel_edit():
            dialog.destroy()
            # Maintain peach scrollbars when dialog closes
            self.root.after(50, self.maintain_peach_scrollbars)
        
        # Save button
        save_btn = tk.Button(
            button_frame,
            text="💾 Save Lyrics",
            command=save_edited_lyrics,
            bg='#238636',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2',
            relief=tk.RAISED,
            padx=20,
            pady=8,
            name='btn_save_edit_lyrics'
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=cancel_edit,
            bg='#da3633',
            fg='white',
            font=('Segoe UI', 10),
            cursor='hand2',
            relief=tk.RAISED,
            padx=20,
            pady=8,
            name='btn_cancel_edit_lyrics'
        )
        cancel_btn.pack(side=tk.RIGHT)
        
        # Bind Escape key to cancel
        dialog.bind('<Escape>', lambda e: cancel_edit())
        
        # Set focus to text area
        lyrics_text.focus_set()
        if not is_editing:
            lyrics_text.mark_set(tk.INSERT, "1.0")
            lyrics_text.see(tk.INSERT)
        
        # Apply appropriate theme to the dialog immediately after all widgets are created
        if hasattr(self, 'current_theme') and self.current_theme == 'peach':
            self.apply_peach_edit_lyrics_dialog(dialog)
            # Maintain peach scrollbars after theme is applied
            self.maintain_peach_scrollbars()
        
    def show_about(self):
        messagebox.showinfo("About TinyTunez", " TinyTunez Music Player\n\nA modern music player with custom button icons\nFeaturing your custom assets\n\nVersion 3.0 Assets")
    
    def apply_peach_theme(self):
        """Apply peach theme to treeview and scrollbar only"""
        if not PEACH_THEME_AVAILABLE:
            print("Peach theme not available, falling back to dark theme")
            self.apply_dark_theme()
            return
        
        try:
            theme = PEACH_THEME
            self.current_theme = 'peach'
            
            # ONLY apply ttk styles for treeview and scrollbar
            if hasattr(self, 'playlist_treeview'):
                style = ttk.Style()
                
                # Apply peach theme to treeview
                style.configure(
                    'Custom.Treeview',
                    background=theme['treeview_bg'],
                    foreground=theme['treeview_fg'],
                    fieldbackground=theme['treeview_bg'],
                    selectbackground=theme['scrollbar_thumb'],
                    selectforeground=theme['text_on_primary'],
                    borderwidth=0,
                    font=('Segoe UI', 10)
                )
                
                # Apply peach theme to treeview heading
                style.configure(
                    'Custom.Treeview.Heading',
                    background=theme['scrollbar_thumb'],
                    foreground=theme['text_primary'],
                    fieldbackground=theme['scrollbar_thumb'],
                    relief='raised',
                    font=('Segoe UI', 10, 'bold')
                )
                
                # Apply peach theme to scrollbar
                style.configure(
                    'TScrollbar',
                    background=theme['scrollbar_thumb'],
                    troughcolor=theme['scrollbar_bg'],
                    bordercolor=theme['scrollbar_bg'],
                    arrowcolor=theme['text_secondary'],
                    lightcolor=theme['primary_light'],
                    darkcolor=theme['primary_dark'],
                    relief='raised'
                )
                
                style.configure(
                    'Vertical.TScrollbar',
                    background=theme['scrollbar_thumb'],
                    troughcolor=theme['scrollbar_bg'],
                    bordercolor=theme['scrollbar_bg'],
                    arrowcolor=theme['text_secondary'],
                    lightcolor=theme['primary_light'],
                    darkcolor=theme['primary_dark'],
                    relief='raised'
                )
                
                # Configure scrollbar hover states
                style.map('TScrollbar', 
                    background=[
                        ('active', theme['scrollbar_thumb']),
                        ('!active', theme['scrollbar_thumb']),
                        ('pressed', theme['primary_dark']),
                        ('hover', theme['scrollbar_hover'])
                    ],
                    arrowcolor=[
                        ('active', theme['text_secondary']),
                        ('!active', theme['text_secondary']),
                        ('pressed', theme['text_primary']),
                        ('hover', theme['text_primary'])
                    ]
                )
                
                style.map('Vertical.TScrollbar', 
                    background=[
                        ('active', theme['scrollbar_thumb']),
                        ('!active', theme['scrollbar_thumb']),
                        ('pressed', theme['primary_dark']),
                        ('hover', theme['scrollbar_hover'])
                    ],
                    arrowcolor=[
                        ('active', theme['text_secondary']),
                        ('!active', theme['text_secondary']),
                        ('pressed', theme['text_primary']),
                        ('hover', theme['text_primary'])
                    ]
                )
                
                style.map(
                    'Custom.Treeview',
                    background=[('selected', theme['scrollbar_thumb'])],
                    foreground=[('selected', theme['text_on_primary'])]
                )
                
                self.playlist_treeview.configure(style='Custom.Treeview')
                
                # Apply peach theme to header frame and its contents
                self.apply_peach_header_frame(theme)
                
                self.apply_peach_playlist_header(theme)
                
                self.apply_peach_player_controls(theme)
                
                # Apply peach theme to all buttons (except ImageButtons)
                self.apply_peach_buttons(theme)
                
                # Apply peach theme to main frame specifically first
                self.apply_peach_main_frame(theme)
                
                # Apply peach theme to root window background
                self.root.configure(bg='#D4B5A0')  # Same color as main frame
                
                # Apply peach theme to volume slider specifically
                self.apply_peach_volume_slider(theme)
                
                # Apply peach theme to playlist frame specifically
                self.apply_peach_playlist_frame(theme)
                
                # Apply peach theme to song info frame specifically
                self.apply_peach_song_info_frame(theme)
                
                # Apply peach theme to lyrics frame specifically
                self.apply_peach_lyrics_frame(theme)
                
                # Apply peach theme to search entry directly
                if hasattr(self, 'search_entry'):
                    self.search_entry.configure(bg='#FFFFFF', fg=theme['input_fg'], insertbackground=theme['text_primary'])
                    self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0)  # Remove padding
                
                # Also update the search entry frame padding
                search_entry_frame = self.find_widget_by_name(self.root, 'search_entry_frame')
                if search_entry_frame:
                    search_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0, pady=0)  # Remove frame padding
            
            # Update all open Edit Lyrics dialogs
            self.update_all_edit_lyrics_dialogs_theme()
            
            # Update all open Select Music Folders dialogs
            self.update_all_folder_selection_dialogs_theme()
            
            # Update all open Settings dialogs
            self.update_all_settings_dialogs_theme()
            
            # Save theme preference to settings
            self.settings['theme'] = 'peach'
            self.save_settings()
            
        except Exception as e:
            print(f"Error applying peach theme: {e}")
            self.apply_dark_theme()  # Fallback
    
    def apply_peach_playlist_header(self, theme):
        """Apply peach theme to header frame and its contents
            self.apply_peach_header_frame(theme)
            
            # Apply dark theme to header frame and its contents
            self.restore_dark_header_frame()
            
            # Apply dark theme to playlist header and its contents"""
        try:
            # Find the playlist header frame
            playlist_header = None
            for widget in self.root.winfo_children():
                result = self.find_widget_by_name(widget, 'playlist_header_frame')
                if result:
                    playlist_header = result
                    break
            
            if not playlist_header:
                print("Playlist header frame not found")
                return
            
            # Apply peach theme to header frame
            playlist_header.configure(bg=theme['bg_header'])
            
            # Apply to all children in the header
            self.apply_peach_header_children(playlist_header, theme)
            
        except Exception as e:
            print(f"Error applying peach playlist header: {e}")
    
    def apply_peach_player_controls(self, theme):
        """Apply peach theme to player controls frame and all contents"""
        try:
            # Find the player controls frame
            player_controls = None
            for widget in self.root.winfo_children():
                result = self.find_widget_by_name(widget, 'player_controls_frame')
                if result:
                    player_controls = result
                    break
            
            if not player_controls:
                print("Player controls frame not found")
                return
            
            # Apply peach theme to player controls frame
            player_controls.configure(bg=theme['bg_header'])
            
            # Apply to all children in the player controls
            self.apply_peach_player_controls_children(player_controls, theme)
            
        except Exception as e:
            print(f"Error applying peach player controls: {e}")
    
    def apply_peach_player_controls_children(self, parent, theme):
        """Apply peach theme to all children in player controls"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Individual ImageButton frames (prev_btn_frame, play_btn_frame, etc.)
                if widget_name in ['prev_btn_frame', 'play_btn_frame', 'pause_btn_frame', 'stop_btn_frame', 'next_btn_frame', 'shuffle_btn_frame']:
                    widget.configure(bg=theme['bg_header'])  # #FFE0CC for individual button frames
                    self.apply_peach_player_controls_children(widget, theme)  # Recursively apply to children
                
                # Controls frame and volume frame
                elif widget_name in ['controls_frame', 'volume_frame']:
                    widget.configure(bg=theme['bg_header'])
                    self.apply_peach_player_controls_children(widget, theme)  # Recursively apply to children
                
                # ImageButton - apply peach background with no pressed state
                elif widget_class == 'Button' and hasattr(widget, 'is_image_button'):
                    widget.configure(
                        bg=theme['bg_header'],  # #FFE0CC for ImageButtons
                        activebackground=theme['bg_header'],  # Same color when pressed
                        relief=tk.FLAT  # Keep flat appearance
                    )
                
                # Labels - apply readable text color against peach background
                elif widget_class == 'Label':
                    widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])  # #2D1810 text on #FFE0CC background
                
                # Recursively apply to other children
                else:
                    self.apply_peach_player_controls_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach player controls children: {e}")
    
    def find_widget_by_name(self, parent, name):
        """Find widget by name recursively"""
        try:
            if hasattr(parent, '_name') and parent._name == name:
                return parent
            
            for child in parent.winfo_children():
                result = self.find_widget_by_name(child, name)
                if result:
                    return result
        except:
            pass
        return None
    
    def apply_peach_header_frame(self, theme):
        """Apply peach theme to header frame and its contents"""
        try:
            header_frame = self.find_widget_by_name(self.root, 'header_frame')
            if header_frame:
                header_frame.configure(bg=theme['bg_header'])  # #FFE0CC
                
                # Apply peach theme to all children in the header frame
                self.apply_peach_header_children(header_frame, theme)
        except Exception as e:
            print(f"Error applying peach header frame: {e}")
    
    def apply_peach_header_children(self, parent, theme):
        """Apply peach theme to all children in header frame"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Frame children - apply peach background
                if widget_class == 'Frame':
                    widget.configure(bg=theme['bg_header'])
                    self.apply_peach_header_children(widget, theme)  # Recursively apply to children
                
                # Labels - apply peach styling
                elif widget_class == 'Label':
                    if widget_name == 'app_title_label':
                        widget.configure(bg=theme['bg_header'], fg='#FFB366')  # Peach accent color
                    elif widget_name == 'app_subtitle_label':
                        widget.configure(bg=theme['bg_header'], fg='#2D1810')  # Dark text
                    else:
                        # General labels
                        widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])
                
                # ImageButton - apply peach background
                elif widget_class == 'Button' and hasattr(widget, 'is_image_button'):
                    widget.configure(bg=theme['bg_header'])  # #FFE0CC for ImageButton
                
                # Recursively apply to other children
                else:
                    self.apply_peach_header_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach header children: {e}")
    
    def apply_peach_playlist_header_children(self, parent, theme):
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Header label
                if widget_name == 'playlist_header_label':
                    widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])
                
                # Search frame
                elif widget_name == 'search_frame':
                    widget.configure(bg=theme['bg_header'])
                    self.apply_peach_header_children(widget, theme)  # Recursively apply to children
                
                # Playlist buttons frame (Edit, Remove, Clear buttons)
                elif widget_name == 'playlist_buttons_frame':
                    widget.configure(bg=theme['bg_header'])
                    # Buttons inside will be styled by the general button styling
                
                # Search entry frame
                elif widget_name == 'search_entry_frame':
                    widget.configure(bg='#FFFFFF', highlightbackground=theme['border'], highlightcolor=theme['focused'])
                
                # Search entry
                elif widget_name == 'search_entry':
                    widget.configure(bg='#FFFFFF', fg=theme['input_fg'], insertbackground=theme['text_primary'])
                
                # Clear button canvas
                elif widget_name == 'clear_search_canvas':
                    widget.configure(bg='#FFFFFF')
                    # Update the circular background and X symbol colors
                    widget.delete("all")
                    widget.create_oval(2, 2, 14, 14, fill=theme['border'], outline=theme['border'])
                    widget.create_text(8, 8, text="✕", font=('Segoe UI', 8, 'bold'), fill=theme['text_secondary'])
                
                # Recursively apply to other children
                else:
                    self.apply_peach_header_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach header children: {e}")
    
    def apply_peach_volume_slider(self, theme):
        """Apply peach theme to volume slider specifically"""
        try:
            if hasattr(self, 'volume_slider'):
                self.volume_slider.configure(
                    bg=theme['scale_bg'],
                    troughcolor=theme['scale_trough'],
                    activebackground=theme['scale_active'],
                    fg=theme['scale_fg'],
                    highlightbackground=theme['scale_border'],  # Only this border
                    highlightthickness=1,                        # Single border
                    borderwidth=0                               # No additional border
                )
            else:
                pass
        except Exception as e:
            print(f"Error applying peach volume slider: {e}")
    
    def apply_peach_lyrics_frame(self, theme):
        """Apply peach theme to lyrics frame and all its contents"""
        try:
            lyrics_frame = self.find_widget_by_name(self.root, 'lyrics_frame')
            if lyrics_frame:
                lyrics_frame.configure(bg=theme['bg_header'])  # #FFE0CC
                
                # Apply peach theme to all children in the lyrics frame
                self.apply_peach_lyrics_children(lyrics_frame, theme)
        except Exception as e:
            print(f"Error applying peach lyrics frame: {e}")
    
    def apply_peach_lyrics_children(self, parent, theme):
        """Apply peach theme to all children in lyrics frame"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Lyrics header frame
                if widget_name == 'lyrics_header_frame':
                    widget.configure(bg=theme['bg_header'])  # #FFE0CC
                    self.apply_peach_lyrics_children(widget, theme)  # Recursively apply to children
                
                # Lyrics header label
                elif widget_name == 'lyrics_header_label':
                    widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])  # #FFE0CC, #2D1810
                
                # Lyrics status label
                elif widget_name == 'lyrics_status_label':
                    widget.configure(bg=theme['bg_header'], fg=theme['text_secondary'])  # #FFE0CC, #8B6F47
                
                # Lyrics text frame
                elif widget_name == 'lyrics_text_frame':
                    widget.configure(bg='#FFFFFF')  # White background for text area
                    self.apply_peach_lyrics_children(widget, theme)  # Recursively apply to children
                
                # Lyrics text widget
                elif widget_name == 'lyrics_text':
                    widget.configure(
                        bg='#FFFFFF',  # White background
                        fg=theme['text_primary'],  # #2D1810
                        insertbackground=theme['text_primary'],  # #2D1810
                        selectbackground=theme['scrollbar_thumb'],  # #E8A87C
                        selectforeground=theme['text_on_primary']  # #FFFFFF
                    )
                
                # Edit lyrics button
                elif widget_name == 'edit_lyrics_btn':
                    widget.configure(
                        bg=theme['primary'],  # #FF9A76
                        fg=theme['text_on_primary'],  # #FFFFFF
                        activebackground=theme['primary_dark'],  # #E8A87C
                        activeforeground=theme['text_on_primary']
                    )
                
                # Open folder button
                elif widget_name == 'open_lyrics_folder_btn':
                    widget.configure(
                        bg=theme['accent'],  # #4A9EFF
                        fg=theme['text_on_primary'],  # #FFFFFF
                        activebackground=theme['primary'],  # #FF9A76
                        activeforeground=theme['text_on_primary']
                    )
                
                # Frame children - apply peach background
                elif widget_class == 'Frame':
                    if widget_name.startswith('lyrics_'):
                        widget.configure(bg=theme['bg_header'])  # #FFE0CC
                        self.apply_peach_lyrics_children(widget, theme)  # Recursively apply to children
                
                # Recursively apply to other children
                else:
                    self.apply_peach_lyrics_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach lyrics children: {e}")
    
    def apply_peach_main_frame(self, theme):
        """Apply peach theme to main frame and all its contents"""
        try:
            main_frame = self.find_widget_by_name(self.root, 'main_frame')
            if main_frame:
                main_frame.configure(bg='#D4B5A0')  # Same color as search_entry border
                
                # Apply peach theme to all children in the main frame
                self.apply_peach_main_children(main_frame, theme)
        except Exception as e:
            print(f"Error applying peach main frame: {e}")
    
    def apply_peach_main_children(self, parent, theme):
        """Apply peach theme to all children in main frame"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Left panel - apply peach background
                if widget_name == 'left_panel':
                    self.apply_peach_main_children(widget, theme)  # Recursively apply to children
                
                # Skip specific frames that have their own styling
                elif widget_name in ['player_controls_frame', 'volume_frame', 'playlist_header_frame', 'song_info_frame']:
                    pass  # Don't apply peach background to these frames
                
                # Frame children - apply peach background only if not lyrics frames and not special frames
                elif widget_class == 'Frame':
                    if not widget_name.startswith('lyrics_') and widget_name not in ['player_controls_frame', 'volume_frame', 'playlist_header_frame', 'song_info_frame']:
                        widget.configure(bg='#D4B5A0')  # Same color as main frame
                        self.apply_peach_main_children(widget, theme)  # Recursively apply to children
                
                # Recursively apply to other children
                else:
                    self.apply_peach_main_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach main children: {e}")
    
    def apply_peach_playlist_frame(self, theme):
        """Apply peach theme to playlist frame specifically"""
        try:
            playlist_frame = self.find_widget_by_name(self.root, 'playlist_frame')
            if playlist_frame:
                playlist_frame.configure(bg=theme['bg_header'])  # #FFE0CC
            else:
                pass
        except Exception as e:
            print(f"Error applying peach playlist frame: {e}")
    
    def apply_peach_song_info_frame(self, theme):
        """Apply peach theme to song info frame and its contents"""
        try:
            song_info_frame = self.find_widget_by_name(self.root, 'song_info_frame')
            if song_info_frame:
                song_info_frame.configure(bg=theme['bg_header'])  # #FFE0CC
                
                # Apply peach theme to all children in the song info frame
                self.apply_peach_song_info_children(song_info_frame, theme)
                
                # Also try to find and style the visualization frames directly
                time_viz_frame = self.find_widget_by_name(self.root, 'time_viz_frame')
                if time_viz_frame:
                    time_viz_frame.configure(bg=theme['bg_header'])  # #FFE0CC
                    self.apply_peach_song_info_children(time_viz_frame, theme)
                
                viz_frame = self.find_widget_by_name(self.root, 'viz_frame')
                if viz_frame:
                    viz_frame.configure(bg=theme['input_border'])  # Same as search entry border (#D4B5A0)
                    self.apply_peach_song_info_children(viz_frame, theme)
                
                # Also try to find and style progress bar elements directly
                progress_bg = self.find_widget_by_name(self.root, 'progress_bg')
                if progress_bg:
                    progress_bg.configure(bg='#FFFFFF', highlightbackground=theme['input_border'], highlightthickness=1)  # White background with peach border
                
                progress_fill = self.find_widget_by_name(self.root, 'progress_fill')
                if progress_fill:
                    progress_fill.configure(bg='#FFB366')  # Peach accent color for fill
            else:
                pass
        except Exception as e:
            print(f"Error applying peach song info frame: {e}")
    
    def apply_peach_song_info_children(self, parent, theme):
        """Apply peach theme to all children in song info frame"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Frame children - apply peach background
                if widget_class == 'Frame':
                    # Special handling for info_border_frame
                    if widget_name == 'info_border_frame':
                        widget.configure(highlightbackground=theme['input_border'], highlightthickness=1)  # Peach border
                    else:
                        widget.configure(bg=theme['bg_header'])
                    self.apply_peach_song_info_children(widget, theme)  # Recursively apply to children
                
                # ModernFrame children - apply peach background
                elif widget_class == 'TFrame' or hasattr(widget, '__class__') and widget.__class__.__name__ == 'ModernFrame':
                    widget.configure(bg=theme['bg_header'])
                    self.apply_peach_song_info_children(widget, theme)  # Recursively apply to children
                
                # Labels - apply peach styling
                elif widget_class == 'Label':
                    # Special handling for specific labels
                    if widget_name in ['app_title_label', 'app_subtitle_label']:
                        widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])
                    elif widget_name in ['song_title_label', 'song_artist_label']:
                        widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])
                    elif widget_name in ['song_length_label', 'current_time_label']:
                        widget.configure(bg=theme['bg_header'], fg=theme['text_secondary'])
                    elif widget_name == 'album_art_label':
                        widget.configure(bg=theme['bg_header'], highlightbackground=theme['input_border'], highlightthickness=1)  # Peach border
                        # Adjust placement to show border (reduce from 60x60 to 58x58 and center)
                        widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=58, height=58)
                    else:
                        # General labels
                        widget.configure(bg=theme['bg_header'], fg=theme['text_primary'])
                
                # Canvas - keep visualization canvas black, no border
                elif widget_class == 'Canvas':
                    if widget_name == 'visualization_canvas':
                        widget.configure(
                            bg=theme['visualization_bg'],  # Always black
                            highlightthickness=0  # Remove border
                        )
                    else:
                        widget.configure(bg=theme['bg_primary'])
                
                # Visualization frame - apply search entry border color as background
                elif widget_name == 'viz_frame':
                    widget.configure(bg=theme['input_border'])  # Same as search entry border (#D4B5A0)
                    self.apply_peach_song_info_children(widget, theme)  # Recursively apply to children
                
                # Time/visualization frame - apply peach background
                elif widget_name == 'time_viz_frame':
                    widget.configure(bg=theme['bg_header'])  # #FFE0CC
                    self.apply_peach_song_info_children(widget, theme)  # Recursively apply to children
                
                # Recursively apply to other children
                else:
                    self.apply_peach_song_info_children(widget, theme)
                    
        except Exception as e:
            print(f"Error applying peach song info children: {e}")
    
    def apply_peach_buttons(self, theme):
        """Apply peach theme to all buttons (except ImageButtons)"""
        try:
            # Find all buttons recursively
            self.find_and_style_buttons(self.root, theme)
            
        except Exception as e:
            print(f"Error applying peach buttons: {e}")
    
    def find_and_style_buttons(self, parent, theme):
        """Recursively find and style all buttons"""
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                widget_name = getattr(widget, '_name', '')
                
                # Style regular buttons (not ImageButtons)
                if widget_class == 'Button' and not hasattr(widget, 'is_image_button'):
                    widget.configure(
                        bg=theme['primary'], 
                        fg=theme['text_on_primary'], 
                        relief=tk.RAISED,
                        activebackground=theme['pressed'],  # Pressed state color
                        activeforeground=theme['text_on_primary']  # Keep text color on press
                    )
                
                # Recursively check children
                self.find_and_style_buttons(widget, theme)
                
        except Exception as e:
            pass
    
    def apply_peach_widgets_recursive(self, parent):
        """Apply peach theme to all widgets recursively"""
        if not PEACH_THEME_AVAILABLE:
            return
            
        theme = PEACH_THEME
        
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                
                # Handle different widget types
                if widget_class == 'Frame':
                    try:
                        widget.configure(bg=theme['bg_primary'])
                    except tk.TclError:
                        pass  # Skip if this widget doesn't support bg
                
                elif widget_class == 'Label':
                    try:
                        parent_bg = widget.master.cget('bg') if hasattr(widget.master, 'cget') else theme['bg_primary']
                        widget.configure(bg=parent_bg, fg=theme['text_primary'])
                    except tk.TclError:
                        pass
                
                elif widget_class == 'Button':
                    try:
                        widget.configure(bg=theme['button_bg'], fg=theme['button_fg'])
                    except tk.TclError:
                        pass
                
                elif widget_class == 'Entry':
                    try:
                        widget.configure(bg=theme['input_bg'], fg=theme['input_fg'], insertbackground=theme['text_primary'])
                    except tk.TclError:
                        pass
                
                elif widget_class == 'Text':
                    try:
                        widget.configure(bg=theme['bg_primary'], fg=theme['text_primary'], insertbackground=theme['text_primary'])
                    except tk.TclError:
                        pass
                
                elif widget_class == 'Canvas':
                    try:
                        # Special handling for visualization canvas
                        if hasattr(self, 'visualization_canvas') and widget == self.visualization_canvas:
                            widget.configure(bg=theme['visualization_bg'])  # Always black
                        else:
                            widget.configure(bg=theme['bg_primary'])
                    except tk.TclError:
                        pass
                
                elif widget_class == 'Scale':
                    try:
                        widget.configure(
                            bg=theme['scale_bg'], 
                            troughcolor=theme['scale_trough'], 
                            activebackground=theme['scale_active'],
                            fg=theme['scale_fg'],
                            highlightbackground=theme['scale_border'],
                            highlightcolor=theme['scale_border']
                        )
                    except tk.TclError:
                        pass
                
                elif widget_class == 'Scrollbar':
                    try:
                        widget.configure(bg=theme['scrollbar_thumb'], troughcolor=theme['scrollbar_bg'], activebackground=theme['scrollbar_hover'])
                    except tk.TclError:
                        pass
                
                # Handle ttk widgets (these need different approach)
                elif widget_class.startswith('T'):
                    # ttk widgets - will be handled by ttk.Style
                    pass
                
                # Handle custom widgets
                elif hasattr(widget, '__class__'):
                    class_name = widget.__class__.__name__
                    
                    if class_name == 'ModernFrame':
                        widget.configure(bg=theme['bg_primary'])
                    elif class_name == 'ModernLabel':
                        parent_bg = widget.master.cget('bg') if hasattr(widget.master, 'cget') else theme['bg_primary']
                        widget.configure(bg=parent_bg, fg=theme['text_primary'])
                    elif class_name == 'ImageButton':
                        # ImageButton might need special handling
                        pass  # Keep as is for now
                
                # Recursively apply to children
                self.apply_peach_widgets_recursive(widget)
                
        except Exception as e:
            print(f"Error in peach theme recursive application: {e}")
    
    def restore_dark_header_frame(self):
        """Restore dark theme to header frame and its contents"""
        try:
            header_frame = self.find_widget_by_name(self.root, 'header_frame')
            if header_frame:
                header_frame.configure(bg='#0d1117')  # Original dark background from create_widgets
                
                # Restore dark theme to all children in the header frame
                self.restore_dark_header_children(header_frame)
            else:
                pass
        except Exception as e:
            print(f"Error restoring dark header frame: {e}")
    
    def restore_dark_header_children(self, parent):
        """Restore dark theme to all children in header frame"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Frame children - restore original dark background
                if widget_class == 'Frame':
                    widget.configure(bg='#0d1117')  # Original dark background
                    self.restore_dark_header_children(widget)  # Recursively apply to children
                
                # Labels - restore original dark styling from create_widgets
                elif widget_class == 'Label':
                    if widget_name == 'app_title_label':
                        widget.configure(bg='#0d1117', fg='#4a9eff')  # Exact original from create_widgets line 530-531
                    elif widget_name == 'app_subtitle_label':
                        widget.configure(bg='#0d1117', fg='#8b949e')  # Exact original from create_widgets line 540-541
                    elif widget_name == 'header_icon_label':
                        widget.configure(bg='#0d1117', fg='#4a9eff')  # Exact original from create_widgets line 523
                    else:
                        # General labels in header - use original background
                        widget.configure(bg='#0d1117', fg='#f0f6fc')
                
                # ImageButton - restore original dark background from create_widgets
                elif widget_class == 'Button' and hasattr(widget, 'is_image_button'):
                    widget.configure(bg='#0d1117')  # Exact original from create_widgets line 519
                
                # Recursively apply to other children
                else:
                    self.restore_dark_header_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark header children: {e}")
    
    def apply_dark_theme(self):
        """Apply TinyTunez dark theme (default) - comprehensive restoration"""
        try:
            # Set current theme to dark
            self.current_theme = 'dark'
            
            # Restore root window background first
            self.root.configure(bg='#0d1117')
            
            # Apply dark scrollbar styling (this is the same as during initialization)
            style = ttk.Style()
            style.configure(
                'TScrollbar',
                background='#30363d',
                troughcolor='#21262d',
                bordercolor='#30363d',
                arrowcolor='#8b949e',
                lightcolor='#262c32',
                darkcolor='#262c32',
                relief='raised'
            )
            
            style.configure(
                'Vertical.TScrollbar',
                background='#30363d',
                troughcolor='#21262d',
                bordercolor='#30363d',
                arrowcolor='#8b949e',
                lightcolor='#262c32',
                darkcolor='#262c32',
                relief='raised'
            )
            
            style.map('TScrollbar', 
                background=[('active', '#30363d'), ('!active', '#30363d')],
                arrowcolor=[('active', '#8b949e'), ('!active', '#8b949e')]
            )
            
            style.map('Vertical.TScrollbar', 
                background=[('active', '#30363d'), ('!active', '#30363d')],
                arrowcolor=[('active', '#8b949e'), ('!active', '#8b949e')]
            )
            
            # Reset treeview to default dark styling
            if hasattr(self, 'playlist_treeview'):
                style.configure(
                    'Custom.Treeview',
                    background='#0d1117',
                    foreground='#f0f6fc',
                    fieldbackground='#0d1117',
                    selectbackground='#1f6feb',
                    selectforeground='#ffffff',
                    borderwidth=0,
                    font=('Segoe UI', 10)
                )
                
                style.configure(
                    'Custom.Treeview.Heading',
                    background='#21262d',
                    foreground='#f0f6fc',
                    fieldbackground='#21262d',
                    relief='raised',
                    font=('Segoe UI', 10, 'bold')
                )
                
                # Restore dark selection mapping
                style.map(
                    'Custom.Treeview',
                    background=[('selected', '#4A6984')],
                    foreground=[('selected', '#ffffff')]
                )
                
                # Apply the style
                self.playlist_treeview.configure(style='Custom.Treeview')
                
                # Add tooltip to show current selection highlight color
                self.add_treeview_tooltip()
            
            # Restore dark theme to all components in the correct order
            self.restore_dark_main_frame()
            self.restore_dark_playlist_header()
            self.restore_dark_player_controls()
            self.restore_dark_playlist_frame()
            self.restore_dark_song_info_frame()
            self.restore_dark_lyrics_frame()
            self.restore_dark_buttons()
            self.restore_dark_labels()
            self.restore_dark_search_entry()
            self.restore_dark_header_frame()
            self.restore_dark_volume_slider()
            
            # Update all open Edit Lyrics dialogs
            self.update_all_edit_lyrics_dialogs_theme()
            
            # Update all open Select Music Folders dialogs
            self.update_all_folder_selection_dialogs_theme()
            
            # Update all open Settings dialogs
            self.update_all_settings_dialogs_theme()
            
            # Save theme preference to settings
            self.settings['theme'] = 'dark'
            self.save_settings()
            
            print("Dark theme fully restored!")
            
        except Exception as e:
            print(f"Error applying dark theme: {e}")
    
    def restore_dark_playlist_header(self):
        """Restore dark theme to playlist header frame and all contents"""
        try:
            # Find the playlist header frame
            playlist_header = None
            for widget in self.root.winfo_children():
                result = self.find_widget_by_name(widget, 'playlist_header_frame')
                if result:
                    playlist_header = result
                    break
            
            if not playlist_header:
                print("Playlist header frame not found for dark restoration")
                return
            
            # Apply dark theme to header frame
            playlist_header.configure(bg='#161b22')
            
            # Apply to all children in the header
            self.restore_dark_header_children(playlist_header)
            
        except Exception as e:
            print(f"Error restoring dark playlist header: {e}")
    
    def restore_dark_playlist_frame(self):
        """Restore dark theme to playlist frame"""
        try:
            playlist_frame = self.find_widget_by_name(self.root, 'playlist_frame')
            if playlist_frame:
                playlist_frame.configure(bg='#161b22')  # Original dark color
            else:
                pass
        except Exception as e:
            print(f"Error restoring dark playlist frame: {e}")
    
    def restore_dark_song_info_frame(self):
        """Restore dark theme to song info frame"""
        try:
            song_info_frame = self.find_widget_by_name(self.root, 'song_info_frame')
            if song_info_frame:
                song_info_frame.configure(bg='#161b22')  # Original dark color
                
                # Apply dark theme to all children in the song info frame
                self.restore_dark_song_info_children(song_info_frame)
                
                # Also try to find and restore the visualization frames directly
                time_viz_frame = self.find_widget_by_name(self.root, 'time_viz_frame')
                if time_viz_frame:
                    time_viz_frame.configure(bg='#161b22')  # Original dark background
                    self.restore_dark_song_info_children(time_viz_frame)
                else:
                    pass
                
                viz_frame = self.find_widget_by_name(self.root, 'viz_frame')
                if viz_frame:
                    viz_frame.configure(bg='#21262d')  # Original dark background
                    self.restore_dark_song_info_children(viz_frame)
                else:
                    pass
                
                # Also try to find and restore current_time_frame directly
                current_time_frame = self.find_widget_by_name(self.root, 'current_time_frame')
                if current_time_frame:
                    current_time_frame.configure(bg='#21262d')  # Original dark background
                else:
                    pass
                
                # Also try to find and restore progress_frame directly
                progress_frame = self.find_widget_by_name(self.root, 'progress_frame')
                if progress_frame:
                    progress_frame.configure(bg='#161b22')  # Original dark background
                    self.restore_dark_song_info_children(progress_frame)
                else:
                    pass
                
                # Also try to find and restore progress bar elements directly
                progress_bg = self.find_widget_by_name(self.root, 'progress_bg')
                if progress_bg:
                    progress_bg.configure(bg='#21262d', highlightthickness=0)  # Original dark progress bar background color, no border
                else:
                    pass
                
                progress_fill = self.find_widget_by_name(self.root, 'progress_fill')
                if progress_fill:
                    progress_fill.configure(bg='#4A9EFF')  # Original dark progress bar fill color
                else:
                    pass
            else:
                pass
        except Exception as e:
            print(f"Error restoring dark song info frame: {e}")
    
    def restore_dark_song_info_children(self, parent):
        """Restore dark theme to all children in song info frame"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Frame children - restore dark background
                if widget_class == 'Frame':
                    # Special handling for info_border_frame
                    if widget_name == 'info_border_frame':
                        widget.configure(highlightbackground='#30363d', highlightthickness=1)  # Dark mode border
                    else:
                        widget.configure(bg='#161b22')
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # ModernFrame children - restore dark background
                elif widget_class == 'TFrame' or hasattr(widget, '__class__') and widget.__class__.__name__ == 'ModernFrame':
                    widget.configure(bg='#161b22')
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # Labels - restore dark styling
                elif widget_class == 'Label':
                    # Special handling for specific labels
                    if widget_name in ['app_title_label', 'app_subtitle_label']:
                        widget.configure(bg='#0d1117', fg='#4a9eff')  # Original dark colors for title
                        if widget_name == 'app_subtitle_label':
                            widget.configure(fg='#8b949e')  # Original dark color for subtitle
                    elif widget_name in ['song_title_label', 'song_artist_label']:
                        widget.configure(bg='#161b22', fg='#f0f6fc')
                    elif widget_name in ['song_length_label', 'current_time_label']:
                        widget.configure(bg='#161b22', fg='#8b949e')
                    elif widget_name == 'album_art_label':
                        widget.configure(bg='#161b22', highlightthickness=0)  # Remove border in dark mode
                        # Restore original placement (60x60 centered)
                        widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                    else:
                        # General labels
                        widget.configure(bg='#161b22', fg='#f0f6fc')
                
                # Special handling for current_time_frame
                elif widget_name == 'current_time_frame':
                    widget.configure(bg='#21262d')  # Original dark background
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # Special handling for progress_frame
                elif widget_name == 'progress_frame':
                    widget.configure(bg='#161b22')  # Original dark background
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # Special handling for progress bar elements
                elif widget_name in ['progress_bg', 'progress_fill']:
                    if widget_name == 'progress_bg':
                        widget.configure(bg='#21262d', highlightthickness=0)  # Original dark progress bar background color, no border
                    else:
                        widget.configure(bg='#4A9EFF')  # Original dark progress bar fill color
                
                # Canvas - keep visualization canvas black, no border
                elif widget_class == 'Canvas':
                    if widget_name == 'visualization_canvas':
                        widget.configure(
                            bg='#000000',  # Always black for visualization
                            highlightthickness=0  # Remove border
                        )
                    else:
                        widget.configure(bg='#0d1117')
                
                # Progress bar frame
                elif widget_name == 'progress_frame':
                    widget.configure(bg='#161b22')
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # Visualization frame - restore dark background
                elif widget_name == 'viz_frame':
                    widget.configure(bg='#21262d')  # Original dark background
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # Time/visualization frame - restore dark background
                elif widget_name == 'time_viz_frame':
                    widget.configure(bg='#161b22')  # Original dark background
                    self.restore_dark_song_info_children(widget)  # Recursively apply to children
                
                # Recursively apply to other children
                else:
                    self.restore_dark_song_info_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark song info children: {e}")
    
    def restore_dark_main_frame(self):
        """Restore dark theme to main frame"""
        try:
            main_frame = self.find_widget_by_name(self.root, 'main_frame')
            if main_frame:
                main_frame.configure(bg='#0d1117')  # Original dark background
                self.restore_dark_main_children(main_frame)
            else:
                pass
        except Exception as e:
            print(f"Error restoring dark main frame: {e}")
    
    def restore_dark_main_children(self, parent):
        """Restore dark theme to all children in main frame"""
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                if widget_class == 'Frame':
                    widget.configure(bg='#0d1117')
                    self.restore_dark_main_children(widget)  # Recursively apply to children
        except Exception as e:
            print(f"Error restoring dark main children: {e}")
    
    def restore_dark_lyrics_frame(self):
        """Restore dark theme to lyrics frame"""
        try:
            lyrics_frame = self.find_widget_by_name(self.root, 'lyrics_frame')
            if lyrics_frame:
                lyrics_frame.configure(bg='#161b22')  # Original dark background
                self.restore_dark_lyrics_children(lyrics_frame)
            else:
                pass
        except Exception as e:
            print(f"Error restoring dark lyrics frame: {e}")
    
    def restore_dark_lyrics_children(self, parent):
        """Restore dark theme to all children in lyrics frame"""
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                widget_name = getattr(widget, '_name', '')
                
                if widget_class == 'Frame':
                    widget.configure(bg='#161b22')
                    self.restore_dark_lyrics_children(widget)  # Recursively apply to children
                elif widget_class == 'Label':
                    widget.configure(bg='#161b22', fg='#f0f6fc')
                elif widget_class == 'Text':
                    widget.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#f0f6fc')
                elif widget_class == 'Button':
                    if not hasattr(widget, 'is_image_button'):
                        # Special handling for Open Folder button
                        button_text = widget.cget('text') if hasattr(widget, 'cget') else ''
                        if 'Open Folder' in button_text or widget_name == '!button2':
                            widget.configure(
                                bg='#238636',  # Original dark mode green
                                fg='white',     # Original dark mode white text
                                activebackground='#2ea043',
                                activeforeground='white'
                            )
                        else:
                            widget.configure(bg='#21262d', fg='#f0f6fc')
        except Exception as e:
            print(f"Error restoring dark lyrics children: {e}")
    
    def restore_dark_volume_slider(self):
        """Restore dark theme to volume slider"""
        try:
            if hasattr(self, 'volume_slider'):
                self.volume_slider.configure(
                    bg='#21262d',
                    troughcolor='#161b22',
                    activebackground='#4A9EFF',
                    fg='#f0f6fc',
                    highlightbackground='#4A6984',  # Original dark mode border color
                    highlightcolor='#4A6984'      # Original dark mode border color
                )
        except Exception as e:
            print(f"Error restoring dark volume slider: {e}")
    
    def restore_dark_player_controls(self):
        """Restore dark theme to player controls frame and all contents"""
        try:
            # Find the player controls frame
            player_controls = None
            for widget in self.root.winfo_children():
                result = self.find_widget_by_name(widget, 'player_controls_frame')
                if result:
                    player_controls = result
                    break
            
            if not player_controls:
                print("Player controls frame not found for dark restoration")
                return
            
            # Apply dark theme to player controls frame
            player_controls.configure(bg='#161b22')
            
            # Apply to all children in the player controls
            self.restore_dark_player_controls_children(player_controls)
            
        except Exception as e:
            print(f"Error restoring dark player controls: {e}")
    
    def restore_dark_player_controls_children(self, parent):
        """Restore dark theme to all children in player controls"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Control button frames (prev_btn_frame, play_btn_frame, pause_btn_frame, etc.)
                if widget_name in ['prev_btn_frame', 'play_btn_frame', 'pause_btn_frame', 'stop_btn_frame', 'next_btn_frame', 'shuffle_btn_frame']:
                    widget.configure(bg='#161b22')  # Original dark frame color
                
                # Controls frame and volume frame
                elif widget_name in ['controls_frame', 'volume_frame']:
                    widget.configure(bg='#161b22')
                    self.restore_dark_player_controls_children(widget)  # Recursively apply to children
                
                # ImageButton itself - no styling needed (transparent background)
                elif widget_class == 'Button' and hasattr(widget, 'is_image_button'):
                    pass  # Keep ImageButton transparent to show frame background
                
                # Scale (volume slider) - restore to original dark styling with border
                elif widget_class == 'Scale':
                    widget.configure(
                        bg='#21262d',
                        fg='#4a9eff',
                        troughcolor='#30363d',
                        activebackground='#4a9eff',
                        highlightthickness=1,      # Keep border
                        highlightbackground='#4A6984',  # Better contrast border color
                        borderwidth=0              # No additional border
                    )
                
                # Labels - restore to original dark styling
                elif widget_class == 'Label':
                    # Volume label specifically
                    if widget_name == 'volume_label':
                        widget.configure(bg='#161b22', fg='#8b949e')
                    else:
                        # Other labels in player controls
                        widget.configure(bg='#161b22', fg='#f0f6fc')
                
                # Recursively apply to other children
                else:
                    self.restore_dark_player_controls_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark player controls children: {e}")
    
    def restore_dark_header_children(self, parent):
        """Restore dark theme to all children in playlist header"""
        try:
            for widget in parent.winfo_children():
                widget_name = getattr(widget, '_name', '')
                widget_class = widget.winfo_class()
                
                # Header label
                if widget_name == 'playlist_header_label':
                    widget.configure(bg='#161b22', fg='#f0f6fc')
                
                # Search frame
                elif widget_name == 'search_frame':
                    widget.configure(bg='#161b22')
                    self.restore_dark_header_children(widget)  # Recursively apply to children
                
                # Playlist buttons frame (Edit, Remove, Clear buttons)
                elif widget_name == 'playlist_buttons_frame':
                    widget.configure(bg='#161b22')
                
                # Search entry frame
                elif widget_name == 'search_entry_frame':
                    widget.configure(bg='#0d1117', highlightbackground='#30363d', highlightcolor='#1f6feb')
                
                # Search entry
                elif widget_name == 'search_entry':
                    widget.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#f0f6fc')
                
                # Clear button canvas
                elif widget_name == 'clear_search_canvas':
                    widget.configure(bg='#0d1117')
                    # Update the circular background and X symbol colors
                    widget.delete("all")
                    widget.create_oval(2, 2, 14, 14, fill='#30363d', outline='#30363d')
                    widget.create_text(8, 8, text="✕", font=('Segoe UI', 8, 'bold'), fill='#8b949e')
                
                # Recursively apply to other children
                else:
                    self.restore_dark_header_children(widget)
                    
        except Exception as e:
            print(f"Error restoring dark header children: {e}")
    
    def restore_dark_buttons(self):
        """Restore dark theme to all buttons (except ImageButtons)"""
        try:
            # Find all buttons recursively
            self.find_and_restore_dark_buttons(self.root)
            
            # Specifically restore ImageButtons after general button restoration
            self.restore_dark_imagebuttons()
            
        except Exception as e:
            print(f"Error restoring dark buttons: {e}")
    
    def restore_dark_imagebuttons(self):
        """Specifically restore ImageButtons to their original class defaults"""
        try:
            imagebutton_widgets = []
            self.find_imagebuttons_recursive(self.root, imagebutton_widgets)
            
            for img_btn in imagebutton_widgets:
                widget_name = getattr(img_btn, '_name', 'unnamed')
                parent_name = getattr(img_btn.master, '_name', '') if hasattr(img_btn.master, '_name') else ''
                
                # Header ImageButton - restore to original dark colors
                if parent_name == 'header_frame':
                    img_btn.configure(
                        bg='#0d1117',  # Original from create_widgets line 519
                        relief=tk.FLAT,
                        border=0,
                        cursor='hand2',
                        activebackground='#21262d'
                    )
                else:
                    # Other ImageButtons - restore to standard dark colors
                    img_btn.configure(
                        bg='#161b22',
                        relief=tk.FLAT,
                        border=0,
                        cursor='hand2',
                        activebackground='#21262d'
                    )
                
        except Exception as e:
            print(f"Error restoring dark ImageButtons: {e}")
    
    def find_imagebuttons_recursive(self, parent, imagebutton_list):
        """Recursively find all ImageButtons"""
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                
                if widget_class == 'Button':
                    widget_name = getattr(widget, '_name', 'unnamed')
                    # Check both the is_image_button attribute and the widget name pattern
                    if hasattr(widget, 'is_image_button') and widget.is_image_button:
                        imagebutton_list.append(widget)
                    elif widget_name.startswith('!imagebutton'):
                        # Also set the attribute for future reference
                        widget.is_image_button = True
                        imagebutton_list.append(widget)
                    else:
                        pass
                
                self.find_imagebuttons_recursive(widget, imagebutton_list)
        except:
            pass
    
    def find_and_restore_dark_buttons(self, parent):
        """Recursively find and restore dark theme to all buttons"""
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                widget_name = getattr(widget, '_name', '')
                
                # Style regular buttons (not ImageButtons) with original dark theme colors
                if widget_class == 'Button' and not hasattr(widget, 'is_image_button'):
                    # Special handling for Open Folder button
                    button_text = widget.cget('text') if hasattr(widget, 'cget') else ''
                    if 'Open Folder' in button_text or widget_name == '!button2':
                        widget.configure(
                            bg='#238636',  # Original dark mode green
                            fg='white',     # Original dark mode white text
                            activebackground='#2ea043',
                            activeforeground='white',
                            relief=tk.RAISED
                        )
                    else:
                        widget.configure(bg='#30363d', fg='white', relief=tk.RAISED)
                
                # ImageButton - restore to original ImageButton class defaults
                elif widget_class == 'Button' and hasattr(widget, 'is_image_button'):
                    # Reset to ImageButton class defaults (from lines 91-98)
                    widget.configure(
                        bg='#161b22',
                        relief=tk.FLAT,
                        border=0,
                        cursor='hand2',
                        activebackground='#21262d'
                    )
                
                # Recursively check children
                self.find_and_restore_dark_buttons(widget)
                
        except Exception as e:
            pass
    
    def restore_dark_labels(self):
        """Restore dark theme to all labels in the application"""
        try:
            self.restore_dark_labels_recursive(self.root)
        except Exception as e:
            print(f"Error restoring dark labels: {e}")
    
    def restore_dark_labels_recursive(self, parent):
        """Recursively restore dark theme to all labels"""
        try:
            for widget in parent.winfo_children():
                widget_class = widget.winfo_class()
                widget_name = getattr(widget, '_name', '')
                
                if widget_class == 'Label':
                    # Header labels - restore to original dark colors from create_widgets
                    if widget_name == 'app_title_label':
                        widget.configure(bg='#0d1117', fg='#4a9eff')  # Exact original from create_widgets line 530-531
                    elif widget_name == 'app_subtitle_label':
                        widget.configure(bg='#0d1117', fg='#8b949e')  # Exact original from create_widgets line 540-541
                    elif widget_name == 'header_icon_label':
                        widget.configure(bg='#0d1117', fg='#4a9eff')  # Exact original from create_widgets line 523
                    # Volume label specifically
                    elif widget_name == 'volume_label':
                        widget.configure(bg='#161b22', fg='#8b949e')
                    # Playlist header label
                    elif widget_name == 'playlist_header_label':
                        widget.configure(bg='#161b22', fg='#f0f6fc')
                    # Other labels - restore to dark theme
                    else:
                        # Try to determine the appropriate background
                        parent_bg = widget.master.cget('bg') if hasattr(widget.master, 'cget') else '#161b22'
                        widget.configure(bg=parent_bg, fg='#f0f6fc')
                
                # Recursively check children
                self.restore_dark_labels_recursive(widget)
                
        except Exception as e:
            pass
    
    def restore_dark_search_entry(self):
        """Restore dark theme to search entry"""
        try:
            if hasattr(self, 'search_entry'):
                self.search_entry.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#f0f6fc')
                self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0)  # Keep original padding (0)
            
            # Also update the search entry frame padding to original
            search_entry_frame = self.find_widget_by_name(self.root, 'search_entry_frame')
            if search_entry_frame:
                search_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=0, pady=0)  # Keep original padding (0)
                
        except Exception as e:
            print(f"Error restoring dark search entry: {e}")

    def add_treeview_tooltip(self):
        """Add selection highlight color info to existing treeview tooltip"""
        try:
            # Get the current selection color from the style
            style = ttk.Style()
            try:
                style_map = style.map('Custom.Treeview', 'background')
                selection_color = '#1f6feb'  # Default fallback
                
                if style_map:
                    for state, color in style_map:
                        if state == 'selected':
                            selection_color = color
                            break
            except:
                selection_color = '#1f6feb'
            
            # Simply print the color info to console for now
            # Since the existing tooltip system is complex, we'll just add console output
            print(f"Selection Highlight Color: {selection_color}")
            
            # Also add a simple click handler to show the color
            if hasattr(self, 'playlist_treeview'):
                def show_selection_color(event):
                    print(f"Selection Highlight Color: {selection_color}")
                    # Create a simple color display
                    color_window = tk.Toplevel(self.root)
                    color_window.wm_overrideredirect(True)
                    color_window.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                    
                    color_frame = tk.Frame(color_window, bg=selection_color, relief='solid', borderwidth=2)
                    color_frame.pack()
                    
                    label = tk.Label(
                        color_frame,
                        text=f"Selection: {selection_color}",
                        bg=selection_color,
                        fg='white' if selection_color != '#ffffff' else 'black',
                        font=('Segoe UI', 10, 'bold'),
                        padx=10,
                        pady=6
                    )
                    label.pack()
                    
                    # Auto-hide after 3 seconds
                    color_window.after(3000, color_window.destroy)
                
                # Add right-click to show color
                self.playlist_treeview.bind('<Button-3>', show_selection_color)
                
        except Exception as e:
            print(f"Error adding treeview color info: {e}")
    
    def hide_color_tooltip(self):
        """Hide the color tooltip"""
        try:
            if hasattr(self, '_color_tooltip') and self._color_tooltip:
                self._color_tooltip.destroy()
                self._color_tooltip = None
        except:
            pass
    
    def fresh_dark_theme_rebuild(self):
        """Complete fresh rebuild of dark theme - clean application"""
        try:
            # Reset root
            self.root.configure(bg='#0d1117')
            
            # BRUTE FORCE: Reset EVERYTHING by walking the entire widget tree
            self.reset_all_widgets_brute_force(self.root)
            
            # Then do targeted rebuilds for specific areas
            self.rebuild_title_area_fresh()
            self.rebuild_song_info_fresh()
            self.rebuild_containers_fresh()
            self.rebuild_playlist_area_fresh()
            self.rebuild_lyrics_area_fresh()
            self.rebuild_controls_fresh()
            
        except Exception as e:
            print(f"Error in fresh dark theme rebuild: {e}")
    
    def reset_all_widgets_brute_force(self, parent):
        """Brute force reset of ALL widgets to dark theme"""
        try:
            for widget in parent.winfo_children():
                try:
                    widget_type = widget.winfo_class()
                    
                    # Reset based on widget type
                    if widget_type == 'Frame':
                        if hasattr(widget, 'configure'):
                            # Check if this is a header frame (height 40)
                            if hasattr(widget, 'winfo_height') and widget.winfo_height() == 40:
                                widget.configure(bg='#21262d')  # Header color
                            else:
                                widget.configure(bg='#0d1117')  # Main dark color
                    
                    elif widget_type == 'Label':
                        if hasattr(widget, 'configure'):
                            parent_bg = widget.master.cget('bg') if hasattr(widget.master, 'cget') else '#0d1117'
                            widget.configure(bg=parent_bg, fg='#f0f6fc')
                    
                    elif widget_type == 'Button':
                        if hasattr(widget, 'configure'):
                            if widget.cget('relief') == tk.FLAT:
                                widget.configure(bg='#30363d', fg='#f0f6fc', activebackground='#40474f')
                            else:
                                widget.configure(bg='#161b22', fg='#f0f6fc', activebackground='#21262d')
                    
                    elif widget_type == 'Entry':
                        if hasattr(widget, 'configure'):
                            widget.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff')
                    
                    elif widget_type == 'Text':
                        if hasattr(widget, 'configure'):
                            widget.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff', selectbackground='#21262d')
                    
                    elif widget_type == 'Canvas':
                        if hasattr(widget, 'configure'):
                            # Check if this is the visualization canvas
                            if hasattr(self, 'visualization_canvas') and widget == self.visualization_canvas:
                                widget.configure(bg='#000000')
                            else:
                                widget.configure(bg='#0d1117')
                    
                    elif widget_type == 'Scale':
                        if hasattr(widget, 'configure'):
                            widget.configure(bg='#21262d', troughcolor='#30363d', activebackground='#4a9eff')
                    
                    elif widget_type == 'Treeview':
                        # Treeview is handled by ttk.Style, but let's be sure
                        pass
                    
                    # Recursively process children
                    self.reset_all_widgets_brute_force(widget)
                    
                except:
                    # If any widget fails, continue with others
                    pass
                    
        except:
            pass
    
    def rebuild_title_area_fresh(self):
        """Fresh rebuild of title area"""
        if hasattr(self, 'title_frame'):
            self.title_frame.configure(bg='#0d1117')
            for child in self.title_frame.winfo_children():
                if isinstance(child, ModernLabel):
                    text = str(child.cget('text'))
                    if 'TinyTunez' in text:
                        child.configure(bg='#0d1117', fg='#4a9eff')
                    else:
                        child.configure(bg='#0d1117', fg='#8b949e')
                elif isinstance(child, tk.Button):
                    child.configure(bg='#161b22', fg='#f0f6fc', activebackground='#21262d')
    
    def rebuild_song_info_fresh(self):
        """Fresh rebuild of song info area"""
        if hasattr(self, 'info_card'):
            self.info_card.configure(bg='#161b22')
            
            # Album art area
            if hasattr(self, 'album_frame'):
                self.album_frame.configure(bg='#21262d')
                if hasattr(self, 'album_music_icon'):
                    self.album_music_icon.configure(bg='#21262d')
                if hasattr(self, 'album_img_label'):
                    self.album_img_label.configure(bg='#21262d')
            
            # Song info elements
            for child in self.info_card.winfo_children():
                if isinstance(child, ModernFrame) and child != self.album_frame:
                    child.configure(bg='#161b22')
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ModernLabel):
                            subchild.configure(bg='#161b22', fg='#f0f6fc')
                        elif isinstance(subchild, tk.Canvas):
                            subchild.configure(bg='#000000')  # Visualization
                        elif isinstance(subchild, tk.Scale):
                            subchild.configure(bg='#21262d', troughcolor='#30363d', activebackground='#4a9eff')
                        elif isinstance(subchild, tk.Button):
                            subchild.configure(bg='#30363d', fg='#f0f6fc')
    
    def rebuild_containers_fresh(self):
        """Fresh rebuild of main containers"""
        if hasattr(self, 'main_container'):
            self.main_container.configure(bg='#0d1117')
        if hasattr(self, 'left_frame'):
            self.left_frame.configure(bg='#0d1117')
    
    def rebuild_playlist_area_fresh(self):
        """Fresh rebuild of playlist area"""
        # Find all playlist-related frames and reset them
        for widget in self.root.winfo_children():
            self.reset_playlist_widgets_fresh(widget)
    
    def reset_playlist_widgets_fresh(self, widget):
        """Recursively reset playlist widgets to fresh dark theme"""
        try:
            if isinstance(widget, ModernFrame):
                # Check if this might be a playlist container
                children = widget.winfo_children()
                has_treeview = any(isinstance(child, ttk.Treeview) for child in children)
                has_search = any(isinstance(child, tk.Entry) for child in children)
                
                if has_treeview or has_search:
                    widget.configure(bg='#161b22')
                    for child in children:
                        if isinstance(child, ModernFrame):
                            if child.winfo_height() <= 50:  # Header frame
                                child.configure(bg='#21262d')
                                for subchild in child.winfo_children():
                                    if isinstance(subchild, ModernLabel):
                                        subchild.configure(bg='#21262d', fg='#f0f6fc')
                                    elif isinstance(subchild, tk.Button):
                                        subchild.configure(bg='#30363d', fg='#f0f6fc')
                            else:
                                child.configure(bg='#161b22')
                        elif isinstance(child, tk.Entry):
                            child.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff')
                else:
                    # Recursively check children
                    for child in children:
                        self.reset_playlist_widgets_fresh(child)
        except:
            pass
    
    def rebuild_lyrics_area_fresh(self):
        """Fresh rebuild of lyrics area"""
        # Find all lyrics-related frames and reset them
        for widget in self.root.winfo_children():
            self.reset_lyrics_widgets_fresh(widget)
    
    def reset_lyrics_widgets_fresh(self, widget):
        """Recursively reset lyrics widgets to fresh dark theme"""
        try:
            if isinstance(widget, ModernFrame):
                # Check if this might be a lyrics container
                children = widget.winfo_children()
                has_text = any(isinstance(child, tk.Text) for child in children)
                
                if has_text:
                    widget.configure(bg='#161b22')
                    for child in children:
                        if isinstance(child, ModernFrame):
                            if child.winfo_height() <= 50:  # Header frame
                                child.configure(bg='#21262d')
                                for subchild in child.winfo_children():
                                    if isinstance(subchild, ModernLabel):
                                        subchild.configure(bg='#21262d', fg='#f0f6fc')
                                    elif isinstance(subchild, tk.Button):
                                        subchild.configure(bg='#30363d', fg='#f0f6fc')
                        elif isinstance(child, tk.Text):
                            child.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff', selectbackground='#21262d')
                else:
                    # Recursively check children
                    for child in children:
                        self.reset_lyrics_widgets_fresh(child)
        except:
            pass
    
    def rebuild_controls_fresh(self):
        """Fresh rebuild of player controls"""
        # Find and reset control buttons and sliders
        for widget in self.root.winfo_children():
            self.reset_control_widgets_fresh(widget)
    
    def reset_control_widgets_fresh(self, widget):
        """Recursively reset control widgets to fresh dark theme"""
        try:
            if isinstance(widget, ModernFrame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button) and child.cget('relief') == tk.FLAT:
                        child.configure(bg='#30363d', fg='#f0f6fc', activebackground='#40474f')
                    elif isinstance(child, tk.Scale):
                        child.configure(bg='#21262d', troughcolor='#30363d', activebackground='#4a9eff')
                    else:
                        self.reset_control_widgets_fresh(child)
        except:
            pass
    
    def reset_all_frames_to_dark_direct(self):
        """Direct reset of all frames to dark theme without recursive color mixing"""
        try:
            # Reset specific known frames directly
            frames_to_reset = [
                ('main_container', '#0d1117'),
                ('left_frame', '#0d1117'),
                ('info_card', '#161b22'),
                ('album_frame', '#21262d'),
                ('title_frame', '#0d1117'),
                ('progress_frame', '#161b22'),
                ('lyrics_text_frame', '#0d1117')
            ]
            
            for frame_name, color in frames_to_reset:
                if hasattr(self, frame_name):
                    frame = getattr(self, frame_name)
                    frame.configure(bg=color)
                    # Reset direct children
                    for child in frame.winfo_children():
                        self.reset_child_to_dark_direct(child, color)
            
        except Exception as e:
            print(f"Error in direct frame reset: {e}")
    
    def reset_child_to_dark_direct(self, child, parent_bg):
        """Reset child widget to dark theme based on its type"""
        try:
            if isinstance(child, ModernLabel):
                if parent_bg == '#0d1117':
                    child.configure(bg=parent_bg, fg='#f0f6fc')
                elif parent_bg == '#161b22':
                    child.configure(bg=parent_bg, fg='#f0f6fc')
                elif parent_bg == '#21262d':
                    child.configure(bg=parent_bg, fg='#f0f6fc')
                else:
                    child.configure(bg=parent_bg, fg='#f0f6fc')
            
            elif isinstance(child, tk.Button) and child.cget('relief') == tk.FLAT:
                child.configure(bg='#30363d', fg='#f0f6fc')
            
            elif isinstance(child, tk.Entry):
                child.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff')
            
            elif isinstance(child, tk.Text):
                child.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff', selectbackground='#21262d')
            
            elif isinstance(child, tk.Canvas):
                # Visualization canvas stays black
                if hasattr(self, 'visualization_canvas') and child == self.visualization_canvas:
                    child.configure(bg='#000000')
                else:
                    child.configure(bg=parent_bg)
            
            elif isinstance(child, tk.Scale):
                child.configure(bg='#21262d', troughcolor='#30363d', activebackground='#4a9eff')
            
        except:
            pass
    
    def fix_stuck_dark_elements(self):
        """Fix specific elements that might be stuck with incorrect colors"""
        try:
            # Fix title labels that might be stuck
            if hasattr(self, 'title_frame'):
                for child in self.title_frame.winfo_children():
                    if isinstance(child, ModernLabel):
                        if 'TinyTunez' in str(child.cget('text')):
                            child.configure(fg='#4a9eff')  # Blue for main title
                        else:
                            child.configure(fg='#8b949e')  # Gray for subtitle
            
            # Fix song info card background
            if hasattr(self, 'info_card'):
                self.info_card.configure(bg='#161b22')
            
            # Fix album art area
            if hasattr(self, 'album_frame'):
                self.album_frame.configure(bg='#21262d')
                if hasattr(self, 'album_music_icon'):
                    self.album_music_icon.configure(bg='#21262d')
                if hasattr(self, 'album_img_label'):
                    self.album_img_label.configure(bg='#21262d')
            
            # Force UI update
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error fixing stuck dark elements: {e}")
    
    def complete_dark_theme_restoration(self):
        """Complete restoration of dark theme - rebuilds from scratch"""
        try:
            # Reset root
            self.root.configure(bg='#0d1117')
            
            # Reset main containers
            if hasattr(self, 'main_container'):
                self.main_container.configure(bg='#0d1117')
            if hasattr(self, 'left_frame'):
                self.left_frame.configure(bg='#0d1117')
            
            # Reset title area completely
            if hasattr(self, 'title_frame'):
                self.title_frame.configure(bg='#0d1117')
                for child in self.title_frame.winfo_children():
                    if isinstance(child, ModernLabel):
                        child.configure(bg='#0d1117', fg='#4a9eff' if 'TinyTunez' in str(child.cget('text')) else '#8b949e')
                    elif isinstance(child, tk.Button):
                        child.configure(bg='#161b22', activebackground='#21262d')
            
            # Reset song info card completely
            if hasattr(self, 'info_card'):
                self.info_card.configure(bg='#161b22')
                # Reset album art
                if hasattr(self, 'album_frame'):
                    self.album_frame.configure(bg='#21262d')
                    if hasattr(self, 'album_music_icon'):
                        self.album_music_icon.configure(bg='#21262d')
                    if hasattr(self, 'album_img_label'):
                        self.album_img_label.configure(bg='#21262d')
                
                # Reset song info elements
                for child in self.info_card.winfo_children():
                    if isinstance(child, ModernFrame) and child != self.album_frame:
                        child.configure(bg='#161b22')
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ModernLabel):
                                subchild.configure(bg='#161b22', fg='#f0f6fc')
                            elif isinstance(subchild, tk.Canvas):
                                subchild.configure(bg='#000000')
                            elif isinstance(subchild, tk.Scale):
                                subchild.configure(bg='#21262d', troughcolor='#30363d', activebackground='#4a9eff')
                            elif isinstance(subchild, tk.Button):
                                subchild.configure(bg='#30363d')
            
            # Reset playlist area
            self.reset_playlist_area_dark()
            
            # Reset lyrics area
            self.reset_lyrics_area_dark()
            
            # Force complete UI refresh
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error in complete dark theme restoration: {e}")
    
    def reset_playlist_area_dark(self):
        """Reset playlist area to dark theme"""
        try:
            # Find and reset playlist frames
            for widget in self.root.winfo_children():
                self.find_and_reset_playlist_frames(widget)
        except:
            pass
    
    def find_and_reset_playlist_frames(self, widget):
        """Recursively find and reset playlist frames"""
        try:
            if isinstance(widget, ModernFrame):
                # Check if this looks like a playlist frame
                children = widget.winfo_children()
                for child in children:
                    if isinstance(child, ModernFrame) and child.winfo_height() == 40:
                        # This looks like a playlist header
                        widget.configure(bg='#161b22')
                        child.configure(bg='#21262d')
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ModernLabel):
                                subchild.configure(bg='#21262d', fg='#f0f6fc')
                        break
                    else:
                        self.find_and_reset_playlist_frames(child)
        except:
            pass
    
    def reset_lyrics_area_dark(self):
        """Reset lyrics area to dark theme"""
        try:
            # Find and reset lyrics frames
            for widget in self.root.winfo_children():
                self.find_and_reset_lyrics_frames(widget)
        except:
            pass
    
    def find_and_reset_lyrics_frames(self, widget):
        """Recursively find and reset lyrics frames"""
        try:
            if isinstance(widget, ModernFrame):
                # Check if this looks like a lyrics frame
                children = widget.winfo_children()
                for child in children:
                    if isinstance(child, ModernFrame) and child.winfo_height() == 40:
                        # This looks like a lyrics header
                        widget.configure(bg='#161b22')
                        child.configure(bg='#21262d')
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ModernLabel):
                                subchild.configure(bg='#21262d', fg='#f0f6fc')
                            elif isinstance(subchild, tk.Button):
                                subchild.configure(bg='#30363d')
                        break
                    else:
                        self.find_and_reset_lyrics_frames(child)
        except:
            pass
    
    def force_dark_theme_reset(self):
        """Force reset specific elements that might be stuck with incorrect colors"""
        # Prevent infinite recursion
        if hasattr(self, '_resetting_dark_theme'):
            return
        
        self._resetting_dark_theme = True
        
        try:
            # Reset root and main containers
            self.root.configure(bg='#0d1117')
            if hasattr(self, 'main_container'):
                self.main_container.configure(bg='#0d1117')
            if hasattr(self, 'left_frame'):
                self.left_frame.configure(bg='#0d1117')
            
            # Reset title frame and all its children
            if hasattr(self, 'title_frame'):
                self.title_frame.configure(bg='#0d1117')
                for child in self.title_frame.winfo_children():
                    if isinstance(child, ModernLabel):
                        child.configure(bg='#0d1117')
                    elif isinstance(child, tk.Button):
                        child.configure(bg='#161b22', activebackground='#21262d')
            
            # Reset all frames recursively to be thorough
            self.reset_all_frames_recursively(self.root, '#0d1117', '#21262d', '#161b22')
            
            # Force UI update
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error in force dark theme reset: {e}")
        finally:
            # Clear the flag after a short delay
            self.root.after(200, lambda: setattr(self, '_resetting_dark_theme', False))
    
    def reset_all_frames_recursively(self, parent, main_bg, header_bg, button_bg):
        """Recursively reset all frames to dark theme colors"""
        for widget in parent.winfo_children():
            try:
                if isinstance(widget, ModernFrame):
                    # Check if this should be a header frame
                    if widget.winfo_height() == 40 or any(hasattr(child, 'cget') and child.winfo_class() == 'Label' and ('Playlist' in str(child.cget('text')) or 'Lyrics' in str(child.cget('text'))) for child in widget.winfo_children()):
                        widget.configure(bg=header_bg)
                    else:
                        widget.configure(bg=main_bg)
                    
                    # Recursively update children
                    self.reset_all_frames_recursively(widget, main_bg, header_bg, button_bg)
                
                elif isinstance(widget, ModernLabel):
                    parent_bg = widget.master.cget('bg') if hasattr(widget.master, 'cget') else main_bg
                    widget.configure(bg=parent_bg, fg='#f0f6fc')
                
                elif isinstance(widget, tk.Button) and widget.cget('relief') == tk.FLAT:
                    widget.configure(bg=button_bg, fg='#f0f6fc')
                
                elif isinstance(widget, tk.Entry):
                    widget.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff')
                
                elif isinstance(widget, tk.Text):
                    widget.configure(bg='#0d1117', fg='#f0f6fc', insertbackground='#4a9eff', selectbackground='#21262d')
                
            except:
                pass
    
    def update_special_widgets_dark(self, bg_color, header_bg, progress_fill):
        """Update special widgets for dark theme"""
        # Dark theme colors
        button_bg = '#30363d'
        
        try:
            # Update title area (behind TinyTunez title)
            if hasattr(self, 'title_frame'):
                self.title_frame.configure(bg=header_bg)
                # Update title and subtitle labels
                for child in self.title_frame.winfo_children():
                    if isinstance(child, ModernLabel):
                        child.configure(bg=header_bg)
                    elif isinstance(child, tk.Button):
                        child.configure(bg=header_bg)  # Use header_bg instead of empty string
            
            # Update album art frame
            if hasattr(self, 'album_frame'):
                self.album_frame.configure(bg=header_bg)
                # Update music icon if it exists
                if hasattr(self, 'album_music_icon'):
                    self.album_music_icon.configure(bg=header_bg)
                # Update image label if it exists
                if hasattr(self, 'album_img_label'):
                    self.album_img_label.configure(bg=header_bg)
            
            # Update visualization canvas
            if hasattr(self, 'visualization_canvas'):
                self.visualization_canvas.configure(bg='#000000')  # Always black for visualization
            
            # Update volume slider
            if hasattr(self, 'volume_slider'):
                self.volume_slider.configure(bg=bg_color, troughcolor=header_bg, activebackground=progress_fill)
            
            # Update mute button if it exists
            if hasattr(self, 'mute_btn'):
                self.mute_btn.configure(bg=button_bg)  # Use button_bg instead of empty string
                
        except Exception as e:
            print(f"Error updating special widgets: {e}")
    
    def update_special_widgets(self, parent, bg_color, fg_color, header_bg, header_fg, 
                            button_bg, time_bg, progress_bg, progress_fill):
        """Recursively update all custom widget colors"""
        for widget in parent.winfo_children():
            try:
                if isinstance(widget, ModernFrame):
                    if widget.winfo_height() == 40 or any(hasattr(child, 'cget') and child.winfo_class() == 'Label' and ('Playlist' in str(child.cget('text')) or 'Lyrics' in str(child.cget('text'))) for child in widget.winfo_children()):
                        widget.configure(bg=header_bg)
                    elif hasattr(self, 'progress_frame') and widget == self.progress_frame:
                        # Update progress bar colors
                        if hasattr(self, 'progress_bg'):
                            self.progress_bg.configure(bg=progress_bg)
                        if hasattr(self, 'progress_fill'):
                            self.progress_fill.configure(bg=progress_fill)
                        widget.configure(bg=bg_color)
                    elif hasattr(self, 'lyrics_text_frame') and widget == self.lyrics_text_frame:
                        # Update lyrics text frame
                        widget.configure(bg=bg_color)
                    elif any(hasattr(child, 'cget') and 'time' in str(child.cget('bg')).lower() for child in widget.winfo_children()):
                        widget.configure(bg=time_bg)
                    elif any('progress' in str(child.winfo_name()).lower() for child in widget.winfo_children()):
                        widget.configure(bg=progress_bg)
                    else:
                        widget.configure(bg=bg_color)
                
                elif isinstance(widget, ModernLabel):
                    parent_bg = widget.master.cget('bg') if hasattr(widget.master, 'cget') else bg_color
                    if parent_bg == header_bg:
                        widget.configure(bg=header_bg, fg=header_fg)
                    elif parent_bg == time_bg:
                        widget.configure(bg=time_bg, fg=fg_color)
                    else:
                        widget.configure(bg=parent_bg, fg=fg_color)
                
                elif isinstance(widget, tk.Button) and widget.cget('relief') == tk.FLAT:
                    widget.configure(bg=button_bg, fg=fg_color)
                
                elif isinstance(widget, tk.Entry):
                    widget.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
                
                elif isinstance(widget, tk.Text):
                    # Special handling for lyrics text widget
                    if hasattr(self, 'lyrics_text') and widget == self.lyrics_text:
                        widget.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color, selectbackground=header_bg)
                    else:
                        widget.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
                
                elif isinstance(widget, tk.Canvas):
                    widget.configure(bg=bg_color)
                
                # Recursively update children
                self.update_widget_colors(widget, bg_color, fg_color, header_bg, header_fg,
                                       button_bg, time_bg, progress_bg, progress_fill)
            except:
                # Skip widgets that don't support color changes
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TinyTunez(root)
    root.mainloop()
