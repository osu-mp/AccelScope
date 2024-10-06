import tkinter as tk
from tkinter import ttk, filedialog

from models.project_config import DirectoryEntry, FileEntry


class ProjectBrowser(tk.Frame):
    def __init__(self, parent, project_config, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_config = project_config        # TODO: get rid of
        self.project_service = project_service

        # Add the title label with no padding and specific style
        self.title_label = tk.Label(self, text="Project Browser", font=("Helvetica", 10))
        self.title_label.pack(side=tk.TOP, anchor=tk.W, padx=0, pady=0)

        # Create a frame for Treeview to ensure tight layout
        self.tree_frame = tk.Frame(self)  # Additional container to remove extra borders
        self.tree_frame.pack(fill=tk.BOTH, expand=True)


        # Create the Treeview widget
        self.tree = ttk.Treeview(self.tree_frame, show="tree", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("green", foreground="green")
        self.tree.tag_configure("red", foreground="red")

        # Set up the root node
        if self.project_config:
            self.root_node = self.tree.insert('', 'end', self.project_config.proj_name, text=self.project_config.proj_name, open=True)

        # Set up the context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Add Subdirectory", command=self.add_subdirectory)
        self.menu.add_command(label="Add CSV File", command=self.add_csv)

        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click on Windows/Linux
        self.tree.bind("<Double-1>", self.on_double_click)

    def show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.post(event.x_root, event.y_root)

    def add_subdirectory(self):
        # Get the selected item in the tree
        selected_item = self.tree.selection()[0]

        # Prompt user to enter a new directory name
        new_dir_name = tk.simpledialog.askstring("New Directory", "Enter name for the new directory:")

        if new_dir_name:
            # Get the full path for the selected item
            full_path = self.get_full_path(selected_item)

            # Update the project configuration
            self.project_service.add_directory(full_path, new_dir_name)

            # Create a unique ID for the new directory
            new_id = f"{selected_item}/{new_dir_name}"
            self.tree.insert(selected_item, 'end', new_id, text=new_dir_name)

            # Expand all parent nodes to make sure the new item is visible
            self.tree.see(new_id)

    def get_full_path(self, item_id):
        """Construct the full path for the given tree item ID using unique identifiers."""
        segments = []
        current_item = item_id

        # Traverse up the tree to construct the full path
        while current_item:
            parent = self.tree.parent(current_item)
            # Avoid adding the project name itself to the segments
            if parent:
                segments.append(self.tree.item(current_item, "text"))
            current_item = parent

        # Reverse to get the correct path order
        segments.reverse()
        return '/'.join(segments)

    def add_csv(self):
        selected_item = self.tree.selection()[0]
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])

        if filepath:
            full_path = self.get_full_path(selected_item)
            relative_path = filepath.replace(self.project_config.data_root_directory, "").lstrip('/').lstrip('\\')

            # Create a new FileEntry with default user_verified as False
            file_entry = FileEntry(path=relative_path, user_verified=False)
            self.project_service.add_file(full_path, file_entry)

            # Add the new file to the tree view and update its color based on user_verified status
            new_id = self.tree.insert(selected_item, 'end', text=relative_path.split('/')[-1])
            self.update_tree_item_color(file_entry.file_id, file_entry.user_verified)

            # Open the file in the viewer
            self.parent.open_file(file_entry)

    def update_tree_item_color(self, file_id, user_verified):
        """Update the color of the tree item based on the user_verified status."""
        item_id = self.find_tree_item_by_file_id(file_id)
        if item_id:
            color = "green" if user_verified else "red"
            self.tree.item(item_id, tags=("user_verified",))
            self.tree.tag_configure("user_verified", foreground=color)

    def find_tree_item_by_file_id(self, file_id):
        """Find the tree item ID for the given file ID."""
        # TODO : this is not properly working when user checks/unchecks verified box
        for item in self.tree.get_children():
            if self.tree.item(item, "values") and self.tree.item(item, "values")[0] == file_id:
                return item
        return None

    def load_project(self):
        # Clear the tree first
        self.tree.delete(*self.tree.get_children())

        if not self.project_service or not self.project_service.current_project_config:
            return

        # Add root node
        self.root_node = self.tree.insert('', 'end', self.project_config.proj_name, text=self.project_config.proj_name, open=True)

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
            text_color = "green" if entry.user_verified else "red"
            self.tree.insert(parent_node, 'end', text=entry.path.split('/')[-1], values=(entry.file_id), tags=(text_color,))

    def on_double_click(self, event):
        """Handle double-click on a tree item"""
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, 'values')

        if item_values:
            file_id = item_values[0]
            file_entry = self.project_service.find_file_by_id(file_id)

            if file_entry:
                self.parent.open_file(file_entry)

    def set_project_config(self, project_config):
        self.project_config = project_config
        self.load_project()
