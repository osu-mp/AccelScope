from models.file_entry import FileEntry


class DirectoryEntry:
	"""
	Structure to allow recursive dir/file structure in project config
	"""
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
