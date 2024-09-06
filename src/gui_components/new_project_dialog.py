import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from src.services.project_config import ProjectConfig

class NewProjectDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("New Project")
        self.geometry("400x300")

        # Project Location
        ttk.Label(self, text="Project File Location:").pack()
        self.location_entry = ttk.Entry(self)
        self.location_entry.pack(fill=tk.X)
        ttk.Button(self, text="Browse", command=self.select_file).pack()

        # Data Root
        ttk.Label(self, text="Input data root:").pack()
        self.data_root_entry = ttk.Entry(self)
        self.data_root_entry.pack(fill=tk.X)
        ttk.Button(self, text="Browse", command=self.select_directory).pack()

        # Output Style
        ttk.Label(self, text="Output Style:").pack()
        self.output_style = ttk.Combobox(self, values=["Output all data", "Output data only between labels"])
        self.output_style.pack(fill=tk.X)

        # Confirmation Buttons
        ttk.Button(self, text="Cancel", command=self.destroy).pack()
        ttk.Button(self, text="Create Project", command=self.create_project).pack()

    def select_file(self):
        # Prompt the user to select a file path for saving a JSON file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Project File"
        )

        if not file_path:
            return  # User cancelled the dialog

        # Check if the file already exists
        try:
            with open(file_path, 'r') as f:
                # If the file can be opened, ask for confirmation to overwrite
                if messagebox.askokcancel("Confirm Overwrite",
                                          "This file already exists. Do you want to overwrite it?"):
                    self.location_entry.delete(0, tk.END)
                    self.location_entry.insert(0, file_path)
                # Otherwise, do not do anything, the user cancelled the overwrite
        except FileNotFoundError:
            # File does not exist, so it's safe to use the selected file path
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, file_path)

    def select_directory(self):
        directory = filedialog.askdirectory()
        self.data_root_entry.delete(0, tk.END)
        self.data_root_entry.insert(0, directory)

    def create_project(self):
        # Get values from the dialog's input fields
        location = self.location_entry.get()
        data_root = self.data_root_entry.get()

        print("Creating project at:", location)
        print(f"{data_root=}")

        # Initialize the project configuration with the specified location
        project_config = ProjectConfig(location)
        project_config.initialize_empty_config(data_root)

        # Save the new configuration to create the JSON file
        project_config.save_config()

        # Close the dialog after creating the project
        self.destroy()
