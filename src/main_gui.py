import logging
import tkinter as tk
from tkinter import ttk
from tkinter import Menu

from gui_components.project_browser import ProjectBrowser
from gui_components.viewer import Viewer  # Make sure to have the Viewer class in viewer.py or adjust the import based on your structure
from gui_components.status_bar import StatusBar

from gui_components.new_project_dialog import NewProjectDialog
from models.project_config import ProjectConfig

from services.config_manager import ConfigManager
"""
TODO
Import BEBE prediction CSVs into viewer, show human labels vs BEBE predictions

"""

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AccelScope - Main Application')
        self.geometry('1200x800')  # Adjust size as needed
        self.setup_logging()

        self.config_manager = ConfigManager(app_parent=self)
        # self.project_config = None
        # self.config_manager = ConfigManager()

        # Setup the entire GUI in one go
        self.setup_gui()

        # Optionally load the project
        # self.open_project()

        # attempt to open the last CSV the user had open during last run
        self.config_manager.try_to_load_last_csv()

    def setup_gui(self):
        """Sets up the entire user interface."""

        # Create the menus
        self.create_menus()

        project_config = self.config_manager.get_project_config()

        # Create the status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create the PanedWindow (for project browser, viewer, and info pane)
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='lightgray')
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Initialize the project browser as one pane (left side)
        self.project_browser = ProjectBrowser(self, project_config=project_config, config_manager=self.config_manager)
        self.paned_window.add(self.project_browser, minsize=100)
        self.project_browser.load_project()

        # Initialize the info pane first, as it needs to be passed to the viewer
        self.info_pane = ttk.Frame(self.paned_window, width=200, relief=tk.SUNKEN)
        info_pane_label = tk.Label(self.info_pane, text='Info Pane', bg='blue')
        info_pane_label.pack(fill=tk.BOTH, expand=True)

        # Initialize the main viewer/content area as another pane (middle)
        self.viewer = Viewer(self, config_manager=self.config_manager, width=600, relief=tk.SUNKEN)#, info_pane=self.info_pane)
        self.paned_window.add(self.viewer, minsize=200)
        self.viewer.set_project_config(project_config)


        # Add the info pane (right side)
        self.paned_window.add(self.info_pane, minsize=100)

    # def __init__(self):
    #     super().__init__()
    #     self.title('AccelScope - Main Application')
    #     self.geometry('1200x800')  # Adjust size as needed
    #
    #     self.project_config = None
    #
    #     self.create_menus()
    #
    #     # Create the status bar
    #     self.status_bar = StatusBar(self)
    #     self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    #
    #     # Create the viewer instance once
    #     self.viewer = Viewer(self, self.status_bar)
    #     self.viewer = Viewer(self, self.status_bar)
    #     self.viewer.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    #
    #     # Create the project browser
    #     self.project_browser = ProjectBrowser(self, project_config=self.load_project_config())
    #     self.project_browser.pack(side=tk.LEFT, fill=tk.Y)
    #
    #     # self.setup_gui()
    #
    #     # TODO remove
    #     self.open_project()
    #
    #     self.clear_gui()
    #     self.create_menus()
    #
    #     # Create the button bar
    #     self.button_bar = ButtonBar(self)
    #     self.button_bar.pack(side=tk.TOP, fill=tk.X)
    #
    #     # Create the status bar
    #     self.status_bar = StatusBar(self)
    #     self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    #     self.status_bar.set("Status bar")
    #
    #     # Create a horizontal PanedWindow
    #     self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='lightgray')
    #     self.paned_window.pack(fill=tk.BOTH, expand=True)
    #
    #     # Initialize the project browser as one pane
    #     self.project_browser = ProjectBrowser(self, self.project_config, width=200, relief=tk.SUNKEN)
    #     if self.project_config:
    #         self.project_browser.load_project()
    #     self.paned_window.add(self.project_browser, minsize=100)  # Ensure a minimum size
    #
    #     # Initialize the main viewer/content area as another pane
    #     # self.viewer = Viewer(self, data_path='../test/data/F202_2018-05-20.csv', width=600, relief=tk.SUNKEN)
    #     self.viewer = Viewer(self, status_bar=self.status_bar, width=600, relief=tk.SUNKEN)
    #     self.viewer.set_project_config(self.project_config)
    #     # self.viewer_content = ttk.Frame(self.paned_window, width=600, relief=tk.SUNKEN)
    #     # self.paned_window.add(self.viewer_content, minsize=200)  # Slightly larger minimum size
    #     self.paned_window.add(self.viewer, minsize=200)
    #     # viewer_label = tk.Label(self.viewer_content, text='Viewer Area', bg='green')
    #     # viewer_label.pack(fill=tk.BOTH, expand=True)
    #
    #     # Initialize an info pane related to the viewer as the third pane
    #     self.info_pane = ttk.Frame(self.paned_window, width=200, relief=tk.SUNKEN)
    #     self.paned_window.add(self.info_pane, minsize=100)
    #     info_pane_label = tk.Label(self.info_pane, text='Info Pane', bg='blue')
    #     info_pane_label.pack(fill=tk.BOTH, expand=True)
    #
    # def clear_gui(self):
    #     # Remove all components in the main window
    #     for widget in self.winfo_children():
    #         widget.destroy()


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

    # def setup_gui(self):
    #     pass


    def file_imported(self, file_path):
        self.viewer.load_data(file_path)
        self.status_bar.set(f"Successfully loaded CSV into viewer: {self.viewer.get_data_path()}")

    def open_new_project_dialog(self):
        # This method ensures the dialog is properly parented to the main application window
        new_project_dialog = NewProjectDialog(self)
        new_project_dialog.transient(self)  # Optionally make the dialog transient
        new_project_dialog.grab_set()  # Optional, but makes the dialog modal

    def open_project(self):
        raise Exception("TODO")
        self.project_config = ProjectConfig("D:/OSU/AccelScopeDemo/test.json")
        self.project_config.load_config()
        self.viewer.set_project_config(self.project_config)

        # self.project_browser = ProjectBrowser(self, self.project_config)
        # self.setup_gui()

    # def load_project_config(self):
    #     # Load the project config (example placeholder)
    #     return ProjectConfig("D:/OSU/AccelScopeDemo/test.json")

    def open_file(self, file_entry):
        self.status_bar.set(f"Attempting to load CSV: {file_entry.path}")
        self.viewer.load_file_entry(file_entry)
        csv_name = self.viewer.get_data_path()
        self.status_bar.set(f"Loaded CSV: {csv_name}")

        # Save the project and the file_id of the currently opened file
        self.config_manager.save_last_project(self.config_manager.last_project,
                                              file_entry.file_id)

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

    def load_csv(self, file_path):
        """Loads the CSV in the viewer and updates the status bar"""
        self.status_bar.set(f"Attempting to load CSV: {file_path}")
        self.viewer.load_data(file_path)
        csv_name = self.viewer.get_data_path()
        self.status_bar.set(f"Loaded CSV: {csv_name}")

    def set_status(self, msg):
        """
        Display the msg in the status bar
        """
        self.status_bar.set(msg)


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
