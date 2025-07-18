import os
import sys
sys.path.append('../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import json
import ast
import torch
import pandas as pd
import numpy as np
from tqdm import tqdm
from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForCausalLM
from torch.utils.data import DataLoader

from logparser import Drain
from bert_pytorch.dataset import LogDataset, WordVocab
from bert_pytorch.model.bert import BERT
from bert_pytorch.model.log_model import BERTLog
import time

# === Config ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
input_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'datasets', 'Hadoop')
abnormal_file = os.path.join(input_dir, 'abnormal_label.txt')
output_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')
log_file = "rca_abnormal_hadoop.log"
log_structured_file = os.path.join(output_dir, log_file + "_structured.csv")
log_templates_file = os.path.join(output_dir, log_file + "_templates.csv")
log_sequence_file = os.path.join(output_dir, "rca_abnormal_sequence.csv")
TEMPLATE_FILE = log_templates_file
PARAMS_FILE = os.path.join(output_dir, "bert", "parameters.txt")
CENTER_PATH = os.path.join(output_dir, "bert", "best_center.pt")
TRAIN_FILE = os.path.join(output_dir, "train")

TOP_EVENTS = 5
MAX_RCA_TOKENS = 200
MISTRAL_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# === Utility Functions ===
def parse_log_with_drain():
    regex = [
        r"appattempt_\d+_\d+_\d+",
        r"job_\d+_\d+",
        r"task_\d+_\d+_[a-z]+_\d+",
        r"container_\d+",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"(?<!\w)\d{5,}(?!\w)",
        r"[a-f0-9]{8,}"
    ]
    log_format = r'\[<AppId>] <Date> <Time> <Level> \[<Process>] <Component>: <Content>'
    parser = Drain.LogParser(log_format, indir=input_dir, outdir=output_dir, depth=5, st=0.5, rex=regex, keep_para=True)
    parser.parse(log_file)

def hadoop_sampling():
    df = pd.read_csv(log_structured_file)
    data_dict = defaultdict(list)
    for _, row in tqdm(df.iterrows(), total=len(df), desc="🔍 Grouping logs by AppId"):
        app_id = row.get("AppId")
        event_id = row.get("EventId")
        if pd.notnull(app_id) and pd.notnull(event_id):
            data_dict[app_id].append(str(event_id))
    pd.DataFrame(list(data_dict.items()), columns=['AppId', 'EventSequence']).to_csv(log_sequence_file, index=False)

def load_parameters(param_path):
    options = {}
    with open(param_path, 'r') as f:
        for line in f:
            if ':' not in line:
                continue
            key, val = line.strip().split(':', 1)
            key = key.strip()
            val = val.strip()
            if val.lower() == 'true': val = True
            elif val.lower() == 'false': val = False
            elif val.lower() == 'none': val = None
            else:
                try: val = int(val)
                except ValueError:
                    try: val = float(val)
                    except ValueError: pass
            options[key] = val
    return options

def call_mistral(prompt, tokenizer, model_mistral, device):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model_mistral.generate(
        **inputs,
        max_length=inputs['input_ids'].shape[1] + MAX_RCA_TOKENS,
        do_sample=False,
        top_k=50,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)[len(prompt):].strip()

def generate_prompt(event_templates):
    prompt = "The system encountered a failure. Below are the key log events preceding the anomaly:\n\n"
    for i, event in enumerate(event_templates, 1):
        prompt += f"{i}. {event.strip()}\n"
    prompt += ("\nBased on the above log events, identify the most likely root cause of the issue.\n"
               "Explain the cause in one or two sentences, using technical reasoning if possible.\n")
    return prompt

def compute_distance_to_center(cls_output, center):
    return torch.norm(cls_output - center, dim=1).item()

def compute_logkey_anomaly(masked_output, masked_label, top_k=5):
    num_undetected = 0
    for i, token in enumerate(masked_label):
        if token not in torch.argsort(-masked_output[i])[:top_k]:
            num_undetected += 1
    return num_undetected, len(masked_label)

def detect_anomalies_and_explain():
    print("\n🔍 Running RCA pipeline...")
    parse_log_with_drain()
    hadoop_sampling()

    options = load_parameters(PARAMS_FILE)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    options["device"] = device
    # token=""
    cache_dir = "/content/drive/MyDrive/hf_cache"
    tokenizer = AutoTokenizer.from_pretrained(MISTRAL_MODEL, cache_dir=cache_dir)
    model_mistral = AutoModelForCausalLM.from_pretrained(MISTRAL_MODEL, torch_dtype=torch.float32, cache_dir=cache_dir).to(device)
    model_mistral.eval()

    vocab = WordVocab.load_vocab(options["vocab_path"])
    center_dict = torch.load(CENTER_PATH, map_location=device)
    center = center_dict["center"] if isinstance(center_dict, dict) else center_dict

    sequences_df = pd.read_csv(log_sequence_file)
    data, app_ids = [], []
    for _, row in sequences_df.iterrows():
        try:
            seq = ast.literal_eval(row["EventSequence"])
            if len(seq) >= options["min_len"]:
                data.append(seq)
                app_ids.append(row["AppId"])
        except Exception as e:
            print(f"⚠️ Skipping row due to parse error: {e}")

    dummy_times = [[0] * len(seq) for seq in data]
    dataset = LogDataset(data, dummy_times, vocab, seq_len=options["seq_len"], on_memory=True, mask_ratio=options["mask_ratio"])
    test_loader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=dataset.collate_fn)

    try:
        model = torch.load(options["model_path"], map_location=device)
    except:
        bert = BERT(len(vocab), options["hidden"], options["layers"], options["attn_heads"], options["max_len"])
        model = BERTLog(bert, vocab_size=len(vocab)).to(device)
        model.load_state_dict(torch.load(options["model_path"], map_location=device))
    model.to(device)
    model.eval()

    sequences = []
    with open(TRAIN_FILE, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            if len(tokens) >= options["min_len"]:
                sequences.append(tokens)

    dummy_times = [[0] * len(seq) for seq in sequences]
    train_loader = DataLoader(LogDataset(sequences, dummy_times, vocab, seq_len=options["seq_len"], on_memory=True, mask_ratio=options["mask_ratio"]), batch_size=1, shuffle=False, collate_fn=dataset.collate_fn)

    train_scores = []
    for batch in tqdm(train_loader, desc="📏 Computing train distances..."):
        batch = {k: v.to(device) for k, v in batch.items()}
        output = model(batch["bert_input"], batch["time_input"])
        cls_output = output["cls_output"]
        dist = compute_distance_to_center(cls_output, center)
        train_scores.append(dist)

    mean, std = np.mean(train_scores), np.std(train_scores)
    templates = pd.read_csv(TEMPLATE_FILE)
    event_template_dict = dict(zip(templates["EventId"], templates["EventTemplate"]))
    print("\n======================")
    print("🔍 FULL RCA SCAN REPORT")
    print("======================\n")

    with torch.no_grad():
        for i, batch in enumerate(test_loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            output = model(batch["bert_input"], batch["time_input"])
            cls_output = output["cls_output"]
            score = compute_distance_to_center(cls_output, center)
            z_score = (score - mean) / std
            masked_output = output["logkey_output"][0]
            masked_label = batch["bert_label"][0]
            num_undetected, masked_total = compute_logkey_anomaly(masked_output, masked_label)
            undetected_ratio = num_undetected / masked_total if masked_total > 0 else 0

            is_deep = z_score > 2
            is_logkey = undetected_ratio > 0.5
            print(f"AppId: {app_ids[i]} | Score: {score:.4f} | z: {z_score:.2f} | Undetected: {undetected_ratio:.2f}", end='')
            if not (is_deep or is_logkey):
                print(" | 🟢 Status: Normal\n")
                continue
            print(" | 🔴 Status: Abnormal")
            # event_templates = [
            #     templates.loc[templates["EventId"] == eid, "EventTemplate"].values[0]
            #     if len(templates.loc[templates["EventId"] == eid]) > 0 else f"[Missing Event {eid}]"
            #     for eid in data[i][:TOP_EVENTS]
            # ]
            t0 = time.time()
            event_templates = [
                event_template_dict.get(eid, f"[Missing Event {eid}]")
                for eid in data[i][:TOP_EVENTS]
            ]
            t1 = time.time()
            print("Template fetch:", t1 - t0)
            t2 = time.time()
            prompt = generate_prompt(event_templates)
            t3 = time.time()
            print("Prompt fetch:", t3 - t2)
            t4 = time.time()
            explanation = call_mistral(prompt, tokenizer, model_mistral, device)
            t5 = time.time()
            print("explanation fetch:", t5 - t4)
            print("🧰 Events:")
            for j, evt in enumerate(event_templates, 1):
                print(f"   {j}. {evt}")
            print("\n🧠 Mistral-7B RCA Explanation:")
            print(explanation)
            print("-" * 60)

if __name__ == "__main__":
    detect_anomalies_and_explain()
