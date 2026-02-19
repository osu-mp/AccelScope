import os
import tkinter as tk
from tkinter import ttk

from gui_components.gui_theme import PAD_LG


class OutputProgressDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Generating Output")

        self.progress_label = ttk.Label(self, text="Preparing output generation...")
        self.progress_label.pack(pady=PAD_LG)

        self.progress_bar = ttk.Progressbar(self, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=PAD_LG, pady=PAD_LG)

        self.cancel_button = ttk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=PAD_LG)

        self.cancelled = False

    def update_progress(self, current, total, file_path):
        """Update progress bar and label. Called from main thread via after()."""
        if total > 0:
            self.progress_bar['value'] = (current / total) * 100
        filename = os.path.basename(file_path) if file_path else ""
        if current < total:
            self.progress_label.config(text=f"Processing file {current + 1} of {total}: {filename}")
        else:
            self.progress_label.config(text="Finalizing output...")

    def cancel(self):
        self.cancelled = True
        self.destroy()
