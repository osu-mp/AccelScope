import tkinter as tk
from tkinter import ttk

class OutputProgressDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Generating Output")

        self.progress_label = ttk.Label(self, text="Generating output, please wait...")
        self.progress_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)
        self.progress_bar.start()

        self.cancel_button = ttk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=10)

        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        self.destroy()
