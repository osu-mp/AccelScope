from models.label import Label


class FileEntry:
	"""
	Represents a CSV file in the project config (unique id plus user generated labels)
	"""
	def __init__(self, path, file_id=None, labels=None):
		"""
		:param path: relative path to CSV file (project config contains root directory)
		:param file_id: can be emtpy, project service will ensure it is unique
		:param labels:
		"""
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
