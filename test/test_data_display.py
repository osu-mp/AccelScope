import unittest
from models.data_display import DataDisplay


class TestDataDisplay(unittest.TestCase):

	def setUp(self):
		self.data_display = DataDisplay(
			input_name="Acc X [g]",
			display_name="X-axis",
			color="red",
			alpha=0.6,
			output_name="Acc X [g]"
		)

	def test_to_dict(self):
		expected_dict = {
			'input_name': "Acc X [g]",
			'display_name': "X-axis",
			'color': "red",
			'alpha': 0.6,
			'output_name': "Acc X [g]"
		}
		self.assertEqual(self.data_display.to_dict(), expected_dict)

	def test_from_dict(self):
		data = {
			'input_name': "Acc X [g]",
			'display_name': "X-axis",
			'color': "red",
			'alpha': 0.6,
			'output_name': "Acc X [g]"
		}
		obj = DataDisplay.from_dict(data)
		self.assertEqual(obj.input_name, "Acc X [g]")
		self.assertEqual(obj.display_name, "X-axis")
		self.assertEqual(obj.color, "red")
		self.assertEqual(obj.alpha, 0.6)
		self.assertEqual(obj.output_name, "Acc X [g]")


if __name__ == "__main__":
	unittest.main()
