import tkinter as tk
from tkinter import ttk


class AboutDialog(tk.Toplevel):
	"""
	Dialog with information about this program and support
	"""
	def __init__(self, parent):
		super().__init__(parent)

		self.title("About")
		self.resizable(False, False)

		self.create_widgets()

	def create_widgets(self):
		# Create a label for the title
		title_label = ttk.Label(self, text="About AccelScope", font=("Helvetica", 14, "bold"))
		title_label.grid(row=0, column=0, pady=(10, 5))

		# TODO: add description, link to github, and contact info


		# Add a Close button to close the dialog
		close_button = ttk.Button(self, text="Close", command=self.destroy)
		close_button.grid(row=1, column=0, pady=(10, 10))
