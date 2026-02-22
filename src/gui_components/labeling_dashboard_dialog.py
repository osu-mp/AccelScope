import tkinter as tk
from tkinter import ttk
from datetime import timedelta

from gui_components.gui_theme import PAD_MD, PAD_LG, FONT_TITLE, FONT_HEADING, FONT_BODY


class LabelingDashboardDialog(tk.Toplevel):
    """Read-only dashboard showing project-wide labeling progress and statistics."""

    def __init__(self, parent, file_entries, label_displays, reviewers):
        super().__init__(parent)
        self.title("Labeling Dashboard")
        self.resizable(True, True)
        self.minsize(480, 300)

        self.file_entries = file_entries
        self.label_displays = label_displays
        self.reviewers = reviewers

        self._compute_stats()
        self._build_ui()

    def _is_fully_verified(self, fe):
        """Return True if file is fully verified (green status)."""
        num_verified = len(fe.verified_by)
        if num_verified == 0:
            return False
        num_reviewers = len(self.reviewers)
        if num_reviewers == 0:
            return True
        return num_verified >= num_reviewers

    def _format_duration(self, total_seconds):
        """Format seconds as 'X.Y sec' or 'X.Y min'."""
        if total_seconds < 60:
            return f"{total_seconds:.1f} sec"
        return f"{total_seconds / 60:.1f} min"

    def _compute_stats(self):
        """Compute all dashboard statistics from file entries."""
        self.total_files = len(self.file_entries)
        self.files_with_labels = sum(1 for fe in self.file_entries if fe.labels)
        self.files_fully_verified = sum(1 for fe in self.file_entries if self._is_fully_verified(fe))
        self.total_labels = sum(len(fe.labels) for fe in self.file_entries)

        # Per-behavior stats: {display_name: {"labels": int, "files": set, "duration_sec": float}}
        self.behavior_stats = {}
        for ld in self.label_displays:
            self.behavior_stats[ld.display_name] = {"labels": 0, "files": set(), "duration_sec": 0.0}

        for fe in self.file_entries:
            for label in fe.labels:
                if label.behavior in self.behavior_stats:
                    stats = self.behavior_stats[label.behavior]
                    stats["labels"] += 1
                    stats["files"].add(fe.id)
                    stats["duration_sec"] += label.duration.total_seconds()

        # Per-reviewer stats
        self.reviewer_stats = {}
        for username, info in self.reviewers.items():
            count = sum(1 for fe in self.file_entries if username in fe.verified_by)
            self.reviewer_stats[username] = {
                "alias": info.get("alias", username[:2].upper()),
                "count": count,
            }

    def _build_ui(self):
        """Build the dialog layout."""
        # Scrollable canvas
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        self.content_frame = ttk.Frame(canvas)

        self.content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>") if e.widget is self else None)

        frame = self.content_frame

        # Section A — Overview stats
        ttk.Label(frame, text="Overview", font=FONT_TITLE).pack(anchor=tk.W, padx=PAD_LG, pady=(PAD_LG, PAD_MD))

        stats_frame = ttk.Frame(frame)
        stats_frame.pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)

        stat_items = [
            ("Total Files", str(self.total_files)),
            ("Files with Labels", str(self.files_with_labels)),
            ("Files Fully Verified", str(self.files_fully_verified)),
            ("Total Labels", str(self.total_labels)),
        ]
        for i, (header, value) in enumerate(stat_items):
            row, col = divmod(i, 2)
            cell = ttk.Frame(stats_frame)
            cell.grid(row=row, column=col, padx=PAD_LG, pady=PAD_MD, sticky=tk.W)
            ttk.Label(cell, text=header, font=FONT_BODY).pack(anchor=tk.W)
            ttk.Label(cell, text=value, font=FONT_HEADING).pack(anchor=tk.W)

        # Section B — Verification progress bar
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)

        pct = (self.files_fully_verified / self.total_files * 100) if self.total_files > 0 else 0
        ttk.Label(frame, text="Verification Progress", font=FONT_TITLE).pack(
            anchor=tk.W, padx=PAD_LG, pady=(PAD_MD, PAD_MD))

        progress_bar = ttk.Progressbar(frame, length=400, mode='determinate', maximum=100, value=pct)
        progress_bar.pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)

        ttk.Label(frame, text=f"{self.files_fully_verified} / {self.total_files} files verified ({pct:.0f}%)",
                  font=FONT_BODY).pack(anchor=tk.W, padx=PAD_LG)

        # Section C — Per-behavior breakdown
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)
        ttk.Label(frame, text="Behavior Breakdown", font=FONT_TITLE).pack(
            anchor=tk.W, padx=PAD_LG, pady=(PAD_MD, PAD_MD))

        columns = ("behavior", "color", "labels", "files", "duration")
        behavior_tree = ttk.Treeview(frame, columns=columns, show="headings",
                                     height=min(len(self.label_displays) + 1, 10))
        behavior_tree.heading("behavior", text="Behavior")
        behavior_tree.heading("color", text="Color")
        behavior_tree.heading("labels", text="Labels")
        behavior_tree.heading("files", text="Files")
        behavior_tree.heading("duration", text="Total Duration")

        behavior_tree.column("behavior", width=120)
        behavior_tree.column("color", width=60, anchor=tk.CENTER)
        behavior_tree.column("labels", width=60, anchor=tk.CENTER)
        behavior_tree.column("files", width=60, anchor=tk.CENTER)
        behavior_tree.column("duration", width=100, anchor=tk.E)

        for ld in self.label_displays:
            stats = self.behavior_stats.get(ld.display_name, {"labels": 0, "files": set(), "duration_sec": 0.0})
            tag_name = f"color_{ld.display_name}"
            behavior_tree.tag_configure(tag_name, foreground=ld.color)
            behavior_tree.insert("", tk.END, values=(
                ld.display_name,
                "\u2588",
                stats["labels"],
                len(stats["files"]),
                self._format_duration(stats["duration_sec"]),
            ), tags=(tag_name,))

        behavior_tree.pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)

        # Section D — Per-reviewer verification (only if reviewers configured)
        if self.reviewers:
            ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)
            ttk.Label(frame, text="Reviewer Verification", font=FONT_TITLE).pack(
                anchor=tk.W, padx=PAD_LG, pady=(PAD_MD, PAD_MD))

            rev_columns = ("reviewer", "alias", "files_verified", "pct")
            reviewer_tree = ttk.Treeview(frame, columns=rev_columns, show="headings",
                                         height=min(len(self.reviewers) + 1, 10))
            reviewer_tree.heading("reviewer", text="Reviewer")
            reviewer_tree.heading("alias", text="Alias")
            reviewer_tree.heading("files_verified", text="Files Verified")
            reviewer_tree.heading("pct", text="%")

            reviewer_tree.column("reviewer", width=120)
            reviewer_tree.column("alias", width=60, anchor=tk.CENTER)
            reviewer_tree.column("files_verified", width=100, anchor=tk.CENTER)
            reviewer_tree.column("pct", width=60, anchor=tk.E)

            for username, rev_stats in self.reviewer_stats.items():
                rev_pct = (rev_stats["count"] / self.total_files * 100) if self.total_files > 0 else 0
                reviewer_tree.insert("", tk.END, values=(
                    username,
                    rev_stats["alias"],
                    rev_stats["count"],
                    f"{rev_pct:.0f}%",
                ))

            reviewer_tree.pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)

        # Close button
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=PAD_LG, pady=PAD_MD)
        ttk.Button(frame, text="Close", command=self.destroy).pack(pady=PAD_LG)
