import logging
import tkinter as tk
from tkinter import Menu

from gui_components.info_pane import InfoPane
from gui_components.project_browser import ProjectBrowser
from gui_components.viewer import Viewer
from gui_components.status_bar import StatusBar
from gui_components.new_project_dialog import NewProjectDialog
from models.project_config import ProjectConfig
from services.config_manager import ConfigManager
from services.user_app_config_service import UserAppConfigService

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AccelScope')
        self.setup_logging()

        self.user_app_config = UserAppConfigService.load_from_file()

        self.config_manager = ConfigManager(app_parent=self)

        # Setup the entire GUI in one go
        self.setup_gui()

        # attempt to open the last CSV the user had open during last run
        self.config_manager.try_to_load_last_csv()

        # Capture any resizes (of main window or individual panes) into user config file
        self.bind("<Configure>", self.on_resize)
        self.paned_window.bind("<<PaneConfigure>>", self.on_resize)

        self.restore_user_settings()

    def restore_user_settings(self):
        """Restores user settings from UserAppConfig."""
        if self.user_app_config.window_geometry:
            self.geometry(self.user_app_config.window_geometry)

        if self.user_app_config.window_state:
            self.state(self.user_app_config.window_state)

        if self.user_app_config.project_browser_width:
            self.paned_window.paneconfig(self.project_browser, width=self.user_app_config.project_browser_width)

        if self.user_app_config.viewer_width:
            self.paned_window.paneconfig(self.viewer, width=self.user_app_config.viewer_width)

        if self.user_app_config.info_width:
            self.paned_window.paneconfig(self.info_pane, width=self.user_app_config.info_width)

    def on_resize(self, event):
        """Capture window resize events and update UserAppConfig."""
        self.user_app_config.window_geometry = f"{self.winfo_width()}x{self.winfo_height()}"
        self.user_app_config.window_state = self.state()

        # sash_coord(0) gets the x-position of the first sash (between the project browser and viewer)
        sash_position_0 = self.paned_window.sash_coord(0)[0]
        # sash_coord(1) gets the x-position of the second sash (between the viewer and info pane)
        sash_position_1 = self.paned_window.sash_coord(1)[0]

        self.user_app_config.project_browser_width = sash_position_0
        self.user_app_config.viewer_width = sash_position_1 - sash_position_0
        self.user_app_config.info_width = self.paned_window.winfo_width() - sash_position_1

        # Save updated config
        UserAppConfigService.save_to_file(self.user_app_config)

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
        self.paned_window.add(self.project_browser, minsize=50)
        self.project_browser.load_project()

        # Initialize the main viewer/content area as another pane (middle)
        self.viewer = Viewer(self, config_manager=self.config_manager, relief=tk.SUNKEN)
        self.paned_window.add(self.viewer, minsize=200)
        self.viewer.set_project_config(project_config)

        # info pane for legend info/controls
        self.info_pane = InfoPane(self, config_manager=self.config_manager)
        self.paned_window.add(self.info_pane, minsize=50)

        # Set the reference of InfoPane in the Viewer
        self.viewer.set_info_pane(self.info_pane)

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
        logging.info(msg)


if __name__ == '__main__':
    app = MainApplication()
    app.mainloop()
