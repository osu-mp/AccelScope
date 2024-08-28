import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from accel_data_parser import AccelDataParser

class Label:
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

class Viewer:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data_parser = AccelDataParser(data_path)
        self.labels = []
        self.start_label_time = None

    def load_data(self):
        self.data = self.data_parser.read_data()
        self.prepare_plot()

    def prepare_plot(self):
        self.root = tk.Tk()
        self.root.title("Accelerometer Data Viewer")

        self.frame = tk.Frame(self.root)
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.time_label = tk.Label(self.control_frame, text="Time: ")
        self.time_label.pack(pady=10)

        self.status_label = tk.Label(self.control_frame, text="Left click to start labeling a behavior")
        self.status_label.pack(pady=10)

        self.x_var = tk.BooleanVar(value=True)
        self.y_var = tk.BooleanVar(value=True)
        self.z_var = tk.BooleanVar(value=True)

        self.x_checkbox = tk.Checkbutton(self.control_frame, text="X-axis", variable=self.x_var, command=self.update_plot)
        self.y_checkbox = tk.Checkbutton(self.control_frame, text="Y-axis", variable=self.y_var, command=self.update_plot)
        self.z_checkbox = tk.Checkbutton(self.control_frame, text="Z-axis", variable=self.z_var, command=self.update_plot)

        self.x_checkbox.pack(anchor=tk.W)
        self.y_checkbox.pack(anchor=tk.W)
        self.z_checkbox.pack(anchor=tk.W)

        self.plot_data()

        self.canvas.mpl_connect('motion_notify_event', self.update_time_readout)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def plot_data(self):
        self.ax.clear()

        if self.x_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc X [g]'], label='X-axis')
        if self.y_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc Y [g]'], label='Y-axis')
        if self.z_var.get():
            self.ax.plot(self.data['Timestamp'], self.data['Acc Z [g]'], label='Z-axis')

        self.ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)

        self.canvas.draw()

    def update_time_readout(self, event):
        if event.inaxes:
            time_str = mdates.num2date(event.xdata).strftime('%H:%M:%S.%f')[:-3]
            cursor_time = pd.Timestamp(mdates.num2date(event.xdata)).tz_localize(None)
            nearest_index = self.data['Timestamp'].sub(cursor_time).abs().idxmin()
            x_val = self.data['Acc X [g]'].iloc[nearest_index]
            y_val = self.data['Acc Y [g]'].iloc[nearest_index]
            z_val = self.data['Acc Z [g]'].iloc[nearest_index]
            self.time_label.config(text=f"Time: {time_str} \n X: {x_val:.3f}g \n Y: {y_val:.3f}g \n Z: {z_val:.3f}g")

    def update_plot(self):
        self.plot_data()

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

    def on_click(self, event):
        if event.inaxes:
            if event.button == 1:  # Left click
                if self.start_label_time:
                    # End of labeling
                    end_time = mdates.num2date(event.xdata)
                    behavior = self.prompt_for_behavior()
                    if behavior:
                        self.labels.append(Label(self.start_label_time, end_time, behavior))
                        print("Labels")
                        for label in self.labels:
                            print(label)
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

    def prompt_for_behavior(self):
        # Prompt the user to select a behavior
        behavior = tk.simpledialog.askstring("Select Behavior", "Enter behavior (Stalk, Kill Phase 1, Kill Phase 2, Feeding, Walking):")
        valid_behaviors = ['Stalk', 'Kill Phase 1', 'Kill Phase 2', 'Feeding', 'Walking']
        if behavior in valid_behaviors:
            return behavior
        else:
            tk.messagebox.showerror("Invalid Input", "Please enter a valid behavior.")
            return None

    def run(self):
        self.load_data()
        self.root.mainloop()
