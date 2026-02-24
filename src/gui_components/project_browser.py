import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from accel_data_parser import AccelDataParser
from gui_components.gui_theme import PAD_SM, PAD_MD, FONT_BODY
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry


class ProjectBrowser(ttk.Frame):
    def __init__(self, parent, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_service = project_service

        # Add the title label with no padding and specific style
        self.title_label = ttk.Label(self, text="Project Browser", font=FONT_BODY)
        self.title_label.pack(side=tk.TOP, anchor=tk.W, padx=PAD_SM, pady=PAD_SM)

        # Create filter bar between title and tree
        self._create_filter_bar()

        # Create a frame for Treeview to ensure tight layout
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create the Treeview widget
        self.tree = ttk.Treeview(self.tree_frame, show="tree", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("green", foreground="green")
        self.tree.tag_configure("yellow", foreground="#B8860B")
        self.tree.tag_configure("red", foreground="red")

        # Set up the context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Add Subdirectory", command=self.add_subdirectory)
        self.menu.add_command(label="Add CSV File", command=self.add_csv)
        self.menu.add_command(label="Delete File", command=self.delete_file)

        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click on Windows/Linux
        self.tree.bind("<Double-1>", self.on_double_click)

    def _create_filter_bar(self):
        """Create a filter bar with text search and status filter."""
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=PAD_SM, pady=PAD_SM)

        self.filter_entry = ttk.Entry(filter_frame)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, PAD_SM))
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        self.status_filter_var = tk.StringVar(value="All")
        self.status_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.status_filter_var,
            values=["All", "Verified", "Partial", "Unverified"], state="readonly", width=10
        )
        self.status_filter_combo.pack(side=tk.LEFT, padx=(0, PAD_SM))
        self.status_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        clear_btn = ttk.Button(filter_frame, text="Clear", width=5, command=self._clear_filter)
        clear_btn.pack(side=tk.LEFT)

    def _clear_filter(self):
        """Reset filter controls and reload the tree."""
        self.filter_entry.delete(0, tk.END)
        self.status_filter_var.set("All")
        self._apply_filter()

    def _apply_filter(self):
        """Reload the tree with current filter criteria."""
        self.tree.delete(*self.tree.get_children())

        if not self.project_service or not self.project_service.current_project_config:
            return

        text_filter = self.filter_entry.get().strip().lower()
        status_filter = self.status_filter_var.get()

        proj_name = self.project_service.get_project_name()
        root_node = self.tree.insert('', 'end', proj_name, text=proj_name, open=True)

        for entry in self.project_service.get_entries():
            self._populate_tree(root_node, entry, text_filter, status_filter)

    def _entry_matches_filter(self, entry, text_filter, status_filter):
        """Check if a file or directory (recursively) matches the filter criteria."""
        if isinstance(entry, FileEntry):
            filename = entry.path.split('/')[-1].split('\\')[-1].lower()
            if text_filter and text_filter not in filename:
                return False
            if status_filter != "All":
                color = self._get_verification_color(entry.verified_by)
                if status_filter == "Verified" and color != "green":
                    return False
                if status_filter == "Partial" and color != "yellow":
                    return False
                if status_filter == "Unverified" and color != "red":
                    return False
            return True
        elif isinstance(entry, DirectoryEntry):
            return any(self._entry_matches_filter(child, text_filter, status_filter)
                       for child in entry.entries)
        return False

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
            data_root_dir = self.project_service.get_project_root_dir()
            if not filepath.startswith(data_root_dir):
                self.parent.set_status(f"Unable to add file, only files in project root ({data_root_dir}) are allowed")
                return

            # Ensure the file can be loaded, show error dialog if parsing fails
            try:
                data_parser = AccelDataParser(filepath)
                data = data_parser.read_data()
            except Exception as e:
                self.parent.set_status("Unable to add file as this file does not contain valid accelerometer data")
                messagebox.showerror("Error", f"Unable to parse CSV file: {filepath}\n\nError: {str(e)}")
                return

            full_path = self.get_full_path(selected_item)

            relative_path = filepath.replace(data_root_dir, "").lstrip('/').lstrip('\\')

            file_entry = FileEntry(path=relative_path)
            self.project_service.add_file(full_path, file_entry)

            self.tree.insert(selected_item, 'end', text=relative_path.split('/')[-1], values=(file_entry.id,))
            self.update_tree_item_color(file_entry.id, file_entry.verified_by)

            # Open the file in the viewer
            self.parent.open_file(file_entry)

    def _get_verification_color(self, verified_by):
        """Return 'red', 'yellow', or 'green' based on reviewer verification state."""
        return self.project_service.get_verification_color(verified_by)

    def update_tree_item_color(self, id, verified_by):
        """Update the color of the tree item based on the verified_by list."""
        item_id = self.find_tree_item_by_id(id)
        if item_id:
            color = self._get_verification_color(verified_by)
            self.tree.item(item_id, tags=(color,))

    def find_tree_item_by_id(self, id):
        """Find the tree item ID for the given file ID."""
        # Recursively search through all items in the tree
        for item in self.tree.get_children(''):
            result = self._search_tree(item, id)
            if result:
                return result
        return None

    def _search_tree(self, item, id):
        """Helper function to recursively search the tree for a file ID."""
        if self.tree.item(item, "values") and self.tree.item(item, "values")[0] == id:
            return item
        for child_item in self.tree.get_children(item):
            result = self._search_tree(child_item, id)
            if result:
                return result
        return None

    def load_project(self):
        # Clear the tree first
        self.tree.delete(*self.tree.get_children())

        if not self.project_service or not self.project_service.current_project_config:
            return

        # Add root node
        proj_name = self.project_service.get_project_name()
        root_node = self.tree.insert('', 'end', proj_name, text=proj_name, open=True)

        # Recursively add all directories and files
        for entry in self.project_service.get_entries():
            self._populate_tree(root_node, entry)

    def _populate_tree(self, parent_node, entry, text_filter="", status_filter="All"):
        """
        Recursively populates the tree view with the given directory structure or file entry.
        Args:
            parent_node: The tree node under which the entries will be added.
            entry: A DirectoryEntry or FileEntry instance to be added to the tree.
            text_filter: Lowercase text to filter filenames by substring.
            status_filter: "All", "Verified", or "Unverified".
        """
        has_filter = text_filter or status_filter != "All"

        if isinstance(entry, DirectoryEntry):
            if has_filter and not self._entry_matches_filter(entry, text_filter, status_filter):
                return
            # Add a directory node
            dir_node = self.tree.insert(parent_node, 'end', text=entry.name, open=True)
            # Recursively populate its children
            for child_entry in entry.entries:
                self._populate_tree(dir_node, child_entry, text_filter, status_filter)
        elif isinstance(entry, FileEntry):
            if has_filter and not self._entry_matches_filter(entry, text_filter, status_filter):
                return
            # Use the file's id as a hidden value for easy lookup later
            color_tag = self._get_verification_color(entry.verified_by)
            self.tree.insert(parent_node, 'end', text=entry.path.split('/')[-1], values=(entry.id,),
                             tags=(color_tag,))

    def on_double_click(self, event):
        """Handle double-click on a tree item"""
        selected_item = self.tree.selection()[0]
        item_values = self.tree.item(selected_item, 'values')

        if item_values:
            id = item_values[0]
            file_entry = self.project_service.find_file_by_id(id)

            if file_entry:
                self.parent.open_file(file_entry)

    def delete_file(self):
        """Delete a file from the project configuration and tree view."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_values = self.tree.item(selected_item, 'values')
        if not item_values:
            return

        id = item_values[0]
        file_entry = self.project_service.find_file_by_id(id)

        if not file_entry:
            return

        # Confirm deletion with the user
        confirm = messagebox.askyesno("Delete File", f"Are you sure you want to delete {file_entry.path}?")
        if not confirm:
            return

        # Remove the file entry from the project configuration
        self.project_service.delete_file_by_id(id)

        # Remove the item from the tree view
        self.tree.delete(selected_item)

        self.parent.set_status(f"Deleted file: {file_entry.path}")
