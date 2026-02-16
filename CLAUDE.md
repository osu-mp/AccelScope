# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AccelScope is a Tkinter-based accelerometer data visualization and labeling tool for wildlife movement research. Users annotate time-series CSV data with behavior labels and export to formats like BEBE (Bio-logger Ethogram Benchmark).

## Environment & Running

```bash
# The project uses a local conda env at .conda/
c:/repos/AccelScope/.conda/python.exe src/main.py

# Or with conda activated:
conda activate accel-scope
python src/main.py
```

The environment.yml is UTF-16-LE encoded — use Python's `encoding='utf-16-le'` when modifying it programmatically.

## Testing

```bash
# Run all tests (quiet summary view)
c:/repos/AccelScope/.conda/python.exe test/run_all_tests.py

# Run a single test file (verbose)
c:/repos/AccelScope/.conda/python.exe -m pytest test/test_output_settings.py

# Or with unittest directly
c:/repos/AccelScope/.conda/python.exe -m unittest test.test_output_settings
```

Tests use `unittest`. Test data lives in `test/configs/` and `test/data/`.

## Architecture

### Layered Structure (`src/`)

- **`main.py`** — Entry point. `MainApplication(tk.Tk)` coordinates all GUI components, project loading, and output generation.
- **`models/`** — Data classes with `to_dict()`/`from_dict()` serialization. Key models: `ProjectConfig`, `FileEntry`, `Label`, `OutputSettings`, `LabelDisplay`.
- **`services/`** — Business logic. `ProjectService` manages project lifecycle, multi-user data root resolution, and file path mapping. `UserAppConfigService` persists UI state.
- **`gui_components/`** — Tkinter dialogs and panes: `Viewer` (matplotlib plots), `ProjectBrowser` (file tree), `InfoPane` (labels/metadata), various dialogs.
- **`input_types/`** — Interface-based input loading. `VectronicMotionInput` reads Vectronic Motion CSVs (combines UTC DateTime + Milliseconds into Timestamp column, skiprows=1).
- **`output_types/`** — Interface-based output generation. `BEBEOutput` produces per-clip headerless CSVs + `dataset_metadata.yaml`.
- **`data_processing/`** — Analysis utilities (`AccelDataProcessor`, `BacktrackAnalysis`).

### Key Patterns

- **Multi-user data roots**: `ProjectConfig.data_root_directory` maps OS usernames to paths. `ProjectService` resolves the current user's path at load time, stores it under the `"active"` key.
- **Plugin interfaces**: `InputInterface` and `OutputGeneratorInterface` are abstract bases. New formats extend these.
- **File identity**: `FileEntry` has a UUID-based `id`, allowing the same CSV to appear multiple times with different labels.
- **Labels use `datetime.time`** (not full datetime) — stored as `HH:MM:SS.ffffff` strings. This means multi-day spans are not yet supported.
- **Downsampling**: `OutputSettings.downsample_methods` is a list — multiple methods can be selected, each producing a separate output subfolder.

### Data Flow: Output Generation

1. `GenerateOutputDialog` collects settings, sets `result_ready = True` on confirm
2. `MainApplication.start_output_generation()` launches `BEBEOutput.generate_output()` in a background thread
3. BEBEOutput: collects all `FileEntry` objects → loads each CSV → filters by output period → assigns integer labels (0=unknown, 1+=label_display order) → downsamples → writes headerless CSVs to `{method}/clip_data/{clip_id}.csv` → writes `dataset_metadata.yaml`

### Project Config (JSON)

Project configs store everything: directory tree of `DirectoryEntry`/`FileEntry`, `label_display` (behavior→color→output_value mappings), `input_settings`, `output_settings`. See `test/configs/yellowstone_cougars.json` for a real example.
