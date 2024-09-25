import unittest
from models.label_display import LabelDisplay


class TestLabelDisplay(unittest.TestCase):

	def setUp(self):
		self.label_display = LabelDisplay(
			display_name="Stalk",
			color="orange",
			alpha=0.2,
			output_value="STALK"
		)

	def test_to_dict(self):
		expected_dict = {
			'display_name': "Stalk",
			'color': "orange",
			'alpha': 0.2,
			'output_value': "STALK"
		}
		self.assertEqual(self.label_display.to_dict(), expected_dict)

	def test_from_dict(self):
		data = {
			'display_name': "Stalk",
			'color': "orange",
			'alpha': 0.2,
			'output_value': "STALK"
		}
		obj = LabelDisplay.from_dict(data)
		self.assertEqual(obj.display_name, "Stalk")
		self.assertEqual(obj.color, "orange")
		self.assertEqual(obj.alpha, 0.2)
		self.assertEqual(obj.output_value, "STALK")


if __name__ == "__main__":
	unittest.main()
