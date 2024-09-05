import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import tkinter as tk
from tkinter import simpledialog, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from accel_data_parser import AccelDataParser


class Label:        # TODO: move out of this file
    def __init__(self, start_time, end_time, behavior):
        self.start_time = start_time
        self.end_time = end_time
        self.behavior = behavior
        self.duration = self.end_time - self.start_time

    def __str__(self):
        # Format the start_time and end_time to show only the time
        start_time_str = self.start_time.strftime('%H:%M:%S.%f')[:-3]
        end_time_str = self.end_time.strftime('%H:%M:%S.%f')[:-3]

        return f"{self.behavior} : {start_time_str} - {end_time_str} ({self.duration})"


class BehaviorDialog(simpledialog.Dialog):      # TODO: move out of this file
    def body(self, master):
        tk.Label(master, text="Select Behavior:").grid(row=0)
        self.var = tk.StringVar(master)
        self.var.set("Stalk")  # default value
        self.options = ['Stalk', 'Kill Phase 1', 'Kill Phase 2', 'Feeding', 'Walking']
        self.dropdown = ttk.Combobox(master, textvariable=self.var, values=self.options, state='readonly')
        self.dropdown.grid(row=0, column=1)
        return self.dropdown  # return the dropdown as the initial focus widget

    def apply(self):
        self.result = self.var.get()  # set the result from the dialog to the selected option


class Viewer(tk.Frame):
    def __init__(self, parent, data_path, **kwargs):
        super().__init__(parent, **kwargs)
        self.data_path = data_path
        self.data_parser = AccelDataParser(data_path)
        self.labels = []
        self.start_label_time = None
        self.current_xlim = None  # used to keep pan/zoom consistent across user actions
        self.current_ylim = None
        self.selected_label = None
        self.dragging = False
        self.load_data()

    def load_data(self):
        self.data = self.data_parser.read_data()
        self.prepare_plot()
        self.set_initial_limits()

    # Initialize plot limits after data is loaded
    def set_initial_limits(self):
        self.current_xlim = [self.data['Timestamp'].min(), self.data['Timestamp'].max()]
        self.ax.set_xlim(self.current_xlim)
        self.ax.set_ylim([self.data[['Acc X [g]', 'Acc Y [g]', 'Acc Z [g]']].min().min(),
                          self.data[['Acc X [g]', 'Acc Y [g]', 'Acc Z [g]']].max().max()])
        self.canvas.draw()

    def prepare_plot(self):
        # Setup the matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)  # Use self as the master
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Right control frame for additional controls and info
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox for user labels
        self.user_labels_listbox = tk.Listbox(self.control_frame, height=10)
        self.user_labels_listbox.pack(pady=20)

        # Time label display
        self.time_label = tk.Label(self.control_frame, text="Time: ")
        self.time_label.pack(pady=10)

        # Status label display
        self.status_label = tk.Label(self.control_frame, text="Left click to start labeling a behavior")
        self.status_label.pack(pady=10)

        # Checkboxes for axis control
        self.x_var = tk.BooleanVar(value=True)
        self.y_var = tk.BooleanVar(value=True)
        self.z_var = tk.BooleanVar(value=True)
        self.x_checkbox = tk.Checkbutton(self.control_frame, text="X-axis", variable=self.x_var,
                                         command=self.update_plot)
        self.y_checkbox = tk.Checkbutton(self.control_frame, text="Y-axis", variable=self.y_var,
                                         command=self.update_plot)
        self.z_checkbox = tk.Checkbutton(self.control_frame, text="Z-axis", variable=self.z_var,
                                         command=self.update_plot)
        self.x_checkbox.pack(anchor=tk.W)
        self.y_checkbox.pack(anchor=tk.W)
        self.z_checkbox.pack(anchor=tk.W)

        # Plot the initial data
        self.plot_data()

        # Connect mouse and scroll events
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)

    def plot_data(self):
        self.ax.clear()

        # Define colors for each behavior
        behavior_colors = {
            'Stalk': 'orange',
            'Kill Phase 1': 'purple',
            'Kill Phase 2': 'green',
            'Feeding': 'blue',
            'Walking': 'red'
        }
        self.rectangles = {}

        # Plot the labeled sections as semi-transparent boxes
        for label in self.labels:
            color = behavior_colors.get(label.behavior, 'gray')  # Default to gray if behavior is unknown
            start_num = mdates.date2num(label.start_time)
            end_num = mdates.date2num(label.end_time)

            bottom, top = self.current_ylim
            rect = Rectangle((start_num, bottom), end_num - start_num, top - bottom, color=color, alpha=0.2, lw=2,
                             edgecolor=color, label=label.behavior)

            self.ax.add_patch(rect)
            self.rectangles[label] = rect

        # Plot the accelerometer data based on the selected axes
        if self.x_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc X [g]'], label='X-axis', color='red', alpha=0.6)
        if self.y_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc Y [g]'], label='Y-axis', color='black', alpha=0.5)
        if self.z_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc Z [g]'], label='Z-axis', color='blue', alpha=0.7)

        if self.current_xlim:
            self.ax.set_xlim(self.current_xlim)
        if self.current_ylim:
            self.ax.set_ylim(self.current_ylim)

        # Update the legend
        self.ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)

    def on_mouse_move(self, event):
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

        near_edge = False
        for label, rect in self.rectangles.items():
            if event.xdata and (abs(rect.get_x() - event.xdata) <= 0.01 or abs(
                    rect.get_x() + rect.get_width() - event.xdata) <= 0.01):
                self.canvas.get_tk_widget().config(cursor="sb_h_double_arrow")
                self.selected_label = label
                near_edge = True
                break
        if not near_edge:
            self.canvas.get_tk_widget().config(cursor="")
            self.selected_label = None

    def update_plot(self):
        self.plot_data()
        self.canvas.draw()

    def on_scroll(self, event):
        if event.key == 'control':
            xlim = self.ax.get_xlim()
            xdata = mdates.num2date(event.xdata)
            if xdata is None:
                return
            zoom_factor = 1.2 if event.button == 'up' else 1 / 1.2
            x_range = (xlim[1] - xlim[0]) / zoom_factor
            new_xlim = [
                mdates.date2num(xdata - (xdata - mdates.num2date(xlim[0])) / zoom_factor),
                mdates.date2num(xdata + (mdates.num2date(xlim[1]) - xdata) / zoom_factor)
            ]
            self.ax.set_xlim(new_xlim)
            self.canvas.draw_idle()
        else:
            xlim = self.ax.get_xlim()
            x_range = mdates.num2date(xlim[1]) - mdates.num2date(xlim[0])
            shift = pd.Timedelta(seconds=x_range.total_seconds() * 0.05)
            if event.button == 'down':
                new_xlim = [mdates.num2date(xlim[0]) - shift, mdates.num2date(xlim[1]) - shift]
            elif event.button == 'up':
                new_xlim = [mdates.num2date(xlim[0]) + shift, mdates.num2date(xlim[1]) + shift]
            data_min = pd.Timestamp(self.data['Timestamp'].min()).tz_localize(None)
            data_max = pd.Timestamp(self.data['Timestamp'].max()).tz_localize(None)
            new_xlim[0] = max(data_min, new_xlim[0].replace(tzinfo=None))
            new_xlim[1] = min(data_max, new_xlim[1].replace(tzinfo=None))
            self.ax.set_xlim(mdates.date2num(new_xlim))
            self.canvas.draw_idle()

        self.current_xlim = self.ax.get_xlim()  # Update stored x limits after interaction
        self.current_ylim = self.ax.get_ylim()  # Update stored y limits after interaction
        self.canvas.draw_idle()

    def on_click(self, event):
        if event.inaxes:
            if event.button == 1:  # Left click
                for label, rect in self.rectangles.items():
                    if event.xdata and (abs(rect.get_x() - event.xdata) <= 0.01):
                        self.dragging = True
                        self.selected_label = label
                        self.drag_edge = 'start'  # Dragging the start edge
                        self.drag_start = event.xdata
                        return
                    elif event.xdata and (abs(rect.get_x() + rect.get_width() - event.xdata) <= 0.01):
                        self.dragging = True
                        self.selected_label = label
                        self.drag_edge = 'end'  # Dragging the end edge
                        self.drag_start = event.xdata
                        return

                if self.start_label_time:
                    # End of labeling
                    end_time = mdates.num2date(event.xdata)
                    behavior = self.prompt_for_behavior()
                    if behavior:
                        new_label = Label(self.start_label_time, end_time, behavior)
                        self.labels.append(new_label)
                        self.user_labels_listbox.insert(tk.END, str(new_label))
                    self.start_label_time = None
                    self.status_label.config(text="Left click to start labeling a behavior")
                else:
                    # Start of labeling
                    self.start_label_time = mdates.num2date(event.xdata)
                    self.status_label.config(text="Left click to label end of behavior or right click to cancel")
            elif event.button == 3:  # Right click
                # Cancel labeling
                if self.start_label_time:
                    self.start_label_time = None
                    self.status_label.config(text="Left click to start labeling a behavior")

            self.update_plot()
            self.current_xlim = self.ax.get_xlim()  # Store limits after interaction
            self.current_ylim = self.ax.get_ylim()

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

            self.canvas.get_tk_widget().config(cursor="")

    def update_label_list(self):
        # Clear existing entries in the listbox
        self.user_labels_listbox.delete(0, tk.END)

        # Repopulate the listbox with updated label data
        for label in sorted(self.labels, key=lambda x: x.start_time):  # Sort labels by start time
            self.user_labels_listbox.insert(tk.END, str(label))

    def prompt_for_behavior(self):
        # Prompt the user to select a behavior
        dialog = BehaviorDialog(None, title="Select Behavior")
        return dialog.result


    def run(self):
        self.load_data()
        self.root.mainloop()
