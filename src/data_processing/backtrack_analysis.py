import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import multiprocessing
from tqdm import tqdm
import pickle
import gc

# Define the directory and threshold
ROOT_DIR = r'D:\OSU\cougar_data'
BACKTRACK_REPORT_FILE = 'backtrack_report.txt'
ERROR_REPORT_FILE = 'error_report.txt'
INCOMPLETE_DAYS_FILE = 'incomplete_days.txt'
PKL_FILE = 'backtrack_results.pkl'  # Pickle file to store intermediate results
BATCH_SIZE = 100  # Number of files to process before saving intermediate results

# Regex pattern to match the correct file paths
file_pattern = re.compile(r".*\\MotionData_.*\\\d{4}\\\d{2}.*\\\d{2}.*\.csv$")

# Function to save intermediate results
def save_intermediate_results(data, file_name):
    with open(file_name, 'wb') as file:
        pickle.dump(data, file)

# Function to load intermediate results
def load_intermediate_results(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'rb') as file:
            return pickle.load(file)
    return {}

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
    backtrack_results = load_intermediate_results(PKL_FILE)  # Load previous results, if any
    error_files = []
    incomplete_day_files = []

    # Find all valid files
    files = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk(root_dir)
             for filename in filenames if filename.endswith('.csv') and file_pattern.match(os.path.join(dirpath, filename))]

    # If max_files is set, limit the number of files processed
    if max_files:
        files = files[:max_files]

    # Remove files already processed
    files_to_process = [file for file in files if file not in backtrack_results]

    total_cores = multiprocessing.cpu_count()
    processes_to_use = max(1, total_cores - 4)  # Leave 2-4 cores free

    for i in range(0, len(files_to_process), BATCH_SIZE):
        batch_files = files_to_process[i:i + BATCH_SIZE]

        # Process each batch of files in parallel
        with multiprocessing.Pool(processes=processes_to_use) as pool:
            results = list(tqdm(pool.imap(process_csv, batch_files), total=len(batch_files), desc="Processing CSV files"))

        # Store the results in a dictionary where file paths are the keys
        for (df, backtracks, start_time, end_time), file_path in zip(results, batch_files):
            if df is None:
                error_files.append(file_path)
                continue

            # Track incomplete days
            if (start_time > pd.Timestamp('00:30:00').time()) or (end_time < pd.Timestamp('23:30:00').time()):
                incomplete_day_files.append((file_path, start_time, end_time))

            # Store the backtrack result in the dictionary
            backtrack_results[file_path] = {
                'backtracks': len(backtracks),
                'start_time': start_time,
                'end_time': end_time
            }

        # Save intermediate results and clear memory
        save_intermediate_results(backtrack_results, PKL_FILE)
        gc.collect()  # Force garbage collection to free memory

    # Write error file report
    with open(ERROR_REPORT_FILE, 'w') as ef:
        ef.write("\n".join(error_files))

    # Write incomplete day files report
    with open(INCOMPLETE_DAYS_FILE, 'w') as idf:
        for file_info in incomplete_day_files:
            idf.write(f"{file_info[0]} - Start: {file_info[1]}, End: {file_info[2]}\n")

    # Summarize and plot results
    summarize_results(backtrack_results)

def summarize_results(backtrack_results):
    # Extract information for reporting and plotting
    backtrack_files = [file for file, result in backtrack_results.items() if result['backtracks'] > 0]
    backtrack_counts = [result['backtracks'] for result in backtrack_results.values() if result['backtracks'] > 0]

    # Write backtrack report
    with open(BACKTRACK_REPORT_FILE, 'w') as br:
        br.write(f"Total files with backtracks: {len(backtrack_files)}\n")
        if len(backtrack_files) > 0:
            br.write(f"Average backtracks per file: {sum(backtrack_counts) / len(backtrack_files):.2f}\n")
        br.write("\nFiles with backtracks and the number of backtracks per file:\n")
        for file, count in zip(backtrack_files, backtrack_counts):
            br.write(f"{file} - Backtracks: {count}\n")

    # Plot pie chart for files with and without backtracks
    plt.figure(figsize=(6, 6))
    labels = ['With Backtracks', 'Without Backtracks']
    sizes = [len(backtrack_files), len(backtrack_results) - len(backtrack_files)]
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

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')  # Use 'spawn' for Windows
    analyze_backtracks(ROOT_DIR)
