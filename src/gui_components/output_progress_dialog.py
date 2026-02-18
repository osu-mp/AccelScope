import tkinter as tk
from tkinter import ttk

from gui_components.gui_theme import PAD_LG


class OutputProgressDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Generating Output")

        self.progress_label = ttk.Label(self, text="Generating output, please wait...")
        self.progress_label.pack(pady=PAD_LG)

        self.progress_bar = ttk.Progressbar(self, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=PAD_LG, pady=PAD_LG)
        self.progress_bar.start()

        self.cancel_button = ttk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=PAD_LG)

        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        self.destroy()
