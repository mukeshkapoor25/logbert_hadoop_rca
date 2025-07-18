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

# === Paths ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
input_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'datasets', 'Hadoop')
abnormal_file = os.path.join(input_dir, 'abnormal_label.txt')
output_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')
log_file = "combined_hadoop.log"

log_structured_file = os.path.join(output_dir, log_file + "_structured.csv")
log_templates_file = os.path.join(output_dir, log_file + "_templates.csv")
log_sequence_file = os.path.join(output_dir, "hadoop_sequence.csv")

# === 1. Label extractor ===
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

# === 2. Merge logs (without prepending AppId) ===
def merge_logs(input_base_path, output_file):
    with open(output_file, "w") as out:
        for app_folder in os.listdir(input_base_path):
            full_path = os.path.join(input_base_path, app_folder)
            if os.path.isdir(full_path):
                for file in os.listdir(full_path):
                    if file.endswith(".log"):
                        with open(os.path.join(full_path, file), "r") as f:
                            for line in f:
                                if line.strip():
                                    out.write(line)

# === 3. Drain parser ===
def parse_log_with_drain():
    regex = [
        r"\d{4}-\d{2}-\d{2}",
        r"\d{2}:\d{2}:\d{2},\d{3}",
        r"\b\d+\b"
    ]
    log_format = "<Date> <Time> <Level> \[<Process>\] <Component>: <Content>"

    parser = Drain.LogParser(
        log_format=log_format,
        indir=input_dir,
        outdir=output_dir,
        depth=5,
        st=0.5,
        rex=regex,
        keep_para=False
    )
    parser.parse(log_file)

    df = pd.read_csv(log_structured_file)
    print(f"✅ Parsed {len(df)} lines")

# === 4. Map EventIds to numeric ===
def mapping():
    df = pd.read_csv(log_templates_file)
    df.sort_values(by="Occurrences", ascending=False, inplace=True)
    template_map = {event: idx + 1 for idx, event in enumerate(df["EventId"])}
    with open(os.path.join(output_dir, "hadoop_log_templates.json"), "w") as f:
        json.dump(template_map, f)

# === 5. Group by AppId using filename matching ===
def hadoop_sampling():
    df = pd.read_csv(log_structured_file)

    # Re-assign AppId by matching filenames
    app_id_mapping = {}
    for app_folder in os.listdir(input_dir):
        full_path = os.path.join(input_dir, app_folder)
        if os.path.isdir(full_path):
            for file in os.listdir(full_path):
                if file.endswith(".log"):
                    file_path = os.path.join(full_path, file)
                    with open(file_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line and line in df["Content"].values:
                                app_id_mapping[line] = app_folder

    df["AppId"] = df["Content"].apply(lambda x: app_id_mapping.get(x, None))

    with open(os.path.join(output_dir, "hadoop_log_templates.json")) as f:
        event_map = json.load(f)

    df["EventId"] = df["EventId"].apply(lambda x: event_map.get(x, -1))

    data_dict = defaultdict(list)
    for _, row in tqdm(df.iterrows(), total=len(df)):
        app_id = row.get("AppId")
        if pd.notnull(app_id):
            data_dict[app_id].append(row["EventId"])

    pd.DataFrame(list(data_dict.items()), columns=['AppId', 'EventSequence']).to_csv(log_sequence_file, index=False)
    print(f"✅ hadoop_sequence.csv written with {len(data_dict)} sequences.")

# === 6. Train/Test split ===
def generate_train_test(label_dict, ratio=0.9, abnormal_ratio=0.5, rca_ratio=0.1):
    df = pd.read_csv(log_sequence_file)
    df["Label"] = df["AppId"].apply(lambda x: label_dict.get(x, -1))

    normal_seq = df[df["Label"] == 0]["EventSequence"].sample(frac=1, random_state=42)
    abnormal_seq_full = df[df["Label"] == 1]["EventSequence"].sample(frac=1, random_state=42)

    rca_len = int(len(abnormal_seq_full) * rca_ratio)
    rca_abnormal = abnormal_seq_full.iloc[:rca_len]
    abnormal_seq = abnormal_seq_full.iloc[rca_len:]

    train_len = int(len(normal_seq) * ratio)
    train_normal = normal_seq.iloc[:train_len]
    test_normal = normal_seq.iloc[train_len:]

    abnormal_train_len = int(len(abnormal_seq) * abnormal_ratio)
    train_abnormal = abnormal_seq.iloc[:abnormal_train_len]
    test_abnormal = abnormal_seq.iloc[abnormal_train_len:]

    train = pd.concat([train_normal, train_abnormal]).sample(frac=1, random_state=42)

    df_to_file(train, os.path.join(output_dir, "train"))
    df_to_file(test_normal, os.path.join(output_dir, "test_normal"))
    df_to_file(test_abnormal, os.path.join(output_dir, "test_abnormal"))
    df_to_file(rca_abnormal, os.path.join(output_dir, "rca_abnormal"))

def df_to_file(df, file_name):
    with open(file_name, 'w') as f:
        for row in df:
            f.write(" ".join([str(e) for e in eval(row)]) + "\n")

# === Main ===
if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    label_dict = extract_labels_from_file(abnormal_file)
    merge_logs(input_dir, os.path.join(input_dir, log_file))
    parse_log_with_drain()
    mapping()
    hadoop_sampling()
    generate_train_test(label_dict)
