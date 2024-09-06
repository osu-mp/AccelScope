import json
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

class ProjectConfig:
    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.data_root_directory = None
        self.root_directory = Directory("Root")

    def initialize_empty_config(self, data_root_directory):
        self.data_root_directory = data_root_directory
        self.root_directory = Directory("Root")  # Reinitialize to ensure it's empty

    def load_config(self):
        if self.config_path.exists():
            with open(self.config_path, 'r') as file:
                data = json.load(file)
                self.data_root_directory = data['data_root_directory']
                self.root_directory = Directory.from_dict(data['root_directory'])

    def save_config(self):
        with open(self.config_path, 'w') as file:
            data = {
                "data_root_directory": self.data_root_directory,
                "root_directory": self.root_directory.to_dict()
            }
            json.dump(data, file, indent=4)