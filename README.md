# AccelScope - Accelerometer Data Visualization Tool

AccelScope is a powerful tool designed to visualize and label accelerometer data. It supports viewing large datasets, annotating behaviors, and exporting the data for further analysis. Initially focused on wildlife movement data (e.g., cougars and wolves), AccelScope offers a generic solution for exploring and annotating time series data from accelerometers.

## Features
- Visualize X, Y, and Z axis data over time
- Label data with user-defined behaviors
- Zoom in/out with intuitive mouse and keyboard controls
- Pan through the data efficiently
- Hotkey to zoom all labels into view (F), and show all data (A)
- Customizable graph opacity, axis controls, and user comments per CSV

## Getting Started

### Prerequisites
Make sure you have the following installed:
- Python 3.8 or later
- conda (if using the provided `environment.yml`)

### Setting Up the Environment

#### Option 1: Using Conda
1. Clone the repository:
   ```bash
   git clone https://github.com/osu-mp/accelscope.git
   cd accelscope
   ```

2. Create the environment using `environment.yml`:
   ```bash
   conda env create -f environment.yml
   ```

3. Activate the environment:
   ```bash
   conda activate accel-scope
   ```

#### Option 2: Using setup.py
Alternatively, you can use `setup.py` to install the necessary dependencies:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/accelscope.git
   cd accelscope
   ```

2. Install the required packages:
   ```bash
   python setup.py install
   ```

## Running the Tool

After setting up the environment, you can run the tool:

```bash
python src/main.py
```

## Creating a Project

1. Launch the app and go to `File -> New Project`.
2. Enter the project details including the project name, location, and root data directory.
3. After creating the project, use the Project Browser to add subdirectories and CSV files.
4. Select a CSV file to visualize the data in the main window.

## Hotkeys

- `F`: Zoom to fit all labels.
- `A`: Zoom to show all data.
- `Arrow keys`: Pan left/right and zoom in/out.
- `Delete`: Remove a selected label.

## Customization

- **Comments**: Add comments to each CSV file for better context and analysis.
- **User Verified Checkbox**: Verify CSV data and adjust its color in the Project Browser.
- **Axis Controls**: Show/hide specific axes from the data display (X, Y, Z).
