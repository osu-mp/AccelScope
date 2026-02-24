import tkinter as tk
from tkinter import ttk

from gui_components.gui_theme import PAD_MD, PAD_LG, FONT_BODY


class VerificationThresholdDialog(tk.Toplevel):
    """Dialog to configure the verification threshold percentage."""

    def __init__(self, parent, current_threshold=1.0):
        super().__init__(parent)
        self.title("Verification Threshold")
        self.resizable(False, False)

        self.result_ready = False
        self.result_threshold = current_threshold

        frame = ttk.Frame(self, padding=PAD_LG)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Minimum percentage of reviewers required\nfor a file to be marked as verified (green):",
                  font=FONT_BODY, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, PAD_MD))

        spin_frame = ttk.Frame(frame)
        spin_frame.pack(fill=tk.X, pady=PAD_MD)

        self.threshold_var = tk.IntVar(value=int(current_threshold * 100))
        self.spinbox = ttk.Spinbox(spin_frame, from_=0, to=100, increment=10,
                                   textvariable=self.threshold_var, width=5)
        self.spinbox.pack(side=tk.LEFT)
        ttk.Label(spin_frame, text="%", font=FONT_BODY).pack(side=tk.LEFT, padx=PAD_MD)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(PAD_MD, 0))

        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.RIGHT, padx=PAD_MD)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)

    def _on_ok(self):
        try:
            value = int(self.threshold_var.get())
            value = max(0, min(100, value))
        except (ValueError, tk.TclError):
            value = 100
        self.result_threshold = value / 100.0
        self.result_ready = True
        self.destroy()
