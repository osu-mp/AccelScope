import json
import logging
import os
from tkinter import filedialog, messagebox

from gui_components.new_project_dialog import NewProjectDialog
from models.project_config import ProjectConfig, DirectoryEntry, FileEntry


class ConfigManager:
    LAST_PROJECT_FILE = 'last_project.json'

    def __init__(self, app_parent):
        self.app_parent = app_parent
        self.current_project_config = None
        self.load_last_project()

    def load_last_project(self):
        """Load the last opened project if available."""
        if os.path.exists(self.LAST_PROJECT_FILE):
            try:
                with open(self.LAST_PROJECT_FILE, 'r') as f:
                    self.active_project = json.load(f).get("active_project", "")
                    if self.active_project and os.path.exists(self.active_project):
                        self.load_project(self.active_project)
                    else:
                        self.prompt_for_project()
            except json.JSONDecodeError:
                self.prompt_for_project()  # Invalid JSON, prompt for a new project
        else:
            self.prompt_for_project()

    def prompt_for_project(self):
        """Prompt the user to load or create a new project (e.g., via a file dialog)."""
        response = messagebox.askyesno("Open Project", "Do you want to open an existing project?")
        if response:
            self.active_project = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")],
                                                             title="Open Project File")
            if self.active_project:
                self.load_project(self.active_project)
        else:
            # Create a new project using NewProjectDialog
            new_project_dialog = NewProjectDialog(parent=self.app_parent)
            new_project_dialog.grab_set()
            self.app_parent.wait_window(new_project_dialog)

            # Load the new project if one was created
            if new_project_dialog.location_entry.get():
                self.active_project = new_project_dialog.location_entry.get()
                self.load_project(self.active_project)

    def save_last_project(self):
        """Save the path of the currently active project to the last_project.json file."""
        if self.active_project:
            with open(self.LAST_PROJECT_FILE, 'w') as f:
                json.dump({"active_project": self.active_project}, f)

    def save_current_project(self):
        """Save the current project configuration to the active project file."""
        if self.current_project_config and self.active_project:
            with open(self.active_project, 'w') as f:
                json.dump(self.current_project_config.to_dict(), f, indent=4)

    def load_project(self, active_project):
        """Loads the project config from the given path and sets it as the active project."""
        try:
            with open(active_project, 'r') as f:
                project_data = json.load(f)
                self.current_project_config = ProjectConfig.from_dict(project_data)
                self.save_last_project()  # Save the path of the current project
            logging.info(f"Loaded project: {active_project}")
        except Exception as e:
            logging.error(f"Error loading project: {e}")

    def get_file_entry(self, file_id):
        """Retrieve the file entry by file ID."""
        if self.current_project_config:
            return self.current_project_config.find_file_by_id(file_id)
        return None

    def update_labels(self, file_id, labels):
        """For the given file id, update the labels in the file and save the changes."""
        file_entry = self.current_project_config.find_file_by_id(file_id)
        if file_entry:
            file_entry.set_labels(labels)
            self.save_current_project()
            logging.info(f"Updated labels for file with ID {file_id}.")
        else:
            logging.error(f"File with ID {file_id} not found.")

    def get_file_path(self, file_entry):
        """Get the full file path for the given file entry."""
        return os.path.join(self.current_project_config.data_root_directory, file_entry.path)

    def get_project_config(self):
        if self.current_project_config:
            return self.current_project_config
        else:
            logging.warn("No active project config")