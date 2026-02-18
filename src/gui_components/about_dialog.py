import tkinter as tk
from tkinter import ttk
import webbrowser
from tkinter import messagebox

from gui_components.gui_theme import PAD_MD, PAD_LG, FONT_TITLE

class AboutDialog(tk.Toplevel):
    """
    Dialog with information about this program and support.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.title("About AccelScope")
        self.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        # Create a label for the title
        title_label = ttk.Label(self, text="About AccelScope", font=FONT_TITLE)
        title_label.grid(row=0, column=0, pady=(PAD_LG, PAD_MD), padx=PAD_LG)

        # Add a description label (multi-line)
        description_text = (
            "AccelScope is an accelerometer data visualization tool designed to support "
            "the analysis of large datasets. It allows users to visualize, annotate behaviors, "
            "and export data for further processing."
        )
        description_label = ttk.Label(self, text=description_text, wraplength=400, justify="left")
        description_label.grid(row=1, column=0, pady=(PAD_MD, PAD_LG), padx=PAD_LG)

        # Add a GitHub link
        github_label = ttk.Label(self, text="GitHub: AccelScope Repository", foreground="blue", cursor="hand2")
        github_label.grid(row=2, column=0, pady=(0, PAD_LG), padx=PAD_LG)
        github_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/osu-mp/AccelScope"))

        # Create a contact information label with the email acting as a link
        contact_label = ttk.Label(self, text="Contact: paceym@oregonstate.edu", foreground="blue", cursor="hand2")
        contact_label.grid(row=3, column=0, pady=(0, PAD_LG), padx=PAD_LG)
        contact_label.bind("<Button-1>", lambda e: self.copy_email_to_clipboard())

        # Add a Close button to close the dialog
        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.grid(row=4, column=0, pady=(PAD_LG, PAD_LG), padx=PAD_LG)

    def open_link(self, url):
        webbrowser.open_new(url)

    def copy_email_to_clipboard(self):
        """
        Copy the email address to the system clipboard and show a confirmation message.
        """
        self.clipboard_clear()  # Clear the clipboard
        self.clipboard_append("paceym@oregonstate.edu")  # Add the email to the clipboard
        messagebox.showinfo("Copied", "Email address copied to clipboard.")
