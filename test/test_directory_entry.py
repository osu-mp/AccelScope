import unittest
from models.file_entry import FileEntry
from models.directory_entry import DirectoryEntry


class TestDirectoryEntry(unittest.TestCase):

    def test_directory_entry_creation(self):
        """Test creating a DirectoryEntry instance."""
        directory_entry = DirectoryEntry(name="TestDir")
        self.assertEqual(directory_entry.name, "TestDir")
        self.assertEqual(directory_entry.entries, [])

    def test_directory_entry_with_files(self):
        """Test creating DirectoryEntry with FileEntry children."""
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", id="123")
        directory_entry = DirectoryEntry(name="TestDir", entries=[file_entry])
        self.assertEqual(len(directory_entry.entries), 1)
        self.assertIsInstance(directory_entry.entries[0], FileEntry)
        self.assertEqual(directory_entry.entries[0].id, "123")

    def test_directory_entry_to_dict(self):
        """Test converting DirectoryEntry to a dictionary."""
        file_entry = FileEntry(path="data/F202_2018-05-20.csv", id="123")
        directory_entry = DirectoryEntry(name="TestDir", entries=[file_entry])
        dir_dict = directory_entry.to_dict()
        expected = {
            "name": "TestDir",
            "entries": [
                {
                    "path": "data/F202_2018-05-20.csv",
                    "id": "123",
                    "labels": [],
                    "comment": "",
                    "user_verified": False,
                }
            ]
        }
        self.assertEqual(dir_dict, expected)

    def test_directory_entry_from_dict(self):
        """Test creating DirectoryEntry from a dictionary."""
        data = {
            "name": "TestDir",
            "entries": [
                {
                    "path": "data/F202_2018-05-20.csv",
                    "id": "123",
                    "labels": []
                }
            ]
        }
        directory_entry = DirectoryEntry.from_dict(data)
        self.assertEqual(directory_entry.name, "TestDir")
        self.assertEqual(len(directory_entry.entries), 1)
        self.assertIsInstance(directory_entry.entries[0], FileEntry)
        self.assertEqual(directory_entry.entries[0].id, "123")


if __name__ == "__main__":
    unittest.main()
