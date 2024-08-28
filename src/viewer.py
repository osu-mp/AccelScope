import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from accel_data_parser import AccelDataParser  # Ensure correct import based on structure

class Viewer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data_parser = AccelDataParser(data_path)  # Initialize your data parser

    def load_data(self):
        # Load the data using AccelDataParser
        self.data = self.data_parser.read_data()
        self.prepare_plot()

    def prepare_plot(self):
        # Create the main Tkinter window
        self.root = tk.Tk()
        self.root.title("Accelerometer Data Viewer")

        # Create a frame for the plot and controls
        self.frame = tk.Frame(self.root)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Create a frame for the right-side controls (time readout, legend, checkboxes)
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Time readout label
        self.time_label = tk.Label(self.control_frame, text="Time: ")
        self.time_label.pack(pady=10)

        # Checkboxes for axis toggling
        self.x_var = tk.BooleanVar(value=True)
        self.y_var = tk.BooleanVar(value=True)
        self.z_var = tk.BooleanVar(value=True)

        self.x_checkbox = tk.Checkbutton(self.control_frame, text="X-axis", variable=self.x_var, command=self.update_plot)
        self.y_checkbox = tk.Checkbutton(self.control_frame, text="Y-axis", variable=self.y_var, command=self.update_plot)
        self.z_checkbox = tk.Checkbutton(self.control_frame, text="Z-axis", variable=self.z_var, command=self.update_plot)

        self.x_checkbox.pack(anchor=tk.W)
        self.y_checkbox.pack(anchor=tk.W)
        self.z_checkbox.pack(anchor=tk.W)

        # Plot the accelerometer data
        self.plot_data()

        # Bind mouse events
        self.canvas.mpl_connect('motion_notify_event', self.update_time_readout)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def plot_data(self):
        # Clear previous plots
        self.ax.clear()

        # Plot the data based on the selected axes
        if self.x_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc X [g]'], label='X-axis')
        if self.y_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc Y [g]'], label='Y-axis')
        if self.z_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc Z [g]'], label='Z-axis')

        # Update the legend
        self.ax.legend(loc='upper left', bbox_to_anchor=(1, 1))

        # Format x-axis to show time
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))  # Format the ticks as HH:MM:SS
        plt.xticks(rotation=45)

        # Redraw the canvas
        self.canvas.draw()

    def update_time_readout(self, event):
        # Update the time readout label based on the cursor position
        if event.inaxes:
            # Convert cursor x-position to time including milliseconds
            time_str = mdates.num2date(event.xdata).strftime('%H:%M:%S.%f')[:-3]  # Truncate to milliseconds

            # Find the nearest time index in the data
            cursor_time = pd.Timestamp(mdates.num2date(event.xdata)).tz_localize(None)
            nearest_index = self.data['Timestamp'].sub(cursor_time).abs().idxmin()

            # Get corresponding x, y, z values
            x_val = self.data['Acc X [g]'].iloc[nearest_index]
            y_val = self.data['Acc Y [g]'].iloc[nearest_index]
            z_val = self.data['Acc Z [g]'].iloc[nearest_index]

            # Update the label with time and acceleration values
            self.time_label.config(text=f"Time: {time_str} \n X: {x_val:.3f}g \n Y: {y_val:.3f}g \n Z: {z_val:.3f}g")

    def update_plot(self):
        # Update the plot based on checkbox states
        self.plot_data()

    def on_scroll(self, event):
        if event.key == 'control':
            # Zoom functionality
            xlim = self.ax.get_xlim()
            xdata = mdates.num2date(event.xdata)  # Convert the xdata to datetime

            if xdata is None:
                return

            zoom_factor = 1.2 if event.button == 'up' else 1 / 1.2

            # Calculate new x-axis limits based on cursor position
            x_range = (xlim[1] - xlim[0]) / zoom_factor
            new_xlim = [
                mdates.date2num(xdata - (xdata - mdates.num2date(xlim[0])) / zoom_factor),
                mdates.date2num(xdata + (mdates.num2date(xlim[1]) - xdata) / zoom_factor)
            ]

            # Apply new limits
            self.ax.set_xlim(new_xlim)
            self.canvas.draw_idle()

        else:
            # Panning functionality
            xlim = self.ax.get_xlim()
            x_range = mdates.num2date(xlim[1]) - mdates.num2date(xlim[0])

            shift = pd.Timedelta(seconds=x_range.total_seconds() * 0.05)

            if event.button == 'down':
                # Scroll down pans left
                new_xlim = [mdates.num2date(xlim[0]) - shift, mdates.num2date(xlim[1]) - shift]
            elif event.button == 'up':
                # Scroll up pans right
                new_xlim = [mdates.num2date(xlim[0]) + shift, mdates.num2date(xlim[1]) + shift]

            # Convert all timestamps to the same timezone-aware/naive state
            data_min = pd.Timestamp(self.data['Timestamp'].min()).tz_localize(None)
            data_max = pd.Timestamp(self.data['Timestamp'].max()).tz_localize(None)

            # Ensure panning doesn't go beyond the data limits
            new_xlim[0] = max(data_min, new_xlim[0].replace(tzinfo=None))
            new_xlim[1] = min(data_max, new_xlim[1].replace(tzinfo=None))

            # Apply the new limits
            self.ax.set_xlim(mdates.date2num(new_xlim))  # Convert datetime objects to Matplotlib format
            self.canvas.draw_idle()

    def run(self):
        # Load the data and start the GUI loop
        self.load_data()
        self.root.mainloop()
