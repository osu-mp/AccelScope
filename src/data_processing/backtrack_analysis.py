import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from multiprocessing import Pool
from tqdm import tqdm

# Define the directory and threshold
ROOT_DIR = r'D:\OSU\cougar_data'
# BACKTRACK_THRESHOLD = pd.Timedelta(seconds=1)
BACKTRACK_REPORT_FILE = 'backtrack_report.txt'
ERROR_REPORT_FILE = 'error_report.txt'
INCOMPLETE_DAYS_FILE = 'incomplete_days.txt'

# Regex pattern to match the correct file paths
file_pattern = re.compile(r".*\\MotionData_.*\\\d{4}\\\d{2}.*\\\d{2}.*\.csv$")

def process_csv(file_path):
    try:
        # Read the CSV file, skipping the first line which contains metadata
        df = pd.read_csv(
            file_path,
            skiprows=1,  # Skip the first row containing metadata
            header=0,  # The actual column headers start from the second line
            dtype={"Milliseconds": "float", "Acc X [g]": "float", "Acc Y [g]": "float", "Acc Z [g]": "float"},
            low_memory=False
        )

        # Check if 'UTC DateTime' exists
        if 'UTC DateTime' not in df.columns:
            raise ValueError(f"'UTC DateTime' column not found in {file_path}. Available columns: {df.columns.tolist()}")

        # Combine 'UTC DateTime' and 'Milliseconds' into a single timestamp
        df['Timestamp'] = pd.to_datetime(df['UTC DateTime'], format='%H:%M:%S', errors='coerce') + pd.to_timedelta(df['Milliseconds'], unit='ms')

        # Drop rows where 'Timestamp' could not be parsed
        df = df.dropna(subset=['Timestamp']).reset_index(drop=True)

        # Initialize variables for tracking backtracks
        max_time = pd.Timestamp.min
        backtracks = []

        # Iterate through each row and detect backtracks
        for idx, row in df.iterrows():
            current_time = row['Timestamp'].time()

            # Detect rollover (i.e., when time goes back after midnight)
            if current_time < max_time.time() and current_time.hour == 0:
                backtracks.append((row['Timestamp'], max_time))

            # Check if the current time is earlier than the max encountered time (i.e., backtrack)
            if row['Timestamp'] < max_time:
                backtracks.append((row['Timestamp'], max_time))
            else:
                max_time = row['Timestamp']  # Update the max time

        # Get start and end times of the file
        start_time = df['Timestamp'].iloc[0].time()
        end_time = df['Timestamp'].iloc[-1].time()

        return df, backtracks, start_time, end_time

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, [], None, None  # Ensure backtracks is returned as an empty list instead of None


def analyze_backtracks(root_dir, max_files=None):
    backtrack_file_count = 0
    total_backtracks = 0
    all_backtrack_times = []
    error_files = []
    incomplete_day_files = []
    start_times = []
    end_times = []
    backtrack_files = []
    backtrack_counts = []

    # Find all valid files
    files = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk(root_dir)
             for filename in filenames if
             filename.endswith('.csv') and file_pattern.match(os.path.join(dirpath, filename))]

    # If max_files is set, limit the number of files processed
    if max_files:
        files = files[:max_files]

    # Process each file in parallel
    with Pool() as pool:
        results = list(tqdm(pool.imap(process_csv, files), total=len(files), desc="Processing CSV files"))

    for (df, backtracks, start_time, end_time), file_path in zip(results, files):
        if df is None:
            error_files.append(file_path)
            continue

        # Track files with incomplete days
        if (start_time > pd.Timestamp('00:30:00').time()) or (end_time < pd.Timestamp('23:30:00').time()):
            incomplete_day_files.append((file_path, start_time, end_time))

        # Record start and end times for all files
        start_times.append(start_time)
        end_times.append(end_time)

        # Check if backtracks is non-empty (list check)
        if len(backtracks) > 0:
            backtrack_file_count += 1
            total_backtracks += len(backtracks)
            backtrack_files.append(file_path)
            backtrack_counts.append(len(backtracks))
            all_backtrack_times.extend([bt[0].time() for bt in backtracks])  # Extracting the time from the backtrack timestamps

    # Write error file report
    with open(ERROR_REPORT_FILE, 'w') as ef:
        ef.write("\n".join(error_files))

    # Write backtrack report
    with open(BACKTRACK_REPORT_FILE, 'w') as br:
        br.write(f"Total files with backtracks: {backtrack_file_count}\n")
        if backtrack_file_count > 0:
            br.write(f"Average backtracks per file: {total_backtracks / backtrack_file_count:.2f}\n")
        br.write("\nFiles with backtracks:\n")
        br.write("\n".join(backtrack_files))

    # Write incomplete day files report
    with open(INCOMPLETE_DAYS_FILE, 'w') as idf:
        for file_info in incomplete_day_files:
            idf.write(f"{file_info[0]} - Start: {file_info[1]}, End: {file_info[2]}\n")

    # Plot pie chart for files with and without backtracks
    plt.figure(figsize=(6, 6))
    labels = ['With Backtracks', 'Without Backtracks']
    sizes = [backtrack_file_count, len(files) - backtrack_file_count]
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Files With and Without Backtracks')
    plt.savefig('backtrack_pie_chart.png')
    plt.show()

    # Plot summary of backtrack counts
    plt.figure(figsize=(10, 6))
    sns.histplot(backtrack_counts, bins=20)
    plt.title('Distribution of Backtrack Counts per File')
    plt.xlabel('Number of Backtracks')
    plt.ylabel('Number of Files')
    plt.savefig('backtrack_summary.png')
    plt.show()

    # Plot heatmap for start and end times
    plt.figure(figsize=(10, 6))
    sns.histplot([t.hour for t in start_times], bins=24, kde=False, color='blue', label='Start Times')
    sns.histplot([t.hour for t in end_times], bins=24, kde=False, color='red', label='End Times')
    plt.title('Start and End Times by Hour')
    plt.xlabel('Hour of Day')
    plt.ylabel('Frequency')
    plt.legend()
    plt.savefig('start_end_times_heatmap.png')
    plt.show()


if __name__ == "__main__":
    analyze_backtracks(ROOT_DIR)
