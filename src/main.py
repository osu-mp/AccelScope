import csv
import logging
import os.path
import threading
import tkinter as tk
from tkinter import Menu, filedialog, messagebox

from gui_components import gui_theme
from gui_components.about_dialog import AboutDialog
from gui_components.edit_input_settings_dialog import EditInputSettingsDialog
from gui_components.edit_label_display_dialog import EditLabelDisplayDialog
from gui_components.info_pane import InfoPane
from gui_components.generate_output_dialog import GenerateOutputDialog
from gui_components.preferences_dialog import PreferencesDialog
from gui_components.hotkey_dialog import HotkeyDialog
from gui_components.output_progress_dialog import OutputProgressDialog
from gui_components.project_browser import ProjectBrowser
from gui_components.viewer import Viewer
from gui_components.status_bar import StatusBar
from gui_components.new_project_dialog import NewProjectDialog
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.label import Label
from output_types.bebe_output import BEBEOutput
from services.project_service import ProjectService
from services.user_app_config_service import UserAppConfigService


class _GenerationCancelled(Exception):
    """Raised when the user cancels output generation."""
    pass


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AccelScope')
        self.setup_logging()
        gui_theme.apply_theme(self)

        # Create UserAppConfigService which manages the user configuration
        self.user_app_config_service = UserAppConfigService()
        self.user_app_config = self.user_app_config_service.config  # Access config instance for read-only purposes

        self.INFO_PANE_MAX_WIDTH = self.user_app_config.info_pane_max_width

        self.project_service = ProjectService()

        last_opened_project = self.user_app_config_service.config.last_opened_project
        if last_opened_project and os.path.exists(last_opened_project):
            self.project_service.load_project(last_opened_project)
            self._prompt_data_root_if_invalid()

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

    # Default max width for the info pane; overridden from user config in __init__
    INFO_PANE_MAX_WIDTH = 300

    def on_resize(self, event):
        """Capture window resize events and update UserAppConfig."""
        # Update user config via service, keeping main_gui read-only for config
        self.user_app_config_service.update_window_geometry(f"{self.winfo_width()}x{self.winfo_height()}")
        self.user_app_config_service.update_window_state(self.state())

        # Get the current sash positions to calculate the widths of different panes
        sash_position_0 = self.paned_window.sash_coord(0)[0]
        sash_position_1 = self.paned_window.sash_coord(1)[0]
        total_width = self.paned_window.winfo_width()
        info_width = total_width - sash_position_1

        # Clamp the info pane to its max width — push extra space to the viewer
        if info_width > self.INFO_PANE_MAX_WIDTH and total_width > 0:
            new_sash_1 = total_width - self.INFO_PANE_MAX_WIDTH
            if new_sash_1 > sash_position_0 + 200:  # keep viewer at least 200px
                try:
                    self.paned_window.sash_place(1, new_sash_1, 0)
                    sash_position_1 = new_sash_1
                    info_width = self.INFO_PANE_MAX_WIDTH
                except tk.TclError:
                    pass

        self.user_app_config_service.update_pane_widths(
            project_browser_width=sash_position_0,
            viewer_width=sash_position_1 - sash_position_0,
            info_width=info_width
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
        self.paned_window.add(self.project_browser, minsize=gui_theme.PANE_MIN_BROWSER)
        self.project_browser.load_project()

        # Initialize the main viewer/content area as another pane (middle)
        self.viewer = Viewer(self, project_service=self.project_service, relief=tk.SUNKEN)
        self.paned_window.add(self.viewer, minsize=gui_theme.PANE_MIN_VIEWER)
        self.viewer.set_project_config(project_config)

        # info pane for legend info/controls
        self.info_pane = InfoPane(self, project_service=self.project_service)
        self.paned_window.add(self.info_pane, minsize=gui_theme.PANE_MIN_INFO)

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
        proj_menu.add_command(label='Change Data Root...', command=self.change_data_root)
        proj_menu.add_command(label='Edit Behavior Labels...', command=self.edit_label_display)
        proj_menu.add_command(label='Edit Input Settings...', command=self.edit_input_settings)
        proj_menu.add_separator()
        proj_menu.add_command(label='Export Labels to CSV...', command=self.export_labels_csv)
        proj_menu.add_command(label='Import Labels from CSV...', command=self.import_labels_csv)
        proj_menu.add_separator()
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
            self._prompt_data_root_if_invalid()
            self.user_app_config_service.set_last_opened_project(project_path)

            self.project_browser.load_project()

            self.viewer.clear_plot()
            self.viewer.set_project_config(self.project_service.current_project_config)
            self.info_pane.set_project_service(self.project_service)

    def open_file(self, file_entry):
        self.status_bar.set(f"Attempting to load CSV: {file_entry.path}")
        self.viewer.load_file_entry(file_entry)
        csv_name = self.viewer.get_data_path()
        self.status_bar.set(f"Loaded CSV: {csv_name}")

        # Set the file entry in the InfoPane
        self.info_pane.set_file_entry(file_entry)

        self.user_app_config_service.set_last_opened_file(file_entry.id)

    def _prompt_data_root_if_invalid(self):
        """If the active data root is invalid, prompt the user to select a valid directory."""
        if self.project_service.is_data_root_valid():
            return
        logging.warning("Data root directory is invalid or missing for this user.")
        new_path = filedialog.askdirectory(title="Select Data Root Directory")
        if new_path:
            self.project_service.update_user_data_root(new_path)
            logging.info(f"Data root updated to: {new_path}")
        else:
            logging.warning("User cancelled data root selection. Files may not resolve.")
            if hasattr(self, 'status_bar'):
                self.status_bar.set("Warning: Data root not set. File paths may not resolve.")

    def change_data_root(self):
        """Allow user to change the data root directory via a folder picker."""
        if not self.project_service.current_project_config:
            messagebox.showwarning("No Project", "No project is currently open.")
            return
        new_path = filedialog.askdirectory(title="Select Data Root Directory")
        if new_path:
            self.project_service.update_user_data_root(new_path)
            self.status_bar.set(f"Data root updated to: {new_path}")
            # Refresh the project browser to reflect any changes
            self.project_browser.load_project()

    def edit_label_display(self):
        """Open dialog to edit behavior types (label_display)."""
        if not self.project_service.current_project_config:
            messagebox.showwarning("No Project", "No project is currently open.")
            return

        # Count how many labels use each behavior across all files
        usage_counts = {}
        self._count_label_usage(self.project_service.get_entries(), usage_counts)

        label_displays = self.project_service.current_project_config.label_display
        dialog = EditLabelDisplayDialog(self, label_displays, label_usage_counts=usage_counts)
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

        if dialog.result_ready and dialog.result_label_displays is not None:
            self.project_service.current_project_config.label_display = dialog.result_label_displays
            self.project_service.save_project()
            # Refresh viewer and info pane to reflect new colors/labels
            self.viewer.set_project_config(self.project_service.current_project_config)
            self.viewer.update_plot()
            self.info_pane.update_legend()
            self.set_status("Behavior labels updated.")

    def edit_input_settings(self):
        """Open dialog to edit input settings (type, frequency, y-range, regex, plot title)."""
        if not self.project_service.current_project_config:
            messagebox.showwarning("No Project", "No project is currently open.")
            return

        config = self.project_service.current_project_config
        dialog = EditInputSettingsDialog(
            self,
            input_settings=config.input_settings,
            y_range=config.y_range,
            individual_id_regex=config.individual_id_regex,
            plot_title_format=config.plot_title_format,
        )
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

        if dialog.result_ready:
            config.input_settings = dialog.result_input_settings
            config.y_range = dialog.result_y_range
            config.individual_id_regex = dialog.result_individual_id_regex
            config.plot_title_format = dialog.result_plot_title_format
            self.project_service.save_project()
            self.viewer.set_project_config(config)
            self.viewer.update_plot()
            self.set_status("Input settings updated.")

    def _collect_file_entries(self, entries, result):
        """Recursively collect all FileEntry objects from the project tree."""
        for entry in entries:
            if isinstance(entry, FileEntry):
                result.append(entry)
            elif isinstance(entry, DirectoryEntry):
                self._collect_file_entries(entry.entries, result)

    def export_labels_csv(self):
        """Export all labels from the project to a CSV file."""
        if not self.project_service.current_project_config:
            messagebox.showwarning("No Project", "No project is currently open.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Labels to CSV",
        )
        if not file_path:
            return

        file_entries = []
        self._collect_file_entries(self.project_service.get_entries(), file_entries)

        label_count = 0
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["file_id", "file_path", "behavior", "start_time", "end_time"])
            for fe in file_entries:
                for label in fe.labels:
                    writer.writerow([
                        fe.id,
                        fe.path,
                        label.behavior,
                        Label._serialize_time(label.start_time),
                        Label._serialize_time(label.end_time),
                    ])
                    label_count += 1

        messagebox.showinfo("Export Complete", f"Exported {label_count} labels to:\n{file_path}")
        self.set_status(f"Exported {label_count} labels to CSV.")

    def import_labels_csv(self):
        """Import labels from a CSV file into the project."""
        if not self.project_service.current_project_config:
            messagebox.showwarning("No Project", "No project is currently open.")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")],
            title="Import Labels from CSV",
        )
        if not file_path:
            return

        # Read and group rows by file_id
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows_by_file = {}
                for row in reader:
                    fid = row["file_id"]
                    rows_by_file.setdefault(fid, []).append(row)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to read CSV:\n{e}")
            return

        imported_labels = 0
        imported_files = 0
        skipped_files = []

        for file_id, rows in rows_by_file.items():
            # Look up file entry by ID, fall back to path
            fe = self.project_service.find_file_by_id(file_id)
            if fe is None:
                # Try matching by path from the first row
                target_path = rows[0].get("file_path", "")
                file_entries = []
                self._collect_file_entries(self.project_service.get_entries(), file_entries)
                for candidate in file_entries:
                    if candidate.path == target_path:
                        fe = candidate
                        break

            if fe is None:
                skipped_files.append(file_id)
                continue

            # Check for existing labels
            if fe.labels:
                answer = messagebox.askyesnocancel(
                    "File Already Has Labels",
                    f'"{fe.path}" already has {len(fe.labels)} labels.\n'
                    f'Replace with {len(rows)} labels from CSV?',
                )
                if answer is None:
                    # Cancel entire import
                    self.set_status("Import cancelled.")
                    return
                if not answer:
                    # Skip this file
                    continue

            # Create Label objects
            try:
                new_labels = [
                    Label(r["start_time"], r["end_time"], r["behavior"])
                    for r in rows
                ]
            except (ValueError, KeyError) as e:
                messagebox.showerror("Import Error",
                                     f"Error parsing labels for file {fe.path}:\n{e}")
                continue

            fe.labels = new_labels
            imported_labels += len(new_labels)
            imported_files += 1

        self.project_service.save_project()

        # Refresh viewer and info pane
        self.viewer.update_plot()
        self.info_pane.set_project_service(self.project_service)

        summary = f"Imported {imported_labels} labels for {imported_files} files."
        if skipped_files:
            summary += f" {len(skipped_files)} files skipped (not found)."
        messagebox.showinfo("Import Complete", summary)
        self.set_status(summary)

    def _count_label_usage(self, entries, usage_counts):
        """Recursively count label behavior usage across all file entries."""
        if not entries:
            return
        for entry in entries:
            if isinstance(entry, DirectoryEntry):
                self._count_label_usage(entry.entries, usage_counts)
            elif isinstance(entry, FileEntry):
                for label in entry.labels:
                    behavior = label.behavior if hasattr(label, 'behavior') else label.get('behavior', '')
                    usage_counts[behavior] = usage_counts.get(behavior, 0) + 1

    def edit_preferences(self):
        """Open preferences dialog and apply changes."""
        config = self.user_app_config
        dialog = PreferencesDialog(
            self,
            comment_save_delay=config.comment_save_delay,
            info_pane_max_width=config.info_pane_max_width,
        )
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

        if dialog.result_ready:
            self.user_app_config_service.update_preferences(
                comment_save_delay=dialog.result_comment_save_delay,
                info_pane_max_width=dialog.result_info_pane_max_width,
            )
            # Apply info pane max width
            self.INFO_PANE_MAX_WIDTH = dialog.result_info_pane_max_width
            # Apply comment save delay to info pane
            self.info_pane._comment_save_delay = dialog.result_comment_save_delay
            self.set_status("Preferences saved.")

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
        if not self.project_service.current_project_config:
            messagebox.showwarning("No Project", "No project is currently open.")
            return

        # Open the GenerateOutputDialog
        input_frequency = None
        if self.project_service.current_project_config.input_settings:
            input_frequency = self.project_service.current_project_config.input_settings.input_frequency
        output_dialog = GenerateOutputDialog(self, input_frequency=input_frequency)
        output_dialog.transient(self)
        output_dialog.grab_set()
        self.wait_window(output_dialog)

        # Retrieve the output settings from the dialog after it closes
        if output_dialog.result_ready and output_dialog.output_settings and output_dialog.output_directory:
            logging.info("Starting output generation...")
            self.start_output_generation(output_dialog.output_settings, output_dialog.output_directory)
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
        # Check if output directory already has content
        if os.path.isdir(output_directory) and os.listdir(output_directory):
            if not messagebox.askyesno(
                "Output Directory Not Empty",
                f"The output directory already contains files:\n{output_directory}\n\n"
                "Existing files may be overwritten. Continue?"
            ):
                self.set_status("Output generation cancelled.")
                return

        # Open the progress dialog
        progress_dialog = OutputProgressDialog(self)
        progress_dialog.transient(self)
        progress_dialog.grab_set()

        # Run the output generation in a separate thread to keep GUI responsive
        threading.Thread(
            target=self._run_output_generation,
            args=(output_settings, output_directory, progress_dialog),
            daemon=True
        ).start()

    def _run_output_generation(self, output_settings, output_directory, progress_dialog):
        """Run BEBE output generation in a background thread."""
        try:
            bebe = BEBEOutput()

            def progress_callback(current, total, file_path):
                if progress_dialog.cancelled:
                    raise _GenerationCancelled()
                self.after(0, lambda c=current, t=total, f=file_path: progress_dialog.update_progress(c, t, f))

            output_files = bebe.generate_output(
                self.project_service.current_project_config,
                output_directory,
                output_settings,
                progress_callback=progress_callback
            )

            if not progress_dialog.cancelled:
                logging.info(f"Output generation completed. {len(output_files)} files written.")
                self.after(0, lambda: self._on_generation_complete(progress_dialog, len(output_files)))
        except _GenerationCancelled:
            logging.info("Output generation cancelled by user.")
            self.after(0, lambda: self.set_status("Output generation cancelled."))
        except Exception as e:
            logging.error(f"Error during output generation: {e}")
            self.after(0, lambda: self._on_generation_error(progress_dialog, str(e)))

    def _on_generation_complete(self, progress_dialog, file_count):
        """Called on the main thread when generation completes."""
        try:
            progress_dialog.destroy()
        except tk.TclError:
            pass
        messagebox.showinfo("Success", f"Output generation completed. {file_count} files written.")

    def _on_generation_error(self, progress_dialog, error_msg):
        """Called on the main thread when generation fails."""
        try:
            progress_dialog.destroy()
        except tk.TclError:
            pass
        messagebox.showerror("Error", f"Output generation failed: {error_msg}")


if __name__ == '__main__':
    app = MainApplication()
    app.mainloop()
