from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class InfoPane(tk.Frame):
    def __init__(self, parent, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_service = project_service
        self.current_file_entry = None  # Store the current FileEntry being viewed

        self.viewer = self.parent.viewer
        self.axis_vars = {}

        # Store the project config for accessing the data_display information
        self.project_config = self.project_service.get_project_config()

        self.label = tk.Label(self, text='Info Pane')
        self.label.pack(fill=tk.X, pady=5)

        # Initialize the cursor report frame here
        self.cursor_report_frame = tk.Frame(self)
        self.cursor_report_frame.pack(fill=tk.NONE, pady=10)

        # Report cursor x/y/z/time
        self.create_cursor_report()
        self.add_separator()

        # User Verified Checkbox
        self.user_verified_var = tk.BooleanVar()
        self.user_verified_checkbox = tk.Checkbutton(self, text="User Verified", variable=self.user_verified_var,
                                                     command=self.on_user_verified_change)
        self.user_verified_checkbox.pack(fill=tk.X, pady=5)
        self.add_separator()

        # Comments Section
        self.comments_label = tk.Label(self, text="Comments")
        self.comments_label.pack(fill=tk.X, pady=5)

        self.comments_text = tk.Text(self, height=4, width=40)
        self.comments_text.pack(fill=tk.X, pady=5)
        self.comments_text.bind("<KeyRelease>", self.on_comments_change)  # Detect changes to comments
        self.add_separator()

        # Dynamically generate checkboxes for each data_display item
        self.data_display_vars = {}
        self.create_data_display_checkboxes()

        # Add separator between Axis Control and Labels
        self.add_separator()

        # Create the "Labeled Actions" label only once
        self.labeled_actions_label = tk.Label(self, text="Labeled Actions")
        self.labeled_actions_label.pack(fill=tk.X, pady=5)

        # Create the initial legend for both data display and labeled actions
        self.create_legend()

    def create_cursor_report(self):
        """Create a section that displays values at the user's cursor position."""
        # Clear the frame before creating new labels (if dynamically reloaded)
        for widget in self.cursor_report_frame.winfo_children():
            widget.destroy()

        self.labels = {}

        # Add "Time" label
        time_label = tk.Label(self.cursor_report_frame, text="Time:", anchor="w", width=4)
        time_label.grid(row=0, column=0, sticky="w")
        self.labels['Time'] = tk.Label(self.cursor_report_frame, text="-", anchor="e")
        self.labels['Time'].grid(row=0, column=1, sticky="e")

        # Add labels for each data display item
        if self.project_config:
            for idx, display in enumerate(self.project_config.data_display, start=1):
                data_label = tk.Label(self.cursor_report_frame, text=f"{display.display_name}:", anchor="w", width=4)
                data_label.grid(row=idx, column=0, sticky="w")
                self.labels[display.input_name] = tk.Label(self.cursor_report_frame, text="-", anchor="e", width=6)
                self.labels[display.input_name].grid(row=idx, column=1, sticky="e")

    def update_cursor_report(self, time, data_values):
        """Update the labels to display current cursor position values."""
        if 'Time' in self.labels and self.labels['Time'].winfo_exists():
            self.labels['Time'].config(text=time if time else "-")

        for input_name, value in data_values.items():
            if input_name in self.labels and self.labels[input_name].winfo_exists():
                self.labels[input_name].config(text=value if value is not None else "-")

    def reset_cursor_report(self):
        """Reset cursor report values to '-' when the cursor leaves the viewer."""
        self.update_cursor_report(None, {key: None for key in self.labels if key != 'Time'})

    def reset_ui(self):
        """Reset dynamic components (checkboxes, legend) when a new project is loaded."""
        if hasattr(self, 'checkbox_container'):
            self.checkbox_container.destroy()
        if hasattr(self, 'legend_canvas'):
            self.legend_canvas.get_tk_widget().destroy()
        self.data_display_vars.clear()

    def create_data_display_checkboxes(self):
        """Dynamically creates checkboxes for each data_display item from the project config."""
        tk.Label(self, text="Axis Control").pack(fill=tk.X, pady=5)

        # Create a container for the checkboxes
        self.checkbox_container = tk.Frame(self)
        self.checkbox_container.pack(fill=tk.NONE, pady=5, anchor=tk.N)

        # Iterate through each data_display entry in the project config
        project_config = self.project_service.get_project_config()
        if not project_config:
            return
        for display in project_config.data_display:
            var = tk.BooleanVar(value=True)
            self.axis_vars[display.input_name] = var

            checkbox_frame = tk.Frame(self.checkbox_container, highlightbackground=display.color, highlightcolor=display.color,
                                      highlightthickness=2, bd=0, padx=1, pady=1)
            checkbox_frame.pack(anchor=tk.NW, pady=2, fill=tk.X)

            checkbox = tk.Checkbutton(checkbox_frame, text=display.display_name, variable=var, command=self.update_viewer)
            checkbox.pack(anchor=tk.W, padx=5)

    def update_viewer(self):
        """Update the viewer when axis checkboxes are changed."""
        active_axes = [axis for axis, var in self.axis_vars.items() if var.get()]
        self.viewer.set_active_axes(active_axes)

    def create_legend(self):
        """Create or update the legend for the labeled actions."""
        # Create a matplotlib figure for the legend
        fig, ax = plt.subplots(figsize=(2, 5))  # Adjust the size as needed
        ax.axis('off')

        lines = []
        labels = []

        # Labels/Annotations Legend
        if self.viewer.labels:
            for label in sorted(self.viewer.labels, key=lambda x: x.start_time):
                # Get label color and alpha from the project config
                label_display = self.project_service.get_label_display(label.behavior)
                color = label_display.color if label_display else 'gray'
                alpha = label_display.alpha if label_display else 0.5

                # Calculate the duration of the behavior
                duration_str = self.calculate_duration(label.start_time, label.end_time)

                # Create a dummy rectangle for the legend
                rect = plt.Rectangle((0, 0), 1, 1, color=color, alpha=alpha)
                lines.append(rect)
                labels.append(f"{label.behavior} ({duration_str})")

        # Create the legend from the dummy elements
        legend = ax.legend(lines, labels, loc='center', frameon=False)

        # Check if the canvas has been initialized before accessing it
        if hasattr(self, 'legend_canvas'):
            self.legend_canvas.get_tk_widget().destroy()  # Remove the old canvas

        # Create or update the Tkinter canvas to display the legend
        self.legend_canvas = FigureCanvasTkAgg(fig, master=self)
        self.legend_canvas.get_tk_widget().pack(fill=tk.BOTH, pady=5, expand=True)
        self.legend_canvas.draw_idle()

    def update_label_durations(self):
        """Update the legend whenever labels change."""
        self.update_legend()

    def update_legend(self):
        """Refresh the legend in the InfoPane when labels are added/updated."""
        if hasattr(self, 'legend_canvas'):
            self.legend_canvas.get_tk_widget().destroy()
        self.create_legend()

    def add_separator(self):
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', pady=10)

    def set_project_service(self, project_service):
        """
        Called when the project is reloaded (resets legend, checkboxes, and cursor report).
        """
        self.project_service = project_service
        self.reset_ui()
        self.create_data_display_checkboxes()  # Regenerate dynamic checkboxes based on new project config
        self.create_cursor_report()  # Regenerate the cursor report for new project data
        self.create_legend()  # Refresh the legend based on new project data

    def set_file_entry(self, file_entry):
        """Update the current FileEntry and update the UI elements."""
        self.current_file_entry = file_entry
        if file_entry:
            self.user_verified_var.set(file_entry.user_verified)
            if file_entry.user_verified:
                self.user_verified_checkbox.select()
            else:
                self.user_verified_checkbox.deselect()

            if file_entry.comment:
                self.comments_text.delete("1.0", tk.END)
                self.comments_text.insert(tk.END, file_entry.comment)

    def on_user_verified_change(self):
        """Handle changes to the user_verified checkbox."""
        if self.current_file_entry:
            self.current_file_entry.user_verified = self.user_verified_var.get()
            self.parent.set_status(f"User verified status changed to: {self.current_file_entry.user_verified}")
            self.project_service.save_project()
            self.parent.project_browser.update_tree_item_color(self.current_file_entry.id,
                                                               self.current_file_entry.user_verified)

    @staticmethod
    def calculate_duration(start_time, end_time):
        """Calculate the duration between two times and return a formatted string."""
        if isinstance(start_time, datetime):
            start_time = start_time.time()
        if isinstance(end_time, datetime):
            end_time = end_time.time()

        start_dt = datetime.combine(datetime.min, start_time)
        end_dt = datetime.combine(datetime.min, end_time)

        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        duration = end_dt - start_dt
        if duration < timedelta(minutes=1):
            duration_str = f"{duration.total_seconds():.1f} sec"
        else:
            minutes = duration.total_seconds() / 60
            duration_str = f"{minutes:.1f} min"

        return duration_str

    def on_comments_change(self, event):
        """Handle changes to the comments text field."""
        if self.current_file_entry:
            new_comment = self.comments_text.get("1.0", tk.END).strip()
            self.current_file_entry.comment = new_comment
            self.project_service.save_project()
