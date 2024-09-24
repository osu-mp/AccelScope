import tkinter as tk
from tkinter import ttk


class InfoPane(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.label = tk.Label(self, text='Info Pane')
        self.label.pack(fill=tk.BOTH, expand=True)

        # Axis control checkboxes
        self.x_var = tk.BooleanVar(value=True)
        self.y_var = tk.BooleanVar(value=True)
        self.z_var = tk.BooleanVar(value=True)

        tk.Label(self, text="Axis Control").pack(pady=5)

        self.x_checkbox = tk.Checkbutton(self, text="X-axis", variable=self.x_var, command=self.update_viewer)
        self.x_checkbox.pack(anchor=tk.W)

        self.y_checkbox = tk.Checkbutton(self, text="Y-axis", variable=self.y_var, command=self.update_viewer)
        self.y_checkbox.pack(anchor=tk.W)

        self.z_checkbox = tk.Checkbutton(self, text="Z-axis", variable=self.z_var, command=self.update_viewer)
        self.z_checkbox.pack(anchor=tk.W)

        # User label listbox
        tk.Label(self, text="Labels").pack(pady=5)
        self.user_labels_listbox = tk.Listbox(self, height=10)
        self.user_labels_listbox.pack(pady=5)

        # Legend
        tk.Label(self, text="Legend").pack(pady=5)
        self.legend_frame = tk.Frame(self)
        self.legend_frame.pack(pady=5)

    def update_viewer(self):
        # Update the viewer when axis checkboxes are changed
        self.master.viewer.update_plot()

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