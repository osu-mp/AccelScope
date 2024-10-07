import tkinter as tk
from tkinter import ttk

class HotkeyDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Hotkeys")
        self.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        # Create a label for the title
        title_label = ttk.Label(self, text="Available Hotkeys", font=("Helvetica", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        # Define hotkeys and descriptions
        hotkeys = [
            ("F", "Zoom to fit all labels"),
            ("Up Arrow", "Zoom in"),
            ("Down Arrow", "Zoom out"),
            ("Left Arrow", "Pan left"),
            ("Right Arrow", "Pan right"),
            ("Delete", "Delete selected label")
        ]

        # Create table headers
        header_font = ("Helvetica", 12, "bold")
        hotkey_header = ttk.Label(self, text="Hotkey", font=header_font)
        description_header = ttk.Label(self, text="Description", font=header_font)
        hotkey_header.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        description_header.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Create table rows for each hotkey
        for i, (hotkey, description) in enumerate(hotkeys, start=2):
            hotkey_label = ttk.Label(self, text=hotkey)
            description_label = ttk.Label(self, text=description)
            hotkey_label.grid(row=i, column=0, padx=10, pady=2, sticky="w")
            description_label.grid(row=i, column=1, padx=10, pady=2, sticky="w")

        # Add a Close button to close the dialog
        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.grid(row=i + 1, column=0, columnspan=2, pady=(10, 10))
