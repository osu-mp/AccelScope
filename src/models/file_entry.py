from models.label import Label


class FileEntry:
	"""
	Represents a CSV file in the project config (unique id plus user generated labels)
	"""

	def __init__(self, path, id=None, labels=None, user_verified=False, comment=""):
		"""
		:param path: relative path to CSV file (project config contains root directory)
		:param id: can be emtpy, project service will ensure it is unique
		:param labels:
		"""
		self.path = path
		self.id = id
		self.labels = labels or []
		self.user_verified = user_verified
		self.comment = comment

	def to_dict(self):
		return {
			"path": self.path,
			"id": self.id,
			"labels": [label.to_dict() for label in self.labels],
			"user_verified": self.user_verified,
			"comment": self.comment
		}

	@staticmethod
	def from_dict(data):
		labels = [Label.from_dict(label) for label in data.get("labels", [])]
		return FileEntry(path=data["path"],
		                 id=data["id"],
		                 labels=labels,
		                 user_verified=data.get("user_verified", False),
                comment=data.get("comment", "")
		                 )

	def set_labels(self, labels):
		self.labels = labels
