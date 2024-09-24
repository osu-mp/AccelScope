import tkinter as tk
from tkinter import ttk, filedialog

from models.project_config import DirectoryEntry, FileEntry


class ProjectBrowser(tk.Frame):
    def __init__(self, parent, project_config, config_manager, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_config = project_config
        self.config_manager = config_manager

        # Add the title label with no padding and specific style
        self.title_label = tk.Label(self, text="Project Browser", font=("Helvetica", 10))
        self.title_label.pack(side=tk.TOP, anchor=tk.W, padx=0, pady=0)

        # Create a frame for Treeview to ensure tight layout
        self.tree_frame = tk.Frame(self)  # Additional container to remove extra borders
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create the Treeview widget
        self.tree = ttk.Treeview(self.tree_frame, show="tree", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Set up the root node
        if self.project_config:
            self.root_node = self.tree.insert('', 'end', text=self.project_config.proj_name, open=True)

        # Set up the context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Add Subdirectory", command=self.add_subdirectory)
        self.menu.add_command(label="Import CSV File", command=self.import_csv)

        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click on Windows/Linux
        self.tree.bind("<Double-1>", self.on_double_click)

    def show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.post(event.x_root, event.y_root)

    def add_subdirectory(self):
        selected_item = self.tree.selection()[0]
        new_dir_name = tk.simpledialog.askstring("New Directory", "Enter name for the new directory:")
        if new_dir_name:
            full_path = self.get_full_path(selected_item)  # Get the full path for the selected item
            # Add new directory to the tree view
            new_id = self.tree.insert(selected_item, 'end', text=new_dir_name)
            full_new_path = self.get_full_path(new_id)  # Full path including new directory

            # Update the project configuration
            self.project_config.add_directory(full_path, new_dir_name, full_new_path)
            # Save the updated configuration
            self.project_config.save_config()

    def get_full_path(self, item_id):
        path = []
        while item_id:
            path.insert(0, self.tree.item(item_id, 'text'))
            item_id = self.tree.parent(item_id)
        return '/'.join(path)

    def import_csv(self):
        selected_item = self.tree.selection()[0]
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])

        if filepath:
            full_path = self.get_full_path(selected_item)

            # Get the relative path based on the data_root_directory
            relative_path = filepath.replace(self.project_config.data_root_directory, "").lstrip('/').lstrip('\\')

            # Insert the file into the tree and update the project configuration
            self.tree.insert(selected_item, 'end', text=relative_path.split('/')[-1])

            # Update the actual project configuration with the relative path
            file_entry = FileEntry(relative_path)
            self.project_config.add_file(full_path, file_entry)
            self.project_config.save_config()

            # Notify the main GUI that a file was imported
            self.master.file_imported(filepath)

    def load_project(self):
        # Clear the tree first
        self.tree.delete(*self.tree.get_children())

        # Add root node
        self.root_node = self.tree.insert('', 'end', text=self.project_config.proj_name, open=True)

        # Recursively add all directories and files
        for entry in self.project_config.entries:
            self._populate_tree(self.root_node, entry)

    def _populate_tree(self, parent_node, entry):
        """
        Recursively populates the tree view with the given directory structure or file entry.
        Args:
            parent_node: The tree node under which the entries will be added.
            entry: A DirectoryEntry or FileEntry instance to be added to the tree.
        """
        if isinstance(entry, DirectoryEntry):
            # Add a directory node
            dir_node = self.tree.insert(parent_node, 'end', text=entry.name, open=True)
            # Recursively populate its children
            for child_entry in entry.entries:
                self._populate_tree(dir_node, child_entry)
        elif isinstance(entry, FileEntry):
            # use the file's id as a hidden value for easy lookup later
            self.tree.insert(parent_node, 'end', text=entry.path.split('/')[-1], values=(entry.file_id))

    def on_double_click(self, event):
        """Handle double-click on a tree item"""
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, 'values')

        if item_values:
            file_id = item_values[0]
            file_entry = self.config_manager.get_file_entry(file_id)

            if file_entry:
                self.parent.open_file(file_entry)
                # Combine the data root directory with the relative path stored in FileEntry
                full_file_path = f"{self.project_config.data_root_directory}/{file_entry.path}"

                # Inform the main application to load the file in the viewer
                # self.master.load_csv(full_file_path)
