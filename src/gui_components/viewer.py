import copy
import logging
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import tkinter as tk
from tkinter import simpledialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from accel_data_parser import AccelDataParser
from models.label import Label
from gui_components.behavior_selection_dialog import BehaviorSelectionDialog


class Viewer(tk.Frame):
    def __init__(self, parent, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_service = project_service
        self.info_pane = None
        self.active_axes = []
        if self.project_service and self.project_service.get_project_config():
            self.active_axes = [display.input_name for display in
                                self.project_service.get_project_config().data_display]  # All axes active by default

        self.data_path = None
        self.data = None
        self.labels = []
        self.start_label_time = None
        self.current_xlim = None  # used to keep pan/zoom consistent across user actions
        self.current_ylim = None
        self.selected_label = None
        self.dragging = False
        self.project_config = None
        self.file_entry = None  # Reference to the project config's FileEntry for the loaded CSV
        self.setup_viewer()

    def set_info_pane(self, info_pane):
        """Sets a reference to the InfoPane instance."""
        self.info_pane = info_pane

    def setup_viewer(self):
        # Setup for the viewer (figure, canvas, etc.)
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bind the Delete key to the delete label function
        self.canvas.get_tk_widget().bind("<Delete>", self.on_delete_key)

        # Bind the arrow keys for zoom and pan actions
        self.canvas.get_tk_widget().bind("<Up>", self.on_key_zoom_in)
        self.canvas.get_tk_widget().bind("<Down>", self.on_key_zoom_out)
        self.canvas.get_tk_widget().bind("<Left>", self.on_key_pan_left)
        self.canvas.get_tk_widget().bind("<Right>", self.on_key_pan_right)

    def on_key_zoom_in(self, event):
        """Handle zoom in on the center of the plot when the Up arrow key is pressed."""
        xlim = self.ax.get_xlim()
        x_center = (xlim[0] + xlim[1]) / 2  # Calculate the center of the plot
        self.zoom(x_center, 1.2)  # Zoom in with a factor of 1.2

    def on_key_zoom_out(self, event):
        """Handle zoom out on the center of the plot when the Down arrow key is pressed."""
        xlim = self.ax.get_xlim()
        x_center = (xlim[0] + xlim[1]) / 2  # Calculate the center of the plot
        self.zoom(x_center, 1 / 1.2)  # Zoom out with a factor of 1/1.2

    # New methods for handling key presses for panning
    def on_key_pan_left(self, event):
        """Handle pan left when the Left arrow key is pressed."""
        self.pan(direction="left")

    def on_key_pan_right(self, event):
        """Handle pan right when the Right arrow key is pressed."""
        self.pan(direction="right")

    # Extract the panning code into a reusable method
    def pan(self, direction):
        """Handle panning in the given direction."""
        xlim = self.ax.get_xlim()
        x_range = mdates.num2date(xlim[1]) - mdates.num2date(xlim[0])
        shift = pd.Timedelta(seconds=x_range.total_seconds() * 0.05)

        if direction == "left":
            new_xlim = [mdates.num2date(xlim[0]) - shift, mdates.num2date(xlim[1]) - shift]
        elif direction == "right":
            new_xlim = [mdates.num2date(xlim[0]) + shift, mdates.num2date(xlim[1]) + shift]

        # Get data boundaries as naive datetime
        data_min = pd.Timestamp(self.data['Timestamp'].min()).tz_localize(None).to_pydatetime()
        data_max = pd.Timestamp(self.data['Timestamp'].max()).tz_localize(None).to_pydatetime()

        # Convert new limits to naive datetime for comparison
        new_xlim = [new_xlim[0].replace(tzinfo=None), new_xlim[1].replace(tzinfo=None)]

        # Check if new limits exceed data boundaries
        if new_xlim[0] < data_min:
            new_xlim[0] = data_min
            new_xlim[1] = min(data_max, data_min + x_range)
            self.parent.set_status("Unable to scroll left, this is the start of the data")
        elif new_xlim[1] > data_max:
            new_xlim[1] = data_max
            new_xlim[0] = max(data_min, data_max - x_range)
            self.parent.set_status("Unable to scroll right, this is the end of the data")
        else:
            self.parent.set_status(f"Panning {direction}")

        # Set the new limits and redraw the canvas
        self.ax.set_xlim(mdates.date2num(new_xlim))
        self.canvas.draw_idle()

        # Update stored limits after interaction
        self.current_xlim = self.ax.get_xlim()
        self.current_ylim = self.ax.get_ylim()

    def on_scroll(self, event):
        """
        Handle zoom/pan when the user scrolls the mousewheel.
        :param event:
        :return:
        """
        # Ignore events if the cursor is not in the plot area
        if not event.xdata:
            return

        if event.key == 'control':
            zoom_factor = 1.2 if event.button == 'up' else 1 / 1.2
            self.zoom(event.xdata, zoom_factor)
        else:
            direction = "left" if event.button == 'down' else "right"
            self.pan(direction)

    def on_delete_key(self, event):
        """Handle the Delete key to remove a selected label."""
        if self.selected_label:
            self.delete_label(self.selected_label)

    def set_project_config(self, project_config):
        if project_config:
            self.project_config = project_config

            # relative_path = self.data_path.replace(self.project_config.data_root_directory, "").lstrip(
            #     '/')
            #
            # self.file_entry = self.project_config.find_file_by_name(relative_path)

    def load_file_entry(self, file_entry):
        file_path = self.project_service.get_file_path(file_entry)

        self.parent.set_status(f"Attempting to load {file_path}")

        # Clear previous data
        self.data_path = file_path
        self.ax.clear()
        self.labels.clear()  # Clear existing labels
        self.file_entry = copy.deepcopy(file_entry)

        # Load the new CSV file and parse data
        data_parser = AccelDataParser(file_path)
        self.data = data_parser.read_data()

        if self.data is not None:
            # Reload the labels even if the file is opened again
            if self.file_entry:
                self.labels = self.file_entry.labels  # Repopulate the labels
                self.update_label_list()  # Update the label listbox

            self.setup_mouse_events()

        # Update the status bar with the name of the loaded file
        self.parent.set_status(f"Loaded: {file_path}")

    def get_data_path(self):
        if self.data_path:
            # Return the filename without the .csv extension
            return self.data_path.split('/')[-1].replace('.csv', '')
        return None

    def setup_mouse_events(self):
        # Plot the initial data
        self.plot_data()

        # Connect mouse and scroll events
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('axes_leave_event', self.on_mouse_leave)

    def set_active_axes(self, active_axes):
        """Set the active axes based on user input from InfoPane."""
        self.active_axes = active_axes
        self.update_plot()  # Trigger a plot update whenever active axes change

    def plot_data(self):
        self.ax.clear()

        self.rectangles = {}

        # Set Y-limits based on actual data range if they haven't been set before
        self.set_y_limits()
        bottom, top = self.current_ylim  # Use correct Y-limits from the data range

        # Plot the labeled sections as semi-transparent boxes
        for label in self.labels:
            if label.start_time is None or label.end_time is None:
                logging.warning(f"Label '{label.behavior}' has invalid start or end time and will be skipped.")
                continue

            label_display = self.project_service.get_label_display(label.behavior)

            if label_display:
                color = label_display.color
                alpha = label_display.alpha
            else:
                color = 'gray'
                alpha = 0.2

            start_num = mdates.date2num(label.start_time)
            end_num = mdates.date2num(label.end_time)

            rect = Rectangle((start_num, bottom), end_num - start_num, top - bottom, color=color, alpha=alpha, lw=2)

            self.ax.add_patch(rect)
            self.rectangles[label] = rect

        for display in self.project_config.data_display:
            if display.input_name in self.active_axes:
                input_name = display.input_name
                color = display.color
                alpha = display.alpha
                self.ax.plot(self.data['Timestamp'], self.data[input_name], color=color, alpha=alpha)

        if self.current_xlim:
            self.ax.set_xlim(self.current_xlim)
        if self.current_ylim:
            self.ax.set_ylim(self.current_ylim)

        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Total Body Acceleration")
        self.ax.set_title(self.project_service.get_plot_title(self.file_entry))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)
        self.canvas.draw_idle()

    def set_y_limits(self):
        # Dynamically set Y-limits based on the min and max of the configured data axes
        y_min, y_max = None, None

        # Iterate over the data_display config to determine min and max values
        for display in self.project_config.data_display:
            input_name = display.input_name  # Access the attribute directly
            current_min = self.data[input_name].min()
            current_max = self.data[input_name].max()

            if y_min is None or current_min < y_min:
                y_min = current_min
            if y_max is None or current_max > y_max:
                y_max = current_max

        # Provide a default if no valid limits were found
        if y_min is None or y_max is None:
            y_min, y_max = -1, 1  # Provide a fallback range if no data was available or limits couldn't be determined

        self.current_ylim = [y_min, y_max]

    def save_labels_to_project_config(self):
        """
        Save all the labels for the active file to the project config
        This should be called anytime the labels are changed.
        :return:
        """
        if self.file_entry:
            self.project_service.update_labels(self.file_entry.file_id, self.labels)
        else:
            logging.warning("Unable to save labels to project config as no file entry found")

    def on_mouse_move(self, event):
        if event.inaxes:
            # Prepare data for cursor report
            cursor_time = mdates.num2date(event.xdata).replace(tzinfo=None) if event.xdata else None
            if not cursor_time:
                time_str = '-'
            else:
                # TODO: is there a cleaner way to do this (format milliseconds)
                ms = cursor_time.strftime('%f')[:3]
                time_str = cursor_time.strftime('%H:%M:%S') + f".{ms}"
            data_values = {}

            # Convert Timestamp column to timezone-naive if it has timezone info
            timestamp_data = self.data['Timestamp'].dt.tz_localize(None)

            for display in self.project_config.data_display:
                if display.input_name in self.data.columns:
                    index = (timestamp_data - pd.Timestamp(cursor_time)).abs().idxmin()
                    data_values[display.input_name] = f"{self.data.iloc[index][display.input_name]:.2f}"

            # Update the InfoPane with current cursor position
            if self.info_pane:
                self.info_pane.update_cursor_report(time_str, data_values)

        if event.inaxes and self.dragging and self.selected_label:
            rect = self.rectangles[self.selected_label]
            # Only adjust the rectangle during the drag, not the label data.
            if self.drag_edge == 'start':
                if event.xdata < rect.get_x() + rect.get_width():  # Prevent overlap
                    # Calculate the new width by subtracting the new x position from the old x position plus the old width
                    new_width = (rect.get_x() + rect.get_width()) - event.xdata
                    rect.set_x(event.xdata)
                    rect.set_width(new_width)
                    self.ax.figure.canvas.draw_idle()  # Efficient redraw of the plot
            elif self.drag_edge == 'end':
                if event.xdata > rect.get_x():  # Prevent overlap
                    rect.set_width(event.xdata - rect.get_x())
                    self.ax.figure.canvas.draw_idle()  # Efficient redraw of the plot

            return

        # Adjust the detection threshold based on the current axis limits (considering zoom level)
        x_min, x_max = self.ax.get_xlim()
        axis_width = x_max - x_min
        threshold = axis_width * 0.005  # Use 0.5% of the axis width as the detection threshold

        near_edge = False
        for label, rect in self.rectangles.items():
            if event.xdata:
                rect_start = rect.get_x()
                rect_end = rect.get_x() + rect.get_width()

                # Check if the mouse is within the threshold of the start or end of the rectangle
                if abs(rect_start - event.xdata) <= threshold or abs(rect_end - event.xdata) <= threshold:
                    self.canvas.get_tk_widget().config(cursor="sb_h_double_arrow")
                    self.selected_label = label
                    near_edge = True
                    break

        if not near_edge:
            self.canvas.get_tk_widget().config(cursor="")
            self.selected_label = None

    def on_mouse_leave(self, event):
        if self.info_pane:
            self.info_pane.reset_cursor_report()

    def update_plot(self):
        self.plot_data()
        # self.canvas.draw()

    def zoom(self, cursor_xdata, zoom_factor):
        """
        User has requested zoom. Attempt to update view window (do not let them zoom out too far)
        and report the view level to the status bar/log.
        :param cursor_xdata: The x position to zoom around.
        :param zoom_factor: The factor by which to zoom in or out.
        :return:
        """
        xlim = self.ax.get_xlim()
        xdata = mdates.num2date(cursor_xdata)
        if xdata is None:
            return

        # Calculate new x-limits based on zoom factor
        new_xlim = [
            mdates.date2num(xdata - (xdata - mdates.num2date(xlim[0])) / zoom_factor),
            mdates.date2num(xdata + (mdates.num2date(xlim[1]) - xdata) / zoom_factor)
        ]

        # Get the boundaries of the data
        data_min = mdates.date2num(self.data['Timestamp'].min())
        data_max = mdates.date2num(self.data['Timestamp'].max())

        # Add a buffer of 10% to 20% to the data boundaries
        buffer_percentage = 0.1  # 10% buffer
        data_range = data_max - data_min
        data_min_buffer = data_min - buffer_percentage * data_range
        data_max_buffer = data_max + buffer_percentage * data_range

        # Ensure new limits do not extend beyond the data boundaries (with buffer)
        if new_xlim[0] < data_min_buffer:
            new_xlim[0] = data_min_buffer
        if new_xlim[1] > data_max_buffer:
            new_xlim[1] = data_max_buffer

        # Ensure that the entire data is not zoomed out further than the boundaries
        if (new_xlim[1] - new_xlim[0]) >= (data_max_buffer - data_min_buffer):
            new_xlim = [data_min_buffer, data_max_buffer]
            msg = "Unable to zoom out further, all data is currently being shown"
        else:
            # Calculate the zoom level as a percentage of the total data range
            current_zoom_level = (new_xlim[1] - new_xlim[0]) / (data_max_buffer - data_min_buffer) * 100
            msg = f"Zooming in, {current_zoom_level:.0f}% of data visible"

        self.parent.set_status(msg)

        self.ax.set_xlim(new_xlim)
        self.canvas.draw_idle()

    def on_click(self, event):
        if event.inaxes:
            if event.button == 1:  # Left click
                # Save current limits to restore after adding the label
                current_xlim = self.ax.get_xlim()
                current_ylim = self.ax.get_ylim()

                # Calculate the detection threshold based on the current axis limits (considering zoom level)
                x_min, x_max = self.ax.get_xlim()
                axis_width = x_max - x_min
                threshold = axis_width * 0.005  # Use 0.5% of the axis width as the detection threshold

                for label, rect in self.rectangles.items():
                    if event.xdata:
                        rect_start = rect.get_x()
                        rect_end = rect.get_x() + rect.get_width()

                        # Check if the mouse is within the threshold of the start or end of the rectangle
                        if abs(rect_start - event.xdata) <= threshold or abs(rect_end - event.xdata) <= threshold:
                            self.dragging = True
                            self.selected_label = label
                            self.drag_edge = 'start' if abs(rect_start - event.xdata) <= threshold else 'end'
                            self.drag_start = event.xdata
                            return
                        elif not self.start_label_time and rect_start < event.xdata < rect_end:
                            # Inside the rectangle
                            self.selected_label = label
                            self.parent.set_status(f"'{label.behavior}' label selected")
                            return

                if self.start_label_time:
                    # End of labeling
                    end_time = mdates.num2date(event.xdata)

                    start_time, end_time = self.validate_user_label_times(self.start_label_time, end_time)

                    behavior = self.prompt_for_behavior()
                    if behavior:
                        new_label = Label(start_time, end_time, behavior)
                        self.labels.append(new_label)

                        # Update project config
                        self.parent.set_status(
                            f"New label created: {new_label}; Left click to start labeling a behavior")
                        self.save_labels_to_project_config()
                        self.update_label_list()

                    self.start_label_time = None
                else:
                    # Start of labeling
                    self.start_label_time = mdates.num2date(event.xdata)
                    self.parent.set_status("Left click to label end of behavior or right click to cancel")

                # Restore the zoom level after adding the label
                self.update_plot()
                self.ax.set_xlim(current_xlim)
                self.ax.set_ylim(current_ylim)
                self.canvas.draw_idle()

            elif event.button == 3:  # Right click for context menu
                for label, rect in self.rectangles.items():
                    if rect.contains_point((event.x, event.y)):
                        self.show_context_menu(event, label)
                        return  # Only show the context menu for the first found label

            self.current_xlim = self.ax.get_xlim()  # Store limits after interaction
            self.current_ylim = self.ax.get_ylim()

    def validate_user_label_times(self, start_time, end_time):
        """
        Ensure that the label the user is trying to add does not overlap any existing labels.
        This function also ensures that start time is before end time.
        """
        # Ensure start time is before end time
        if start_time > end_time:
            start_time, end_time = end_time, start_time

        # Add a buffer to prevent overlap issues (e.g., 1 second buffer)

        buffer = pd.Timedelta(milliseconds=self.project_service.get_step_time_ms())

        # Ensure these times do not overlap any existing labels
        for label in self.labels:
            if (start_time >= label.start_time - buffer and start_time <= label.end_time + buffer) or \
                    (end_time >= label.start_time - buffer and end_time <= label.end_time + buffer):
                # Adjust start or end to avoid overlap
                if start_time < label.end_time:
                    start_time = label.end_time + buffer
                if end_time > label.start_time:
                    end_time = label.start_time - buffer
                self.parent.set_status(
                    f"Adjusted label times to prevent overlap with existing label '{label.behavior}'")

        return start_time, end_time

    def show_context_menu(self, event, clicked_label):
        """Show context menu on right-click if a label is clicked."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Delete", command=lambda: self.delete_label(clicked_label))
        menu.add_command(label="Change Behavior", command=lambda: self.change_label_behavior(clicked_label))

        # Convert the matplotlib canvas coordinates to tkinter window coordinates
        canvas_widget = self.canvas.get_tk_widget()

        x_root = canvas_widget.winfo_rootx() + event.x
        y_root_adjusted = canvas_widget.winfo_rooty() + int(canvas_widget.winfo_height() - event.y)

        menu.post(x_root, y_root_adjusted)

    def change_label_behavior(self, label):
        """Change the behavior of an existing label."""
        # Retrieve behaviors from the project config
        behaviors = [behavior.display_name for behavior in self.project_config.label_display]

        # Open dialog to select new behavior
        new_behavior = self.prompt_for_behavior()

        # If the user selected a behavior, update the label's behavior
        if new_behavior:
            label.behavior = new_behavior
            self.parent.set_status(f"Existing label changed to {new_behavior}")
            self.save_labels_to_project_config()  # Save changes
            self.update_label_list()  # Update the InfoPane display
            self.update_plot()  # Replot with the updated label

    def delete_label(self, label_to_delete):
        """Delete a label and update the plot and project config."""
        self.labels.remove(label_to_delete)  # Remove the label from the list
        self.save_labels_to_project_config()  # Save the updated labels
        self.update_label_list()  # Update the label display
        self.update_plot()  # Redraw the plot without the deleted label
        self.parent.set_status(f"Deleted label: {label_to_delete}")

    def on_mouse_release(self, event):
        if self.dragging and self.selected_label:
            # Update the label data only when the mouse is released.
            rect = self.rectangles[self.selected_label]
            if self.drag_edge == 'start':
                new_start_time = mdates.num2date(rect.get_x())
                self.selected_label.start_time = new_start_time
            elif self.drag_edge == 'end':
                new_end_time = mdates.num2date(rect.get_x() + rect.get_width())
                self.selected_label.end_time = new_end_time

            self.dragging = False
            self.plot_data()  # Replot to ensure all elements are updated correctly
            self.update_label_list()  # Assuming a method to update the list display of labels
            self.save_labels_to_project_config()
            self.canvas.get_tk_widget().config(cursor="")

    def update_label_list(self):
        if self.info_pane:
            self.info_pane.update_label_durations()

    def prompt_for_behavior(self):
        # Retrieve behaviors from the project config
        behaviors = [label.display_name for label in self.project_config.label_display]

        # If there are no behaviors defined, handle it accordingly
        if not behaviors:
            return None

        # Prompt the user to select a behavior
        dialog = BehaviorSelectionDialog(self, behaviors, title="Select Behavior")
        return dialog.result

    def clear_plot(self):
        """
        Clear the viewer
        :return:
        """
        self.ax.clear()
        self.labels = []
        self.canvas.draw_idle()  # Redraw the plot

