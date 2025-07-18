import os
import sys
sys.path.append('../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import pandas as pd
from tqdm import tqdm
from collections import defaultdict
from logparser import Drain  # Ensure you have the Drain parser from LogPAI

### 🔧 CONFIG ###
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

raw_logs_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'datasets', 'Hadoop')  # 📂 Input: application logs
abnormal_file = os.path.join(raw_logs_dir, 'abnormal_label.txt')  # 📄 Abnormal AppIds
output_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')  # 📤 Output folder
log_format = r'<Date> <Time> <Level> \[<Process>\] <Component>: <Content>'  # ⛏️ Adjust this if needed
regex = []

# ⏳ Step 1: Gather logs + AppId
combined_logs = []
app_id_map = []

print("🔄 Reading and tagging logs...")
for app_folder in os.listdir(raw_logs_dir):
    app_path = os.path.join(raw_logs_dir, app_folder)
    if os.path.isdir(app_path):
        for file in os.listdir(app_path):
            full_path = os.path.join(app_path, file)
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line:
                        combined_logs.append(clean_line)
                        app_id_map.append(app_folder)  # assumes folder name == AppId

print(f"✅ Total log lines collected: {len(combined_logs)}")

# 🔧 Step 2: Write combined log file
os.makedirs(output_dir, exist_ok=True)
log_file = os.path.join(output_dir, 'raw_hadoop.log')
with open(log_file, 'w') as f:
    f.write('\n'.join(combined_logs))

# 🧠 Step 3: Parse logs via Drain
drain_output_dir = os.path.join(output_dir, 'structured')
# os.makedirs(drain_output_dir, exist_ok=True)

drain = Drain.LogParser(
    log_format=log_format,
    indir=raw_logs_dir,
    outdir=output_dir,
    depth=6,
    st=0.5,
    rex=regex
)

print("🧩 Parsing with Drain...")
drain.parse(log_file)

structured_df_path = os.path.join(output_dir, 'structured.csv')
structured_df = pd.read_csv(structured_df_path)

# 🧩 Step 4: Add AppId back
structured_df['AppId'] = app_id_map
structured_df.to_csv(os.path.join(output_dir, 'log_structured.csv'), index=False)

# 💡 Step 5: Save unique EventTemplate-EventId mapping
event_templates = structured_df[['EventId', 'EventTemplate']].drop_duplicates()
event_templates.to_csv(os.path.join(output_dir, 'log_templates.csv'), index=False)

# 📊 Step 6: Generate EventId sequences
print("🔁 Generating EventId sequences...")
grouped = structured_df.groupby('AppId')['EventId'].apply(list).reset_index()
grouped.rename(columns={'EventId': 'EventSequence'}, inplace=True)
grouped['EventSequence'] = grouped['EventSequence'].apply(lambda x: ' '.join(map(str, x)))
grouped.to_csv(os.path.join(output_dir, 'log_sequences.csv'), index=False)

# ⚠️ Step 7: Generate Labels
print("🏷️ Creating label file...")
with open(abnormal_file, 'r') as f:
    abnormal_ids = set(line.strip() for line in f if line.strip())

grouped['Label'] = grouped['AppId'].apply(lambda x: 1 if x in abnormal_ids else 0)
grouped[['AppId', 'Label']].to_csv(os.path.join(output_dir, 'anomaly_label.csv'), index=False)

# ✂️ Step 8: Split into train, test, rca
print("✂️ Splitting for training and RCA...")
normal_df = grouped[grouped['Label'] == 0].sample(frac=1, random_state=42)
abnormal_df = grouped[grouped['Label'] == 1].sample(frac=1, random_state=42)

rca_ratio = 0.1
ab_rca_len = int(len(abnormal_df) * rca_ratio)
rca_df = abnormal_df.iloc[:ab_rca_len]
abnormal_df = abnormal_df.iloc[ab_rca_len:]

train_ratio = 0.8
train_len = int(len(normal_df) * train_ratio)
train_df = normal_df.iloc[:train_len]
test_df = pd.concat([normal_df.iloc[train_len:], abnormal_df], ignore_index=True)

# Save all splits
train_df[['AppId', 'EventSequence', 'Label']].to_csv(os.path.join(output_dir, 'train.csv'), index=False)
test_df[['AppId', 'EventSequence', 'Label']].to_csv(os.path.join(output_dir, 'test.csv'), index=False)
rca_df[['AppId', 'EventSequence', 'Label']].to_csv(os.path.join(output_dir, 'rca.csv'), index=False)

print("✅ Done! All output saved to:", output_dir)
