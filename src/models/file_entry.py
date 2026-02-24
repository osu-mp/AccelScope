from models.label import Label


class FileEntry:
	"""
	Represents a CSV file in the project config (unique id plus user generated labels)
	"""

	def __init__(self, path, id=None, labels=None, verified_by=None, comments=None):
		"""
		:param path: relative path to CSV file (project config contains root directory)
		:param id: can be emtpy, project service will ensure it is unique
		:param labels:
		:param verified_by: list of reviewer usernames who have verified this file
		:param comments: dict mapping username -> comment text
		"""
		self.path = path
		self.id = id
		self.labels = labels or []
		self.verified_by = verified_by if verified_by is not None else []
		self.comments = comments if comments is not None else {}

	def to_dict(self):
		return {
			"path": self.path,
			"id": self.id,
			"labels": [label.to_dict() for label in self.labels],
			"verified_by": list(self.verified_by),
			"comments": dict(self.comments)
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

		# Migration: old "comment" string -> new "comments" dict
		if "comments" in data and isinstance(data["comments"], dict):
			comments = dict(data["comments"])
		elif data.get("comment", ""):
			comments = {"default": data["comment"]}
		else:
			comments = {}

		return FileEntry(path=data["path"],
		                 id=data["id"],
		                 labels=labels,
		                 verified_by=verified_by,
		                 comments=comments
		                 )

	def set_labels(self, labels):
		self.labels = labels

	def get_comment(self, username):
		"""Get the comment for a specific user."""
		return self.comments.get(username, "")

	def set_comment(self, username, text):
		"""Set the comment for a specific user. Deletes the key if text is empty."""
		if text:
			self.comments[username] = text
		elif username in self.comments:
			del self.comments[username]

	def is_verified_by(self, username):
		"""Check if a specific reviewer has verified this file."""
		return username in self.verified_by

	def set_verified_by(self, username, verified):
		"""Add or remove a reviewer from the verified_by list."""
		if verified and username not in self.verified_by:
			self.verified_by.append(username)
		elif not verified and username in self.verified_by:
			self.verified_by.remove(username)
