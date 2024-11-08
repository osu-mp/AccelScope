import logging
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType

class GenerateOutputDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Generate Output")

        self.output_settings = OutputSettings()  # Initialize with default settings
        self.output_directory = None

        # Output Type
        ttk.Label(self, text="Output Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_type_var = tk.StringVar(value=OutputType.BEBE.value)
        self.output_type_combo = ttk.Combobox(self, textvariable=self.output_type_var, values=[e.value for e in OutputType])
        self.output_type_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Downsampling Method
        ttk.Label(self, text="Downsampling Method:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.downsample_method_var = tk.StringVar(value=DownsampleMethod.AVERAGE.value)
        self.downsample_combo = ttk.Combobox(self, textvariable=self.downsample_method_var, values=[e.value for e in DownsampleMethod])
        self.downsample_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        # Output Period
        ttk.Label(self, text="Output Period:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_period_var = tk.StringVar(value=OutputPeriod.ENTIRE_INPUT.value)
        self.output_period_combo = ttk.Combobox(self, textvariable=self.output_period_var, values=[e.value for e in OutputPeriod])
        self.output_period_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # Output Frequency Dropdown
        ttk.Label(self, text="Output Frequency (Hz):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_frequency_var = tk.StringVar(value="16")  # Default to 16 Hz
        self.output_frequency_combo = ttk.Combobox(self, textvariable=self.output_frequency_var,
                                                   values=["1", "2", "4", "8", "16"], state="readonly")
        self.output_frequency_combo.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)

        # Buffer Minutes
        ttk.Label(self, text="Buffer Minutes:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.buffer_minutes_var = tk.IntVar(value=5)
        self.buffer_minutes_spinbox = ttk.Spinbox(self, from_=0, to=60, textvariable=self.buffer_minutes_var)
        self.buffer_minutes_spinbox.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)

        # Round to Minutes
        ttk.Label(self, text="Round to Minutes:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.round_to_minutes_var = tk.IntVar(value=1)
        self.round_to_minutes_spinbox = ttk.Spinbox(self, from_=0, to=60, textvariable=self.round_to_minutes_var)
        self.round_to_minutes_spinbox.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)

        # Output Directory
        ttk.Label(self, text="Output Directory:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_directory_entry = ttk.Entry(self)
        self.output_directory_entry.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(self, text="Browse", command=self.select_output_directory).grid(row=6, column=2, padx=5, pady=5)

        # Action Buttons
        ttk.Button(self, text="Cancel", command=self.destroy).grid(row=7, column=0, padx=5, pady=5)
        ttk.Button(self, text="Generate Output", command=self.generate_output).grid(row=7, column=1, padx=5, pady=5)

        # Configure column layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)

    def select_output_directory(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory_entry.delete(0, tk.END)
            self.output_directory_entry.insert(0, directory)
            self.output_directory = directory

    def generate_output(self):
        # Create OutputSettings from user inputs
        try:
            self.output_settings = OutputSettings(
                output_type=OutputType(self.output_type_var.get()),
                downsample_method=DownsampleMethod(self.downsample_method_var.get()),
                output_period=OutputPeriod(self.output_period_var.get()),
                output_frequency=self.output_frequency_var.get(),
                buffer_minutes=self.buffer_minutes_var.get(),
                round_to_minutes=self.round_to_minutes_var.get()
            )

            logging.info(f"Generating output with settings: {self.output_settings.to_dict()}")
            # Pass the settings to the output generation function
            # Placeholder for actual output generation
            messagebox.showinfo("Success", "Output generated successfully!")
            self.destroy()
        except Exception as e:
            logging.error(f"Failed to generate output: {e}")
            messagebox.showerror("Error", f"Failed to generate output: {e}")
