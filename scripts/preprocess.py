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
abnormal_file = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'datasets', 'Hadoop', 'abnormal_label.txt')
output_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')
log_file = "combined_hadoop.log"

log_structured_file = os.path.join(output_dir, log_file + "_structured.csv")
log_templates_file = os.path.join(output_dir, log_file + "_templates.csv")
log_sequence_file = os.path.join(output_dir, "hadoop_sequence.csv")

# === 1. Extract labels ===
def extract_labels_from_file(filepath):
    label_dict = {}
    current_label = 1  # default to abnormal

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            # Detect Normal/Abnormal section
            if line.endswith("Normal:"):
                current_label = 0
            elif re.match(r".*:\s*$", line):  # Other section headers like 'Disk full:'
                current_label = 1

            # Detect application ID
            match = re.match(r"\+ (application_\d+_\d+)", line)
            if match:
                app_id = match.group(1)
                label_dict[app_id] = current_label

    return label_dict

# === 2. Merge all logs ===
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

# === 3. Parse logs using Drain ===
def parse_log_with_drain():
    regex = [
        r"\[application_\d+_\d+\]",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}:\d{2}:\d{2},\d{3}",
        r"\b\d+\b",
    ]
    log_format = r'\[<AppId>\] <Date> <Time> <Level> \[<Process>\] <Component>: <Content>'

    parser = Drain.LogParser(
        log_format=log_format,
        indir=input_dir,
        outdir=output_dir,
        depth=5,
        st=0.5,
        rex=regex,
        keep_para=True
    )
    parser.parse(log_file)

    # Confirm parsing
    struct_file = os.path.join(output_dir, log_file + "_structured.csv")
    if os.path.exists(struct_file):
        df = pd.read_csv(struct_file)
        print(f"✅ Parsed lines: {len(df)}")
        print(df.head())
    else:
        print("❌ No structured log file generated.")

# === 4. Map EventIds to integer IDs ===
def mapping():
    df = pd.read_csv(log_templates_file)
    df.sort_values(by="Occurrences", ascending=False, inplace=True)
    template_map = {event: idx + 1 for idx, event in enumerate(df["EventId"])}
    with open(os.path.join(output_dir, "hadoop_log_templates.json"), "w") as f:
        json.dump(template_map, f)

# === 5. Group logs by AppId ===
def hadoop_sampling():
    df = pd.read_csv(log_structured_file)
    with open(os.path.join(output_dir, "hadoop_log_templates.json"), "r") as f:
        event_map = json.load(f)

    df["EventId"] = df["EventId"].apply(lambda x: event_map.get(x, -1))

    data_dict = defaultdict(list)
    for _, row in tqdm(df.iterrows()):
        app_id = row.get("AppId")
        if pd.notnull(app_id):
            data_dict[app_id].append(row["EventId"])

    pd.DataFrame(list(data_dict.items()), columns=['AppId', 'EventSequence']).to_csv(log_sequence_file, index=False)
    print(f"✅ hadoop_sequence.csv written with {len(data_dict)} sequences.")

def hadoop_sampling_regex_based():
    try:
        df = pd.read_csv(log_structured_file)
        print(f"📄 Loaded structured log file with {len(df)} rows")
    except Exception as e:
        print(f"❌ Error loading log file: {e}")
        return

    try:
        with open(os.path.join(output_dir, "hadoop_log_templates.json"), "r") as f:
            event_map = json.load(f)
        print(f"🗺️ Event map loaded with {len(event_map)} entries")
    except Exception as e:
        print(f"❌ Error loading event map: {e}")
        return

    # Apply integer ID mapping
    df["EventId"] = df["EventId"].map(event_map).fillna(-1).astype(int)

    # Use regex to extract AppId from 'Content'
    pattern = r'(application_\d+_\d+)'  # Hadoop AppId pattern
    data_dict = defaultdict(list)
    for _, row in tqdm(df.iterrows(), total=len(df), desc="🔍 Extracting AppIds via regex"):
        matches = re.findall(pattern, row.get("Content", ""))
        for app_id in set(matches):  # avoid duplication
            data_dict[app_id].append(row["EventId"])

    pd.DataFrame(list(data_dict.items()), columns=['AppId', 'EventSequence']).to_csv(log_sequence_file, index=False)
    print(f"✅ hadoop_sequence.csv written with {len(data_dict)} sequences.")

#=== 6. Split into train/test sets ===
def generate_train_test(label_dict, ratio=0.9, abnormal_ratio=0.5, rca_ratio=0.1):
    df = pd.read_csv(log_sequence_file)
    df["Label"] = df["AppId"].apply(lambda x: label_dict.get(x, -1))
    
    # Separate and shuffle normal and abnormal sequences
    normal_seq = df[df["Label"] == 0]["EventSequence"].sample(frac=1, random_state=42)
    abnormal_seq_full = df[df["Label"] == 1]["EventSequence"].sample(frac=1, random_state=42)

    # Extract 10% of abnormal data for RCA
    rca_len = int(len(abnormal_seq_full) * rca_ratio)
    rca_abnormal = abnormal_seq_full.iloc[:rca_len]
    abnormal_seq = abnormal_seq_full.iloc[rca_len:]  # remaining abnormal logs

    # Split normal data
    train_len = int(len(normal_seq) * ratio)
    print(train_len, 'line-132')
    train_normal = normal_seq.iloc[:train_len]
    test_normal = normal_seq.iloc[train_len:]

    # Split abnormal data (30% of remaining to train)
    abnormal_train_len = int(len(abnormal_seq) * abnormal_ratio)
    train_abnormal = abnormal_seq.iloc[:abnormal_train_len]
    test_abnormal = abnormal_seq.iloc[abnormal_train_len:]

    # Combine training data
    train = pd.concat([train_normal, train_abnormal]).sample(frac=1, random_state=42)

    # Write to files
    df_to_file(train, os.path.join(output_dir, "train"))
    df_to_file(test_normal, os.path.join(output_dir, "test_normal"))
    df_to_file(test_abnormal, os.path.join(output_dir, "test_abnormal"))
    df_to_file(rca_abnormal, os.path.join(output_dir, "rca_abnormal"))

# def generate_train_test(label_dict, ratio=0.9, train_ratio=0.5, rca_ratio=0.1):
#     df = pd.read_csv(log_sequence_file)
#     df["Label"] = df["AppId"].apply(lambda x: label_dict.get(x, -1))
    
#     # Separate and shuffle abnormal and normal sequences
#     abnormal_seq_full = df[df["Label"] == 1]["EventSequence"].sample(frac=1, random_state=42)
#     normal_seq = df[df["Label"] == 0]["EventSequence"].sample(frac=1, random_state=42)

#     # Step 1: Extract RCA data from abnormal logs
#     rca_len = int(len(abnormal_seq_full) * rca_ratio)
#     rca_abnormal = abnormal_seq_full.iloc[:rca_len]
#     remaining_abnormal = abnormal_seq_full.iloc[rca_len:]

#     # Step 2: Train on a portion of remaining abnormal data
#     train_len = int(len(remaining_abnormal) * train_ratio)
#     train = remaining_abnormal.iloc[:train_len]

#     # Step 3: Test on the rest of abnormal and all normal logs
#     test_abnormal = remaining_abnormal.iloc[train_len:]
#     test_normal = normal_seq

#     # Shuffle the train set for consistency
#     train = train.sample(frac=1, random_state=42)

#     # Write to files
#     df_to_file(train, os.path.join(output_dir, "train"))
#     df_to_file(test_normal, os.path.join(output_dir, "test_normal"))
#     df_to_file(test_abnormal, os.path.join(output_dir, "test_abnormal"))
#     df_to_file(rca_abnormal, os.path.join(output_dir, "rca_abnormal"))
    
# def df_to_file(df, file_name):
#     with open(file_name, 'w') as f:
#         for _, row in df.items():
#             f.write(" ".join([str(e) for e in eval(row)]) + "\n")

def df_to_file(df, file_name):
    with open(file_name, 'w') as f:
        for row in df:
            f.write(" ".join([str(e) for e in eval(row)]) + "\n")

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
    print(f"📘 log_sequence_all.txt created with merged data from: {', '.join(files)}")
# === Main ===
if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    label_dict = extract_labels_from_file(abnormal_file)
    merge_logs(input_dir, os.path.join(input_dir, log_file))
    parse_log_with_drain()
    mapping()
    hadoop_sampling()
    # hadoop_sampling_regex_based()
    generate_train_test(label_dict)
    merge_sequences_for_vocab(output_dir)