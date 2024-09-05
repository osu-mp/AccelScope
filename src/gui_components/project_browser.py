import tkinter as tk
from tkinter import ttk


class ProjectBrowser(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='red')  # Set background color

        # Use tk.PanedWindow instead of ttk.PanedWindow
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='red')
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create an internal frame for the actual browser content
        self.browser_frame = ttk.Frame(self.paned_window, width=200)
        self.browser_frame.pack(fill=tk.BOTH, expand=True)
        self.browser_frame.pack_propagate(False)  # Prevent shrinking

        # Add the internal frame to the paned window with minsize option
        self.paned_window.add(self.browser_frame, minsize=100)

        # Add a label for demonstration
        label = tk.Label(self.browser_frame, text='Project Browser', bg='red')
        label.pack()

        # Optionally create a dummy frame for the paned window to function correctly
        self.dummy_frame = ttk.Frame(self.paned_window, width=50)
        self.dummy_frame.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(self.dummy_frame)