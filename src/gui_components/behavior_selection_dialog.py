import tkinter as tk
from tkinter import simpledialog, ttk


class BehaviorSelectionDialog(simpledialog.Dialog):
    """
    Prompt when user adds a new label to a file. Creates a drop-down of available behaviors and
    returns user's selection or None
    """
    def __init__(self, parent, behaviors, title="Select Behavior"):
        self.behaviors = behaviors
        self.var = None
        self.result = None
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text="Select Behavior:").grid(row=0)
        self.var = tk.StringVar(master)
        self.var.set(self.behaviors[0] if self.behaviors else "")  # Set default value
        dropdown = ttk.Combobox(master, textvariable=self.var, values=self.behaviors, state='readonly')
        dropdown.grid(row=0, column=1)
        return dropdown  # return the dropdown as the initial focus widget

    def apply(self):
        # Set the result from the dialog to the selected option
        self.result = self.var.get() if self.var.get() in self.behaviors else None
