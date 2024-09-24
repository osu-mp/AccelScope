import logging
from models.label import Label


class DirectoryEntry:
    def __init__(self, name, entries=None):
        self.name = name
        self.entries = entries or []  # This will contain both DirectoryEntry and FileEntry instances

    def to_dict(self):
        return {
            "name": self.name,
            "entries": [entry.to_dict() for entry in self.entries]
        }

    @staticmethod
    def from_dict(data):
        entries = []
        for entry in data.get("entries", []):
            if "path" in entry:
                entries.append(FileEntry.from_dict(entry))
            else:
                entries.append(DirectoryEntry.from_dict(entry))
        return DirectoryEntry(data["name"], entries)


class FileEntry:
    def __init__(self, path, file_id, labels=None):
        self.path = path
        self.file_id = file_id
        self.labels = labels or []

    def to_dict(self):
        return {
            "path": self.path,
            "id": self.file_id,
            "labels": [label.to_dict() for label in self.labels]
        }

    @staticmethod
    def from_dict(data):
        labels = [Label.from_dict(label) for label in data.get("labels", [])]
        return FileEntry(data["path"], data["id"], labels)

    def set_labels(self, labels):
        self.labels = labels


class ProjectConfig:
    def __init__(self, proj_name, data_root_directory, entries=None):
        self.proj_name = proj_name
        self.data_root_directory = data_root_directory
        self.entries = entries or []

    def to_dict(self):
        """Convert ProjectConfig instance back to a dictionary."""
        return {
            'proj_name': self.proj_name,
            'data_root_directory': self.data_root_directory,
            'entries': [entry.to_dict() for entry in self.entries]
        }

    @staticmethod
    def from_dict(data):
        logging.debug(f"Creating ProjectConfig from dict: {data}")
        entries = [DirectoryEntry.from_dict(entry) for entry in data.get("entries", [])]
        return ProjectConfig(data["proj_name"], data["data_root_directory"], entries)

    def add_directory(self, parent_full_path, new_dir_name):
        # Find the parent directory using the full path
        logging.debug(f"Adding directory {new_dir_name} under path {parent_full_path}")
        parent_dir = self.find_directory_by_path(parent_full_path)
        if parent_dir:
            new_dir = DirectoryEntry(new_dir_name)
            parent_dir.entries.append(new_dir)  # Append to the entries of the DirectoryEntry
            logging.debug(f"Added directory {new_dir_name} under {parent_dir.name}")
        else:
            logging.error(f"Parent directory not found for path: {parent_full_path}")

    def find_directory_by_path(self, path):
        logging.debug(f"Finding directory by path: {path}")

        # If the path is empty or root, return the top-level entries
        if not path or path == "/":
            return self.entries

        # Split the path and traverse the directory structure
        segments = path.strip('/').split('/')  # Remove leading/trailing slashes and split into segments
        current_entries = self.entries

        # Traverse the path from the top-level entries
        for segment in segments:
            found = False
            for entry in current_entries:
                if isinstance(entry, DirectoryEntry) and entry.name == segment:
                    current_entries = entry.entries
                    found = True
                    break
            if not found:
                logging.error(f"Directory '{segment}' not found in path.")
                return None  # If no matching directory is found, return None

        # Return the final DirectoryEntry object instead of the list of entries
        return entry if isinstance(entry, DirectoryEntry) else None

    def add_file(self, parent_full_path, file_entry):
        logging.debug(f"Adding file {file_entry.path} under path {parent_full_path}")
        parent_dir = self.find_directory_by_path(parent_full_path)

        if parent_dir:
            parent_dir.append(file_entry)
            logging.debug(f"Added file {file_entry.path} under {parent_dir}")
        else:
            logging.error(f"Parent directory not found for path: {parent_full_path}")

    def find_file_by_id(self, file_id):
        """Recursively searches the directory structure to find a file by its id."""
        logging.debug(f"Finding file by id: {file_id}")
        return self._search_file_by_id(self.entries, file_id)

    def _search_file_by_id(self, entries, file_id):
        for entry in entries:
            if isinstance(entry, FileEntry) and entry.file_id == file_id:
                logging.debug(f"Found file: {entry.path}")
                return entry
            elif isinstance(entry, DirectoryEntry):
                found = self._search_file_by_id(entry.entries, file_id)
                if found:
                    return found
        logging.debug(f"File with id {file_id} not found.")
        return None
