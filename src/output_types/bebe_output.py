import os
import re
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yaml

from input_types.vectronic_motion import VectronicMotionInput
from models.directory_entry import DirectoryEntry
from models.file_entry import FileEntry
from models.output_settings import OutputSettings, DownsampleMethod, OutputPeriod
from output_types.output_interface import OutputGeneratorInterface
from models.project_config import ProjectConfig


class BEBEOutput(OutputGeneratorInterface):
	"""
	Output targeting the BEBE (Bio-logger Ethogram Benchmark) tool.
	Converts each input CSV into a separate output CSV per downsample method,
	with a dataset_metadata.yaml per method subfolder.
	"""

	def __init__(self):
		pass

	def generate_output(self, project_config: ProjectConfig, output_dir: str, settings: OutputSettings, progress_callback=None):
		"""
		Generate BEBE output files for all file entries in the project.

		:param project_config: The project configuration.
		:param output_dir: Root output directory.
		:param settings: OutputSettings with selected downsample methods, period, etc.
		:return: List of generated file paths.
		"""
		label_display = project_config.label_display
		# Build label name list: index 0 = "unknown", then each label_display output_value
		label_names = ["unknown"] + [ld.output_value for ld in label_display]
		# Map behavior display_name -> integer label index
		behavior_to_label_idx = {}
		for ld in label_display:
			behavior_to_label_idx[ld.display_name] = label_names.index(ld.output_value)

		input_frequency = project_config.input_settings.input_frequency
		output_frequency = settings.output_frequency
		downsample_ratio = input_frequency // output_frequency if output_frequency > 0 else 1

		# Get the active data root
		data_root = project_config.data_root_directory.get("active")
		if not data_root:
			raise ValueError("No active data root directory set.")

		# Get individual ID regex from config
		individual_id_regex = project_config.individual_id_regex

		# Collect all file entries
		file_entries = []
		self._collect_file_entries(project_config.entries, file_entries)

		if not file_entries:
			logging.warning("No file entries found in project config.")
			return []

		# Create input loader
		loader = VectronicMotionInput(frequency=input_frequency)

		# Track per-method metadata
		# {method_value: {clip_ids: [], individual_ids: set(), clip_to_individual: {}, clip_to_individual_int: {}}}
		method_metadata = {}
		for method in settings.downsample_methods:
			method_metadata[method.value] = {
				"clip_ids": [],
				"individual_ids_set": set(),
				"clip_id_to_individual_id": {},
			}

		# Map individual string IDs to integer IDs
		individual_str_to_int = {}
		next_individual_int = 0

		output_files = []
		total = len(file_entries)

		for i, file_entry in enumerate(file_entries):
			if progress_callback:
				progress_callback(i, total, file_entry.path)
			try:
				result = self._process_file(
					file_entry, data_root, loader, settings, downsample_ratio,
					behavior_to_label_idx, individual_str_to_int, next_individual_int,
					output_dir, method_metadata, individual_id_regex
				)
				if result is not None:
					next_individual_int = result["next_individual_int"]
					individual_str_to_int = result["individual_str_to_int"]
					output_files.extend(result["files"])
			except Exception as e:
				logging.error(f"Error processing {file_entry.path}: {e}")

		if progress_callback:
			progress_callback(total, total, "")

		# Write dataset_metadata.yaml for each method subfolder
		for method in settings.downsample_methods:
			meta = method_metadata[method.value]
			self._write_metadata(
				output_dir, method.value, meta, label_names,
				output_frequency, project_config.proj_name,
				individual_str_to_int
			)

		return output_files

	def _collect_file_entries(self, entries, result):
		"""Recursively collect all FileEntry objects from the project tree."""
		for entry in entries:
			if isinstance(entry, FileEntry):
				result.append(entry)
			elif isinstance(entry, DirectoryEntry):
				self._collect_file_entries(entry.entries, result)

	@staticmethod
	def _extract_individual_id(file_path, regex_pattern):
		"""Extract individual ID from file path using regex with named group 'individual'."""
		normalized = file_path.replace("\\", "/")
		match = re.search(regex_pattern, normalized)
		if match:
			try:
				return match.group("individual")
			except IndexError:
				pass
		# Fallback: first path component
		parts = normalized.split("/")
		return parts[0] if parts else "unknown"

	def _process_file(self, file_entry, data_root, loader, settings, downsample_ratio,
	                   behavior_to_label_idx, individual_str_to_int, next_individual_int,
	                   output_dir, method_metadata, individual_id_regex):
		"""Process a single file entry and write output CSVs for each selected method."""
		file_path = os.path.join(data_root, file_entry.path)
		if not os.path.isfile(file_path):
			logging.warning(f"File not found, skipping: {file_path}")
			return None

		# Extract clip_id and individual_id from the path using config regex
		path_parts = file_entry.path.replace("\\", "/").split("/")
		clip_id = path_parts[0]
		individual_str = self._extract_individual_id(file_entry.path, individual_id_regex)

		# Assign integer individual ID
		if individual_str not in individual_str_to_int:
			individual_str_to_int[individual_str] = next_individual_int
			next_individual_int += 1
		individual_int = individual_str_to_int[individual_str]

		# Load the CSV
		df = loader.load_data(file_path)

		# Apply output period filtering
		if settings.output_period == OutputPeriod.LABELED_WITH_BUFFER:
			df = self._filter_labeled_with_buffer(df, file_entry.labels, settings.buffer_minutes, settings.round_to_minutes)
			if df.empty:
				logging.info(f"No data after period filtering for {file_entry.path}")
				return {"next_individual_int": next_individual_int, "individual_str_to_int": individual_str_to_int, "files": []}

		# Assign label column
		df["label"] = self._assign_labels(df, file_entry.labels, behavior_to_label_idx)
		df["individual_id"] = individual_int

		# Generate a unique clip_id per file entry (use file entry id to disambiguate)
		unique_clip_id = f"{clip_id}_{file_entry.id}"

		output_files = []
		for method in settings.downsample_methods:
			# Downsample
			downsampled = self._downsample(df, method, downsample_ratio)

			# Write the output CSV (headerless)
			method_dir = os.path.join(output_dir, method.value, "clip_data")
			os.makedirs(method_dir, exist_ok=True)

			out_path = os.path.join(method_dir, f"{unique_clip_id}.csv")
			# Columns: AccX, AccY, AccZ, individual_id, label
			out_df = downsampled[["Acc X [g]", "Acc Y [g]", "Acc Z [g]", "individual_id", "label"]]
			out_df.to_csv(out_path, header=False, index=False)
			output_files.append(out_path)

			# Update metadata tracking
			meta = method_metadata[method.value]
			meta["clip_ids"].append(unique_clip_id)
			meta["individual_ids_set"].add(individual_int)
			meta["clip_id_to_individual_id"][unique_clip_id] = individual_int

			logging.info(f"Wrote {method.value} output: {out_path}")

		return {
			"next_individual_int": next_individual_int,
			"individual_str_to_int": individual_str_to_int,
			"files": output_files
		}

	def _filter_labeled_with_buffer(self, df, labels, buffer_minutes, round_to_minutes):
		"""Filter DataFrame to only include rows within buffered/rounded label periods."""
		if "Timestamp" not in df.columns:
			return df
		if not labels:
			return df.iloc[0:0]  # Return empty DataFrame when no labels exist

		# Build datetime ranges from labels (labels are now datetime objects)
		ranges = []
		for label in labels:
			start_dt = label.start_time
			end_dt = label.end_time

			# Apply buffer
			start_dt -= timedelta(minutes=buffer_minutes)
			end_dt += timedelta(minutes=buffer_minutes)

			# Round start down and end up to round_to_minutes boundary
			if round_to_minutes > 0:
				round_delta = timedelta(minutes=round_to_minutes)
				round_seconds = round_delta.total_seconds()
				# Round start down
				start_epoch = start_dt.timestamp()
				start_dt = datetime.fromtimestamp(start_epoch - (start_epoch % round_seconds))
				# Round end up
				end_epoch = end_dt.timestamp()
				remainder = end_epoch % round_seconds
				if remainder > 0:
					end_dt = datetime.fromtimestamp(end_epoch + (round_seconds - remainder))

			ranges.append((start_dt, end_dt))

		# Merge overlapping ranges
		ranges = self._merge_datetime_ranges(ranges)

		# Filter rows whose Timestamp falls within any range
		mask = pd.Series(False, index=df.index)
		row_timestamps = df["Timestamp"]
		for start_dt, end_dt in ranges:
			start_ts = pd.Timestamp(start_dt)
			end_ts = pd.Timestamp(end_dt)
			mask |= (row_timestamps >= start_ts) & (row_timestamps <= end_ts)

		return df[mask].reset_index(drop=True)

	def _merge_datetime_ranges(self, ranges):
		"""Merge overlapping datetime ranges."""
		if not ranges:
			return ranges

		ranges_sorted = sorted(ranges, key=lambda x: x[0])

		merged = [ranges_sorted[0]]
		for start, end in ranges_sorted[1:]:
			if start <= merged[-1][1]:
				merged[-1] = (merged[-1][0], max(merged[-1][1], end))
			else:
				merged.append((start, end))

		return merged

	def _assign_labels(self, df, labels, behavior_to_label_idx):
		"""Assign integer label to each row based on whether its timestamp falls within a label range."""
		label_col = np.zeros(len(df), dtype=int)

		if not labels or "Timestamp" not in df.columns:
			return label_col

		row_timestamps = df["Timestamp"].values

		for label in labels:
			idx = behavior_to_label_idx.get(label.behavior, 0)
			if idx == 0:
				continue

			start_ts = np.datetime64(label.start_time)
			end_ts = np.datetime64(label.end_time)

			mask = (row_timestamps >= start_ts) & (row_timestamps <= end_ts)
			label_col[mask] = idx

		return label_col

	def _downsample(self, df, method, ratio):
		"""Downsample the DataFrame using the specified method and ratio."""
		if ratio <= 1:
			return df.copy()

		acc_cols = ["Acc X [g]", "Acc Y [g]", "Acc Z [g]"]

		if method == DownsampleMethod.NTH_VALUE:
			return df.iloc[::ratio].reset_index(drop=True)

		# For AVERAGE, MIN, MAX: group every `ratio` rows
		n_groups = len(df) // ratio
		if n_groups == 0:
			return df.copy()

		# Trim to exact multiple of ratio
		trimmed = df.iloc[:n_groups * ratio].copy()
		group_ids = np.arange(len(trimmed)) // ratio

		result_rows = []
		for g in range(n_groups):
			group_mask = group_ids == g
			group = trimmed[group_mask]

			if method == DownsampleMethod.AVERAGE:
				acc_values = group[acc_cols].mean()
			elif method == DownsampleMethod.MIN:
				acc_values = group[acc_cols].min()
			elif method == DownsampleMethod.MAX:
				acc_values = group[acc_cols].max()
			else:
				acc_values = group[acc_cols].mean()

			# Label: mode (most frequent) within group
			label_mode = group["label"].mode()
			label_val = label_mode.iloc[0] if not label_mode.empty else 0

			individual_id = group["individual_id"].iloc[0]

			row = {
				"Acc X [g]": acc_values["Acc X [g]"],
				"Acc Y [g]": acc_values["Acc Y [g]"],
				"Acc Z [g]": acc_values["Acc Z [g]"],
				"individual_id": individual_id,
				"label": label_val
			}
			result_rows.append(row)

		return pd.DataFrame(result_rows)

	def _write_metadata(self, output_dir, method_value, meta, label_names,
	                     output_frequency, project_name, individual_str_to_int):
		"""Write dataset_metadata.yaml for a method subfolder."""
		method_dir = os.path.join(output_dir, method_value)
		os.makedirs(method_dir, exist_ok=True)

		clip_ids = meta["clip_ids"]
		individual_ids = sorted(meta["individual_ids_set"])
		clip_id_to_individual_id = meta["clip_id_to_individual_id"]

		# Generate fold assignments (round-robin, capped at 5 folds)
		n_folds = min(len(individual_ids), 5) if individual_ids else 1
		individuals_per_fold = {i: [] for i in range(n_folds)}
		clip_ids_per_fold = {i: [] for i in range(n_folds)}

		for idx, ind_id in enumerate(individual_ids):
			fold = idx % n_folds
			individuals_per_fold[fold].append(ind_id)

		for clip_id in clip_ids:
			ind_id = clip_id_to_individual_id[clip_id]
			for fold, inds in individuals_per_fold.items():
				if ind_id in inds:
					clip_ids_per_fold[fold].append(clip_id)
					break

		metadata = {
			"sr": output_frequency,
			"dataset_name": project_name,
			"clip_ids": clip_ids,
			"individual_ids": individual_ids,
			"clip_id_to_individual_id": clip_id_to_individual_id,
			"label_names": label_names,
			"clip_column_names": ["AccX", "AccY", "AccZ", "individual_id", "label"],
			"n_folds": n_folds,
			"individuals_per_fold": individuals_per_fold,
			"clip_ids_per_fold": clip_ids_per_fold
		}

		yaml_path = os.path.join(method_dir, "dataset_metadata.yaml")
		with open(yaml_path, "w") as f:
			yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

		logging.info(f"Wrote metadata: {yaml_path}")

	def validate_settings(self, settings: OutputSettings):
		"""Validate the provided settings before generating output."""
		if not settings.downsample_methods:
			logging.error("No downsampling methods selected.")
			return False
		if settings.output_frequency <= 0:
			logging.error("Output frequency must be positive.")
			return False
		return True
