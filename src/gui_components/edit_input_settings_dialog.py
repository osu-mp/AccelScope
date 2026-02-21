import re
import tkinter as tk
from tkinter import ttk, messagebox

from gui_components.gui_theme import PAD_SM, PAD_MD, PAD_LG, FONT_BODY, FONT_HEADING
from models.input_settings import InputType


class EditInputSettingsDialog(tk.Toplevel):
    """Dialog for editing project input settings (type, frequency, y-range, regex, plot title)."""

    def __init__(self, parent, input_settings, y_range, individual_id_regex, plot_title_format):
        """
        Args:
            parent: Parent window.
            input_settings: InputSettings instance from project config.
            y_range: List [y_min, y_max].
            individual_id_regex: Regex string with named group 'individual'.
            plot_title_format: Template string using {individual} and {filename_stem}.
        """
        super().__init__(parent)
        self.title("Edit Input Settings")
        self.result_ready = False

        # Result fields
        self.result_input_settings = None
        self.result_y_range = None
        self.result_individual_id_regex = None
        self.result_plot_title_format = None

        # Main frame
        frame = ttk.Frame(self, padding=PAD_LG)
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        # Input Type
        ttk.Label(frame, text="Input Type:", font=FONT_BODY).grid(
            row=row, column=0, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        self._input_type_var = tk.StringVar(value=input_settings.input_type.value)
        input_type_combo = ttk.Combobox(frame, textvariable=self._input_type_var,
                                        values=[t.value for t in InputType],
                                        state="readonly", width=25)
        input_type_combo.grid(row=row, column=1, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        row += 1

        # Input Frequency
        ttk.Label(frame, text="Input Frequency (Hz):", font=FONT_BODY).grid(
            row=row, column=0, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        self._freq_var = tk.IntVar(value=input_settings.input_frequency)
        freq_spin = ttk.Spinbox(frame, from_=1, to=256, increment=1,
                                textvariable=self._freq_var, width=10)
        freq_spin.grid(row=row, column=1, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        row += 1

        # Y-axis Min
        ttk.Label(frame, text="Y-axis Min:", font=FONT_BODY).grid(
            row=row, column=0, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        self._y_min_var = tk.DoubleVar(value=y_range[0])
        y_min_spin = ttk.Spinbox(frame, from_=-100, to=100, increment=0.5,
                                 textvariable=self._y_min_var, width=10)
        y_min_spin.grid(row=row, column=1, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        row += 1

        # Y-axis Max
        ttk.Label(frame, text="Y-axis Max:", font=FONT_BODY).grid(
            row=row, column=0, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        self._y_max_var = tk.DoubleVar(value=y_range[1])
        y_max_spin = ttk.Spinbox(frame, from_=-100, to=100, increment=0.5,
                                 textvariable=self._y_max_var, width=10)
        y_max_spin.grid(row=row, column=1, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        row += 1

        # Individual ID Regex
        ttk.Label(frame, text="Individual ID Regex:", font=FONT_BODY).grid(
            row=row, column=0, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        self._regex_var = tk.StringVar(value=individual_id_regex)
        regex_entry = ttk.Entry(frame, textvariable=self._regex_var, width=40)
        regex_entry.grid(row=row, column=1, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        row += 1

        # Plot Title Format
        ttk.Label(frame, text="Plot Title Format:", font=FONT_BODY).grid(
            row=row, column=0, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        self._title_format_var = tk.StringVar(value=plot_title_format)
        title_entry = ttk.Entry(frame, textvariable=self._title_format_var, width=40)
        title_entry.grid(row=row, column=1, sticky=tk.W, padx=PAD_SM, pady=PAD_SM)
        row += 1

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=PAD_LG)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=PAD_MD)
        ttk.Button(button_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=PAD_MD)

    def _save(self):
        """Validate inputs and save results."""
        # Validate frequency
        try:
            freq = self._freq_var.get()
        except (tk.TclError, ValueError):
            messagebox.showwarning("Invalid Frequency", "Frequency must be a positive integer.", parent=self)
            return
        if freq <= 0:
            messagebox.showwarning("Invalid Frequency", "Frequency must be greater than 0.", parent=self)
            return

        # Validate y-range
        try:
            y_min = self._y_min_var.get()
            y_max = self._y_max_var.get()
        except (tk.TclError, ValueError):
            messagebox.showwarning("Invalid Y Range", "Y-axis min and max must be numbers.", parent=self)
            return
        if y_min >= y_max:
            messagebox.showwarning("Invalid Y Range", "Y-axis min must be less than max.", parent=self)
            return

        # Validate regex
        regex_str = self._regex_var.get().strip()
        try:
            re.compile(regex_str)
        except re.error as e:
            messagebox.showwarning("Invalid Regex", f"Regex error: {e}", parent=self)
            return

        # Validate plot title format
        title_format = self._title_format_var.get().strip()
        if not title_format:
            messagebox.showwarning("Empty Title Format", "Plot title format cannot be empty.", parent=self)
            return

        # Build results
        from models.input_settings import InputSettings
        self.result_input_settings = InputSettings(
            input_type=InputType(self._input_type_var.get()),
            input_frequency=freq,
        )
        self.result_y_range = [y_min, y_max]
        self.result_individual_id_regex = regex_str
        self.result_plot_title_format = title_format
        self.result_ready = True
        self.destroy()
