import tkinter as tk


class StatusBar(tk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.label = tk.Label(self, anchor="w", text="Ready", bg="green", fg="white")
        self.label.pack(fill=tk.X, expand=True)

    def set(self, text):
        self.label.config(text=text)

    def clear(self):
        self.label.config(text="")
