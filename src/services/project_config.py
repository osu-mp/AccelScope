import json
import logging
from pathlib import Path

from models.label import Label

class Directory:
    def __init__(self, name):
        self.name = name
        self.entries = []  # This will contain both Directory and FileEntry instances

    def to_dict(self):
        return {
            "name": self.name,
            "entries": [entry.to_dict() for entry in self.entries]
        }

    @staticmethod
    def from_dict(data):
        dir = Directory(data['name'])
        for entry in data['entries']:
            if 'behavior' in entry:
                dir.entries.append(Label.from_dict(entry))
            elif 'path' in entry:
                dir.entries.append(FileEntry.from_dict(entry))
            else:
                dir.entries.append(Directory.from_dict(entry))
        return dir

class FileEntry:
    def __init__(self, path):
        self.path = path
        self.labels = []

    def to_dict(self):
        return {
            "path": self.path,
            "labels": [label.to_dict() for label in self.labels]
        }

    @staticmethod
    def from_dict(data):
        file_entry = FileEntry(data['path'])
        file_entry.labels = [Label.from_dict(label) for label in data['labels']]
        return file_entry

    def set_labels(self, labels):
        # TODO verify labels
        self.labels = labels

class ProjectConfig:
    def __init__(self, config_path):
        self.proj_name = "TBD"
        self.config_path = Path(config_path)
        self.data_root_directory = None
        self.root_directory = Directory(self.proj_name)
        self.load_config()

    def initialize_empty_config(self, data_root_directory):
        self.data_root_directory = data_root_directory
        self.root_directory = Directory(self.proj_name)  # Reinitialize to ensure it's empty

    def set_proj_name(self, proj_name):
        self.proj_name = proj_name

    def load_config(self):
        logging.info(f"Loading project config from {self.config_path}")
        if self.config_path.exists():
            with open(self.config_path, 'r') as file:
                data = json.load(file)
                self.proj_name = data['proj_name']
                self.data_root_directory = data['data_root_directory']
                self.root_directory = Directory.from_dict(data['root_directory'])
                # self.root_directory = Directory.from_dict(data['root'])

    def save_config(self):
        try:
            with open(self.config_path, 'w') as file:
                data = {
                    "proj_name": self.proj_name,
                    "data_root_directory": self.data_root_directory,
                    "root_directory": self.root_directory.to_dict(),
                }
                json.dump(data, file, indent=4)
            logging.info(f"Configuration saved successfully to: {self.config_path}")
        except Exception as e:
            logging.error("Failed to save configuration:", e)

    def add_directory(self, parent_full_path, new_dir_name, full_new_path):
        # Find the parent directory using the full path
        parent_dir = self.find_directory_by_path(parent_full_path)
        if parent_dir:
            new_dir = Directory(new_dir_name)
            parent_dir.entries.append(new_dir)
            print(f"Added {new_dir_name} under {parent_dir.name}")
            self.save_config()  # Debug: Save and check JSON file
        else:
            print(f"Parent directory not found for path: {parent_full_path}")

    def find_directory_by_path(self, path):
        if not path or path == "/":  # If the path is empty or root
            return self.root_directory

        # Split the path and traverse the directory structure
        segments = path.strip('/').split('/')  # Remove leading/trailing slashes and split into segments
        current_dir = self.root_directory

        # Check if the root directory name matches the first segment
        if segments[0] != current_dir.name:
            return None  # If the root doesn't match, return None

        # Traverse the path from the root directory
        for segment in segments[1:]:
            found = False
            for entry in current_dir.entries:
                if isinstance(entry, Directory) and entry.name == segment:
                    current_dir = entry
                    found = True
                    break
            if not found:
                return None  # If no matching directory is found, return None

        return current_dir  # Return the directory found at the end of the path

    def add_file(self, parent_full_path, file_entry):
        parent_dir = self.find_directory_by_path(parent_full_path)

        if parent_dir:
            parent_dir.entries.append(file_entry)
        else:
            print(f"Parent directory not found for path: {parent_full_path}")

    def find_file_by_name(self, file_name):
        """Recursively searches the directory structure to find a file by its name."""
        return self._search_file(self.root_directory, file_name)

    def _search_file(self, directory, file_name):
        """Helper method to recursively search through directories and find the matching file."""
        for entry in directory.entries:
            if isinstance(entry, FileEntry) and entry.path.endswith(file_name):
                return entry
            elif isinstance(entry, Directory):
                found = self._search_file(entry, file_name)
                if found:
                    return found
        return None
