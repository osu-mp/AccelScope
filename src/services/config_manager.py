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
        if os.path.exists(self.LAST_PROJECT_FILE):
            try:
                with open(self.LAST_PROJECT_FILE, 'r') as f:
                    last_project_data = json.load(f)
                    self.last_project = last_project_data.get("last_opened_project", "")
                    self.last_file_id = last_project_data.get("last_opened_file_id", None)

                    if self.last_project and os.path.exists(self.last_project):
                        self.load_project(self.last_project)
                    else:
                        self.prompt_for_project()
            except json.JSONDecodeError:
                self.prompt_for_project()  # Invalid JSON, prompt for a new project
        else:
            self.prompt_for_project()

    def try_to_load_last_csv(self):
        if self.last_file_id:
            file_entry = self.current_project_config.find_file_by_id(self.last_file_id)
            if file_entry:
                self.app_parent.viewer.load_file_entry(file_entry)
            else:
                logging.warning(f"File with ID {self.last_file_id} not found.")
        else:
            logging.info("No last file ID found.")
    def prompt_for_project(self):
        """Prompt the user to load or create a new project (e.g., via a file dialog)."""
        response = messagebox.askyesno("Open Project", "Do you want to open an existing project?")
        if response:
            self.last_project = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")],
                                                             title="Open Project File")
            if self.last_project:
                self.load_project(self.last_project)
        else:
            # Create a new project using NewProjectDialog
            new_project_dialog = NewProjectDialog(parent=self.app_parent)
            new_project_dialog.grab_set()
            self.app_parent.wait_window(new_project_dialog)

            # Load the new project if one was created
            if new_project_dialog.location_entry.get():
                self.last_project = new_project_dialog.location_entry.get()
                self.load_project(self.last_project)

    def save_last_project(self, project_path, file_id=None):
        """Save the last opened project path and file_id to a JSON file."""
        last_project_data = {
            "last_opened_project": project_path,
            "last_opened_file_id": file_id  # Save file_id if available
        }
        with open(self.LAST_PROJECT_FILE, 'w') as f:
            json.dump(last_project_data, f, indent=4)

    def save_current_project(self):
        """Save the current project configuration to the active project file."""
        if self.current_project_config and self.last_project:
            with open(self.last_project, 'w') as f:
                json.dump(self.current_project_config.to_dict(), f, indent=4)

    def load_project(self, active_project):
        """Loads the project config from the given path and sets it as the active project."""
        try:
            with open(active_project, 'r') as f:
                project_data = json.load(f)
                self.current_project_config = ProjectConfig.from_dict(project_data)
            logging.info(f"Loaded project: {active_project}")
            self.last_project = active_project
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

    def get_label_display(self, behavior):
        """Retrieve the label display settings for a given behavior from the project config."""
        if self.current_project_config:
            # Iterate through the label display section of the project config to find the behavior
            for label_display in self.current_project_config.label_display:
                if label_display.display_name == behavior:
                    return label_display
        return None