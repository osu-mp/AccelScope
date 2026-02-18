import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.label = ttk.Label(self, anchor="w", text="Ready", style="StatusBar.TLabel")
        self.label.pack(fill=tk.X, expand=True)

    def set(self, text):
        self.label.config(text=text)

    def clear(self):
        self.label.config(text="")
