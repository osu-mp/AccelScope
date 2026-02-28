import logging
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk

from gui_components.gui_theme import PAD_SM, PAD_MD, PAD_LG, FONT_BODY, FONT_HEADING


class InfoPane(ttk.Frame):
    def __init__(self, parent, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_service = project_service
        self.current_file_entry = None
        self.viewer = self.parent.viewer
        self.axis_vars = {}
        self._comment_save_after_id = None  # debounce timer for comment auto-save
        self._comment_save_delay = getattr(
            getattr(parent, 'user_app_config', None), 'comment_save_delay', 500
        )

        # Retrieve the input settings and initialize the input interface to access display info
        self.input_interface = self.viewer.get_input_interface()

        # Store the project config for accessing the data_display information
        self.project_config = self.project_service.get_project_config()

        self.label = ttk.Label(self, text='Info Pane', font=FONT_HEADING)
        self.label.pack(fill=tk.X, pady=PAD_MD)

        # Initialize the cursor report frame here
        self.cursor_report_frame = ttk.Frame(self)
        self.cursor_report_frame.pack(fill=tk.NONE, pady=PAD_LG)

        # Report cursor x/y/z/time
        self.create_cursor_report()
        self.add_separator()

        # Verification section
        self.verification_frame = ttk.LabelFrame(self, text="Verification")
        self.verification_frame.pack(fill=tk.X, pady=PAD_MD)
        self.reviewer_vars = {}
        self.reviewer_checkboxes = {}
        self._build_reviewer_checkboxes()
        self.add_separator()

        # Comments Section
        self.comments_frame = ttk.LabelFrame(self, text="Comments")
        self.comments_frame.pack(fill=tk.X, pady=PAD_MD)

        current_user = self.project_service.get_current_reviewer()
        reviewers = self.project_service.get_reviewers()
        alias = reviewers.get(current_user, {}).get("alias", current_user[:2].upper()) if reviewers else current_user[:2].upper()

        self.current_user_alias_label = ttk.Label(self.comments_frame, text=f"{alias} (you)", font=FONT_BODY)
        self.current_user_alias_label.pack(fill=tk.X, padx=PAD_SM, pady=(PAD_SM, 0))
        self.comments_text = tk.Text(self.comments_frame, height=3, width=40)
        self.comments_text.pack(fill=tk.X, padx=PAD_SM, pady=PAD_SM)
        self.comments_text.bind("<KeyRelease>", self.on_comments_change)

        self.other_comments_frame = ttk.Frame(self.comments_frame)
        self.other_comments_frame.pack(fill=tk.X, padx=PAD_SM, pady=PAD_SM)
        self.add_separator()

        # Dynamically generate checkboxes for each data_display item
        self.data_display_vars = {}
        self.create_data_display_checkboxes()

        # Add separator between Axis Control and Labels
        self.add_separator()

        # Create the "Labeled Actions" label only once
        self.labeled_actions_label = ttk.Label(self, text="Labeled Actions", font=FONT_BODY)
        self.labeled_actions_label.pack(fill=tk.X, pady=PAD_MD)

        # Create the initial legend for both data display and labeled actions
        self.legend_canvas = None
        self.create_legend()

    def create_cursor_report(self):
        """Create a section that displays values at the user's cursor position."""
        # Clear the frame before creating new labels (if dynamically reloaded)
        for widget in self.cursor_report_frame.winfo_children():
            widget.destroy()

        self.labels = {}

        # Add "Time" label
        time_label = ttk.Label(self.cursor_report_frame, text="Time:", anchor="w", width=4)
        time_label.grid(row=0, column=0, sticky="w")
        self.labels['Time'] = ttk.Label(self.cursor_report_frame, text="-", anchor="e")
        self.labels['Time'].grid(row=0, column=1, sticky="e")

        # Add labels for each axis based on the AxesConfig from input interface
        if self.input_interface is None:
            return
        axes_config = self.input_interface.get_axes_config()
        for idx, axis_display in enumerate(axes_config.axis_displays, start=1):
            data_label = ttk.Label(self.cursor_report_frame, text=f"{axis_display.display_name}:", anchor="w", width=4)
            data_label.grid(row=idx, column=0, sticky="w")
            self.labels[axis_display.input_name] = ttk.Label(self.cursor_report_frame, text="-", anchor="e", width=6)
            self.labels[axis_display.input_name].grid(row=idx, column=1, sticky="e")

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

    def refresh_user_info(self):
        """Refresh alias label and reviewer checkboxes after a profile update."""
        current_user = self.project_service.get_current_reviewer()
        reviewers = self.project_service.get_reviewers()
        alias = reviewers.get(current_user, {}).get("alias", current_user[:2].upper()) if reviewers else current_user[:2].upper()
        if hasattr(self, 'current_user_alias_label'):
            self.current_user_alias_label.config(text=f"{alias} (you)")
        self._build_reviewer_checkboxes()

    def reset_ui(self):
        """Reset dynamic components (checkboxes, legend) when a new project is loaded."""
        if hasattr(self, 'checkbox_container'):
            self.checkbox_container.destroy()
        if self.legend_canvas is not None:
            self.legend_canvas.destroy()
            self.legend_canvas = None
        self.data_display_vars.clear()

    def create_data_display_checkboxes(self):
        """Create checkboxes for each axis in AxesConfig."""
        ttk.Label(self, text="Axis Control", font=FONT_BODY).pack(fill=tk.X, pady=PAD_MD)
        self.checkbox_container = ttk.Frame(self)
        self.checkbox_container.pack(fill=tk.NONE, pady=PAD_MD, anchor=tk.N)

        if self.input_interface is None:
            return
        axes_config = self.input_interface.get_axes_config()
        for axis_display in axes_config.axis_displays:
            var = tk.BooleanVar(value=True)
            self.axis_vars[axis_display.input_name] = var

            checkbox_frame = tk.Frame(self.checkbox_container, highlightbackground=axis_display.color,
                                      highlightcolor=axis_display.color, highlightthickness=2, bd=0,
                                      padx=PAD_SM, pady=PAD_SM)
            checkbox_frame.pack(anchor=tk.NW, pady=PAD_SM, fill=tk.X)
            checkbox = ttk.Checkbutton(checkbox_frame, text=axis_display.display_name, variable=var,
                                       command=self.update_viewer)
            checkbox.pack(anchor=tk.W, padx=PAD_MD)

    def update_viewer(self):
        """Update the viewer when axis checkboxes are changed."""
        active_axes = [axis for axis, var in self.axis_vars.items() if var.get()]
        logging.info(f"Viewer updated with active axes: {', '.join(active_axes) if active_axes else 'None selected'}")
        self.viewer.set_active_axes(active_axes)

    def create_legend(self):
        """Create or update the legend for the labeled actions using a tk.Canvas."""
        if self.legend_canvas is not None:
            self.legend_canvas.destroy()

        self.legend_canvas = tk.Canvas(self, highlightthickness=0)
        self.legend_canvas.pack(fill=tk.BOTH, pady=PAD_MD, expand=True)

        self._draw_legend_items()

    def _draw_legend_items(self):
        """Draw colored rectangles and text labels on the legend canvas."""
        if not self.viewer.labels:
            return

        rect_size = 14
        x_pad = PAD_MD
        y = PAD_MD

        for label in sorted(self.viewer.labels, key=lambda x: x.start_time):
            label_display = self.project_service.get_label_display(label.behavior)
            color = label_display.color if label_display else 'gray'

            duration_str = self.calculate_duration(label.start_time, label.end_time)
            text = f"{label.behavior} ({duration_str})"

            self.legend_canvas.create_rectangle(
                x_pad, y, x_pad + rect_size, y + rect_size,
                fill=color, outline=color
            )
            self.legend_canvas.create_text(
                x_pad + rect_size + PAD_MD, y + rect_size // 2,
                text=text, anchor="w", font=FONT_BODY
            )

            y += rect_size + PAD_MD

        # Update canvas scroll region to fit content
        self.legend_canvas.configure(scrollregion=self.legend_canvas.bbox("all") or (0, 0, 0, 0))

    def update_label_durations(self):
        """Update the legend whenever labels change."""
        self.update_legend()

    def update_legend(self):
        """Refresh the legend in the InfoPane when labels are added/updated."""
        if self.legend_canvas is not None:
            self.legend_canvas.delete("all")
            self._draw_legend_items()
        else:
            self.create_legend()

    def add_separator(self):
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', pady=PAD_LG)

    def set_project_service(self, project_service):
        """
        Called when the project is reloaded (resets legend, checkboxes, and cursor report).
        """
        self.project_service = project_service
        self.reset_ui()
        self._build_reviewer_checkboxes()
        self.create_data_display_checkboxes()  # Regenerate dynamic checkboxes based on new project config
        self.create_cursor_report()  # Regenerate the cursor report for new project data
        self.create_legend()  # Refresh the legend based on new project data

    def set_file_entry(self, file_entry):
        """Update the current FileEntry and update the UI elements."""
        # Flush any pending comment save before switching files
        if self._comment_save_after_id is not None:
            self.after_cancel(self._comment_save_after_id)
            self._comment_save_after_id = None
            self.project_service.save_project()

        self.current_file_entry = file_entry

        # Always clear comment text first to avoid stale text
        self.comments_text.delete("1.0", tk.END)

        # Clear other users' comments
        for widget in self.other_comments_frame.winfo_children():
            widget.destroy()

        if file_entry:
            for username, var in self.reviewer_vars.items():
                var.set(file_entry.is_verified_by(username))

            # Load current user's comment
            current_user = self.project_service.get_current_reviewer()
            user_comment = file_entry.get_comment(current_user)
            if user_comment:
                self.comments_text.insert(tk.END, user_comment)

            # Show other users' non-empty comments as read-only labels
            reviewers = self.project_service.get_reviewers()
            for username, comment_text in file_entry.comments.items():
                if username == current_user or not comment_text:
                    continue
                alias = reviewers.get(username, {}).get("alias", username[:2].upper()) if reviewers else username
                ttk.Label(self.other_comments_frame, text=f"{alias}:", font=FONT_BODY).pack(
                    anchor=tk.W)
                comment_label = ttk.Label(self.other_comments_frame, text=comment_text, wraplength=200)
                comment_label.pack(anchor=tk.W, padx=(PAD_SM, 0), pady=(0, PAD_SM))

    def _build_reviewer_checkboxes(self):
        """Build one checkbox per reviewer (or a single generic one if no reviewers configured)."""
        for widget in self.verification_frame.winfo_children():
            widget.destroy()
        self.reviewer_vars.clear()
        self.reviewer_checkboxes.clear()

        reviewers = self.project_service.get_reviewers()
        current_user = self.project_service.get_current_reviewer()

        if not reviewers:
            # No reviewers configured — show a single "Verified" checkbox for current user
            var = tk.BooleanVar()
            self.reviewer_vars[current_user] = var
            cb = ttk.Checkbutton(self.verification_frame, text="Verified", variable=var,
                                 command=self._on_reviewer_verified_change)
            cb.pack(anchor=tk.W, padx=PAD_SM, pady=PAD_SM)
            self.reviewer_checkboxes[current_user] = cb
        else:
            for username, info in reviewers.items():
                alias = info.get("alias", username[:2].upper())
                var = tk.BooleanVar()
                self.reviewer_vars[username] = var
                cb = ttk.Checkbutton(self.verification_frame, text=alias, variable=var,
                                     command=self._on_reviewer_verified_change)
                cb.pack(anchor=tk.W, padx=PAD_SM, pady=PAD_SM)
                # Only the current user's checkbox is enabled
                if username != current_user:
                    cb.configure(state="disabled")
                self.reviewer_checkboxes[username] = cb

    def _on_reviewer_verified_change(self):
        """Handle changes to any reviewer verification checkbox."""
        if self.current_file_entry:
            current_user = self.project_service.get_current_reviewer()
            if current_user in self.reviewer_vars:
                verified = self.reviewer_vars[current_user].get()
                self.current_file_entry.set_verified_by(current_user, verified)
                self.parent.set_status(f"Verification by {current_user}: {verified}")
                self.project_service.save_project()
                self.parent.project_browser.update_tree_item_color(
                    self.current_file_entry.id, self.current_file_entry.verified_by)

    @staticmethod
    def calculate_duration(start_time, end_time):
        """Calculate the duration between two times and return a formatted string.
        Both start_time and end_time are datetime objects."""
        duration = end_time - start_time

        if duration < timedelta(minutes=1):
            duration_str = f"{duration.total_seconds():.1f} sec"
        else:
            minutes = duration.total_seconds() / 60
            duration_str = f"{minutes:.1f} min"

        return duration_str

    def on_comments_change(self, event):
        """Handle changes to the comments text field (debounced save)."""
        if self.current_file_entry:
            current_user = self.project_service.get_current_reviewer()
            text = self.comments_text.get("1.0", tk.END).strip()
            self.current_file_entry.set_comment(current_user, text)
            # Debounce: cancel any pending save and schedule a new one after 500ms
            if self._comment_save_after_id is not None:
                self.after_cancel(self._comment_save_after_id)
            self._comment_save_after_id = self.after(self._comment_save_delay, self._save_comment)

    def _save_comment(self):
        """Actually persist the comment after debounce delay."""
        self._comment_save_after_id = None
        self.project_service.save_project()
