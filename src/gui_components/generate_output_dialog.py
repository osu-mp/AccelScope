import logging
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType


class GenerateOutputDialog(tk.Toplevel):
    def __init__(self, parent, input_frequency=None):
        super().__init__(parent)
        self.title("Generate Output")

        self.output_settings = None
        self.output_directory = None
        self.result_ready = False

        # Row 0: Input Frequency (read-only label)
        freq_text = f"Input Frequency: {input_frequency} Hz" if input_frequency is not None else "Input Frequency: Unknown"
        ttk.Label(self, text=freq_text).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)

        # Row 1: Output Frequency Dropdown
        ttk.Label(self, text="Output Frequency (Hz):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_frequency_var = tk.StringVar(value="16")
        self.output_frequency_combo = ttk.Combobox(self, textvariable=self.output_frequency_var,
                                                   values=["1", "2", "4", "8", "16"], state="readonly")
        self.output_frequency_combo.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        # Row 2: Downsampling Method — 4 checkboxes
        ttk.Label(self, text="Downsampling Method:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        checkbox_frame = ttk.Frame(self)
        checkbox_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        self.ds_average_var = tk.BooleanVar(value=True)
        self.ds_nth_var = tk.BooleanVar(value=False)
        self.ds_min_var = tk.BooleanVar(value=False)
        self.ds_max_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(checkbox_frame, text="Average", variable=self.ds_average_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(checkbox_frame, text="Nth Value", variable=self.ds_nth_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(checkbox_frame, text="Min", variable=self.ds_min_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(checkbox_frame, text="Max", variable=self.ds_max_var).pack(side=tk.LEFT)

        # Row 3: Output Period
        ttk.Label(self, text="Output Period:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_period_var = tk.StringVar(value=OutputPeriod.ENTIRE_INPUT.value)
        self.output_period_combo = ttk.Combobox(self, textvariable=self.output_period_var,
                                                values=[e.value for e in OutputPeriod], state="readonly")
        self.output_period_combo.grid(row=3, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        self.output_period_var.trace_add("write", self._on_output_period_changed)

        # Row 4: Buffer Minutes
        ttk.Label(self, text="Buffer Minutes:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.buffer_minutes_var = tk.IntVar(value=5)
        self.buffer_minutes_spinbox = ttk.Spinbox(self, from_=0, to=60, textvariable=self.buffer_minutes_var)
        self.buffer_minutes_spinbox.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        # Row 5: Round to Minutes
        ttk.Label(self, text="Round to Minutes:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.round_to_minutes_var = tk.IntVar(value=1)
        self.round_to_minutes_spinbox = ttk.Spinbox(self, from_=0, to=60, textvariable=self.round_to_minutes_var)
        self.round_to_minutes_spinbox.grid(row=5, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        # Row 6: Output Directory + Browse
        ttk.Label(self, text="Output Directory:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_directory_entry = ttk.Entry(self)
        self.output_directory_entry.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(self, text="Browse", command=self.select_output_directory).grid(row=6, column=2, padx=5, pady=5)

        # Row 7: Cancel / Generate Output buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate Output", command=self.generate_output).pack(side=tk.LEFT, padx=5)

        # Configure column layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=0)

        # Tooltip labels for buffer/round fields
        self._buffer_tooltip = None
        self._round_tooltip = None
        self._setup_tooltips()

        # Set initial state of buffer/round fields
        self._on_output_period_changed()

    def _on_output_period_changed(self, *args):
        """Enable/disable buffer and round fields based on output period selection."""
        is_labeled_buffer = self.output_period_var.get() == OutputPeriod.LABELED_WITH_BUFFER.value
        state = "normal" if is_labeled_buffer else "disabled"
        self.buffer_minutes_spinbox.configure(state=state)
        self.round_to_minutes_spinbox.configure(state=state)

    def _setup_tooltips(self):
        """Bind hover tooltips to buffer and round fields."""
        tooltip_text = "Only applicable when output period is 'Labeled with Buffer'"
        self._bind_tooltip(self.buffer_minutes_spinbox, tooltip_text)
        self._bind_tooltip(self.round_to_minutes_spinbox, tooltip_text)

    def _bind_tooltip(self, widget, text):
        """Bind enter/leave events to show/hide a tooltip on the widget."""
        tooltip_label = None

        def show_tooltip(event):
            nonlocal tooltip_label
            if str(widget.cget("state")) == "disabled":
                tooltip_label = tk.Toplevel(widget)
                tooltip_label.wm_overrideredirect(True)
                x = widget.winfo_rootx() + 20
                y = widget.winfo_rooty() + widget.winfo_height()
                tooltip_label.wm_geometry(f"+{x}+{y}")
                label = ttk.Label(tooltip_label, text=text, background="#ffffe0", relief="solid", borderwidth=1,
                                  padding=(4, 2))
                label.pack()

        def hide_tooltip(event):
            nonlocal tooltip_label
            if tooltip_label:
                tooltip_label.destroy()
                tooltip_label = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def select_output_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory_entry.delete(0, tk.END)
            self.output_directory_entry.insert(0, directory)
            self.output_directory = directory

    def _get_selected_downsample_methods(self):
        """Return list of selected DownsampleMethod enums."""
        methods = []
        if self.ds_average_var.get():
            methods.append(DownsampleMethod.AVERAGE)
        if self.ds_nth_var.get():
            methods.append(DownsampleMethod.NTH_VALUE)
        if self.ds_min_var.get():
            methods.append(DownsampleMethod.MIN)
        if self.ds_max_var.get():
            methods.append(DownsampleMethod.MAX)
        return methods

    def generate_output(self):
        """Create OutputSettings from user inputs and close dialog."""
        try:
            methods = self._get_selected_downsample_methods()
            if not methods:
                messagebox.showwarning("No Method Selected", "Please select at least one downsampling method.")
                return

            if not self.output_directory:
                messagebox.showwarning("No Directory", "Please select an output directory.")
                return

            self.output_settings = OutputSettings(
                output_type=OutputType.BEBE,
                downsample_methods=methods,
                output_period=OutputPeriod(self.output_period_var.get()),
                output_frequency=int(self.output_frequency_var.get()),
                buffer_minutes=self.buffer_minutes_var.get(),
                round_to_minutes=self.round_to_minutes_var.get()
            )

            self.result_ready = True
            logging.info(f"Generating output with settings: {self.output_settings.to_dict()}")
            self.destroy()
        except Exception as e:
            logging.error(f"Failed to generate output: {e}")
            messagebox.showerror("Error", f"Failed to generate output: {e}")
