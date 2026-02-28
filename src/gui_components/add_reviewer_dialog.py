import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from gui_components.gui_theme import PAD_MD, PAD_LG, FONT_BODY
from models.user_config import UserConfig


class AddReviewerDialog(tk.Toplevel):
    """Dialog for adding a reviewer to a project."""

    def __init__(self, parent, existing_users):
        """
        Args:
            parent: Parent window.
            existing_users: List of existing UserConfig objects.
        """
        super().__init__(parent)
        self.title("Add Reviewer")
        self.result_ready = False
        self.result_user_config = None

        self._existing_usernames = {u.username for u in existing_users}

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=PAD_LG)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Username:", font=FONT_BODY).grid(
            row=0, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(frame, textvariable=self.username_var)
        self.username_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(frame, text="Display Name:", font=FONT_BODY).grid(
            row=1, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.display_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.display_name_var).grid(
            row=1, column=1, columnspan=2, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(frame, text="Alias:", font=FONT_BODY).grid(
            row=2, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.alias_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.alias_var, width=8).grid(
            row=2, column=1, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(frame, text="Data Root:", font=FONT_BODY).grid(
            row=3, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.data_root_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.data_root_var).grid(
            row=3, column=1, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)
        ttk.Button(frame, text="Browse", command=self._browse_data_root).grid(
            row=3, column=2, padx=PAD_MD, pady=PAD_MD)
        ttk.Label(frame, text="(optional)", foreground="gray").grid(
            row=4, column=1, sticky=tk.W, padx=PAD_MD)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=PAD_LG, pady=(0, PAD_LG))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=PAD_MD)
        ttk.Button(btn_frame, text="Add", command=self._save).pack(side=tk.RIGHT, padx=PAD_MD)

        self.username_entry.focus_set()
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _browse_data_root(self):
        directory = filedialog.askdirectory()
        if directory:
            self.data_root_var.set(directory)

    def _save(self):
        """Validate inputs and save results."""
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Validation Error", "Username is required.", parent=self)
            self.username_entry.focus_set()
            return

        if username in self._existing_usernames:
            messagebox.showwarning(
                "Duplicate Username",
                f"A reviewer with username '{username}' already exists in this project.",
                parent=self
            )
            self.username_entry.focus_set()
            return

        display_name = self.display_name_var.get().strip() or None
        alias = self.alias_var.get().strip() or None
        data_root = self.data_root_var.get().strip() or ""

        self.result_user_config = UserConfig(
            username=username,
            display_name=display_name,
            alias=alias,
            data_root=data_root,
        )
        self.result_ready = True
        self.destroy()
