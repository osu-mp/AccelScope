import tkinter as tk
from tkinter import ttk, messagebox

from gui_components.gui_theme import PAD_MD, PAD_LG, FONT_BODY, FONT_SMALL


class MyProfileDialog(tk.Toplevel):
    """Dialog for the current user to update their display name and alias."""

    def __init__(self, parent, current_username, current_display_name, current_alias):
        """
        Args:
            parent: Parent window.
            current_username: OS username (read-only, shown for reference).
            current_display_name: Current display name string.
            current_alias: Current alias string.
        """
        super().__init__(parent)
        self.title("My Profile")
        self.resizable(False, False)
        self.result_ready = False
        self.result_display_name = None
        self.result_alias = None

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=PAD_LG)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Username:", font=FONT_BODY).grid(
            row=0, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        ttk.Label(frame, text=current_username, font=FONT_BODY, foreground="gray").grid(
            row=0, column=1, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        ttk.Label(frame, text="(OS username, read-only)", font=FONT_SMALL, foreground="gray").grid(
            row=0, column=2, sticky=tk.W, padx=PAD_MD)

        ttk.Label(frame, text="Display Name:", font=FONT_BODY).grid(
            row=1, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.display_name_var = tk.StringVar(value=current_display_name or "")
        self.display_name_entry = ttk.Entry(frame, textvariable=self.display_name_var, width=30)
        self.display_name_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(frame, text="Alias:", font=FONT_BODY).grid(
            row=2, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.alias_var = tk.StringVar(value=current_alias or "")
        ttk.Entry(frame, textvariable=self.alias_var, width=8).grid(
            row=2, column=1, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        ttk.Label(frame, text="Short label shown on verification badges", font=FONT_SMALL, foreground="gray").grid(
            row=2, column=2, sticky=tk.W, padx=PAD_MD)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD_LG))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=PAD_MD)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=PAD_MD)

        self.display_name_entry.focus_set()
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _save(self):
        display_name = self.display_name_var.get().strip()
        alias = self.alias_var.get().strip()

        if not display_name:
            messagebox.showwarning("Validation Error", "Display name cannot be empty.", parent=self)
            self.display_name_entry.focus_set()
            return

        self.result_display_name = display_name
        self.result_alias = alias
        self.result_ready = True
        self.destroy()
