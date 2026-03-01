import copy
from datetime import datetime, date, time as dt_time, timedelta
import logging
import os
import threading
import time as _time
import numpy as np
import pandas as pd
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import tkinter as tk
from gui_components.behavior_selection_dialog import BehaviorSelectionDialog
from gui_components.label_commands import (
    LabelCommandStack, CreateLabelCommand, DeleteLabelCommand,
    ResizeLabelCommand, ChangeBehaviorCommand
)
from input_types.vectronic_motion import VectronicMotionInput
from models.label import Label
from models.input_settings import InputType


class Viewer(tk.Frame):
    def __init__(self, parent, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_service = project_service
        self.info_pane = None
        self.axes_config = None
        self.active_axes = []
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
        self._last_mouse_move = 0  # throttle timestamp for on_mouse_move
        self._ts_numeric = None  # cached int64 ms timestamps for binary search
        self._ts_naive = None  # cached tz-naive timestamp series
        self._data_min = None  # cached min timestamp
        self._data_max = None  # cached max timestamp
        self._replot_after_id = None  # tkinter after() id for debounced replot
        self._command_stack = LabelCommandStack()
        self._drag_start_time = None  # saved start_time before drag
        self._drag_end_time = None    # saved end_time before drag
        self.drag_edge = None         # 'start', 'end', or 'body'
        self._drag_offset = 0.0       # cursor distance from rect left on body-drag click
        self._drag_width = 0.0        # label width preserved during body drag
        self._drag_gap_idx = 0        # which gap between other labels the body drag is in
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
        self.canvas.get_tk_widget().bind("<a>", self.zoom_out_to_show_all)
        self.canvas.get_tk_widget().bind("<f>", self.zoom_in_on_all_labels)

        # Bind the arrow keys for zoom and pan actions
        self.canvas.get_tk_widget().bind("<Up>", self.on_key_zoom_in)
        self.canvas.get_tk_widget().bind("<Down>", self.on_key_zoom_out)
        self.canvas.get_tk_widget().bind("<Left>", self.on_key_pan_left)
        self.canvas.get_tk_widget().bind("<Right>", self.on_key_pan_right)
        self.canvas.get_tk_widget().bind("<Control-z>", self.on_undo)
        self.canvas.get_tk_widget().bind("<Control-y>", self.on_redo)

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

        # Get data boundaries as naive datetime (using cached values)
        data_min = self._data_min
        data_max = self._data_max

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

        # Schedule a debounced replot for view-aware downsampling
        self._schedule_replot()

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

    def load_file_entry(self, file_entry):
        """Start loading a file entry asynchronously. Status bar updates on start/finish."""
        self.file_entry = copy.deepcopy(file_entry)
        file_path = self.project_service.get_file_path(file_entry)
        filename = os.path.basename(file_path)
        self.parent.set_status(f"Loading {filename}…")

        input_interface = self.get_input_interface()

        def _load():
            try:
                data = input_interface.load_data(file_path)
                input_interface.validate_format(data)
                self.parent.after(0, lambda: self._on_load_complete(file_entry, file_path, input_interface, data))
            except Exception as e:
                logging.error(f"Error loading data from {file_path}: {e}")
                self.parent.after(0, lambda: self.parent.set_status(f"Failed to load: {filename}"))

        threading.Thread(target=_load, daemon=True).start()

    def _on_load_complete(self, file_entry, file_path, input_interface, data):
        """Called on the main thread once background CSV load succeeds."""
        self.data = data

        # Cache timestamp data for performance
        self._ts_numeric = self.data['Timestamp'].values.astype('int64') // 10**6  # ms as int64
        self._ts_naive = self.data['Timestamp'].dt.tz_localize(None)
        self._data_min = pd.Timestamp(self.data['Timestamp'].min()).tz_localize(None).to_pydatetime()
        self._data_max = pd.Timestamp(self.data['Timestamp'].max()).tz_localize(None).to_pydatetime()

        self.set_axes_config(input_interface.get_axes_config())

        self.data_path = file_path
        self.labels = file_entry.labels
        self._command_stack.clear()
        self.current_xlim = None  # reset zoom so new file shows all data
        self.setup_mouse_events()

        filename = os.path.basename(file_path)
        self.parent.set_status(f"Loaded: {filename}")
        self.update_label_list()

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

    def _get_visible_range(self):
        """Return (start_idx, end_idx) slice indices for the currently visible x-range, with a buffer."""
        if self.current_xlim is None or self._ts_numeric is None:
            return 0, len(self._ts_numeric) if self._ts_numeric is not None else 0
        # Convert matplotlib date nums to ms timestamps
        xlim_min_dt = mdates.num2date(self.current_xlim[0]).replace(tzinfo=None)
        xlim_max_dt = mdates.num2date(self.current_xlim[1]).replace(tzinfo=None)
        xlim_min_ms = int(pd.Timestamp(xlim_min_dt).value // 10**6)
        xlim_max_ms = int(pd.Timestamp(xlim_max_dt).value // 10**6)
        # Add 10% buffer on each side so panning doesn't immediately show gaps
        visible_range_ms = xlim_max_ms - xlim_min_ms
        buffer_ms = int(visible_range_ms * 0.1)
        start_idx = max(0, np.searchsorted(self._ts_numeric, xlim_min_ms - buffer_ms))
        end_idx = min(len(self._ts_numeric), np.searchsorted(self._ts_numeric, xlim_max_ms + buffer_ms))
        return start_idx, end_idx

    def _downsample_for_display(self, timestamps, values, max_points=4000):
        """Downsample data for display, preserving visual peaks via min/max per chunk."""
        n = len(timestamps)
        if n <= max_points:
            return timestamps, values
        chunk_size = n // (max_points // 2)  # 2 points per chunk (min + max)
        if chunk_size < 1:
            return timestamps, values
        indices = []
        for i in range(0, n, chunk_size):
            chunk = values[i:i + chunk_size]
            if len(chunk) > 0:
                indices.append(i + chunk.argmin())
                indices.append(i + chunk.argmax())
        indices = sorted(set(indices))
        return timestamps[indices], values[indices]

    def _schedule_replot(self):
        """Debounced replot after zoom/pan — waits 200ms of inactivity before replotting."""
        if self._replot_after_id is not None:
            self.after_cancel(self._replot_after_id)
        self._replot_after_id = self.after(200, self._deferred_replot)

    def _deferred_replot(self):
        """Replot with view-aware downsampling after zoom/pan settles."""
        self._replot_after_id = None
        self.plot_data()

    def _draw_label_rectangles(self):
        """Draw label rectangles on the existing axes. Returns the rectangles dict."""
        self.rectangles = {}
        bottom, top = self.current_ylim

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

            # Labels are datetime objects — use directly with mdates
            start_num = mdates.date2num(label.start_time)
            end_num = mdates.date2num(label.end_time)

            rect = Rectangle((start_num, bottom), end_num - start_num, top - bottom, color=color, alpha=alpha, lw=2)

            self.ax.add_patch(rect)
            self.rectangles[label] = rect

    def _redraw_labels(self):
        """Redraw only label rectangles without replotting data lines."""
        # Remove existing label patches
        for patch in self.ax.patches[:]:
            patch.remove()
        self._draw_label_rectangles()
        self.canvas.draw_idle()

    def plot_data(self):
        self.ax.clear()

        # Set Y-limits based on config or defaults
        self.set_y_limits()

        # Plot the labeled sections as semi-transparent boxes
        self._draw_label_rectangles()

        # Determine visible data range for view-aware downsampling
        start_idx, end_idx = self._get_visible_range()

        for axis_display in self.axes_config.axis_displays:
            # Ensure column exists in data
            if axis_display.input_name in self.data.columns and axis_display.input_name in self.active_axes:
                color = axis_display.color
                alpha = axis_display.alpha
                visible_ts = self.data['Timestamp'].values[start_idx:end_idx]
                visible_vals = self.data[axis_display.input_name].values[start_idx:end_idx]
                ts, vals = self._downsample_for_display(visible_ts, visible_vals)
                self.ax.plot(ts, vals, color=color, alpha=alpha,
                             label=axis_display.display_name)

        if self.current_xlim:
            self.ax.set_xlim(self.current_xlim)
        if self.current_ylim:
            self.ax.set_ylim(self.current_ylim)

        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Total Body Acceleration")
        self.ax.set_title(self.project_service.get_plot_title(self.file_entry))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))  # Forces numeric formatting on y-axis

        plt.xticks(rotation=45)
        self.canvas.draw_idle()

    def set_y_limits(self):
        if self.project_config and hasattr(self.project_config, 'y_range'):
            self.current_ylim = list(self.project_config.y_range)
        else:
            self.current_ylim = [-5, 5]

    def save_labels_to_project_config(self):
        """
        Save all the labels for the active file to the project config
        This should be called anytime the labels are changed.
        :return:
        """
        if self.file_entry:
            self.project_service.update_labels(self.file_entry.id, self.labels)
        else:
            logging.warning("Unable to save labels to project config as no file entry found")

    def _get_sorted_other_intervals(self):
        """Return sorted [(start_num, end_num)] for all labels except the selected one."""
        others = sorted(
            [l for l in self.labels if l is not self.selected_label],
            key=lambda l: l.start_time
        )
        return [(mdates.date2num(l.start_time), mdates.date2num(l.end_time)) for l in others]

    def _compute_gaps(self, other_intervals):
        """Return [(gap_min, gap_max)] for the free regions around other_intervals."""
        gaps = []
        prev_end = -np.inf
        for bs, be in other_intervals:
            gaps.append((prev_end, bs))
            prev_end = be
        gaps.append((prev_end, np.inf))
        return gaps

    def _find_gap_for_cursor(self, cursor_x, other_intervals):
        """Return gap index if cursor is in a free region, None if inside a block."""
        for i, (bs, be) in enumerate(other_intervals):
            if cursor_x < bs:
                return i
            if cursor_x <= be:
                return None  # inside block i
        return len(other_intervals)

    def on_mouse_move(self, event):
        # Handle label dragging first (unthrottled for responsiveness)
        if event.inaxes and self.dragging and self.selected_label:
            rect = self.rectangles[self.selected_label]
            other_ivs = self._get_sorted_other_intervals()

            if self.drag_edge == 'start':
                rect_right = rect.get_x() + rect.get_width()
                if event.xdata < rect_right:
                    # Clamp: can't cross the end of the nearest label to the left
                    left_bound = max(
                        (be for _bs, be in other_ivs if be < rect_right),
                        default=-np.inf
                    )
                    clamped = max(event.xdata, left_bound)
                    rect.set_x(clamped)
                    rect.set_width(rect_right - clamped)
                    self.ax.figure.canvas.draw_idle()

            elif self.drag_edge == 'end':
                rect_left = rect.get_x()
                if event.xdata > rect_left:
                    # Clamp: can't cross the start of the nearest label to the right
                    right_bound = min(
                        (bs for bs, _be in other_ivs if bs > rect_left),
                        default=np.inf
                    )
                    clamped = min(event.xdata, right_bound)
                    rect.set_width(clamped - rect_left)
                    self.ax.figure.canvas.draw_idle()

            elif self.drag_edge == 'body':
                gaps = self._compute_gaps(other_ivs)
                # Hop: update gap when cursor exits a block into a new free region
                new_gap = self._find_gap_for_cursor(event.xdata, other_ivs)
                if new_gap is not None:
                    self._drag_gap_idx = new_gap
                gap_min, gap_max = gaps[self._drag_gap_idx]
                natural_start = event.xdata - self._drag_offset
                if gap_max - gap_min <= self._drag_width:
                    new_start = gap_min  # label fills the whole gap
                elif gap_max == np.inf:
                    new_start = max(natural_start, gap_min)
                else:
                    new_start = max(gap_min, min(natural_start, gap_max - self._drag_width))
                rect.set_x(new_start)
                rect.set_width(self._drag_width)
                self.ax.figure.canvas.draw_idle()

            return

        # Throttle remaining processing to ~30fps
        now = _time.monotonic()
        if now - self._last_mouse_move < 0.033:
            return
        self._last_mouse_move = now

        if event.inaxes:
            # Prepare data for cursor report
            cursor_time = mdates.num2date(event.xdata).replace(tzinfo=None) if event.xdata else None
            if not cursor_time:
                time_str = '-'
            else:
                # Format time with milliseconds
                ms = cursor_time.strftime('%f')[:3]
                time_str = cursor_time.strftime('%H:%M:%S') + f".{ms}"
            data_values = {}

            # Binary search for nearest timestamp (O(log n) instead of O(n))
            if cursor_time is not None and self._ts_numeric is not None:
                cursor_ms = int(pd.Timestamp(cursor_time).value // 10**6)
                idx = np.searchsorted(self._ts_numeric, cursor_ms)
                idx = min(max(idx, 0), len(self._ts_numeric) - 1)

                for axis_display in self.axes_config.axis_displays:
                    if axis_display.input_name in self.data.columns:
                        data_values[axis_display.input_name] = f"{self.data.iloc[idx][axis_display.input_name]:.2f}"

            # Update the InfoPane with current cursor position
            if self.info_pane:
                self.info_pane.update_cursor_report(time_str, data_values)

        # Set threshold and handle rectangle edge detection
        x_min, x_max = self.ax.get_xlim()
        axis_width = x_max - x_min
        threshold = axis_width * 0.005  # 0.5% of axis width for detection

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

    def update_plot(self, labels_only=False):
        if labels_only:
            self._redraw_labels()
        else:
            self.plot_data()

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

        # Get the boundaries of the data (using cached values)
        data_min = mdates.date2num(self._data_min)
        data_max = mdates.date2num(self._data_max)

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
        self.current_xlim = self.ax.get_xlim()
        self.current_ylim = self.ax.get_ylim()
        self.canvas.draw_idle()

        # Schedule a debounced replot for view-aware downsampling
        self._schedule_replot()

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
                            # Capture pre-drag state for undo
                            self._drag_start_time = label.start_time
                            self._drag_end_time = label.end_time
                            return
                        elif not self.start_label_time and rect_start < event.xdata < rect_end:
                            # Inside the rectangle — start body drag
                            self.dragging = True
                            self.selected_label = label
                            self.drag_edge = 'body'
                            self.drag_start = event.xdata
                            self._drag_start_time = label.start_time
                            self._drag_end_time = label.end_time
                            self._drag_offset = event.xdata - rect_start
                            self._drag_width = rect.get_width()
                            other_ivs = self._get_sorted_other_intervals()
                            gap_idx = self._find_gap_for_cursor(event.xdata, other_ivs)
                            self._drag_gap_idx = gap_idx if gap_idx is not None else 0
                            return

                if self.start_label_time:
                    # End of labeling — get full datetime from matplotlib
                    end_time = mdates.num2date(event.xdata).replace(tzinfo=None)

                    start_time, end_time = self.validate_user_label_times(self.start_label_time, end_time)
                    print(f"{start_time=},{end_time=}")

                    behavior = self.prompt_for_behavior()
                    if behavior:
                        new_label = Label(start_time, end_time, behavior)
                        self._command_stack.execute(CreateLabelCommand(new_label), self.labels)

                        # Update project config
                        self.parent.set_status(
                            f"New label created: {new_label}; Left click to start labeling a behavior")
                        self.save_labels_to_project_config()
                        self.update_label_list()

                    self.start_label_time = None
                else:
                    # Start of labeling — store full datetime
                    self.start_label_time = mdates.num2date(event.xdata).replace(tzinfo=None)
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
        Ensure that the start time is before the end time. If not, swap them.
        This function also ensures that the label the user is trying to add does not overlap any existing labels.
        Times are datetime objects.
        """
        # Ensure start time is before end time, if not, swap them
        if start_time > end_time:
            start_time, end_time = end_time, start_time

        # Add a buffer to prevent overlap issues (e.g., 1 step buffer)
        buffer = timedelta(milliseconds=self.project_service.get_step_time_ms())

        # Sort labels to ensure proper iteration
        self.labels.sort(key=lambda x: x.start_time)

        for label in self.labels:
            label_start = label.start_time
            label_end = label.end_time

            # Check for overlap and adjust start/end times to prevent it
            if label_start <= start_time <= label_end:
                start_time = label_end + buffer

            if label_start <= end_time <= label_end:
                end_time = label_start - buffer

            # Ensure no overlap by making sure start_time is not after end_time
            if start_time > end_time:
                start_time, end_time = end_time, start_time

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
            old_behavior = label.behavior
            self._command_stack.execute(
                ChangeBehaviorCommand(label, old_behavior, new_behavior), self.labels)
            self.parent.set_status(f"Existing label changed to {new_behavior}")
            self.save_labels_to_project_config()  # Save changes
            self.update_label_list()  # Update the InfoPane display
            self.update_plot(labels_only=True)  # Only redraw labels, not data

    def delete_label(self, label_to_delete):
        """Delete a label and update the plot and project config."""
        index = self.labels.index(label_to_delete)
        self._command_stack.execute(DeleteLabelCommand(label_to_delete, index), self.labels)
        self.save_labels_to_project_config()  # Save the updated labels
        self.update_label_list()  # Update the label display
        self.update_plot(labels_only=True)  # Only redraw labels, not data
        self.parent.set_status(f"Deleted label: {label_to_delete}")

    def on_mouse_release(self, event):
        if self.dragging and self.selected_label:
            # Update the label data only when the mouse is released.
            rect = self.rectangles[self.selected_label]
            if self.drag_edge == 'start':
                new_start = mdates.num2date(rect.get_x()).replace(tzinfo=None)
                new_end = self.selected_label.end_time
            elif self.drag_edge == 'end':
                new_start = self.selected_label.start_time
                new_end = mdates.num2date(rect.get_x() + rect.get_width()).replace(tzinfo=None)
            elif self.drag_edge == 'body':
                new_start = mdates.num2date(rect.get_x()).replace(tzinfo=None)
                new_end = mdates.num2date(rect.get_x() + rect.get_width()).replace(tzinfo=None)
            else:
                new_start = self.selected_label.start_time
                new_end = self.selected_label.end_time

            # Use command stack for undo support (don't re-execute — apply directly)
            cmd = ResizeLabelCommand(
                self.selected_label,
                self._drag_start_time, self._drag_end_time,
                new_start, new_end
            )
            # Apply the new times directly (redo would double-apply since rect already moved)
            self.selected_label.start_time = new_start
            self.selected_label.end_time = new_end
            self.selected_label.duration = self.selected_label.calculate_duration()
            self._command_stack._undo_stack.append(cmd)
            self._command_stack._redo_stack.clear()

            self.dragging = False
            self._redraw_labels()  # Only redraw labels, not data lines
            self.update_label_list()  # Assuming a method to update the list display of labels
            self.save_labels_to_project_config()
            self.canvas.get_tk_widget().config(cursor="")

    def update_label_list(self):
        if self.info_pane:
            self.info_pane.update_label_durations()

    def prompt_for_behavior(self):
        # Retrieve behaviors from the project config
        behaviors = [label.display_name for label in self.project_config.label_display]

        # If there are no behaviors defined, tell the user
        if not behaviors:
            tk.messagebox.showinfo("No Behaviors", "No behavior labels are defined.\nUse Project > Edit Behavior Labels to add behaviors.")
            return None

        # Prompt the user to select a behavior
        dialog = BehaviorSelectionDialog(self, behaviors, title="Select Behavior")
        return dialog.result

    def on_undo(self, event=None):
        """Undo the last label operation."""
        if self._command_stack.undo(self.labels):
            self.save_labels_to_project_config()
            self.update_label_list()
            self.update_plot(labels_only=True)
            self.parent.set_status("Undo")
        else:
            self.parent.set_status("Nothing to undo")

    def on_redo(self, event=None):
        """Redo the last undone label operation."""
        if self._command_stack.redo(self.labels):
            self.save_labels_to_project_config()
            self.update_label_list()
            self.update_plot(labels_only=True)
            self.parent.set_status("Redo")
        else:
            self.parent.set_status("Nothing to redo")

    def clear_plot(self):
        """
        Clear the viewer
        :return:
        """
        self.ax.clear()
        self.labels = []
        self._command_stack.clear()
        self.canvas.draw_idle()  # Redraw the plot

    def zoom_in_on_all_labels(self, event=None):
        """Zoom the plot to fit all the labels from start of the first to end of the last."""
        if not self.labels:
            # No labels to zoom to
            self.parent.set_status("No labels found to fit in the view.")
            return

        # Labels are datetime objects — use directly
        min_start_time = min(label.start_time for label in self.labels)
        max_end_time = max(label.end_time for label in self.labels)

        # Ensure min and max fit within the actual data boundaries (using cached values)
        data_min = self._data_min
        data_max = self._data_max

        if min_start_time < data_min:
            min_start_time = data_min
        if max_end_time > data_max:
            max_end_time = data_max

        # Convert to numeric format for Matplotlib
        min_start_num = mdates.date2num(min_start_time)
        max_end_num = mdates.date2num(max_end_time)

        # Calculate a 5% margin to add to the limits
        data_range = max_end_num - min_start_num
        margin = data_range * 0.05

        # Set new x-axis limits with the margin
        self.ax.set_xlim(min_start_num - margin, max_end_num + margin)

        # Immediate draw then schedule a view-aware replot (same as scroll zoom)
        self.canvas.draw_idle()
        self.current_xlim = self.ax.get_xlim()
        self.current_ylim = self.ax.get_ylim()
        self._schedule_replot()

        self.parent.set_status(f"Zoomed to fit all labels from {min_start_time.strftime('%H:%M:%S')} to {max_end_time.strftime('%H:%M:%S')}.")

    def zoom_out_to_show_all(self, event=None):
        """Zoom the plot to display all available data."""
        if self.data is None or self.data.empty:
            self.parent.set_status("No data available to display.")
            return

        # Get the min and max values of the data's timestamps (using cached values)
        data_min_num = mdates.date2num(self._data_min)
        data_max_num = mdates.date2num(self._data_max)

        # Calculate a 10% margin to add to the limits
        data_range = data_max_num - data_min_num
        margin = data_range * 0.1

        # Set new x-axis limits with the margin
        self.ax.set_xlim(data_min_num - margin, data_max_num + margin)

        # Immediate draw then schedule a view-aware replot (same as scroll zoom)
        self.canvas.draw_idle()
        self.current_xlim = self.ax.get_xlim()
        self.current_ylim = self.ax.get_ylim()
        self._schedule_replot()

        self.parent.set_status("Zoomed out to show all data.")

    def set_axes_config(self, axes_config):
        """Configure the viewer with a given AxesConfig instance."""
        self.axes_config = axes_config
        # Filter out any axis where `display_name` is "Timestamp" (or similar) to avoid plotting it
        self.active_axes = [axis_display.input_name for axis_display in axes_config.axis_displays if
                            axis_display.display_name != "Timestamp"]
        self.update_plot()  # Trigger plot update based on new config

    def get_input_interface(self):
        """
        Initialize and return the appropriate input interface based on the active project's input settings.
        """
        # Retrieve input settings from the project config
        project_config = self.project_service.get_project_config()
        if project_config is None:
            return None
        input_settings = project_config.input_settings
        input_type = input_settings.input_type
        frequency = input_settings.input_frequency

        # Select the concrete input interface based on `input_type`
        if input_type == InputType.VECTRONIC_MOTION:
            return VectronicMotionInput(frequency=frequency)
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
