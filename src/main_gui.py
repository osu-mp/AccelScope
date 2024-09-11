import logging
import tkinter as tk
from tkinter import ttk
from tkinter import Menu

from gui_components.project_browser import ProjectBrowser
from viewer import Viewer  # Make sure to have the Viewer class in viewer.py or adjust the import based on your structure
from gui_components.status_bar import StatusBar

from gui_components.new_project_dialog import NewProjectDialog
from services.project_config import ProjectConfig

"""
TODO
Import BEBE prediction CSVs into viewer, show human labels vs BEBE predictions

"""

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AccelScope - Main Application')
        self.geometry('1200x800')  # Adjust size as needed

        self.project_config = None

        self.create_menus()

        self.setup_gui()

        # TODO remove
        self.open_project()

    def clear_gui(self):
        # Remove all components in the main window
        for widget in self.winfo_children():
            widget.destroy()


    def create_menus(self):

        # Create the menu bar
        self.menu_bar = Menu(self)
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label='New Project', command=self.open_new_project_dialog)
        file_menu.add_command(label='Open Project', command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.quit)

        proj_menu = Menu(self.menu_bar, tearoff=0)
        proj_menu.add_command(label='Add File', command=self.open_file)

        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label='Preferences', command=self.edit_preferences)

        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label='About', command=self.show_about)

        self.menu_bar.add_cascade(label='File', menu=file_menu)
        self.menu_bar.add_cascade(label='Project', menu=proj_menu)
        self.menu_bar.add_cascade(label='Edit', menu=edit_menu)
        self.menu_bar.add_cascade(label='Help', menu=help_menu)

        self.config(menu=self.menu_bar)

    def setup_gui(self):
        self.clear_gui()
        self.create_menus()

        # Create the button bar
        self.button_bar = ButtonBar(self)
        self.button_bar.pack(side=tk.TOP, fill=tk.X)

        # Create the status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.set("Status bar")

        # Create a horizontal PanedWindow
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='lightgray')
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Initialize the project browser as one pane
        self.project_browser = ProjectBrowser(self, self.project_config, width=200, relief=tk.SUNKEN)
        if self.project_config:
            self.project_browser.load_project()
        self.paned_window.add(self.project_browser, minsize=100)  # Ensure a minimum size

        # Initialize the main viewer/content area as another pane
        self.viewer = Viewer(self, data_path='../test/data/F202_2018-05-20.csv', width=600, relief=tk.SUNKEN)
        # self.viewer_content = ttk.Frame(self.paned_window, width=600, relief=tk.SUNKEN)
        # self.paned_window.add(self.viewer_content, minsize=200)  # Slightly larger minimum size
        self.paned_window.add(self.viewer, minsize=200)
        # viewer_label = tk.Label(self.viewer_content, text='Viewer Area', bg='green')
        # viewer_label.pack(fill=tk.BOTH, expand=True)

        # Initialize an info pane related to the viewer as the third pane
        self.info_pane = ttk.Frame(self.paned_window, width=200, relief=tk.SUNKEN)
        self.paned_window.add(self.info_pane, minsize=100)
        info_pane_label = tk.Label(self.info_pane, text='Info Pane', bg='blue')
        info_pane_label.pack(fill=tk.BOTH, expand=True)


    def open_new_project_dialog(self):
        # This method ensures the dialog is properly parented to the main application window
        new_project_dialog = NewProjectDialog(self)
        new_project_dialog.transient(self)  # Optionally make the dialog transient
        new_project_dialog.grab_set()  # Optional, but makes the dialog modal

    def open_project(self):
        # TODO
        self.project_config = ProjectConfig("D:/OSU/AccelScopeDemo/test.json")
        self.project_config.load_config()

        # self.project_browser = ProjectBrowser(self, self.project_config)
        self.setup_gui()

    def open_file(self):
        pass

    def save_file(self):
        pass  # Implement file save logic

    def edit_preferences(self):
        pass  # Implement preferences editing logic

    def show_about(self):
        pass  # Implement about dialog logic

    def setup_logging(self, level=logging.INFO):
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class ButtonBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs, bg="blue")
        tk.Button(self, text='Action Button').pack()  # Placeholder for button

class InfoDisplay(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        tk.Label(self, text='Info Display').pack()


if __name__ == '__main__':
    app = MainApplication()
    app.mainloop()
