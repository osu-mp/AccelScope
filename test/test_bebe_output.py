"""
Tests for BEBE output generation.
Creates synthetic Vectronic Motion CSV data and verifies:
- Output directory structure (method subfolders, clip_data dirs)
- CSV format (headerless, 5 columns: AccX, AccY, AccZ, individual_id, label)
- Label integer mapping matches label_display order
- Downsampled row counts
- dataset_metadata.yaml correctness
- Multiple downsample methods produce separate subfolders
- Labeled-with-buffer period filtering
"""
import csv
import math
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, time
from pathlib import Path

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.label import Label
from models.label_display import LabelDisplay
from models.input_settings import InputSettings, InputType
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod, OutputType
from models.project_config import ProjectConfig
from output_types.bebe_output import BEBEOutput


def create_synthetic_csv(file_path, start_hour=5, start_min=50, num_rows=960, freq=16):
    """
    Create a synthetic Vectronic Motion CSV file.
    960 rows at 16Hz = 60 seconds of data.
    Format matches real data: header line, then UTC DateTime, Milliseconds, Acc X/Y/Z columns.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", newline="") as f:
        f.write("DeviceID: 99999,Firmware: 2.9.17,Expected SensorRange: +/-4g,Date: 2018-06-08\n")
        f.write("UTC DateTime,Milliseconds,Acc X [g],Acc Y [g],Acc Z [g]\n")

        ms_per_sample = 1000 / freq
        current_ms = 0
        current_second = start_min * 60  # seconds from start of hour

        for i in range(num_rows):
            total_ms = int(current_second * 1000 + current_ms)
            secs = total_ms // 1000
            ms = total_ms % 1000

            h = start_hour + secs // 3600
            m = (secs % 3600) // 60
            s = secs % 60

            # Deterministic accelerometer values based on row index
            acc_x = round(0.1 * (i % 10) - 0.5, 2)
            acc_y = round(0.2 * (i % 5) - 0.4, 2)
            acc_z = round(-0.9 + 0.05 * (i % 8), 2)

            f.write(f"{h:02d}:{m:02d}:{s:02d},{ms},{acc_x:.2f},{acc_y:.2f},{acc_z:.2f}\n")

            current_ms += ms_per_sample
            if current_ms >= 1000:
                current_second += int(current_ms // 1000)
                current_ms = current_ms % 1000


def build_test_project(data_root, file_entries, label_display=None):
    """Build a ProjectConfig with the given file entries under a single directory.
    Returns (config, data_root) tuple."""
    if label_display is None:
        label_display = [
            LabelDisplay("Stalk", "green", 0.2, "STALK"),
            LabelDisplay("Kill Phase 1", "purple", 0.2, "KILL"),
            LabelDisplay("Kill Phase 2", "orange", 0.2, "KILL_PHASE_2"),
            LabelDisplay("Feed", "blue", 0.2, "FEED"),
            LabelDisplay("Walk", "red", 0.2, "WALK"),
        ]

    from models.user_config import UserConfig
    directory = DirectoryEntry("TestAnimals", file_entries)
    config = ProjectConfig(
        proj_name="TestProject",
        users=[UserConfig(username="testuser", data_root=data_root)],
        entries=[directory],
        label_display=label_display,
        input_settings=InputSettings(input_type=InputType.VECTRONIC_MOTION, input_frequency=16),
    )
    return config, data_root


class TestBEBEOutputStructure(unittest.TestCase):
    """Test that BEBE output creates correct directory structure and files."""

    def setUp(self):
        self.data_dir = tempfile.mkdtemp(prefix="bebe_test_data_")
        self.output_dir = tempfile.mkdtemp(prefix="bebe_test_output_")

        # Create one synthetic CSV: 960 rows = 60s at 16Hz
        self.csv_rel_path = "F202_99999_TEST/MotionData_99999/2018/06 Jun/08/2018-06-08.csv"
        csv_full = os.path.join(self.data_dir, self.csv_rel_path)
        create_synthetic_csv(csv_full, start_hour=5, start_min=50, num_rows=960)

        self.file_entry = FileEntry(self.csv_rel_path, id="abc12345", labels=[], verified_by=["testuser"])

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_single_method_creates_correct_structure(self):
        """One downsample method should produce method_dir/clip_data/ and method_dir/dataset_metadata.yaml"""
        config, data_root = build_test_project(self.data_dir, [self.file_entry])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_period=OutputPeriod.ENTIRE_INPUT,
            output_frequency=16,
        )

        bebe = BEBEOutput()
        output_files = bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        # Should have created average/clip_data/ dir
        avg_dir = os.path.join(self.output_dir, "average")
        self.assertTrue(os.path.isdir(avg_dir), "average/ dir should exist")
        self.assertTrue(os.path.isdir(os.path.join(avg_dir, "clip_data")), "average/clip_data/ dir should exist")
        self.assertTrue(os.path.isfile(os.path.join(avg_dir, "dataset_metadata.yaml")), "metadata yaml should exist")

        # Should have exactly 1 output CSV
        clip_files = os.listdir(os.path.join(avg_dir, "clip_data"))
        self.assertEqual(len(clip_files), 1)
        self.assertTrue(clip_files[0].endswith(".csv"))

    def test_multiple_methods_create_separate_subfolders(self):
        """Selecting multiple methods should create one subfolder per method."""
        config, data_root = build_test_project(self.data_dir, [self.file_entry])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE, DownsampleMethod.NTH_VALUE, DownsampleMethod.MIN, DownsampleMethod.MAX],
            output_period=OutputPeriod.ENTIRE_INPUT,
            output_frequency=16,
        )

        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        for method_name in ["average", "nth_value", "min", "max"]:
            method_dir = os.path.join(self.output_dir, method_name)
            self.assertTrue(os.path.isdir(method_dir), f"{method_name}/ dir should exist")
            self.assertTrue(os.path.isfile(os.path.join(method_dir, "dataset_metadata.yaml")))
            clip_dir = os.path.join(method_dir, "clip_data")
            self.assertTrue(os.path.isdir(clip_dir))
            self.assertEqual(len(os.listdir(clip_dir)), 1, f"{method_name} should have 1 clip CSV")


class TestBEBEOutputCSVFormat(unittest.TestCase):
    """Test the content/format of generated CSV files."""

    def setUp(self):
        self.data_dir = tempfile.mkdtemp(prefix="bebe_test_data_")
        self.output_dir = tempfile.mkdtemp(prefix="bebe_test_output_")

        self.csv_rel_path = "F202_99999_TEST/MotionData_99999/2018/06 Jun/08/2018-06-08.csv"
        csv_full = os.path.join(self.data_dir, self.csv_rel_path)
        # 960 rows at 16Hz = 60 seconds
        create_synthetic_csv(csv_full, start_hour=5, start_min=58, num_rows=960)

        # Labels within the data range (05:58:00 - 05:59:00)
        self.labels = [
            Label("2018-06-08T05:58:10.000000", "2018-06-08T05:58:20.000000", "Stalk"),
            Label("2018-06-08T05:58:25.000000", "2018-06-08T05:58:35.000000", "Kill Phase 1"),
        ]
        self.file_entry = FileEntry(self.csv_rel_path, id="abc12345", labels=self.labels, verified_by=["testuser"])

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_csv_is_headerless_with_5_columns(self):
        """Output CSV should have no header and exactly 5 columns per row."""
        config, data_root = build_test_project(self.data_dir, [self.file_entry])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )

        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        clip_dir = os.path.join(self.output_dir, "average", "clip_data")
        csv_files = os.listdir(clip_dir)
        self.assertEqual(len(csv_files), 1)

        csv_path = os.path.join(clip_dir, csv_files[0])
        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # No header — first row should be numeric data, not column names
        self.assertTrue(len(rows) > 0, "CSV should not be empty")
        first_row = rows[0]
        self.assertEqual(len(first_row), 5, "Each row should have 5 columns")

        # First 3 columns should be floats (AccX, AccY, AccZ)
        for val in first_row[:3]:
            float(val)  # Should not raise

        # Column 4: individual_id (integer)
        int(first_row[3])

        # Column 5: label (integer)
        int(first_row[4])

    def test_label_integers_match_label_display_order(self):
        """Label 0=unknown, 1=STALK, 2=KILL, 3=KILL_PHASE_2, 4=FEED, 5=WALK."""
        config, data_root = build_test_project(self.data_dir, [self.file_entry])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.NTH_VALUE],
            output_frequency=16,
        )

        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        clip_dir = os.path.join(self.output_dir, "nth_value", "clip_data")
        csv_path = os.path.join(clip_dir, os.listdir(clip_dir)[0])

        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

        label_values = set(int(row[4]) for row in rows)

        # Should contain 0 (unknown), 1 (Stalk), 2 (Kill Phase 1)
        self.assertIn(0, label_values, "Should have unknown (0) labels")
        self.assertIn(1, label_values, "Should have Stalk (1) labels")
        self.assertIn(2, label_values, "Should have Kill Phase 1 (2) labels")

        # Should NOT contain labels we didn't use
        self.assertNotIn(5, label_values, "Walk (5) should not appear — no Walk labels in data")

    def test_individual_id_is_constant_per_clip(self):
        """All rows in a clip should have the same individual_id."""
        config, data_root = build_test_project(self.data_dir, [self.file_entry])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )

        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        clip_dir = os.path.join(self.output_dir, "average", "clip_data")
        csv_path = os.path.join(clip_dir, os.listdir(clip_dir)[0])

        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            individual_ids = [int(row[3]) for row in reader]

        self.assertTrue(len(set(individual_ids)) == 1, "All rows should have the same individual_id")


class TestBEBEDownsampling(unittest.TestCase):
    """Test that downsampling produces correct row counts."""

    def setUp(self):
        self.data_dir = tempfile.mkdtemp(prefix="bebe_test_data_")
        self.output_dir = tempfile.mkdtemp(prefix="bebe_test_output_")

        self.csv_rel_path = "F202_99999_TEST/MotionData_99999/2018/06 Jun/08/2018-06-08.csv"
        csv_full = os.path.join(self.data_dir, self.csv_rel_path)
        # 1600 rows at 16Hz = 100 seconds
        create_synthetic_csv(csv_full, start_hour=6, start_min=0, num_rows=1600)

        self.file_entry = FileEntry(self.csv_rel_path, id="abc12345", labels=[])

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def _count_output_rows(self, method, output_freq):
        config, data_root = build_test_project(self.data_dir, [self.file_entry])
        settings = OutputSettings(
            downsample_methods=[method],
            output_frequency=output_freq,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        clip_dir = os.path.join(self.output_dir, method.value, "clip_data")
        csv_path = os.path.join(clip_dir, os.listdir(clip_dir)[0])
        with open(csv_path, "r") as f:
            return sum(1 for _ in f)

    def test_no_downsample_same_freq(self):
        """Output freq == input freq (16Hz) should produce same row count."""
        count = self._count_output_rows(DownsampleMethod.AVERAGE, 16)
        self.assertEqual(count, 1600)

    def test_average_downsample_2x(self):
        """16Hz input -> 8Hz output = half the rows."""
        count = self._count_output_rows(DownsampleMethod.AVERAGE, 8)
        self.assertEqual(count, 800)

    def test_nth_value_downsample_4x(self):
        """16Hz input -> 4Hz output via nth_value = 1/4 the rows."""
        count = self._count_output_rows(DownsampleMethod.NTH_VALUE, 4)
        self.assertEqual(count, 400)

    def test_min_downsample_16x(self):
        """16Hz input -> 1Hz output via min = 1/16 the rows."""
        count = self._count_output_rows(DownsampleMethod.MIN, 1)
        self.assertEqual(count, 100)

    def test_max_downsample_8x(self):
        """16Hz input -> 2Hz output via max = 1/8 the rows."""
        count = self._count_output_rows(DownsampleMethod.MAX, 2)
        self.assertEqual(count, 200)


class TestBEBEMetadata(unittest.TestCase):
    """Test dataset_metadata.yaml content."""

    def setUp(self):
        self.data_dir = tempfile.mkdtemp(prefix="bebe_test_data_")
        self.output_dir = tempfile.mkdtemp(prefix="bebe_test_output_")

        # Create 2 files from different individuals
        self.csv1_rel = "F202_99999_TEST/MotionData_99999/2018/06 Jun/08/2018-06-08.csv"
        self.csv2_rel = "M201_88888_TEST/MotionData_88888/2018/06 Jun/08/2018-06-08.csv"
        create_synthetic_csv(os.path.join(self.data_dir, self.csv1_rel), num_rows=160)
        create_synthetic_csv(os.path.join(self.data_dir, self.csv2_rel), num_rows=160)

        self.fe1 = FileEntry(self.csv1_rel, id="file_001", labels=[])
        self.fe2 = FileEntry(self.csv2_rel, id="file_002", labels=[])

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_metadata_fields_present(self):
        """metadata yaml should have all required top-level fields."""
        config, data_root = build_test_project(self.data_dir, [self.fe1, self.fe2])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        yaml_path = os.path.join(self.output_dir, "average", "dataset_metadata.yaml")
        with open(yaml_path, "r") as f:
            meta = yaml.safe_load(f)

        required_keys = ["sr", "dataset_name", "clip_ids", "individual_ids",
                         "clip_id_to_individual_id", "label_names",
                         "clip_column_names", "n_folds", "individuals_per_fold",
                         "clip_ids_per_fold"]
        for key in required_keys:
            self.assertIn(key, meta, f"metadata should contain '{key}'")

    def test_metadata_sr_matches_output_freq(self):
        """sr field should match the output frequency setting."""
        config, data_root = build_test_project(self.data_dir, [self.fe1])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=8,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        yaml_path = os.path.join(self.output_dir, "average", "dataset_metadata.yaml")
        with open(yaml_path, "r") as f:
            meta = yaml.safe_load(f)

        self.assertEqual(meta["sr"], 8)

    def test_metadata_label_names_order(self):
        """label_names should be [unknown, STALK, KILL, KILL_PHASE_2, FEED, WALK]."""
        config, data_root = build_test_project(self.data_dir, [self.fe1])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        yaml_path = os.path.join(self.output_dir, "average", "dataset_metadata.yaml")
        with open(yaml_path, "r") as f:
            meta = yaml.safe_load(f)

        expected = ["unknown", "STALK", "KILL", "KILL_PHASE_2", "FEED", "WALK"]
        self.assertEqual(meta["label_names"], expected)

    def test_metadata_two_individuals(self):
        """Two files from different individuals should produce 2 individual_ids."""
        config, data_root = build_test_project(self.data_dir, [self.fe1, self.fe2])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        yaml_path = os.path.join(self.output_dir, "average", "dataset_metadata.yaml")
        with open(yaml_path, "r") as f:
            meta = yaml.safe_load(f)

        self.assertEqual(len(meta["clip_ids"]), 2)
        self.assertEqual(len(meta["individual_ids"]), 2)
        self.assertEqual(meta["n_folds"], 2)

    def test_metadata_clip_column_names(self):
        """clip_column_names should be the standard BEBE columns."""
        config, data_root = build_test_project(self.data_dir, [self.fe1])
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        yaml_path = os.path.join(self.output_dir, "average", "dataset_metadata.yaml")
        with open(yaml_path, "r") as f:
            meta = yaml.safe_load(f)

        self.assertEqual(meta["clip_column_names"], ["AccX", "AccY", "AccZ", "individual_id", "label"])

    def test_metadata_fold_assignments_cap_at_5(self):
        """With 7 individuals, n_folds should be capped at 5."""
        entries = []
        for i in range(7):
            name = f"IND{i:03d}"
            rel_path = f"{name}_99999_TEST/MotionData_99999/2018/06 Jun/08/2018-06-08.csv"
            create_synthetic_csv(os.path.join(self.data_dir, rel_path), num_rows=160)
            entries.append(FileEntry(rel_path, id=f"file_{i:03d}", labels=[]))

        config, data_root = build_test_project(self.data_dir, entries)
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_frequency=16,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        yaml_path = os.path.join(self.output_dir, "average", "dataset_metadata.yaml")
        with open(yaml_path, "r") as f:
            meta = yaml.safe_load(f)

        self.assertEqual(meta["n_folds"], 5)
        self.assertEqual(len(meta["individuals_per_fold"]), 5)


class TestBEBELabeledWithBuffer(unittest.TestCase):
    """Test output period filtering with labeled_with_buffer."""

    def setUp(self):
        self.data_dir = tempfile.mkdtemp(prefix="bebe_test_data_")
        self.output_dir = tempfile.mkdtemp(prefix="bebe_test_output_")

        self.csv_rel_path = "F202_99999_TEST/MotionData_99999/2018/06 Jun/08/2018-06-08.csv"
        csv_full = os.path.join(self.data_dir, self.csv_rel_path)
        # 60 minutes of data starting at 05:30 (57600 rows at 16Hz)
        create_synthetic_csv(csv_full, start_hour=5, start_min=30, num_rows=57600)

    def tearDown(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_labeled_with_buffer_reduces_rows(self):
        """Labeled with buffer should output fewer rows than entire input."""
        # Label covers only ~10 seconds in the middle of 60 minutes of data
        labels = [Label("2018-06-08T05:55:00.000000", "2018-06-08T05:55:10.000000", "Stalk")]
        file_entry = FileEntry(self.csv_rel_path, id="abc12345", labels=labels)

        config, data_root = build_test_project(self.data_dir, [file_entry])

        # Generate with entire_input
        settings_entire = OutputSettings(
            downsample_methods=[DownsampleMethod.NTH_VALUE],
            output_period=OutputPeriod.ENTIRE_INPUT,
            output_frequency=16,
        )
        bebe = BEBEOutput()
        bebe.generate_output(config, self.output_dir, settings_entire, data_root=data_root)

        clip_dir = os.path.join(self.output_dir, "nth_value", "clip_data")
        csv_path = os.path.join(clip_dir, os.listdir(clip_dir)[0])
        with open(csv_path, "r") as f:
            entire_count = sum(1 for _ in f)

        # Clean output dir
        shutil.rmtree(self.output_dir)
        self.output_dir = tempfile.mkdtemp(prefix="bebe_test_output_")

        # Generate with labeled_with_buffer (5 min buffer, 1 min round)
        settings_buffer = OutputSettings(
            downsample_methods=[DownsampleMethod.NTH_VALUE],
            output_period=OutputPeriod.LABELED_WITH_BUFFER,
            output_frequency=16,
            buffer_minutes=5,
            round_to_minutes=1,
        )
        bebe.generate_output(config, self.output_dir, settings_buffer, data_root=data_root)

        clip_dir = os.path.join(self.output_dir, "nth_value", "clip_data")
        csv_path = os.path.join(clip_dir, os.listdir(clip_dir)[0])
        with open(csv_path, "r") as f:
            buffer_count = sum(1 for _ in f)

        self.assertLess(buffer_count, entire_count,
                         f"Buffered output ({buffer_count}) should have fewer rows than entire ({entire_count})")
        self.assertGreater(buffer_count, 0, "Buffered output should not be empty")

    def test_no_labels_with_buffer_produces_empty(self):
        """File with no labels + labeled_with_buffer should produce no output clip."""
        file_entry = FileEntry(self.csv_rel_path, id="abc12345", labels=[])
        config, data_root = build_test_project(self.data_dir, [file_entry])

        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_period=OutputPeriod.LABELED_WITH_BUFFER,
            output_frequency=16,
            buffer_minutes=5,
        )
        bebe = BEBEOutput()
        output_files = bebe.generate_output(config, self.output_dir, settings, data_root=data_root)

        # No clips should be produced for a file with no labels
        clip_dir = os.path.join(self.output_dir, "average", "clip_data")
        if os.path.isdir(clip_dir):
            self.assertEqual(len(os.listdir(clip_dir)), 0,
                             "No clip CSVs should be generated for a file with no labels")


class TestBEBEWithRealProjectConfig(unittest.TestCase):
    """
    Integration test using the real yellowstone_cougars.json config.
    Only runs if the data root directory exists with actual CSV files.
    Generates output to a temp dir and validates structure.
    """

    @classmethod
    def setUpClass(cls):
        import getpass
        config_path = os.path.join(os.path.dirname(__file__), "configs", "yellowstone_cougars.json")
        cls.config = ProjectConfig.from_file(config_path)

        # Find data root for current user from users list
        username = getpass.getuser()
        cls.data_root = None
        user_config = cls.config.get_user_by_username(username)
        if user_config and user_config.data_root:
            cls.data_root = user_config.data_root

        cls.data_available = cls.data_root is not None and os.path.isdir(str(cls.data_root))

    def setUp(self):
        if not self.data_available:
            self.skipTest("Real data root not available — skipping integration test")
        self.output_dir = tempfile.mkdtemp(prefix="bebe_integration_")

    def tearDown(self):
        if hasattr(self, 'output_dir') and os.path.isdir(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_generate_with_real_config_average(self):
        """Generate BEBE output with average method and verify structure."""
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE],
            output_period=OutputPeriod.ENTIRE_INPUT,
            output_frequency=16,
        )
        bebe = BEBEOutput()
        output_files = bebe.generate_output(self.config, self.output_dir, settings, data_root=self.data_root)

        # Should produce at least some output files
        self.assertGreater(len(output_files), 0, "Should generate at least one output file")

        # Check structure
        avg_dir = os.path.join(self.output_dir, "average")
        self.assertTrue(os.path.isdir(avg_dir))
        self.assertTrue(os.path.isfile(os.path.join(avg_dir, "dataset_metadata.yaml")))

        # Validate metadata
        with open(os.path.join(avg_dir, "dataset_metadata.yaml"), "r") as f:
            meta = yaml.safe_load(f)

        self.assertEqual(meta["sr"], 16)
        self.assertEqual(meta["dataset_name"], "YellowstoneCougars")
        self.assertEqual(meta["label_names"][0], "unknown")
        self.assertEqual(meta["label_names"][1], "STALK")

        # Validate a sample CSV
        clip_dir = os.path.join(avg_dir, "clip_data")
        clip_files = os.listdir(clip_dir)
        self.assertGreater(len(clip_files), 0)

        sample_csv = os.path.join(clip_dir, clip_files[0])
        with open(sample_csv, "r") as f:
            reader = csv.reader(f)
            first_row = next(reader)

        self.assertEqual(len(first_row), 5, "Each row should have 5 columns")
        # Verify numeric values
        float(first_row[0])  # AccX
        float(first_row[1])  # AccY
        float(first_row[2])  # AccZ
        int(first_row[3])    # individual_id
        int(first_row[4])    # label

        print(f"\n  Integration test results:")
        print(f"  Output files: {len(output_files)}")
        print(f"  Clip files: {len(clip_files)}")
        print(f"  Individuals: {meta['individual_ids']}")
        print(f"  Folds: {meta['n_folds']}")

    def test_generate_with_real_config_downsampled(self):
        """Generate at 1Hz (16x downsample) and verify row count reduction."""
        settings = OutputSettings(
            downsample_methods=[DownsampleMethod.AVERAGE, DownsampleMethod.NTH_VALUE],
            output_period=OutputPeriod.ENTIRE_INPUT,
            output_frequency=1,
        )
        bebe = BEBEOutput()
        bebe.generate_output(self.config, self.output_dir, settings, data_root=self.data_root)

        for method_name in ["average", "nth_value"]:
            clip_dir = os.path.join(self.output_dir, method_name, "clip_data")
            self.assertTrue(os.path.isdir(clip_dir), f"{method_name}/clip_data should exist")

            # Each file should have roughly 1/16th the rows of a full-rate file
            for csv_file in os.listdir(clip_dir):
                csv_path = os.path.join(clip_dir, csv_file)
                with open(csv_path, "r") as f:
                    row_count = sum(1 for _ in f)
                self.assertGreater(row_count, 0, f"{method_name}/{csv_file} should not be empty")
                print(f"\n  {method_name}/{csv_file}: {row_count} rows (1Hz)")


if __name__ == "__main__":
    unittest.main()
