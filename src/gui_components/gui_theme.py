"""
Central theme configuration for AccelScope GUI.
Provides spacing constants, font definitions, colors, and ttk style setup.
"""
from tkinter import ttk

# Padding constants
PAD_SM = 2   # Tight spacing (within groups)
PAD_MD = 5   # Standard widget spacing
PAD_LG = 10  # Section/dialog edge spacing

# Font definitions
FONT_TITLE = ("Helvetica", 14, "bold")
FONT_HEADING = ("Helvetica", 12, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)

# Status bar colors
COLOR_STATUS_BG = "#2e7d32"
COLOR_STATUS_FG = "#ffffff"

# Pane minimum sizes (pixels)
PANE_MIN_BROWSER = 150
PANE_MIN_VIEWER = 300
PANE_MIN_INFO = 150


def apply_theme(root):
    """Apply the clam theme with custom style overrides to the root window."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # General frame/label tweaks
    style.configure("TFrame", relief="flat")
    style.configure("TLabel", padding=PAD_SM)
    style.configure("TButton", padding=(PAD_MD, PAD_SM))
    style.configure("TCheckbutton", padding=PAD_SM)

    # Custom style for the status bar
    style.configure(
        "StatusBar.TLabel",
        background=COLOR_STATUS_BG,
        foreground=COLOR_STATUS_FG,
        padding=(PAD_MD, PAD_SM),
    )
