import json
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

        # self.json_file_path = json_file_path
        # self.project_config = None

    def load_last_project(self):
        if os.path.exists(self.LAST_PROJECT_FILE):
            try:
                with open(self.LAST_PROJECT_FILE, 'r') as f:
                    last_project = json.load(f).get("last_opened_project", "")
                    if last_project and os.path.exists(last_project):
                        self.load_project(last_project)
                    else:
                        self.prompt_for_project()
            except json.JSONDecodeError:
                self.prompt_for_project()  # Invalid JSON, prompt for new project
        else:
            self.prompt_for_project()

    def prompt_for_project(self):
        """Prompt the user to load or create a new project (e.g., via a file dialog)."""
        # Here, you would include logic to show a file dialog
        response = messagebox.askyesno("Open Project", "Do you want to open an existing project?")
        if response:
            # Open file dialog to select an existing project JSON file
            project_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Open Project File")
            if project_path:
                self.load_project(project_path)
        else:
            # Open the NewProjectDialog to create a new project
            new_project_dialog = NewProjectDialog(parent=self.app_parent)
            new_project_dialog.grab_set()
            self.app_parent.wait_window(new_project_dialog)  # Wait for the dialog to close

            # If a new project was created, load it
            if new_project_dialog.location_entry.get():
                project_path = new_project_dialog.location_entry.get()
                self.load_project(project_path)

    def save_last_project(self, project_path):
        """Save the last opened project path to a JSON file."""
        with open(self.LAST_PROJECT_FILE, 'w') as f:
            json.dump({"last_opened_project": project_path}, f)

    def save_current_project(self):
        """Save the current project config back to its JSON file."""
        if self.current_project_config:
            project_path = self.current_project_config.project_path
            with open(project_path, 'w') as f:
                json.dump(self.current_project_config.to_dict(), f)

    def load_project(self, project_path):
        """Loads the project config from the given path and sets it as the current config."""
        try:
            with open(project_path, 'r') as f:
                project_data = json.load(f)
                self.current_project_config = ProjectConfig.from_dict(project_data)
                self.save_last_project(project_path)
            self.project_config = ProjectConfig.from_dict(project_data)
        except Exception as e:
            print(f"Error loading project: {e}")

    def get_file_entry(self, file_id):
        """Retrieve the file entry, ensuring it's only looked up once."""
        if self.project_config:
            return self.project_config.find_file_by_id(file_id)
        return None

    def load_config(self):
        """Loads the project configuration from the specified JSON file."""
        with open(self.json_file_path, 'r') as f:
            data = json.load(f)
            root_directory = self._build_directory(data['root_directory'])
            self.project_config = ProjectConfig(data['proj_name'], data['data_root_directory'], root_directory)

    def _build_directory(self, directory_data):
        """Recursively builds a Directory instance from JSON data."""
        directory = DirectoryEntry(directory_data['name'])
        for entry in directory_data['entries']:
            if 'path' in entry:
                file_entry = FileEntry(entry['path'], entry.get('labels', []))
                directory.entries.append(file_entry)
            else:
                sub_directory = self._build_directory(entry)
                directory.entries.append(sub_directory)
        return directory

    def save_config(self):
        """Saves the current project configuration to the JSON file."""
        with open(self.json_file_path, 'w') as f:
            json.dump(self._to_dict(self.project_config), f, indent=4, default=str)

    def _to_dict(self, project_config):
        """Converts the ProjectConfig and its directories/files to a dictionary."""
        return {
            'proj_name': project_config.proj_name,
            'data_root_directory': project_config.data_root_directory,
            'root_directory': self._directory_to_dict(project_config.root_directory)
        }

    def _directory_to_dict(self, directory):
        """Recursively converts a Directory instance to a dictionary."""
        dir_dict = {'name': directory.name, 'entries': []}
        for entry in directory.entries:
            if isinstance(entry, FileEntry):
                dir_dict['entries'].append({'path': entry.path, 'labels': entry.labels})
            elif isinstance(entry, DirectoryEntry):
                dir_dict['entries'].append(self._directory_to_dict(entry))
        return dir_dict

    def get_project_config(self):
        """Returns the currently loaded project configuration."""
        return self.project_config

    def get_file_path(self, file_entry):

        file_path = os.path.join(self.project_config.data_root_directory, file_entry.path)
        return file_path

    def update_labels(self, file_name, new_labels):
        """Updates the labels for a specific file and saves the updated config."""
        file_entry = self.project_config.find_file_by_name(file_name)
        if file_entry:
            file_entry.labels = new_labels
            self.save_config()  # Save after modifying labels
