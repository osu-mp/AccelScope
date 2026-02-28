import logging
import os
import re
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from gui_components.gui_theme import PAD_MD, PAD_LG, PAD_SM, FONT_BODY, FONT_SMALL
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.project_config import DEFAULT_INDIVIDUAL_ID_REGEX
from services.project_service import ProjectService


class NewProjectDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("New Project")
        self.resizable(True, True)

        self.project_service = ProjectService()
        self.created_project_path = None
        self._file_vars = {}   # relative_path -> BooleanVar

        # ── Top form ────────────────────────────────────────────────────────
        form = ttk.Frame(self)
        form.pack(fill=tk.X, padx=PAD_LG, pady=(PAD_LG, 0))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Project Name:").grid(
            row=0, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.name_entry = ttk.Entry(form)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(form, text="Project File Location:").grid(
            row=1, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.location_entry = ttk.Entry(form)
        self.location_entry.grid(row=1, column=1, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)
        ttk.Button(form, text="Browse", command=self.select_file).grid(
            row=1, column=2, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(form, text="Input Data Root:").grid(
            row=2, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.data_root_entry = ttk.Entry(form)
        self.data_root_entry.grid(row=2, column=1, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)
        browse_root_btn = ttk.Button(form, text="Browse", command=self.select_directory)
        browse_root_btn.grid(row=2, column=2, padx=PAD_MD, pady=PAD_MD)

        ttk.Label(form, text="File Extensions:").grid(
            row=3, column=0, sticky=tk.W, padx=PAD_MD, pady=PAD_MD)
        self.extensions_entry = ttk.Entry(form)
        self.extensions_entry.insert(0, ".csv")
        self.extensions_entry.grid(row=3, column=1, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)
        ttk.Label(form, text="e.g. .csv, .txt", foreground="gray", font=FONT_SMALL).grid(
            row=3, column=2, sticky=tk.W, padx=PAD_MD)

        # Flatten option + scan button on same row
        opts_frame = ttk.Frame(form)
        opts_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, padx=PAD_MD, pady=PAD_MD)
        self.flatten_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_frame, text="Flatten by individual ID", variable=self.flatten_var,
            command=self._on_scan
        ).pack(side=tk.LEFT, padx=(0, PAD_LG))
        ttk.Button(opts_frame, text="Scan for Files", command=self._on_scan).pack(side=tk.LEFT)
        self.scan_count_label = ttk.Label(opts_frame, text="", font=FONT_SMALL, foreground="gray")
        self.scan_count_label.pack(side=tk.LEFT, padx=PAD_MD)

        # ── File preview section ─────────────────────────────────────────────
        preview_frame = ttk.LabelFrame(self, text="Files to Import")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_LG, pady=PAD_MD)

        sel_bar = ttk.Frame(preview_frame)
        sel_bar.pack(fill=tk.X, padx=PAD_SM, pady=PAD_SM)
        ttk.Button(sel_bar, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=PAD_SM)
        ttk.Button(sel_bar, text="Deselect All", command=self._deselect_all).pack(side=tk.LEFT, padx=PAD_SM)
        self.selected_count_label = ttk.Label(sel_bar, text="No files scanned yet.", font=FONT_SMALL, foreground="gray")
        self.selected_count_label.pack(side=tk.LEFT, padx=PAD_MD)

        # Scrollable canvas for checkboxes
        canvas_frame = ttk.Frame(preview_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_SM, pady=PAD_SM)
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_frame = ttk.Frame(self.canvas)
        self._scroll_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # ── Bottom buttons ───────────────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=PAD_LG, pady=PAD_LG)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=PAD_MD)
        ttk.Button(btn_frame, text="Create Project", command=self.create_project).pack(side=tk.RIGHT, padx=PAD_MD)

        self.minsize(520, 460)

    # ── Scrollable canvas helpers ────────────────────────────────────────────

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._scroll_window, width=event.width)

    # ── File browsing ────────────────────────────────────────────────────────

    def select_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Project File"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r'):
                if messagebox.askokcancel("Confirm Overwrite",
                                          "This file already exists. Do you want to overwrite it?"):
                    self.location_entry.delete(0, tk.END)
                    self.location_entry.insert(0, file_path)
        except FileNotFoundError:
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, file_path)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.data_root_entry.delete(0, tk.END)
            self.data_root_entry.insert(0, directory)
            self._on_scan()

    # ── File scanning ────────────────────────────────────────────────────────

    def _parse_extensions(self):
        """Return a set of normalised extensions from the extensions entry."""
        raw = self.extensions_entry.get()
        exts = set()
        for part in raw.split(","):
            part = part.strip().lower()
            if part and not part.startswith("."):
                part = "." + part
            if part:
                exts.add(part)
        return exts

    def _on_scan(self):
        data_root = self.data_root_entry.get().strip()
        if not data_root or not os.path.isdir(data_root):
            return
        extensions = self._parse_extensions()
        flatten = self.flatten_var.get()
        self._scan_files(data_root, extensions, flatten)

    def _scan_files(self, data_root, extensions, flatten):
        """Walk data_root, collect matching files, rebuild checkbox tree."""
        # Collect all matching relative paths
        found = []
        for dirpath, _dirs, filenames in os.walk(data_root):
            for filename in sorted(filenames):
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    rel = os.path.relpath(os.path.join(dirpath, filename), data_root)
                    rel = rel.replace("\\", "/")
                    found.append(rel)

        # Optionally flatten by individual ID
        if flatten:
            found = self._flatten_paths(found)

        self.scan_count_label.config(text=f"{len(found)} files found")
        self._build_checkbox_tree(found)
        self._update_count_label()

    def _flatten_paths(self, rel_paths):
        """Remap paths to individual/filename using DEFAULT_INDIVIDUAL_ID_REGEX."""
        result = []
        unknown_count = {}
        for rel in rel_paths:
            filename = rel.split("/")[-1]
            match = re.search(DEFAULT_INDIVIDUAL_ID_REGEX, rel)
            if match:
                try:
                    individual = match.group("individual")
                except IndexError:
                    individual = "Unknown"
            else:
                individual = "Unknown"
            # Avoid collisions if same filename appears under same individual
            candidate = f"{individual}/{filename}"
            if candidate in result:
                stem, ext_part = os.path.splitext(filename)
                n = unknown_count.get(candidate, 1)
                candidate = f"{individual}/{stem}_{n}{ext_part}"
                unknown_count[f"{individual}/{filename}"] = n + 1
            result.append(candidate)
        return result

    # ── Checkbox tree building ───────────────────────────────────────────────

    def _build_checkbox_tree(self, rel_paths):
        """Rebuild scroll_frame with a hierarchical checkbox list."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self._file_vars.clear()

        # Build a nested dict tree from paths
        tree = {}
        for rel in rel_paths:
            parts = rel.split("/")
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = rel  # leaf: value is the full relative path

        self._render_tree_node(tree, depth=0, parent_rel="")

    def _render_tree_node(self, node, depth, parent_rel):
        indent = depth * 16
        for name, value in sorted(node.items(), key=lambda kv: (isinstance(kv[1], dict), kv[0])):
            if isinstance(value, dict):
                # Directory label
                lbl = ttk.Label(self.scroll_frame, text=f"[{name}]", font=FONT_BODY)
                lbl.pack(anchor=tk.W, padx=(PAD_SM + indent, PAD_SM), pady=1)
                self._render_tree_node(value, depth + 1, f"{parent_rel}/{name}" if parent_rel else name)
            else:
                # File checkbox
                var = tk.BooleanVar(value=True)
                self._file_vars[value] = var
                cb = ttk.Checkbutton(
                    self.scroll_frame, text=name, variable=var,
                    command=self._update_count_label
                )
                cb.pack(anchor=tk.W, padx=(PAD_SM + indent, PAD_SM), pady=1)

    # ── Select all / deselect all ────────────────────────────────────────────

    def _select_all(self):
        for var in self._file_vars.values():
            var.set(True)
        self._update_count_label()

    def _deselect_all(self):
        for var in self._file_vars.values():
            var.set(False)
        self._update_count_label()

    def _update_count_label(self):
        total = len(self._file_vars)
        selected = sum(1 for v in self._file_vars.values() if v.get())
        if total == 0:
            self.selected_count_label.config(text="No files scanned yet.")
        else:
            self.selected_count_label.config(text=f"{selected} of {total} selected")

    # ── Project creation ─────────────────────────────────────────────────────

    def _build_entries_from_checked(self):
        """Convert checked file vars into a DirectoryEntry/FileEntry tree."""
        checked = [rel for rel, var in self._file_vars.items() if var.get()]

        # Build nested dict: dir_name -> {... -> relative_path}
        root_dict = {}
        for rel in checked:
            parts = rel.replace("\\", "/").split("/")
            node = root_dict
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = rel

        def dict_to_entries(d):
            entries = []
            for name, val in sorted(d.items()):
                if isinstance(val, dict):
                    sub = dict_to_entries(val)
                    entries.append(DirectoryEntry(name=name, entries=sub))
                else:
                    entries.append(FileEntry(path=val))
            return entries

        return dict_to_entries(root_dict)

    def create_project(self):
        proj_name = self.name_entry.get().strip()
        location = self.location_entry.get().strip()
        data_root = self.data_root_entry.get().strip()

        logging.info(f"Creating new project config at {location}")

        entries = self._build_entries_from_checked()

        try:
            self.project_service.create_project(
                proj_name=proj_name,
                location=location,
                data_root=data_root,
                entries=entries,
            )
            self.created_project_path = location
            self.destroy()
        except Exception as e:
            logging.error(f"Failed to create project: {e}")
            messagebox.showerror("Error", f"Failed to create project: {e}")

    def get_created_project_path(self):
        return self.created_project_path
