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
    regex = [
        r"\[application_\d+_\d+\]",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}:\d{2}:\d{2},\d{3}",
        r"\b\d+\b",
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
def generate_train_test(label_dict, rca_ratio=0.1, normal_test_ratio=0.3):
    df = pd.read_csv(log_sequence_file)
    df["Label"] = df["AppId"].apply(lambda x: label_dict.get(x, -1))

    # Sample full DataFrames so AppId is preserved
    normal_df = df[df["Label"] == 0].sample(frac=1, random_state=42).copy()
    abnormal_df = df[df["Label"] == 1].sample(frac=1, random_state=42).copy()

    # RCA set from top 10% of abnormal
    rca_len = int(len(abnormal_df) * rca_ratio)
    rca_abnormal = abnormal_df.iloc[:rca_len].copy()
    test_abnormal = abnormal_df.iloc[rca_len:].copy()

    # 10% normal for testing
    normal_test_len = int(len(normal_df) * normal_test_ratio)
    test_normal = normal_df.iloc[:normal_test_len].copy()
    train_normal = normal_df.iloc[normal_test_len:].copy()

    # Final sets
    df_to_file(train_normal, os.path.join(output_dir, "train"))
    df_to_file(test_normal, os.path.join(output_dir, "test_normal"))
    df_to_file(test_abnormal, os.path.join(output_dir, "test_abnormal"))
    df_to_file(
        rca_abnormal,
        os.path.join(output_dir, "rca_abnormal"),
        save_csv=True,
        csv_path=os.path.join(output_dir, "rca_abnormal_sequence.csv")
    )



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

# === Run All ===
if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    label_dict = extract_labels_from_file(abnormal_file)
    merge_logs(input_dir, os.path.join(input_dir, log_file))
    parse_log_with_drain()
    mapping()
    hadoop_sampling()
    generate_train_test(label_dict)
    merge_sequences_for_vocab(output_dir)
