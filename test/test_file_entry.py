import unittest
from models.file_entry import FileEntry
from models.label import Label


class TestFileEntry(unittest.TestCase):

    def test_file_entry_creation(self):
        """Test creating a FileEntry instance."""
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", id="123")
        self.assertEqual(file_entry.path, "data/F202_2018-05-20.csv")
        self.assertEqual(file_entry.id, "123")
        self.assertEqual(file_entry.labels, [])
        self.assertEqual(file_entry.verified_by, [])

    def test_file_entry_with_labels(self):
        """Test creating a FileEntry with labels."""
        labels = [
            Label("05:07:10.825020", "06:18:21.373460", "Stalk"),
            Label("07:08:55.710520", "08:35:05.321800", "Kill Phase 1")
        ]
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", id="123", labels=labels)
        self.assertEqual(len(file_entry.labels), 2)
        self.assertEqual(file_entry.labels[0].behavior, "Stalk")
        self.assertEqual(file_entry.labels[1].behavior, "Kill Phase 1")

    def test_file_entry_to_dict(self):
        """Test converting FileEntry to a dictionary."""
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", id="123")
        file_dict = file_entry.to_dict()
        expected = {
            "path": "data/F202_2018-05-20.csv",
            "id": "123",
            "labels": [],
            "comments": {},
            "verified_by": [],
        }
        self.assertEqual(file_dict, expected)

    def test_file_entry_from_dict(self):
        """Test creating FileEntry from a dictionary."""
        data = {
            "path": "data/F202_2018-05-20.csv",
            "id": "123",
            "labels": []
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.path, "data/F202_2018-05-20.csv")
        self.assertEqual(file_entry.id, "123")
        self.assertEqual(file_entry.labels, [])
        self.assertEqual(file_entry.verified_by, [])

    def test_file_entry_from_dict_with_verified_by(self):
        """Test creating FileEntry from a dict with verified_by list."""
        data = {
            "path": "data/test.csv",
            "id": "456",
            "labels": [],
            "verified_by": ["mpace", "sarah"]
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.verified_by, ["mpace", "sarah"])

    def test_migration_user_verified_true(self):
        """Test migration from old user_verified=true to verified_by=['default']."""
        data = {
            "path": "data/test.csv",
            "id": "789",
            "labels": [],
            "user_verified": True
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.verified_by, ["default"])

    def test_migration_user_verified_false(self):
        """Test migration from old user_verified=false to verified_by=[]."""
        data = {
            "path": "data/test.csv",
            "id": "789",
            "labels": [],
            "user_verified": False
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.verified_by, [])

    def test_migration_user_verified_missing(self):
        """Test migration when user_verified key is missing entirely."""
        data = {
            "path": "data/test.csv",
            "id": "789",
            "labels": []
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.verified_by, [])

    def test_is_verified_by(self):
        """Test is_verified_by helper."""
        file_entry = FileEntry(path="test.csv", id="1", verified_by=["mpace"])
        self.assertTrue(file_entry.is_verified_by("mpace"))
        self.assertFalse(file_entry.is_verified_by("sarah"))

    def test_set_verified_by_add(self):
        """Test adding a reviewer via set_verified_by."""
        file_entry = FileEntry(path="test.csv", id="1")
        file_entry.set_verified_by("mpace", True)
        self.assertEqual(file_entry.verified_by, ["mpace"])
        # Adding again should not duplicate
        file_entry.set_verified_by("mpace", True)
        self.assertEqual(file_entry.verified_by, ["mpace"])

    def test_set_verified_by_remove(self):
        """Test removing a reviewer via set_verified_by."""
        file_entry = FileEntry(path="test.csv", id="1", verified_by=["mpace", "sarah"])
        file_entry.set_verified_by("mpace", False)
        self.assertEqual(file_entry.verified_by, ["sarah"])
        # Removing non-existent should be safe
        file_entry.set_verified_by("mpace", False)
        self.assertEqual(file_entry.verified_by, ["sarah"])

    def test_migration_old_comment_string(self):
        """Test migration from old comment string to comments dict."""
        data = {
            "path": "data/test.csv",
            "id": "789",
            "labels": [],
            "comment": "some note"
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.comments, {"default": "some note"})

    def test_migration_old_comment_empty(self):
        """Test migration from old empty comment string to empty comments dict."""
        data = {
            "path": "data/test.csv",
            "id": "789",
            "labels": [],
            "comment": ""
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.comments, {})

    def test_comments_dict_from_dict(self):
        """Test loading a comments dict directly."""
        data = {
            "path": "data/test.csv",
            "id": "789",
            "labels": [],
            "comments": {"mpace": "looks good", "sarah": "needs review"}
        }
        file_entry = FileEntry.from_dict(data)
        self.assertEqual(file_entry.comments, {"mpace": "looks good", "sarah": "needs review"})

    def test_get_comment(self):
        """Test get_comment helper."""
        file_entry = FileEntry(path="test.csv", id="1", comments={"mpace": "hello"})
        self.assertEqual(file_entry.get_comment("mpace"), "hello")
        self.assertEqual(file_entry.get_comment("sarah"), "")

    def test_set_comment(self):
        """Test set_comment helper."""
        file_entry = FileEntry(path="test.csv", id="1")
        file_entry.set_comment("mpace", "a note")
        self.assertEqual(file_entry.comments, {"mpace": "a note"})
        # Setting empty should remove the key
        file_entry.set_comment("mpace", "")
        self.assertEqual(file_entry.comments, {})


if __name__ == "__main__":
    unittest.main()
