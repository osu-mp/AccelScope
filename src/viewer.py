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

        # Create a Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Plot the accelerometer data
        self.plot_data()

        # Bind mouse events
        self.canvas.mpl_connect('button_press_event', self.mark_point)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def plot_data(self):
        # Plot the data (example code, adjust as necessary)
        self.ax.plot(self.data['Timestamp'], self.data['Acc X [g]'], label='X-axis')
        self.ax.plot(self.data['Timestamp'], self.data['Acc Y [g]'], label='Y-axis')
        self.ax.plot(self.data['Timestamp'], self.data['Acc Z [g]'], label='Z-axis')
        self.ax.legend()
        self.ax.set_title('Accelerometer Data')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Acceleration')

        # Format x-axis to show time
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))  # Format the ticks as HH:MM:SS

        # Rotate and format the x labels
        plt.xticks(rotation=45)

        self.canvas.draw()

    def mark_point(self, event):
        # Function to mark points on the graph with a click
        pass  # Implement as needed

    def on_scroll(self, event):
        # Function to handle zooming and panning
        pass  # Implement as needed

    def run(self):
        # Load the data and start the GUI loop
        self.load_data()
        self.root.mainloop()
