import logging
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

import matplotlib.pyplot as plt

# Pixel size of the close × image placed in each tab header
_CLOSE_IMG_SIZE = 12


def _make_close_image(size=_CLOSE_IMG_SIZE):
    """
    Build a tiny PhotoImage with an × drawn pixel-by-pixel.
    Returns the image (caller must keep a reference or it will be GC'd).
    """
    img = tk.PhotoImage(width=size, height=size)
    # Transparent background (uses the widget's background colour)
    bg = '#d9d9d9'
    for y in range(size):
        img.put(' '.join([bg] * size), to=(0, y))
    # Draw two diagonals in dark grey, 2 px thick
    fg = '#404040'
    pad = 2
    for i in range(pad, size - pad):
        for dx in range(2):
            # top-left → bottom-right
            xi, yi = i + dx, i
            if 0 <= xi < size and 0 <= yi < size:
                img.put(fg, to=(xi, yi, xi + 1, yi + 1))
            # top-right → bottom-left
            xj, yj = (size - 1 - i) + dx, i
            if 0 <= xj < size and 0 <= yj < size:
                img.put(fg, to=(xj, yj, xj + 1, yj + 1))
    return img


class _TabFrame(ttk.Frame):
    """
    A ttk.Frame that lives inside a notebook tab.
    Proxies set_status() up to the main application so that Viewer instances
    (which call self.parent.set_status()) work correctly even though their
    direct parent is this frame rather than MainApplication.
    """
    def __init__(self, notebook_widget, main_app, **kwargs):
        super().__init__(notebook_widget, **kwargs)
        self._main_app = main_app

    def set_status(self, msg):
        self._main_app.set_status(msg)


class ViewerNotebook(ttk.Frame):
    """
    Tabbed viewer container that wraps ttk.Notebook.

    Each tab holds one Viewer instance. Exposes the same interface as Viewer
    so main.py and InfoPane can treat it transparently. Closing a tab calls
    plt.close() on the figure to free matplotlib memory.

    Tab management:
      - Double-clicking a file in the project browser opens it in a new tab
        (or switches to its existing tab if already open).
      - Click the × on the tab header to close it.
      - Middle-click a tab, Ctrl+W, or right-click → Close Tab also work.
    """

    def __init__(self, parent, project_service, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.project_service = project_service

        # State shared across all tabs
        self._project_config = None
        self._info_pane = None

        # Tab tracking: file_entry_id -> {'frame', 'viewer', 'entry'}
        self._tabs = {}

        # Close button image — must be kept alive on self
        self._close_img = _make_close_image()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.bind("<Button-1>",   self._on_click)        # × close
        self.notebook.bind("<Button-2>",   self._on_middle_click) # middle-click
        self.notebook.bind("<Button-3>",   self._on_right_click_tab)

        # Ctrl+W closes active tab
        self.bind_all("<Control-w>", lambda e: self._close_active_tab())

        # Right-click context menu
        self._tab_menu = tk.Menu(self, tearoff=0)
        self._tab_menu.add_command(label="Close Tab",      command=self._close_active_tab)
        self._tab_menu.add_command(label="Close All Tabs", command=self._close_all_tabs)

    # ── Public interface (proxies to active Viewer) ──────────────────────────

    def load_file_entry(self, file_entry):
        """Open file_entry in a new tab, or switch to existing tab."""
        from gui_components.viewer import Viewer  # avoids circular import

        fid = file_entry.id

        if fid in self._tabs:
            self.notebook.select(self._tabs[fid]['frame'])
            return

        tab_frame = _TabFrame(self.notebook, main_app=self.parent)
        viewer = Viewer(tab_frame, project_service=self.project_service)
        viewer.pack(fill=tk.BOTH, expand=True)

        if self._project_config:
            viewer.set_project_config(self._project_config)
        if self._info_pane:
            viewer.set_info_pane(self._info_pane)

        viewer.load_file_entry(file_entry)

        tab_label = file_entry.path.split('/')[-1].split('\\')[-1]
        if tab_label.lower().endswith('.csv'):
            tab_label = tab_label[:-4]

        self.notebook.add(tab_frame,
                          text=tab_label,
                          image=self._close_img,
                          compound=tk.RIGHT)
        self._tabs[fid] = {'frame': tab_frame, 'viewer': viewer, 'entry': file_entry}
        self.notebook.select(tab_frame)

    def set_project_config(self, config):
        self._project_config = config
        for tab in self._tabs.values():
            tab['viewer'].set_project_config(config)

    def set_info_pane(self, info_pane):
        self._info_pane = info_pane
        for tab in self._tabs.values():
            tab['viewer'].set_info_pane(info_pane)

    def clear_plot(self):
        """Close all tabs (called when a new project is loaded)."""
        self._close_all_tabs()

    def get_input_interface(self):
        v = self._active_viewer()
        return v.get_input_interface() if v else None

    def get_data_path(self):
        v = self._active_viewer()
        return v.get_data_path() if v else None

    def update_plot(self, labels_only=False):
        v = self._active_viewer()
        if v:
            v.update_plot(labels_only=labels_only)

    def set_active_axes(self, active_axes):
        v = self._active_viewer()
        if v:
            v.set_active_axes(active_axes)

    def update_label_list(self):
        v = self._active_viewer()
        if v:
            v.update_label_list()

    def zoom_in_on_all_labels(self, event=None):
        v = self._active_viewer()
        if v:
            v.zoom_in_on_all_labels(event)

    def zoom_out_to_show_all(self, event=None):
        v = self._active_viewer()
        if v:
            v.zoom_out_to_show_all(event)

    def on_undo(self, event=None):
        v = self._active_viewer()
        if v:
            v.on_undo(event)

    def on_redo(self, event=None):
        v = self._active_viewer()
        if v:
            v.on_redo(event)

    @property
    def labels(self):
        v = self._active_viewer()
        return v.labels if v else []

    @property
    def file_entry(self):
        v = self._active_viewer()
        return v.file_entry if v else None

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _active_viewer(self):
        selected = self.notebook.select()
        if not selected:
            return None
        for tab in self._tabs.values():
            if str(tab['frame']) == selected:
                return tab['viewer']
        return None

    def _active_file_id(self):
        selected = self.notebook.select()
        if not selected:
            return None
        for fid, tab in self._tabs.items():
            if str(tab['frame']) == selected:
                return fid
        return None

    def _tab_index_for_fid(self, fid):
        frame_str = str(self._tabs[fid]['frame'])
        for i, path in enumerate(self.notebook.tabs()):
            if path == frame_str:
                return i
        return None

    # ── Click → close detection ──────────────────────────────────────────────

    def _on_click(self, event):
        """Close a tab when the user clicks its × image."""
        try:
            tab_idx = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return  # click not on any tab

        # The × image is _CLOSE_IMG_SIZE wide, placed at the right of the tab.
        # Compute cumulative tab widths to find the right edge of the target tab.
        try:
            font = tkfont.nametofont("TkDefaultFont")
        except Exception:
            font = tkfont.Font()

        tab_pad = 14  # approximate horizontal padding per tab (clam theme)
        x_cursor = 0
        for i in range(self.notebook.index("end")):
            text = self.notebook.tab(i, "text")
            tab_w = font.measure(text) + _CLOSE_IMG_SIZE + tab_pad
            if i == tab_idx:
                # Right edge of this tab; × occupies the last _CLOSE_IMG_SIZE px
                x_right = x_cursor + tab_w
                if event.x >= x_right - _CLOSE_IMG_SIZE - 2:  # 2 px tolerance
                    self._close_tab_by_index(tab_idx)
                return
            x_cursor += tab_w

    # ── Tab event handlers ───────────────────────────────────────────────────

    def _on_tab_changed(self, event):
        v = self._active_viewer()
        if v and self._info_pane and v.file_entry:
            # Use the canonical FileEntry from _tabs, not v.file_entry which is a deep copy
            canonical = self._tabs.get(v.file_entry.id, {}).get('entry')
            self._info_pane.set_file_entry(canonical or v.file_entry)

    def _on_middle_click(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            self._close_tab_by_index(index)
        except tk.TclError:
            pass

    def _on_right_click_tab(self, event):
        try:
            self.notebook.index(f"@{event.x},{event.y}")
            self._tab_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass

    def _close_active_tab(self):
        fid = self._active_file_id()
        if fid:
            self._close_tab(fid)

    def _close_all_tabs(self):
        for fid in list(self._tabs.keys()):
            self._close_tab(fid)

    def _close_tab_by_index(self, index):
        frame_path = self.notebook.tabs()[index]
        for fid, tab in self._tabs.items():
            if str(tab['frame']) == frame_path:
                self._close_tab(fid)
                return

    def _close_tab(self, fid):
        tab = self._tabs.pop(fid, None)
        if tab is None:
            return
        viewer = tab['viewer']
        try:
            plt.close(viewer.fig)
        except Exception:
            pass
        self.notebook.forget(tab['frame'])
        tab['frame'].destroy()
        logging.debug(f"Closed viewer tab for file id {fid}")

        if not self._tabs and self._info_pane:
            self._info_pane.set_file_entry(None)
