import unittest
from models.file_entry import FileEntry
from models.label import Label


class TestFileEntry(unittest.TestCase):

    def test_file_entry_creation(self):
        """Test creating a FileEntry instance."""
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", file_id="123")
        self.assertEqual(file_entry.path, "data/F202_2018-05-20.csv")
        self.assertEqual(file_entry.file_id, "123")
        self.assertEqual(file_entry.labels, [])

    def test_file_entry_with_labels(self):
        """Test creating a FileEntry with labels."""
        labels = [
            Label("05:07:10.825020", "06:18:21.373460", "Stalk"),
            Label("07:08:55.710520", "08:35:05.321800", "Kill Phase 1")
        ]
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", file_id="123", labels=labels)
        self.assertEqual(len(file_entry.labels), 2)
        self.assertEqual(file_entry.labels[0].behavior, "Stalk")
        self.assertEqual(file_entry.labels[1].behavior, "Kill Phase 1")

    def test_file_entry_to_dict(self):
        """Test converting FileEntry to a dictionary."""
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", file_id="123")
        file_dict = file_entry.to_dict()
        expected = {
            "path": "data/F202_2018-05-20.csv",
            "id": "123",
            "labels": [],
            "comment": "",
            "user_verified": False,
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
        self.assertEqual(file_entry.file_id, "123")
        self.assertEqual(file_entry.labels, [])


if __name__ == "__main__":
    unittest.main()
