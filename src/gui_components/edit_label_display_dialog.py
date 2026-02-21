import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

from gui_components.gui_theme import PAD_SM, PAD_MD, PAD_LG, FONT_BODY
from models.label_display import LabelDisplay


class EditLabelDisplayDialog(tk.Toplevel):
    """Dialog for editing behavior types (label_display) in a project."""

    def __init__(self, parent, label_displays, label_usage_counts=None):
        """
        Args:
            parent: Parent window.
            label_displays: List of LabelDisplay objects to edit (will be copied).
            label_usage_counts: Dict mapping display_name -> count of labels using it.
        """
        super().__init__(parent)
        self.title("Edit Behavior Labels")
        self.result_ready = False
        self.result_label_displays = None
        self._label_usage_counts = label_usage_counts or {}
        self._rows = []

        # Header row
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=PAD_LG, pady=(PAD_LG, PAD_SM))
        ttk.Label(header_frame, text="Name", font=FONT_BODY, width=15).pack(side=tk.LEFT, padx=PAD_SM)
        ttk.Label(header_frame, text="Color", font=FONT_BODY, width=6).pack(side=tk.LEFT, padx=PAD_SM)
        ttk.Label(header_frame, text="Alpha", font=FONT_BODY, width=6).pack(side=tk.LEFT, padx=PAD_SM)
        ttk.Label(header_frame, text="Output Value", font=FONT_BODY, width=10).pack(side=tk.LEFT, padx=PAD_SM)

        # Scrollable area for rows
        self._rows_frame = ttk.Frame(self)
        self._rows_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=PAD_SM)

        for ld in label_displays:
            self._add_row(ld.display_name, ld.color, ld.alpha, ld.output_value)

        # Add / Cancel / Save buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=PAD_LG, pady=PAD_LG)
        ttk.Button(button_frame, text="Add Behavior", command=self._add_new_row).pack(side=tk.LEFT, padx=PAD_MD)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=PAD_MD)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=PAD_MD)

    def _add_row(self, name, color, alpha, output_value):
        """Add an editable row for one behavior."""
        row_frame = ttk.Frame(self._rows_frame)
        row_frame.pack(fill=tk.X, pady=PAD_SM)

        name_var = tk.StringVar(value=name)
        name_entry = ttk.Entry(row_frame, textvariable=name_var, width=15)
        name_entry.pack(side=tk.LEFT, padx=PAD_SM)

        color_var = tk.StringVar(value=color)
        color_btn = tk.Button(row_frame, text="  ", bg=color, width=4,
                              command=lambda: self._pick_color(color_btn, color_var))
        color_btn.pack(side=tk.LEFT, padx=PAD_SM)

        alpha_var = tk.DoubleVar(value=alpha)
        alpha_spin = ttk.Spinbox(row_frame, from_=0.0, to=1.0, increment=0.1,
                                 textvariable=alpha_var, width=5)
        alpha_spin.pack(side=tk.LEFT, padx=PAD_SM)

        output_var = tk.IntVar(value=output_value)
        output_entry = ttk.Entry(row_frame, textvariable=output_var, width=8)
        output_entry.pack(side=tk.LEFT, padx=PAD_SM)

        delete_btn = ttk.Button(row_frame, text="X", width=3,
                                command=lambda: self._delete_row(row_frame))
        delete_btn.pack(side=tk.LEFT, padx=PAD_SM)

        row_data = {
            "frame": row_frame,
            "name_var": name_var,
            "color_var": color_var,
            "alpha_var": alpha_var,
            "output_var": output_var,
            "original_name": name,
        }
        self._rows.append(row_data)

    def _pick_color(self, button, color_var):
        """Open color chooser and update button background."""
        result = colorchooser.askcolor(color=color_var.get(), title="Choose Color")
        if result and result[1]:
            color_var.set(result[1])
            button.configure(bg=result[1])

    def _add_new_row(self):
        """Add a new behavior with defaults."""
        existing_outputs = set()
        for row in self._rows:
            try:
                existing_outputs.add(row["output_var"].get())
            except (tk.TclError, ValueError):
                pass
        next_val = max(existing_outputs, default=0) + 1
        self._add_row("New Behavior", "#808080", 0.3, next_val)

    def _delete_row(self, row_frame):
        """Delete a behavior row, warning if labels use it."""
        row_data = None
        for r in self._rows:
            if r["frame"] is row_frame:
                row_data = r
                break
        if not row_data:
            return

        name = row_data["original_name"]
        count = self._label_usage_counts.get(name, 0)
        if count > 0:
            if not messagebox.askyesno(
                "Behavior In Use",
                f'"{name}" is used by {count} label(s). Delete anyway?'
            ):
                return

        row_frame.destroy()
        self._rows.remove(row_data)

    def _save(self):
        """Validate and save the edited label displays."""
        names = []
        displays = []
        for row in self._rows:
            name = row["name_var"].get().strip()
            if not name:
                messagebox.showwarning("Empty Name", "Behavior names cannot be empty.")
                return
            if name in names:
                messagebox.showwarning("Duplicate Name", f'Duplicate behavior name: "{name}"')
                return
            names.append(name)

            try:
                alpha = row["alpha_var"].get()
            except (tk.TclError, ValueError):
                alpha = 0.3

            try:
                output_value = row["output_var"].get()
            except (tk.TclError, ValueError):
                output_value = 0

            displays.append(LabelDisplay(
                display_name=name,
                color=row["color_var"].get(),
                alpha=alpha,
                output_value=output_value,
            ))

        self.result_label_displays = displays
        self.result_ready = True
        self.destroy()
