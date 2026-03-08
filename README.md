# AccelScope

A Tkinter-based tool for visualizing, annotating, and exporting accelerometer time-series data. Designed for wildlife movement research (cougars, wolves, etc.) but generic enough for any accelerometer dataset. Produces output in BEBE (Bio-logger Ethogram Benchmark) format.

## Features

### Viewer
- Matplotlib-based interactive plot with X/Y/Z acceleration axes
- Multi-tab interface — open several CSV files simultaneously
- Pan and zoom with mouse, scroll wheel, or keyboard
- Real-time cursor report (timestamp + X/Y/Z values) in the info pane
- Toggle individual axes on/off; configurable colors and opacity
- Async CSV loading with status bar progress indicator

### Labeling
- Click-drag on the plot to draw behavior labels
- Drag label edges to resize, drag body to move (with boundary clamping)
- Undo/redo (Ctrl+Z / Ctrl+Y)
- Delete selected label with Delete key
- Per-project behavior types with custom name, color, opacity, and output integer

### Project Management
- **New Project** (Ctrl+N): wizard scans a data root directory, auto-discovers CSVs, lets you flatten by individual ID, select files, and set project options
- **Open Project** (Ctrl+O): load any `.json` project file
- Hierarchical project browser with text and status filters
- Drag-and-drop reordering in the browser
- Color-coded verification status in browser tree (green / yellow / unverified)
- Project JSON auto-saved on every change; restores last-opened project and file on startup

### Multi-User Collaboration
- Each project stores a `users` list mapping OS usernames to data root paths and display aliases
- **My Profile**: set your display name and alias
- **Add Reviewer**: invite collaborators; each reviewer verifies files independently
- **Verification threshold**: configurable percentage of reviewers required for a file to show as fully verified (green)
- Per-file, per-user comments with auto-save

### Import / Export
- Export all labels to CSV (`file_id`, `file_path`, `behavior`, `start_time`, `end_time`)
- Import labels from CSV with conflict resolution (replace / skip / cancel)
- **Generate Output**: produces BEBE-format output with per-method subfolders (`average`, `nth_value`, `min`, `max`), headerless clip CSVs, and `dataset_metadata.yaml`
  - Configurable output frequency (1–16 Hz downsampling)
  - Output period: full file, labeled regions only, or labeled with configurable buffer
  - Label rounding to nearest N minutes

### Labeling Dashboard
- Overview: total files, files with labels, files fully verified
- Per-behavior table: label count, files involved, total duration
- Per-reviewer table: verified file counts

### Configuration
- **Edit Input Settings**: input type, frequency (Hz), Y-axis range, individual ID regex, plot title format
- **Edit Behavior Labels**: add/remove behaviors, set color/opacity/output value
- **Verification Threshold**: set required reviewer percentage
- **Preferences**: comment auto-save delay, info pane width
- **Validate Project Config**: checks all file paths and label integrity

## Hotkeys

| Key | Action |
|-----|--------|
| `A` | Zoom to show all data |
| `F` | Zoom to fit all labels |
| `↑` / `Ctrl+Scroll ↑` | Zoom in |
| `↓` / `Ctrl+Scroll ↓` | Zoom out |
| `←` / `Scroll ↓` | Pan left |
| `→` / `Scroll ↑` | Pan right |
| `Delete` | Delete selected label |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+N` | New Project |
| `Ctrl+O` | Open Project |
| `Ctrl+W` | Close active tab |

## Getting Started

### Prerequisites
- Python 3.8+
- conda (recommended)

### Setup

```bash
git clone https://github.com/osu-mp/AccelScope.git
cd AccelScope
conda env create -f environment.yml
conda activate accel-scope
```

### Run

```bash
python src/main.py
```

Or with the local conda env directly:

```bash
.conda/python.exe src/main.py
```

## Input Format

Currently supports **Vectronic Motion** CSVs:
- Combines `UTC DateTime` + `Milliseconds` columns into a unified `Timestamp`
- Acceleration columns: `Acc X [g]`, `Acc Y [g]`, `Acc Z [g]`
- Skips the first row; filename encodes the date (`YYYY-MM-DD.csv`)

Additional input types can be added by implementing the `InputInterface` base class in `src/input_types/`.

## Project Structure

```
src/
  main.py              # Entry point; MainApplication coordinates all components
  models/              # Data classes with to_dict/from_dict serialization
  services/            # Business logic (ProjectService, UserAppConfigService)
  gui_components/      # Tkinter dialogs and panes
  input_types/         # CSV input format implementations
  output_types/        # Output format implementations (BEBE)
  data_processing/     # Downsampling and analysis utilities
test/
  configs/             # Example project JSON files
  data/                # Test CSV data
```

## Testing

```bash
# Run all tests
python test/run_all_tests.py

# Run a single test file
python -m pytest test/test_output_settings.py
```
