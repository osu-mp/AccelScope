import logging
import os.path
import threading
import tkinter as tk
from tkinter import Menu, filedialog

from gui_components.about_dialog import AboutDialog
from gui_components.info_pane import InfoPane
from gui_components.generate_output_dialog import GenerateOutputDialog
from gui_components.hotkey_dialog import HotkeyDialog
from gui_components.output_progress_dialog import OutputProgressDialog
from gui_components.project_browser import ProjectBrowser
from gui_components.viewer import Viewer
from gui_components.status_bar import StatusBar
from gui_components.new_project_dialog import NewProjectDialog
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.label import Label
from models.output_settings import OutputType
from output_types.bebe_output import BEBEOutput
from services.project_service import ProjectService
from services.user_app_config_service import UserAppConfigService


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AccelScope')
        self.setup_logging()

        # Create UserAppConfigService which manages the user configuration
        self.user_app_config_service = UserAppConfigService()
        self.user_app_config = self.user_app_config_service.config  # Access config instance for read-only purposes

        self.project_service = ProjectService()

        last_opened_project = self.user_app_config_service.config.last_opened_project
        if last_opened_project and os.path.exists(last_opened_project):
            self.project_service.load_project(last_opened_project)

        self.setup_gui()

        self.reopen_last_project_file()

        # Capture any resizes (of main window or individual panes) into user config file
        self.bind("<Configure>", self.on_resize)
        self.paned_window.bind("<<PaneConfigure>>", self.on_resize)

        self.restore_user_settings()

    def reopen_last_project_file(self):
        """
        Attempt to reload the last open CSV from the active project
        :return:
        """
        last_opened_file = self.user_app_config_service.config.last_opened_file
        if last_opened_file:
            file_entry = self.project_service.get_file_entry(last_opened_file)
            if file_entry:
                self.open_file(file_entry)
                # self.viewer.load_file_entry(file_entry)
            else:
                logging.warning(f"File with ID {last_opened_file} not found.")

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
        # Update user config via service, keeping main_gui read-only for config
        self.user_app_config_service.update_window_geometry(f"{self.winfo_width()}x{self.winfo_height()}")
        self.user_app_config_service.update_window_state(self.state())

        # Get the current sash positions to calculate the widths of different panes
        sash_position_0 = self.paned_window.sash_coord(0)[0]
        sash_position_1 = self.paned_window.sash_coord(1)[0]

        self.user_app_config_service.update_pane_widths(
            project_browser_width=sash_position_0,
            viewer_width=sash_position_1 - sash_position_0,
            info_width=self.paned_window.winfo_width() - sash_position_1
        )

        self.user_app_config_service.save_to_file()

    def setup_gui(self):
        """Sets up the entire user interface."""

        # Create the menus
        self.create_menus()

        project_config = self.user_app_config_service.get_project_config()

        # Create the status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create the PanedWindow (for project browser, viewer, and info pane)
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg='lightgray')
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Initialize the project browser as one pane (left side)
        self.project_browser = ProjectBrowser(self, project_service=self.project_service)
        self.paned_window.add(self.project_browser, minsize=50)
        self.project_browser.load_project()

        # Initialize the main viewer/content area as another pane (middle)
        self.viewer = Viewer(self, project_service=self.project_service, relief=tk.SUNKEN)
        self.paned_window.add(self.viewer, minsize=200)
        self.viewer.set_project_config(project_config)

        # info pane for legend info/controls
        self.info_pane = InfoPane(self, project_service=self.project_service)
        self.paned_window.add(self.info_pane, minsize=50)

        # Set the reference of InfoPane in the Viewer
        self.viewer.set_info_pane(self.info_pane)

    def create_menus(self):
        # Create the menu bar
        self.menu_bar = Menu(self)
        file_menu = Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label='New Project', command=self.open_new_project_dialog)
        file_menu.add_command(label='Open Project', command=self.open_project_dialog)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.quit)

        proj_menu = Menu(self.menu_bar, tearoff=0)
        proj_menu.add_command(label='Generate Output', command=self.generate_project_output)
        proj_menu.add_command(label='Validate Project Config', command=self.check_project_inputs)

        edit_menu = Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label='Preferences', command=self.edit_preferences)

        help_menu = Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Hotkeys", command=self.show_hotkeys)
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
        """
        Allows user to create new project
        :return: None (new project is opened, user app config updated)
        """
        # Create and display the NewProjectDialog
        new_project_dialog = NewProjectDialog(self)
        new_project_dialog.transient(self)  # Optionally make the dialog transient
        new_project_dialog.grab_set()  # Optional, but makes the dialog modal
        self.wait_window(new_project_dialog)  # Wait until dialog is closed

        # Check if a new project was successfully created
        new_project_path = new_project_dialog.get_created_project_path()
        self.open_project(new_project_path)

    def open_project_dialog(self):
        """Dialog allowing user to select project JSON, open if exists"""
        project_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Open Project File")
        self.open_project(project_path)

    def open_project(self, project_path):
        """
        Open the given project JSON and reset all panes
        :param project_path:
        :return:
        """
        if project_path:
            if not os.path.exists(project_path):
                logging.error(f"Unable to open {project_path}, file does not exist")
                return
            self.project_service.load_project(project_path)
            self.user_app_config_service.set_last_opened_project(project_path)

            self.project_browser.load_project()

            self.viewer.clear_plot()
            self.info_pane.set_project_service(self.project_service)

    def open_file(self, file_entry):
        self.status_bar.set(f"Attempting to load CSV: {file_entry.path}")
        self.viewer.load_file_entry(file_entry)
        csv_name = self.viewer.get_data_path()
        self.status_bar.set(f"Loaded CSV: {csv_name}")

        # Set the file entry in the InfoPane
        self.info_pane.set_file_entry(file_entry)

        self.user_app_config_service.set_last_opened_file(file_entry.id)

    def edit_preferences(self):
        pass  # Implement preferences editing logic

    def show_hotkeys(self):
        """Display the hotkey dialog."""
        HotkeyDialog(self)

    def show_about(self):
        """Display info about this program"""
        AboutDialog(self)

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

    def generate_project_output(self):
        # Open the GenerateOutputDialog
        output_dialog = GenerateOutputDialog(self)
        output_dialog.transient(self)
        output_dialog.grab_set()
        self.wait_window(output_dialog)

        # Retrieve the output settings from the dialog after it closes
        output_settings = output_dialog.output_settings
        output_directory = output_dialog.output_directory

        if output_settings and output_directory:
            # Initialize the output generation process
            logging.info("Starting output generation...")
            self.start_output_generation(output_settings, output_directory)
        else:
            logging.info("Output generation canceled or incomplete settings.")

    def check_project_inputs(self):
        """
        Validate the project configuration:
        - Verify the project root directory exists.
        - Ensure all referenced CSV files are accessible.
        - Validate that each label's start and end times are correct.
        - Logs and displays messages for any warnings or errors.
        """
        logging.info("Starting project configuration validation...")

        # 1. Verify the project root directory
        try:
            root_directory = self.project_service.get_user_data_path()
            if not os.path.isdir(root_directory):
                error_msg = f"Project root directory does not exist: {root_directory}"
                logging.error(error_msg)
                tk.messagebox.showerror("Validation Error", error_msg)
                return
            logging.info(f"Project root directory exists: {root_directory}")
        except Exception as e:
            logging.error(f"Error resolving root directory: {e}")
            tk.messagebox.showerror("Validation Error", f"Error resolving root directory: {e}")
            return

        # 2. Verify all referenced CSV files
        missing_files = []
        label_errors = []
        for entry in self.project_service.get_entries():
            self._validate_entry_files(entry, missing_files, label_errors)

        # Display missing files
        if missing_files:
            missing_files_message = "\n".join(missing_files)
            logging.error(f"Missing files:\n{missing_files_message}")
            tk.messagebox.showerror("Validation Error", f"Missing files:\n{missing_files_message}")

        # Display label errors
        if label_errors:
            label_errors_message = "\n".join(label_errors)
            logging.error(f"Label validation issues:\n{label_errors_message}")
            tk.messagebox.showerror("Label Validation Error", f"Issues with labels:\n{label_errors_message}")

        # Success message if no issues found
        if not missing_files and not label_errors:
            logging.info("Validation complete: All files and labels are valid.")
            tk.messagebox.showinfo("Validation Complete", "All files and labels are valid.")

    def _validate_entry_files(self, entry, missing_files, label_errors):
        """
        Recursively checks each entry to ensure files exist and validates labels.

        :param entry: DirectoryEntry or FileEntry to validate.
        :param missing_files: List to collect paths of missing files.
        :param label_errors: List to collect validation errors for labels.
        """
        if isinstance(entry, DirectoryEntry):
            for sub_entry in entry.entries:
                self._validate_entry_files(sub_entry, missing_files, label_errors)

        elif isinstance(entry, FileEntry):
            # Use ProjectService to get the full path of the file
            file_path = self.project_service.get_file_path(entry)
            if not os.path.isfile(file_path):
                missing_files.append(f"{file_path} (ID: {entry.id})")
                logging.warning(f"Missing file: {file_path}")

            # Validate labels
            for label_data in entry.labels:
                if isinstance(label_data, dict):  # Only attempt validation if it's a dictionary
                    try:
                        Label.from_dict(label_data)  # Validate via Label class
                    except ValueError as e:
                        error_msg = f"Error in file {entry.path} - {str(e)}"
                        label_errors.append(error_msg)
                        logging.warning(error_msg)

    def start_output_generation(self, output_settings, output_directory):
        # Open the progress dialog
        progress_dialog = OutputProgressDialog(self)
        progress_dialog.transient(self)
        progress_dialog.grab_set()

        # Run the output generation in a separate thread to keep GUI responsive
        self.after(100, lambda: self.generate_output_files(output_settings, output_directory, progress_dialog))

    def generate_output_files(self, output_settings, output_directory, progress_dialog):
        def generate():
            try:
                # Instantiate and configure output class based on output type
                output_class = get_output_class(output_settings.output_type)
                output_instance = output_class(output_settings, output_directory)

                for step in output_instance.generate():
                    if progress_dialog.cancelled:
                        logging.info("Output generation canceled by user.")
                        break
                    # Update progress if needed

                if not progress_dialog.cancelled:
                    logging.info("Output generation completed successfully.")
                progress_dialog.destroy()
            except Exception as e:
                logging.error(f"Error during output generation: {e}")
                progress_dialog.destroy()

        threading.Thread(target=generate, daemon=True).start()

    @staticmethod
    def get_output_class(output_type: OutputType):
        """
        Returns the appropriate output generator class based on the provided output type.

        :param output_type: The output type (enum) from OutputSettings.
        :return: A class implementing OutputGeneratorInterface.
        :raises ValueError: If no class is found for the given output type.
        """
        if output_type == OutputType.BEBE:
            return BEBEOutput
        # Future output types can be added here as elif blocks.

        raise ValueError(f"No output class found for output type: {output_type}")


if __name__ == '__main__':
    app = MainApplication()
    app.mainloop()
