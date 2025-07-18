import os
import sys
sys.path.append('../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import ast
import json
import time
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

# === Config ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
input_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'datasets', 'Hadoop')
output_dir = os.path.join(PROJECT_ROOT, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')
log_file = "rca_abnormal_hadoop.log"
log_structured_file = os.path.join(output_dir, log_file + "_structured.csv")
log_templates_file = os.path.join(output_dir, log_file + "_templates.csv")
log_sequence_file = os.path.join(output_dir, "rca_abnormal_sequence.csv")
TEMPLATE_FILE = log_templates_file
PARAMS_FILE = os.path.join(output_dir, "bert", "parameters.txt")
CENTER_PATH = os.path.join(output_dir, "bert", "best_center.pt")
TRAIN_FILE = os.path.join(output_dir, "train")
HF_CACHE = "/content/drive/MyDrive/hf_cache"

TOP_EVENTS = 5
MAX_RCA_TOKENS = 200
MISTRAL_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# === Log Parsing ===
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

# === Data & Model Loaders ===
def load_parameters(param_path):
    options = {}
    with open(param_path, 'r') as f:
        for line in f:
            if ':' not in line:
                continue
            key, val = line.strip().split(':', 1)
            key, val = key.strip(), val.strip()
            if val.lower() in ['true', 'false', 'none']:
                val = eval(val.capitalize())
            else:
                try: val = int(val)
                except ValueError:
                    try: val = float(val)
                    except ValueError: pass
            options[key] = val
    return options

def load_logbert_model(options, vocab):
    try:
        return torch.load(options["model_path"], map_location=options["device"])
    except:
        bert = BERT(len(vocab), options["hidden"], options["layers"], options["attn_heads"], options["max_len"])
        model = BERTLog(bert, vocab_size=len(vocab)).to(options["device"])
        model.load_state_dict(torch.load(options["model_path"], map_location=options["device"]))
        return model

def load_center(path, device):
    center = torch.load(path, map_location=device)
    return center["center"] if isinstance(center, dict) else center

def extract_sequences(path, min_len):
    df = pd.read_csv(path)
    data, app_ids = [], []
    for _, row in df.iterrows():
        try:
            seq = ast.literal_eval(row["EventSequence"])
            if len(seq) >= min_len:
                data.append(seq)
                app_ids.append(row["AppId"])
        except:
            continue
    return data, app_ids

def prepare_dataloader(sequences, vocab, options):
    dummy_times = [[0] * len(seq) for seq in sequences]
    dataset = LogDataset(sequences, dummy_times, vocab, seq_len=options["seq_len"], on_memory=True, mask_ratio=options["mask_ratio"])
    return DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=dataset.collate_fn)

def calculate_mean_std(loader, model, center, device):
    scores = []
    with torch.no_grad():
        for batch in tqdm(loader, desc="📏 Computing train distances..."):
            batch = {k: v.to(device) for k, v in batch.items()}
            cls_output = model(batch["bert_input"], batch["time_input"])["cls_output"]
            scores.append(torch.norm(cls_output - center, dim=1).item())
    return np.mean(scores), np.std(scores)

# === RCA & Mistral ===
def generate_prompt(event_templates):
    prompt = "The system encountered a failure. Below are the key log events preceding the anomaly:\n\n"
    for i, event in enumerate(event_templates, 1):
        prompt += f"{i}. {event.strip()}\n"
    prompt += "\nBased on the above log events, identify the most likely root cause of the issue.\n"
    prompt += "Explain the cause in one or two sentences, using technical reasoning if possible.\n"
    return prompt

def call_mistral(prompt, tokenizer, model, device):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_length=inputs['input_ids'].shape[1] + MAX_RCA_TOKENS,
        do_sample=False,
        top_k=50,
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)[len(prompt):].strip()

def compute_logkey_anomaly(masked_output, masked_label, top_k=5):
    num_undetected = 0
    for i, token in enumerate(masked_label):
        if token not in torch.argsort(-masked_output[i])[:top_k]:
            num_undetected += 1
    return num_undetected, len(masked_label)

# === Main Execution ===
def detect_anomalies_and_explain():
    print("\n🔍 Running RCA pipeline...")
    parse_log_with_drain()
    hadoop_sampling()

    options = load_parameters(PARAMS_FILE)
    options["device"] = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(MISTRAL_MODEL, cache_dir=HF_CACHE)
    model_mistral = AutoModelForCausalLM.from_pretrained(MISTRAL_MODEL, torch_dtype=torch.float32, cache_dir=HF_CACHE).to(options["device"])
    model_mistral.eval()

    model, vocab = load_logbert_model(options, WordVocab.load_vocab(options["vocab_path"])), WordVocab.load_vocab(options["vocab_path"])
    center = load_center(CENTER_PATH, options["device"])

    test_sequences, app_ids = extract_sequences(log_sequence_file, options["min_len"])
    test_loader = prepare_dataloader(test_sequences, vocab, options)

    train_sequences = [line.strip().split() for line in open(TRAIN_FILE) if len(line.strip().split()) >= options["min_len"]]
    train_loader = prepare_dataloader(train_sequences, vocab, options)

    mean, std = calculate_mean_std(train_loader, model, center, options["device"])
    templates = pd.read_csv(TEMPLATE_FILE)
    event_template_dict = dict(zip(templates["EventId"], templates["EventTemplate"]))

    print("\n======================")
    print("🔍 FULL RCA SCAN REPORT")
    print("======================\n")

    for i, batch in enumerate(test_loader):
        batch = {k: v.to(options["device"]) for k, v in batch.items()}
        output = model(batch["bert_input"], batch["time_input"])
        cls_output = output["cls_output"]
        score = torch.norm(cls_output - center, dim=1).item()
        z_score = (score - mean) / std

        num_undetected, masked_total = compute_logkey_anomaly(output["logkey_output"][0], batch["bert_label"][0])
        undetected_ratio = num_undetected / masked_total if masked_total else 0

        status = "🔴 Abnormal" if z_score > 2 or undetected_ratio > 0.5 else "🟢 Normal"
        print(f"AppId: {app_ids[i]} | Score: {score:.4f} | z: {z_score:.2f} | Undetected: {undetected_ratio:.2f} | Status: {status}")
        if status == "🟢 Normal": continue

        top_eids = test_sequences[i][:TOP_EVENTS]
        event_templates = [event_template_dict.get(eid, f"[Missing Event {eid}]") for eid in top_eids]
        prompt = generate_prompt(event_templates)
        explanation = call_mistral(prompt, tokenizer, model_mistral, options["device"])

        print("🧰 Events:")
        for j, evt in enumerate(event_templates, 1):
            print(f"   {j}. {evt}")
        print("\n🧠 Mistral-7B RCA Explanation:")
        print(explanation)
        print("-" * 60)

if __name__ == "__main__":
    detect_anomalies_and_explain()
