# AccelScope Developer Guide

## Environment Setup

### Prerequisites
- Python 3.8+ (tested with 3.12)
- Conda (recommended) or pip

### Setting Up

**Option 1: Conda (recommended)**
```bash
conda env create -f environment.yml
conda activate accel-scope
```

**Option 2: Local conda env (already in repo)**
```bash
# The repo includes a .conda/ environment
c:/repos/AccelScope/.conda/python.exe src/main.py
```

**Option 3: pip**
```bash
pip install -e .
python src/main.py
```

### Dependencies
Core: `pandas`, `numpy`, `matplotlib`, `pyyaml`, `tkinter` (built-in)

Note: `environment.yml` is UTF-16-LE encoded. When editing programmatically, use `encoding='utf-16-le'`.

## Running the Application

```bash
python src/main.py
```

## Running Tests

```bash
# All tests (quiet summary)
python test/run_all_tests.py

# Single test file (verbose)
python -m unittest test.test_bebe_output -v

# Single test method
python -m unittest test.test_bebe_output.TestBEBEDownsampling.test_average_downsample_2x
```

## Architecture

### Directory Structure

```
src/
  main.py                    # Entry point, MainApplication(tk.Tk)
  models/                    # Data classes with to_dict()/from_dict()
  services/                  # Business logic (ProjectService, UserAppConfigService)
  gui_components/            # Tkinter UI (Viewer, ProjectBrowser, dialogs)
  input_types/               # Input format plugins (VectronicMotionInput)
  output_types/              # Output format plugins (BEBEOutput)
  data_processing/           # Analysis utilities
test/
  test_*.py                  # unittest test files
  configs/                   # Sample project configs for testing
  data/                      # Test data files
```

### Key Design Patterns

**Plugin Interfaces**: `InputInterface` and `OutputGeneratorInterface` are abstract bases. To add a new input/output format, create a new class implementing the interface.

**Multi-user data roots**: `ProjectConfig.data_root_directory` is a dict mapping OS usernames to filesystem paths. `ProjectService` resolves the current user at load time and stores it under the `"active"` key. This allows the same project JSON to work on different machines without editing paths.

**Serialization**: All models use `to_dict()`/`from_dict()` for JSON persistence. Project configs are stored as `.json` files.

**File identity**: Each `FileEntry` gets a UUID-based `id`, allowing the same CSV path to appear multiple times with different label sets.

### Data Flow

1. User opens project JSON via `ProjectService.load_project()`
2. `ProjectService` resolves user-specific data root path
3. `Viewer` loads CSV data via `VectronicMotionInput.load_data()`
4. User annotates data with labels (stored as `Label` objects with `datetime.time` boundaries)
5. Output generation: `BEBEOutput.generate_output()` processes all files, applying period filtering, label assignment, and downsampling

### Label System

Labels use `datetime.time` (not full datetime). Each `LabelDisplay` maps a `display_name` (shown in GUI) to an `output_value` (written to output files). The integer mapping for BEBE output is: 0 = unknown, then 1-N following `label_display` order in the project config.

### Output Generation (BEBE)

For each selected downsample method, creates:
```
output_dir/{method}/
  dataset_metadata.yaml
  clip_data/
    {clip_id}.csv          # headerless: AccX, AccY, AccZ, individual_id, label
```

Individual IDs are extracted from the first path component (text before first underscore). Clip IDs combine the path root with the file entry's unique ID.

## Adding a New Output Format

1. Create `src/output_types/my_output.py` implementing `OutputGeneratorInterface`
2. Implement `generate_output(project_config, output_dir, settings)` and `validate_settings(settings)`
3. Wire it into `main.py` (currently only BEBE is supported)

## Known Issues

- `test_accel_data_parser.py` and `test_accel_data_processor.py` have import path issues (pre-existing)
- Labels don't support multi-day time spans (they use `datetime.time`, not `datetime.datetime`)
- The `environment.yml` uses UTF-16-LE encoding which can cause issues with some tools
