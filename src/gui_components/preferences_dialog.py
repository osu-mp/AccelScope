import tkinter as tk
from tkinter import ttk

from gui_components.gui_theme import PAD_MD, PAD_LG


class PreferencesDialog(tk.Toplevel):
    """Dialog for editing user preferences."""

    def __init__(self, parent, comment_save_delay=500, info_pane_max_width=300):
        super().__init__(parent)
        self.title("Preferences")
        self.result_ready = False
        self.result_comment_save_delay = None
        self.result_info_pane_max_width = None

        # Comment auto-save delay
        ttk.Label(self, text="Comment auto-save delay (ms):").grid(
            row=0, column=0, sticky=tk.W, padx=PAD_LG, pady=PAD_MD)
        self.delay_var = tk.IntVar(value=comment_save_delay)
        ttk.Spinbox(self, from_=100, to=2000, increment=100,
                     textvariable=self.delay_var, width=8).grid(
            row=0, column=1, sticky=tk.EW, padx=PAD_LG, pady=PAD_MD)

        # Info pane max width
        ttk.Label(self, text="Info pane max width (px):").grid(
            row=1, column=0, sticky=tk.W, padx=PAD_LG, pady=PAD_MD)
        self.max_width_var = tk.IntVar(value=info_pane_max_width)
        ttk.Spinbox(self, from_=150, to=600, increment=50,
                     textvariable=self.max_width_var, width=8).grid(
            row=1, column=1, sticky=tk.EW, padx=PAD_LG, pady=PAD_MD)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=PAD_LG)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=PAD_MD)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=PAD_MD)

        self.grid_columnconfigure(1, weight=1)

    def _save(self):
        try:
            self.result_comment_save_delay = self.delay_var.get()
            self.result_info_pane_max_width = self.max_width_var.get()
        except (tk.TclError, ValueError):
            return
        self.result_ready = True
        self.destroy()
