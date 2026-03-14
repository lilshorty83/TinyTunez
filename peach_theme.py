"""
Peach Theme for TinyTunez Music Player
A warm, soft peach color scheme with complementary colors
"""

# Main color palette
PEACH_THEME = {
    # Primary colors
    'primary': '#FFB366',          # Soft peach orange
    'primary_light': '#FFC299',    # Lighter peach
    'primary_dark': '#E8994D',     # Darker peach
    'primary_variant': '#FFA852',  # Peach variant
    
    # Background colors
    'bg_primary': '#FFF8F3',       # Very light peach background
    'bg_secondary': '#FFF0E5',     # Light peach background
    'bg_tertiary': '#FFE8D7',      # Medium light peach
    'bg_accent': '#FFD4B3',        # Peach accent
    'bg_header': '#FFE0CC',        # Header background color
    
    # Surface colors
    'surface': '#FFFFFF',          # White surface
    'surface_variant': '#FFFAF7',  # Very warm white
    'surface_container': '#FFF5ED', # Warm container
    'surface_container_low': '#FFFBF8', # Low elevation container
    'surface_container_high': '#FFEFDF', # High elevation container
    
    # Text colors
    'text_primary': '#2D1810',      # Dark brown text
    'text_secondary': '#5C3D2E',     # Medium brown text
    'text_tertiary': '#8B6F47',      # Light brown text
    'text_disabled': '#A08060',      # Disabled text
    'text_on_primary': '#FFFFFF',    # White text on peach
    'text_inverse': '#FFFFFF',       # Inverted text
    
    # Border and outline colors
    'outline': '#E8D4C3',           # Soft peach outline
    'outline_variant': '#F5E6D8',   # Light outline
    'border': '#D4B5A0',            # Border color
    'divider': '#E8D4C3',           # Divider color
    
    # Interactive colors
    'hover': '#FFA852',             # Hover state
    'pressed': '#E8994D',           # Pressed state
    'focused': '#FFB366',           # Focused state
    'selected': '#FFB366',          # Selected state
    'drag': '#FFC299',              # Drag state
    
    # Status colors
    'success': '#66BB6A',           # Green for success
    'warning': '#FFA726',           # Orange for warning
    'error': '#EF5350',             # Red for error
    'info': '#42A5F5',              # Blue for info
    
    # Widget-specific colors
    'button_bg': '#FFB366',         # Button background
    'button_fg': '#FFFFFF',         # Button text
    'button_hover': '#FFA852',      # Button hover
    'button_pressed': '#E8994D',    # Button pressed
    
    'input_bg': '#FFFFFF',          # Input background
    'input_fg': '#2D1810',          # Input text
    'input_border': '#D4B5A0',      # Input border
    'input_focus': '#FFB366',      # Input focus
    
    'scrollbar_bg': '#FFE8D7',      # Scrollbar background
    'scrollbar_thumb': '#FFB366',   # Scrollbar thumb
    'scrollbar_hover': '#FFA852',   # Scrollbar hover
    
    # Scale (slider) colors
    'scale_bg': '#FFF0E5',           # Scale background
    'scale_trough': '#FFE8D7',      # Scale trough
    'scale_active': '#FFB366',       # Scale active/hover
    'scale_fg': '#2D1810',           # Scale text/foreground
    'scale_border': '#D4B5A0',       # Scale border (same as input border)
    
    'treeview_bg': '#FFFFFF',       # Treeview background
    'treeview_fg': '#2D1810',       # Treeview text
    'treeview_selected': '#FFB366',  # Treeview selection
    'treeview_heading': '#FFF0E5',  # Treeview heading
    
    'visualization_bg': '#000000',  # Always black for music visualization
    
    'menu_bg': '#FFFFFF',           # Menu background
    'menu_fg': '#2D1810',           # Menu text
    'menu_hover': '#FFF0E5',        # Menu hover
}

# Font configurations
PEACH_FONTS = {
    'default': ('Segoe UI', 10),
    'heading': ('Segoe UI', 12, 'bold'),
    'title': ('Segoe UI', 16, 'bold'),
    'small': ('Segoe UI', 9),
    'mono': ('Consolas', 10),
    'button': ('Segoe UI', 10),
    'label': ('Segoe UI', 10),
    'entry': ('Segoe UI', 10),
}

# Style configurations for ttk widgets
PEACH_TTK_STYLES = {
    'TFrame': {
        'background': PEACH_THEME['bg_primary'],
        'borderwidth': 0,
        'relief': 'flat',
    },
    'TLabel': {
        'background': PEACH_THEME['bg_primary'],
        'foreground': PEACH_THEME['text_primary'],
        'font': PEACH_FONTS['default'],
    },
    'TButton': {
        'background': PEACH_THEME['button_bg'],
        'foreground': PEACH_THEME['button_fg'],
        'font': PEACH_FONTS['button'],
        'borderwidth': 1,
        'relief': 'raised',
        'focuscolor': PEACH_THEME['focused'],
    },
    'TEntry': {
        'background': PEACH_THEME['input_bg'],
        'foreground': PEACH_THEME['input_fg'],
        'font': PEACH_FONTS['entry'],
        'borderwidth': 1,
        'relief': 'solid',
        'insertcolor': PEACH_THEME['text_primary'],
    },
    'TScrollbar': {
        'background': PEACH_THEME['scrollbar_thumb'],
        'troughcolor': PEACH_THEME['scrollbar_bg'],
        'bordercolor': PEACH_THEME['scrollbar_bg'],
        'arrowcolor': PEACH_THEME['text_secondary'],
        'lightcolor': PEACH_THEME['primary_light'],
        'darkcolor': PEACH_THEME['primary_dark'],
        'relief': 'raised',
    },
    'Vertical.TScrollbar': {
        'background': PEACH_THEME['scrollbar_thumb'],
        'troughcolor': PEACH_THEME['scrollbar_bg'],
        'bordercolor': PEACH_THEME['scrollbar_bg'],
        'arrowcolor': PEACH_THEME['text_secondary'],
        'lightcolor': PEACH_THEME['primary_light'],
        'darkcolor': PEACH_THEME['primary_dark'],
        'relief': 'raised',
    },
    'Horizontal.TScrollbar': {
        'background': PEACH_THEME['scrollbar_thumb'],
        'troughcolor': PEACH_THEME['scrollbar_bg'],
        'bordercolor': PEACH_THEME['scrollbar_bg'],
        'arrowcolor': PEACH_THEME['text_secondary'],
        'lightcolor': PEACH_THEME['primary_light'],
        'darkcolor': PEACH_THEME['primary_dark'],
        'relief': 'raised',
    },
    'Treeview': {
        'background': PEACH_THEME['treeview_bg'],
        'foreground': PEACH_THEME['treeview_fg'],
        'font': PEACH_FONTS['default'],
        'selectbackground': PEACH_THEME['treeview_selected'],
        'selectforeground': PEACH_THEME['text_on_primary'],
    },
    'Treeview.Heading': {
        'background': PEACH_THEME['treeview_heading'],
        'foreground': PEACH_THEME['text_primary'],
        'font': PEACH_FONTS['heading'],
        'relief': 'raised',
    },
    'TNotebook': {
        'background': PEACH_THEME['bg_primary'],
        'borderwidth': 0,
    },
    'TNotebook.Tab': {
        'background': PEACH_THEME['bg_secondary'],
        'foreground': PEACH_THEME['text_primary'],
        'font': PEACH_FONTS['default'],
        'padding': [12, 8],
    },
    'TMenubutton': {
        'background': PEACH_THEME['menu_bg'],
        'foreground': PEACH_THEME['menu_fg'],
        'font': PEACH_FONTS['default'],
        'relief': 'raised',
    },
}

# Style maps for interactive states
PEACH_TTK_MAPS = {
    'TButton': {
        'background': [
            ('active', PEACH_THEME['button_hover']),
            ('pressed', PEACH_THEME['button_pressed']),
            ('!active', PEACH_THEME['button_bg']),
        ],
        'foreground': [
            ('active', PEACH_THEME['button_fg']),
            ('pressed', PEACH_THEME['button_fg']),
            ('!active', PEACH_THEME['button_fg']),
        ],
    },
    'TScrollbar': {
        'background': [
            ('active', PEACH_THEME['scrollbar_thumb']),
            ('!active', PEACH_THEME['scrollbar_thumb']),
            ('pressed', PEACH_THEME['primary_dark']),
            ('hover', PEACH_THEME['scrollbar_hover']),
        ],
        'arrowcolor': [
            ('active', PEACH_THEME['text_secondary']),
            ('!active', PEACH_THEME['text_secondary']),
            ('pressed', PEACH_THEME['text_primary']),
            ('hover', PEACH_THEME['text_primary']),
        ],
    },
    'TNotebook.Tab': {
        'background': [
            ('selected', PEACH_THEME['bg_primary']),
            ('!selected', PEACH_THEME['bg_secondary']),
        ],
    },
}

def apply_peach_theme(style):
    """
    Apply the peach theme to ttk widgets.
    
    Args:
        style: ttk.Style() instance
    """
    # Configure all widget styles
    for widget_type, config in PEACH_TTK_STYLES.items():
        try:
            style.configure(widget_type, **config)
        except Exception as e:
            print(f"Warning: Could not configure {widget_type}: {e}")
    
    # Configure state maps
    for widget_type, state_map in PEACH_TTK_MAPS.items():
        try:
            style.map(widget_type, **state_map)
        except Exception as e:
            print(f"Warning: Could not map {widget_type}: {e}")
    
    print("Peach theme applied successfully!")

def get_peach_color(color_name):
    """
    Get a color from the peach theme palette.
    
    Args:
        color_name: Name of the color
        
    Returns:
        Color hex code or None if not found
    """
    return PEACH_THEME.get(color_name)

def get_peach_font(font_name):
    """
    Get a font from the peach theme font configuration.
    
    Args:
        font_name: Name of the font
        
    Returns:
        Font tuple or None if not found
    """
    return PEACH_FONTS.get(font_name)

# Theme metadata
THEME_INFO = {
    'name': 'Peach',
    'description': 'A warm, soft peach color scheme with complementary colors',
    'version': '1.0.0',
    'author': 'TinyTunez',
    'colors': list(PEACH_THEME.keys()),
    'supports_dark_mode': False,
    'supports_light_mode': True,
    'primary_color': PEACH_THEME['primary'],
    'background_color': PEACH_THEME['bg_primary'],
    'text_color': PEACH_THEME['text_primary'],
}

if __name__ == "__main__":
    # Test the theme
    print(f"Theme: {THEME_INFO['name']}")
    print(f"Description: {THEME_INFO['description']}")
    print(f"Primary Color: {THEME_INFO['primary_color']}")
    print(f"Background Color: {THEME_INFO['background_color']}")
    print(f"Text Color: {THEME_INFO['text_color']}")
    print(f"Total colors defined: {len(PEACH_THEME)}")
    print(f"Total fonts defined: {len(PEACH_FONTS)}")
    print(f"Total ttk styles defined: {len(PEACH_TTK_STYLES)}")
