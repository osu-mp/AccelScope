"""
Generates the AccelScope User Guide PDF.
Run: python docs/generate_user_guide.py
Output: docs/AccelScope_User_Guide.pdf

Requires: fpdf2 (pip install fpdf2)
"""
import os
from fpdf import FPDF


class UserGuidePDF(FPDF):
    MARGIN = 15
    BLUE = (41, 98, 155)
    DARK = (33, 33, 33)
    GRAY = (100, 100, 100)
    LIGHT_BG = (245, 245, 245)

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(self.MARGIN, self.MARGIN, self.MARGIN)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*self.GRAY)
            self.cell(0, 8, "AccelScope User Guide", align="R")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self):
        self.add_page()
        self.ln(60)
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(*self.BLUE)
        self.cell(0, 15, "AccelScope", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*self.GRAY)
        self.cell(0, 10, "User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(20)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*self.DARK)
        self.cell(0, 8, "Accelerometer Data Visualization & Labeling Tool", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, "For Wildlife Movement Research", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(40)
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*self.GRAY)
        self.cell(0, 8, "Version 0.1", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_heading(self, text):
        self.ln(6)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*self.BLUE)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        # Underline
        self.set_draw_color(*self.BLUE)
        self.set_line_width(0.5)
        y = self.get_y()
        self.line(self.MARGIN, y, self.w - self.MARGIN, y)
        self.ln(4)

    def sub_heading(self, text):
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*self.DARK)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, bold_prefix=None):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.DARK)
        x = self.get_x()
        self.cell(8, 5.5, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 10)
            self.cell(self.get_string_width(bold_prefix) + 1, 5.5, bold_prefix)
            self.set_font("Helvetica", "", 10)
            self.multi_cell(0, 5.5, text)
        else:
            self.multi_cell(0, 5.5, text)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(*self.LIGHT_BG)
        self.set_text_color(*self.DARK)
        lines = text.strip().split("\n")
        for line in lines:
            self.cell(0, 5, "  " + line, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def note_box(self, text):
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80, 80, 80)
        self.set_fill_color(230, 240, 250)
        self.multi_cell(0, 5.5, "Note: " + text, fill=True)
        self.ln(3)


def build_guide():
    pdf = UserGuidePDF()
    pdf.alias_nb_pages()

    # ---- Title Page ----
    pdf.title_page()

    # ---- Table of Contents ----
    pdf.add_page()
    pdf.section_heading("Table of Contents")
    toc = [
        "1. Introduction",
        "2. Installation",
        "3. Getting Started",
        "4. Creating a Project",
        "5. Navigating the Interface",
        "6. Viewing & Labeling Data",
        "7. Keyboard Shortcuts",
        "8. Generating Output",
        "9. Output Format (BEBE)",
        "10. Project Configuration",
        "11. Multi-User Setup",
        "12. Troubleshooting",
    ]
    for item in toc:
        pdf.body_text(item)

    # ---- 1. Introduction ----
    pdf.add_page()
    pdf.section_heading("1. Introduction")
    pdf.body_text(
        "AccelScope is a desktop application for visualizing, annotating, and exporting "
        "accelerometer data. Originally designed for wildlife movement research (cougar and "
        "wolf tracking), it provides a general-purpose tool for exploring time-series "
        "accelerometer data and labeling behavioral events."
    )
    pdf.body_text("Key capabilities:")
    pdf.bullet("Visualize X, Y, and Z accelerometer axes over time")
    pdf.bullet("Annotate data with user-defined behavior labels (e.g., Stalk, Kill, Feed)")
    pdf.bullet("Zoom, pan, and navigate large datasets efficiently")
    pdf.bullet("Export labeled data to BEBE format for machine learning pipelines")
    pdf.bullet("Support multiple users working on the same project from different machines")

    # ---- 2. Installation ----
    pdf.section_heading("2. Installation")
    pdf.sub_heading("Prerequisites")
    pdf.bullet("Python 3.8 or later")
    pdf.bullet("Conda (recommended) or pip")

    pdf.sub_heading("Option 1: Using Conda (Recommended)")
    pdf.body_text("Clone the repository and create the environment:")
    pdf.code_block(
        "git clone https://github.com/osu-mp/AccelScope.git\n"
        "cd AccelScope\n"
        "conda env create -f environment.yml\n"
        "conda activate accel-scope"
    )

    pdf.sub_heading("Option 2: Using pip")
    pdf.code_block(
        "git clone https://github.com/osu-mp/AccelScope.git\n"
        "cd AccelScope\n"
        "pip install -e ."
    )

    pdf.sub_heading("Running AccelScope")
    pdf.code_block("python src/main.py")

    # ---- 3. Getting Started ----
    pdf.add_page()
    pdf.section_heading("3. Getting Started")
    pdf.body_text(
        "When you first launch AccelScope, you will see an empty workspace with three panes: "
        "the Project Browser (left), the Viewer (center), and the Info Pane (right). "
        "To begin working, you need to either create a new project or open an existing one."
    )
    pdf.body_text(
        "AccelScope organizes work into projects. Each project is a JSON configuration file "
        "that references your data files, stores your labels, and tracks output settings. "
        "Your actual CSV data files remain in their original location on disk."
    )

    # ---- 4. Creating a Project ----
    pdf.section_heading("4. Creating a Project")
    pdf.body_text("To create a new project:")
    pdf.bullet("Go to File > New Project")
    pdf.bullet("Enter a project name (e.g., 'YellowstoneCougars')")
    pdf.bullet("Choose a location to save the project JSON file")
    pdf.bullet("Select the root data directory containing your CSV files")
    pdf.ln(2)
    pdf.body_text(
        "After creating the project, use the Project Browser to organize your data. "
        "Right-click to add subdirectories (e.g., by animal ID) and add CSV files within them. "
        "Each file entry gets a unique ID, so you can reference the same CSV multiple times "
        "with different label sets."
    )
    pdf.note_box(
        "The project file stores relative paths to your CSVs. The data root directory "
        "maps these relative paths to absolute file locations. Different users can set "
        "different data root paths (see Multi-User Setup)."
    )

    # ---- 5. Navigating the Interface ----
    pdf.add_page()
    pdf.section_heading("5. Navigating the Interface")

    pdf.sub_heading("Project Browser (Left Pane)")
    pdf.body_text(
        "Displays your project's directory tree. Click on a CSV file to load it into the "
        "Viewer. Right-click for context menu options (add directory, add file, delete). "
        "Files with verified labels appear in a different color."
    )

    pdf.sub_heading("Viewer (Center Pane)")
    pdf.body_text(
        "The main data visualization area. Displays accelerometer data as a time-series "
        "plot with X (red), Y (black), and Z (blue) axes. Labeled regions appear as "
        "colored overlays on the plot. Use mouse scroll to zoom and drag to pan."
    )

    pdf.sub_heading("Info Pane (Right Pane)")
    pdf.body_text(
        "Shows metadata about the currently loaded file, including its labels, the label "
        "legend, and controls for adding/editing annotations. You can also add comments "
        "and mark files as verified."
    )

    pdf.sub_heading("Status Bar (Bottom)")
    pdf.body_text("Displays status messages about the current operation (file loading, etc.).")

    # ---- 6. Viewing & Labeling Data ----
    pdf.section_heading("6. Viewing & Labeling Data")
    pdf.body_text("After loading a CSV file in the Viewer:")
    pdf.bullet("Scroll the mouse wheel to zoom in/out on the time axis")
    pdf.bullet("Click and drag to pan through the data")
    pdf.bullet("Use the Info Pane to create labels by selecting a behavior and time range")
    pdf.bullet("Labels are saved automatically to the project JSON when modified")
    pdf.ln(2)
    pdf.body_text(
        "Each label has a start time, end time, and behavior type. The available behaviors "
        "are defined in the project's label_display configuration (e.g., Stalk, Kill Phase 1, "
        "Kill Phase 2, Feed, Walk). Each behavior has a display color and an output value "
        "that will be used when generating output files."
    )

    # ---- 7. Keyboard Shortcuts ----
    pdf.add_page()
    pdf.section_heading("7. Keyboard Shortcuts")
    shortcuts = [
        ("F", "Zoom to fit all labels in view"),
        ("A", "Zoom to show all data"),
        ("Left/Right Arrow", "Pan left/right through the data"),
        ("Up/Down Arrow", "Zoom in/out"),
        ("Delete", "Remove the selected label"),
    ]
    for key, desc in shortcuts:
        pdf.bullet(desc, bold_prefix=f"{key}: ")

    # ---- 8. Generating Output ----
    pdf.section_heading("8. Generating Output")
    pdf.body_text("To export your labeled data, go to Project > Generate Output. The dialog provides:")
    pdf.ln(1)
    pdf.bullet("The current input frequency (read-only, from project settings)", bold_prefix="Input Frequency: ")
    pdf.bullet(
        "Choose the target sampling rate. Data will be downsampled from the input frequency "
        "to this value (e.g., 16 Hz to 1 Hz).",
        bold_prefix="Output Frequency: "
    )
    pdf.bullet(
        "Select one or more methods. Each selected method produces a separate output subfolder. "
        "Average: mean of N samples. Nth Value: take every Nth sample. Min/Max: minimum or "
        "maximum of N samples.",
        bold_prefix="Downsampling Method: "
    )
    pdf.bullet(
        "Entire Input: export all data. Labeled with Buffer: export only the time ranges "
        "around labels, expanded by the buffer and rounded to the specified boundaries.",
        bold_prefix="Output Period: "
    )
    pdf.bullet(
        "Minutes of extra data to include before and after each labeled region "
        "(only active when Output Period is 'Labeled with Buffer').",
        bold_prefix="Buffer Minutes: "
    )
    pdf.bullet(
        "Round the start/end of buffered regions to the nearest N-minute boundary "
        "(only active when Output Period is 'Labeled with Buffer').",
        bold_prefix="Round to Minutes: "
    )
    pdf.bullet("Where to save the generated files.", bold_prefix="Output Directory: ")
    pdf.ln(2)
    pdf.body_text(
        "Click Generate Output to start. A progress dialog will appear while files are "
        "being processed. The operation runs in the background so the GUI remains responsive."
    )

    # ---- 9. Output Format (BEBE) ----
    pdf.add_page()
    pdf.section_heading("9. Output Format (BEBE)")
    pdf.body_text(
        "AccelScope generates output in the BEBE (Bio-logger Ethogram Benchmark) format, "
        "designed for training and evaluating behavior classification models."
    )

    pdf.sub_heading("Directory Structure")
    pdf.code_block(
        "output_dir/\n"
        "  average/\n"
        "    dataset_metadata.yaml\n"
        "    clip_data/\n"
        "      F202_27905_010518_072219_abc12345.csv\n"
        "      M201_88888_020319_091500_def67890.csv\n"
        "  nth_value/\n"
        "    dataset_metadata.yaml\n"
        "    clip_data/\n"
        "      ..."
    )

    pdf.sub_heading("Clip CSV Format")
    pdf.body_text(
        "Each clip CSV is headerless with 5 columns:"
    )
    pdf.bullet("AccX, AccY, AccZ: accelerometer values (float)")
    pdf.bullet("individual_id: integer identifier for the animal (mapped from the folder name)")
    pdf.bullet(
        "label: integer behavior label. 0 = unknown/unlabeled. "
        "1+ = behaviors in the order they appear in your project's label_display setting"
    )
    pdf.body_text("Example label mapping for the Yellowstone Cougars project:")
    pdf.code_block(
        "0 = unknown (unlabeled data)\n"
        "1 = STALK\n"
        "2 = KILL\n"
        "3 = KILL_PHASE_2\n"
        "4 = FEED\n"
        "5 = WALK"
    )

    pdf.sub_heading("Metadata YAML")
    pdf.body_text("Each method subfolder includes a dataset_metadata.yaml containing:")
    pdf.bullet("sr: output sampling rate in Hz")
    pdf.bullet("dataset_name: project name")
    pdf.bullet("clip_ids: list of all clip identifiers")
    pdf.bullet("individual_ids: list of unique animal integer IDs")
    pdf.bullet("clip_id_to_individual_id: mapping from clip to animal")
    pdf.bullet("label_names: ordered list of label names (index 0 = unknown)")
    pdf.bullet("clip_column_names: column names for the CSV data")
    pdf.bullet("n_folds: number of cross-validation folds (capped at 5)")
    pdf.bullet("individuals_per_fold: round-robin assignment of animals to folds")
    pdf.bullet("clip_ids_per_fold: which clips belong to each fold")

    # ---- 10. Project Configuration ----
    pdf.add_page()
    pdf.section_heading("10. Project Configuration")
    pdf.body_text(
        "Projects are stored as JSON files. The main sections are:"
    )
    pdf.bullet("proj_name: the project name", bold_prefix="")
    pdf.bullet(
        "data_root_directory: maps usernames to filesystem paths where CSV data is stored",
        bold_prefix=""
    )
    pdf.bullet("entries: the directory/file tree with labels", bold_prefix="")
    pdf.bullet(
        "label_display: defines available behaviors, their colors, and output values",
        bold_prefix=""
    )
    pdf.bullet("input_settings: input type and frequency (e.g., VectronicMotion at 16 Hz)", bold_prefix="")
    pdf.bullet("output_settings: default output generation settings", bold_prefix="")

    pdf.ln(2)
    pdf.body_text(
        "You can edit the project JSON directly in a text editor for bulk changes "
        "(e.g., adding many files at once or adjusting label_display colors). "
        "Be careful to maintain valid JSON syntax."
    )

    # ---- 11. Multi-User Setup ----
    pdf.section_heading("11. Multi-User Setup")
    pdf.body_text(
        "AccelScope supports multiple users working on the same project from different "
        "machines. The project JSON stores a data_root_directory mapping that associates "
        "OS usernames with filesystem paths."
    )
    pdf.body_text("Example configuration:")
    pdf.code_block(
        '"data_root_directory": {\n'
        '    "default": ".",\n'
        '    "alice": "D:/research/cougar_data",\n'
        '    "bob": "/home/bob/cougar_data"\n'
        '}'
    )
    pdf.body_text(
        "When AccelScope opens a project, it detects the current OS username and uses the "
        "matching path. If no match is found, it falls back to the 'default' path. "
        "If the resolved path doesn't exist, you'll be prompted to select a valid directory."
    )
    pdf.body_text(
        "You can also change the data root at any time via Project > Change Data Root."
    )

    # ---- 12. Troubleshooting ----
    pdf.add_page()
    pdf.section_heading("12. Troubleshooting")

    pdf.sub_heading("'Data root not set' warning")
    pdf.body_text(
        "This means AccelScope couldn't find a valid data directory for your username. "
        "Use Project > Change Data Root to point to the folder containing your CSV data. "
        "The path will be saved in the project JSON under your OS username."
    )

    pdf.sub_heading("CSV files not loading")
    pdf.body_text(
        "AccelScope currently expects Vectronic Motion CSV format: a header line followed by "
        "columns 'UTC DateTime', 'Milliseconds', 'Acc X [g]', 'Acc Y [g]', 'Acc Z [g]'. "
        "If your data uses a different format, verify the input_type in your project config. "
        "Use Project > Validate Project Config to check all file paths and labels."
    )

    pdf.sub_heading("Output generation is slow")
    pdf.body_text(
        "Large CSV files (millions of rows) take time to process. Output generation runs "
        "in a background thread so the GUI stays responsive. For faster iteration, consider "
        "using 'Labeled with Buffer' output period to process only the relevant portions, "
        "or use a higher output frequency to reduce downsampling computation."
    )

    pdf.sub_heading("Labels not appearing correctly")
    pdf.body_text(
        "Labels use time-of-day values (HH:MM:SS). They do not currently support multi-day "
        "spans. If a label's start time equals or exceeds its end time, it will be rejected. "
        "Ensure your label times fall within the data's time range."
    )

    return pdf


if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "AccelScope_User_Guide.pdf")
    pdf = build_guide()
    pdf.output(output_path)
    print(f"User guide generated: {output_path}")
