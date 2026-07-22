"""
Modern Dark Slate Design System for Tkinter.
"""

class Theme:
    # Background Colors
    BG_DARK = "#0F172A"       # Deep Slate Background
    BG_SIDEBAR = "#1E293B"    # Sidebar Background
    BG_CARD = "#1E293B"       # Card / Container Frame
    BG_CARD_HOVER = "#334155" # Card Hover
    BG_INPUT = "#0F172A"      # Input Field Background

    # Primary Accent Colors
    PRIMARY = "#3B82F6"       # Vivid Blue Accent
    PRIMARY_HOVER = "#2563EB" # Primary Hover
    SUCCESS = "#10B981"       # Emerald Green Success
    WARNING = "#F59E0B"       # Amber Warning
    DANGER = "#EF4444"        # Red Danger

    # Text Colors
    TEXT_MAIN = "#F8FAFC"      # White/Off-white Primary Text
    TEXT_MUTED = "#94A3B8"     # Muted Gray Secondary Text
    TEXT_SIDEBAR = "#CBD5E1"   # Sidebar Navigation Text

    # Borders & Dividers
    BORDER = "#334155"

    # Fonts
    FONT_FAMILY = "Segoe UI" if True else "Helvetica"
    FONT_TITLE = (FONT_FAMILY, 16, "bold")
    FONT_SUBTITLE = (FONT_FAMILY, 12, "bold")
    FONT_BODY = (FONT_FAMILY, 10, "normal")
    FONT_SMALL = (FONT_FAMILY, 9, "normal")
    FONT_MONO = ("Consolas", 9, "normal")
