import tkinter as tk
from tkinter import ttk


class InfoPane(tk.Frame):
    def __init__(self, parent, config_manager, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.config_manager = config_manager
        self.viewer = self.parent.viewer
        self.axis_vars = {}

        # Store the project config for accessing the data_display information
        self.project_config = self.config_manager.get_project_config()

        self.label = tk.Label(self, text='Info Pane')
        self.label.pack(fill=tk.BOTH, expand=True)

        #  Dynamically generate checkboxes for each data_display item
        self.data_display_vars = {}  # Dictionary to hold BooleanVars for each data axis

        self.create_data_display_checkboxes()

        # User label listbox for behaviors (this can be populated later)
        tk.Label(self, text="Labels").pack(pady=5)
        self.user_labels_listbox = tk.Listbox(self, height=10)
        self.user_labels_listbox.pack(pady=5)

        # Legend placeholder (this can be populated with behavior/annotation information)
        tk.Label(self, text="Legend").pack(pady=5)
        self.legend_frame = tk.Frame(self)
        self.legend_frame.pack(pady=5)

    def create_data_display_checkboxes(self):
        """Dynamically creates checkboxes for each data_display item from the project config."""
        # Create a label for the section
        tk.Label(self, text="Axis Control").pack(pady=5)

        # Iterate through each data_display entry in the project config
        for display in self.config_manager.get_project_config().data_display:
            var = tk.BooleanVar(value=True)
            self.axis_vars[display.input_name] = var

            # Create a frame with a colored border for the checkbox
            checkbox_frame = tk.Frame(self, highlightbackground=display.color, highlightcolor=display.color,
                                      highlightthickness=2, bd=0, padx=1, pady=1)
            checkbox_frame.pack(anchor=tk.W, pady=2)

            checkbox = tk.Checkbutton(checkbox_frame, text=display.display_name, variable=var,
                                      command=self.update_viewer)
            checkbox.pack(anchor=tk.W, padx=2)

    def update_viewer(self):
        """Update the viewer when axis checkboxes are changed."""
        # Collect which axes are enabled (based on the BooleanVars) and update the viewer
        active_axes = [axis for axis, var in self.axis_vars.items() if var.get()]
        self.viewer.set_active_axes(active_axes)

    def update_label_list(self, labels):
        # Update the label list in the Info Pane
        self.user_labels_listbox.delete(0, tk.END)
        for label in sorted(labels, key=lambda x: x.start_time):
            self.user_labels_listbox.insert(tk.END, str(label))

    def update_legend(self, legend_info):
        # Clear old legend
        for widget in self.legend_frame.winfo_children():
            widget.destroy()

        handles, labels = legend_info
        for handle, label in zip(handles, labels):
            color = handle.get_color()
            tk.Label(self.legend_frame, text=label, bg=color, width=10).pack(side=tk.TOP, pady=2)

    def update_info(self, content):
        """Update the InfoPane with new content, for example, when a project is loaded."""
        if content:
            self.label.config(text=content)
        else:
            self.label.config(text="Info Pane: No project loaded")