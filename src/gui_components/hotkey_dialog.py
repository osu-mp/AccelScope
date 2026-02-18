import tkinter as tk
from tkinter import ttk

from gui_components.gui_theme import PAD_SM, PAD_MD, PAD_LG, FONT_TITLE, FONT_HEADING


class HotkeyDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Hotkeys")
        self.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        # Create a label for the title
        title_label = ttk.Label(self, text="Available Hotkeys", font=FONT_TITLE)
        title_label.grid(row=0, column=0, columnspan=2, pady=(PAD_LG, PAD_MD))

        # Define hotkeys and descriptions
        hotkeys = [
            ("A", "Zoom out to show all data"),
            ("F", "Zoom in fit all labels"),
            ("Up Arrow", "Zoom in"),
            ("Down Arrow", "Zoom out"),
            ("Left Arrow", "Pan left"),
            ("Right Arrow", "Pan right"),
            ("Delete", "Delete selected label")
        ]

        # Create table headers
        hotkey_header = ttk.Label(self, text="Hotkey", font=FONT_HEADING)
        description_header = ttk.Label(self, text="Description", font=FONT_HEADING)
        hotkey_header.grid(row=1, column=0, padx=PAD_LG, pady=PAD_MD, sticky="w")
        description_header.grid(row=1, column=1, padx=PAD_LG, pady=PAD_MD, sticky="w")

        # Create table rows for each hotkey
        for i, (hotkey, description) in enumerate(hotkeys, start=2):
            hotkey_label = ttk.Label(self, text=hotkey)
            description_label = ttk.Label(self, text=description)
            hotkey_label.grid(row=i, column=0, padx=PAD_LG, pady=PAD_SM, sticky="w")
            description_label.grid(row=i, column=1, padx=PAD_LG, pady=PAD_SM, sticky="w")

        # Add a Close button to close the dialog
        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.grid(row=i + 1, column=0, columnspan=2, pady=(PAD_LG, PAD_LG))
