import os
import sys
sys.path.append('../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import json
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
from logparser import Drain

# === Config ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
input_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'datasets', 'Hadoop')
abnormal_file = os.path.join(input_dir, 'abnormal_label.txt')
output_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')
log_file = "combined_hadoop.log"

log_structured_file = os.path.join(output_dir, log_file + "_structured.csv")
log_templates_file = os.path.join(output_dir, log_file + "_templates.csv")
log_sequence_file = os.path.join(output_dir, "hadoop_sequence.csv")

# === 1. Extract labels ===
def extract_labels_from_file(filepath):
    label_dict = {}
    current_label = 1
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.endswith("Normal:"):
                current_label = 0
            elif re.match(r".*:\s*$", line):
                current_label = 1
            match = re.match(r"\+ (application_\d+_\d+)", line)
            if match:
                app_id = match.group(1)
                label_dict[app_id] = current_label
    return label_dict

# === 2. Merge logs ===
def merge_logs(input_base_path, output_file):
    with open(output_file, "w") as out:
        for app_folder in os.listdir(input_base_path):
            full_path = os.path.join(input_base_path, app_folder)
            if os.path.isdir(full_path):
                for log_file in os.listdir(full_path):
                    if log_file.endswith(".log"):
                        with open(os.path.join(full_path, log_file), "r") as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    out.write(f"[{app_folder}] {line}\n")

# === 3. Drain parsing ===
def parse_log_with_drain():
    # regex = [
    #     r"\[application_\d+_\d+\]",
    #     r"\d{4}-\d{2}-\d{2}",
    #     r"\d{2}:\d{2}:\d{2},\d{3}",
    #     r"\b\d+\b",
    # ]
    regex = [
      r"appattempt_\d+_\d+_\d+",                     # AppAttempt IDs (very dynamic)
      r"job_\d+_\d+",                                # Job IDs
      r"task_\d+_\d+_[a-z]+_\d+",                    # Task IDs
      r"container_\d+",                              # Container IDs
      r"\b(?:\d{1,3}\.){3}\d{1,3}\b",                # IP addresses
      r"(?<!\w)\d{5,}(?!\w)",                        # Long numeric values (e.g., sizes, IDs)
      r"[a-f0-9]{8,}",                               # Hex/UUID-like tokens
    ]
    log_format = r'\[<AppId>\] <Date> <Time> <Level> \[<Process>\] <Component>: <Content>'
    parser = Drain.LogParser(log_format, indir=input_dir, outdir=output_dir, depth=5, st=0.5, rex=regex, keep_para=True)
    parser.parse(log_file)
    if os.path.exists(log_structured_file):
        df = pd.read_csv(log_structured_file)
        print(f"✅ Parsed lines: {len(df)}")
        print(df.head())
    else:
        print("❌ No structured log file generated.")

# === 4. Save event template map (not required for RCA) ===
def mapping():
    df = pd.read_csv(log_templates_file)
    df.sort_values(by="Occurrences", ascending=False, inplace=True)
    template_map = {event: idx + 1 for idx, event in enumerate(df["EventId"])}
    with open(os.path.join(output_dir, "hadoop_log_templates.json"), "w") as f:
        json.dump(template_map, f)

# === 5. Group logs by AppId using EventId ===
def hadoop_sampling():
    df = pd.read_csv(log_structured_file)
    data_dict = defaultdict(list)
    for _, row in tqdm(df.iterrows(), total=len(df), desc="🔍 Grouping logs by AppId"):
        app_id = row.get("AppId")
        event_id = row.get("EventId")
        if pd.notnull(app_id) and pd.notnull(event_id):
            data_dict[app_id].append(str(event_id))
    pd.DataFrame(list(data_dict.items()), columns=['AppId', 'EventSequence']).to_csv(log_sequence_file, index=False)
    print(f"✅ hadoop_sequence.csv written with {len(data_dict)} sequences.")

# === 6. Save .txt and optional .csv for RCA ===
def df_to_file(df, file_name, save_csv=False, csv_path=None):
    # Determine sequences
    if isinstance(df, pd.DataFrame) and "EventSequence" in df.columns:
        sequences = df["EventSequence"]
    elif isinstance(df, pd.Series):
        sequences = df
    else:
        raise ValueError("Expected DataFrame with 'EventSequence' or Series of event sequences.")

    # Save to .txt
    with open(file_name, 'w') as f:
        for row in sequences:
            f.write(" ".join([str(e) for e in eval(row)]) + "\n")

    # Save to CSV (if applicable)
    if (
        save_csv and csv_path and
        isinstance(df, pd.DataFrame) and
        "AppId" in df.columns and
        "EventSequence" in df.columns
    ):
        df[["AppId", "EventSequence"]].to_csv(csv_path, index=False)
        print(f"📄 RCA CSV saved to: {csv_path}")

# === 7. Train/Test/RCA Split ===
def generate_train_test(label_dict, normal_test_ratio=0.3):
    df = pd.read_csv(log_sequence_file)
    df["Label"] = df["AppId"].apply(lambda x: label_dict.get(x, -1))

    # Shuffle normal and abnormal data
    normal_df = df[df["Label"] == 0].sample(frac=1, random_state=42).copy()
    abnormal_df = df[df["Label"] == 1].sample(frac=1, random_state=42).copy()

    # Split normal data into train and test
    normal_test_len = int(len(normal_df) * normal_test_ratio)
    test_normal = normal_df.iloc[:normal_test_len].copy()
    train_normal = normal_df.iloc[normal_test_len:].copy()

    # All abnormal goes to test
    test_abnormal = abnormal_df.copy()

    # Save datasets
    df_to_file(train_normal, os.path.join(output_dir, "train"))
    df_to_file(test_normal, os.path.join(output_dir, "test_normal"))
    df_to_file(test_abnormal, os.path.join(output_dir, "test_abnormal"))



# === 8. Merge all for vocab generation ===
def merge_sequences_for_vocab(output_dir):
    files = ["train", "test_normal", "test_abnormal", "rca_abnormal"]
    merged_path = os.path.join(output_dir, "log_sequence_all.txt")
    with open(merged_path, "w") as outfile:
        for fname in files:
            fpath = os.path.join(output_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "r") as infile:
                    for line in infile:
                        if line.strip():
                            outfile.write(line)
    print(f"📘 log_sequence_all.txt created from: {', '.join(files)}")

def split_combined_log_for_train_test_and_rca(combined_log_path, label_dict, output_dir, rca_ratio=0.1):
    print("🚧 Splitting combined log into train/test (90%) and RCA (10% abnormal)...")

    # Separate AppIds
    normal_ids = [aid for aid, label in label_dict.items() if label == 0]
    abnormal_ids = [aid for aid, label in label_dict.items() if label == 1]

    # Shuffle
    from random import shuffle
    shuffle(normal_ids)
    shuffle(abnormal_ids)

    # Select 10% of abnormal for RCA
    rca_abnormal_count = int(len(abnormal_ids) * rca_ratio)
    rca_app_ids = set(abnormal_ids[:rca_abnormal_count])

    # Remaining for Train/Test
    train_test_app_ids = set(normal_ids + abnormal_ids[rca_abnormal_count:])

    # File paths
    train_test_log = os.path.join(input_dir, "combined_hadoop.log")
    rca_log = os.path.join(input_dir, "rca_abnormal_hadoop.log")

    with open(combined_log_path, "r") as infile, \
         open(train_test_log, "w") as out_train, \
         open(rca_log, "w") as out_rca:

        for line in infile:
            match = re.match(r"\[(application_\d+_\d+)\]", line)
            if match:
                app_id = match.group(1)
                if app_id in rca_app_ids:
                    out_rca.write(line)
                elif app_id in train_test_app_ids:
                    out_train.write(line)

    print(f"✅ combined_hadoop.log written with {len(train_test_app_ids)} AppIds")
    print(f"✅ rca_abnormal_hadoop.log written with {len(rca_app_ids)} AppIds")
    return train_test_log, rca_log, rca_app_ids



# === Run All ===
if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)

    # 1. Extract AppId labels
    label_dict = extract_labels_from_file(abnormal_file)

    # 2. Merge all raw logs temporarily
    full_combined_path = os.path.join(input_dir, "combined_full_raw.log")
    merge_logs(input_dir, full_combined_path)

    # 3. Split into 90% Train/Test and 10% RCA
    train_test_log, rca_log, _ =  split_combined_log_for_train_test_and_rca(
        full_combined_path, label_dict, output_dir, rca_ratio=0.1
    )

    # === Train/Test Preprocessing ===
    log_file = os.path.basename(train_test_log)  # combined_hadoop.log
    parse_log_with_drain()
    mapping()
    hadoop_sampling()
    generate_train_test(label_dict)
    merge_sequences_for_vocab(output_dir)


