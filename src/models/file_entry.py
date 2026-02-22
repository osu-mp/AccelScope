from models.label import Label


class FileEntry:
	"""
	Represents a CSV file in the project config (unique id plus user generated labels)
	"""

	def __init__(self, path, id=None, labels=None, verified_by=None, comment=""):
		"""
		:param path: relative path to CSV file (project config contains root directory)
		:param id: can be emtpy, project service will ensure it is unique
		:param labels:
		:param verified_by: list of reviewer usernames who have verified this file
		"""
		self.path = path
		self.id = id
		self.labels = labels or []
		self.verified_by = verified_by if verified_by is not None else []
		self.comment = comment

	def to_dict(self):
		return {
			"path": self.path,
			"id": self.id,
			"labels": [label.to_dict() for label in self.labels],
			"verified_by": list(self.verified_by),
			"comment": self.comment
		}

	@staticmethod
	def from_dict(data):
		labels = [Label.from_dict(label) for label in data.get("labels", [])]

		# Support new verified_by list, with migration from old user_verified bool
		if "verified_by" in data:
			verified_by = list(data["verified_by"])
		elif data.get("user_verified", False):
			verified_by = ["default"]
		else:
			verified_by = []

		return FileEntry(path=data["path"],
		                 id=data["id"],
		                 labels=labels,
		                 verified_by=verified_by,
                comment=data.get("comment", "")
		                 )

	def set_labels(self, labels):
		self.labels = labels

	def is_verified_by(self, username):
		"""Check if a specific reviewer has verified this file."""
		return username in self.verified_by

	def set_verified_by(self, username, verified):
		"""Add or remove a reviewer from the verified_by list."""
		if verified and username not in self.verified_by:
			self.verified_by.append(username)
		elif not verified and username in self.verified_by:
			self.verified_by.remove(username)
