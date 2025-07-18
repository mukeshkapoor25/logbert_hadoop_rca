import sys
import os
sys.path.append('../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ast
import torch
import pandas as pd
import numpy as np
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM
from torch.utils.data import DataLoader

from bert_pytorch.dataset import LogDataset, WordVocab
from bert_pytorch.model.bert import BERT
from bert_pytorch.model.log_model import BERTLog

# === CONFIG ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_DIR = os.path.join(BASE_DIR, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')
PARAMS_FILE = os.path.join(OUTPUT_DIR, "bert", "parameters.txt")
CENTER_PATH = os.path.join(OUTPUT_DIR, "bert", "best_center.pt")
TEMPLATE_FILE = os.path.join(OUTPUT_DIR, "combined_hadoop.log_templates.csv")
SEQUENCE_FILE = os.path.join(OUTPUT_DIR, "rca_abnormal_sequence.csv")
TRAIN_FILE = os.path.join(OUTPUT_DIR, "train")

TOP_EVENTS = 5
MAX_RCA_TOKENS = 200
MISTRAL_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

# === Load parameters.txt ===
def load_parameters(param_path):
    options = {}
    with open(param_path, 'r') as f:
        for line in f:
            if ':' not in line:
                continue
            key, val = line.strip().split(':', 1)
            key = key.strip()
            val = val.strip()
            if val.lower() == 'true':
                val = True
            elif val.lower() == 'false':
                val = False
            elif val.lower() == 'none':
                val = None
            else:
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        pass
            options[key] = val
    print(options)
    return options

options = load_parameters(PARAMS_FILE)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
options["device"] = device
token = "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"
cache_dir = "/content/drive/MyDrive/hf_cache"
print("\n🧠 Loading Mistral-7B...")
tokenizer = AutoTokenizer.from_pretrained(MISTRAL_MODEL,token=token,cache_dir=cache_dir)
model_mistral = AutoModelForCausalLM.from_pretrained(MISTRAL_MODEL, torch_dtype=torch.float32, token=token,cache_dir=cache_dir).to(device)
model_mistral.eval()

def call_mistral(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model_mistral.generate(
        **inputs,
        max_length=inputs['input_ids'].shape[1] + MAX_RCA_TOKENS,
        do_sample=True,
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

def load_train_scores(model, vocab, center):
    sequences = []
    with open(TRAIN_FILE, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            if len(tokens) >= options["min_len"]:
                sequences.append(tokens)

    dummy_times = [[0] * len(seq) for seq in sequences]
    dataset = LogDataset(sequences, dummy_times, vocab,
                         seq_len=options["seq_len"],
                         on_memory=True,
                         mask_ratio=options["mask_ratio"])

    loader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=dataset.collate_fn)
    model.eval()
    train_scores = []
    with torch.no_grad():
        for batch in tqdm(loader, desc="Computing train scores"):
            batch = {k: v.to(device) for k, v in batch.items()}
            output = model(batch["bert_input"], batch["time_input"])
            cls_output = output["cls_output"]
            dist = compute_distance_to_center(cls_output, center)
            train_scores.append(dist)

    return train_scores

def detect_anomalies_and_explain():
    vocab = WordVocab.load_vocab(options["vocab_path"])
    center_dict = torch.load(CENTER_PATH, map_location=device, weights_only=False)
    center = center_dict["center"] if isinstance(center_dict, dict) else center_dict

    print("\n📅 Loading vocab and sequences...")
    sequences_df = pd.read_csv(SEQUENCE_FILE)
    if 'AppId' not in sequences_df.columns or 'EventSequence' not in sequences_df.columns:
        raise KeyError("Required columns 'AppId' and 'EventSequence' not found in the CSV.")

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
    dataset = LogDataset(data, dummy_times, vocab,
                         seq_len=options["seq_len"],
                         on_memory=True,
                         mask_ratio=options["mask_ratio"])

    test_loader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=dataset.collate_fn)

    print("📦 Loading LogBERT model...")
    try:
        model = torch.load(options["model_path"], map_location=device, weights_only=False)
    except Exception as e:
        print(f"Fallback to state_dict loading due to: {e}")
        bert = BERT(
            vocab_size=len(vocab),
            hidden=options["hidden"],
            n_layers=options["layers"],
            attn_heads=options["attn_heads"],
            max_len=options["max_len"]
        )
        model = BERTLog(bert, vocab_size=len(vocab)).to(device)
        model.load_state_dict(torch.load(options["model_path"], map_location=device, weights_only=False))

    model.to(device)

    train_scores = load_train_scores(model, vocab, center)
    mean, std = np.mean(train_scores), np.std(train_scores)
    # threshold = mean + 2 * std
    # print(f"\n📊 Threshold (mean + 2*std): {threshold:.4f}\n")

    templates = pd.read_csv(TEMPLATE_FILE)

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
            app_id = app_ids[i]
            seq = data[i]

            print(f"AppId: {app_id} | Score: {score:.4f} | z: {z_score:.2f} | Undetected: {undetected_ratio:.2f}", end='')

            if not (is_deep or is_logkey):
                print(" | 🟢 Status: Normal\n")
                continue

            print(" | 🔴 Status: Abnormal")

            event_ids = seq[:TOP_EVENTS]
            event_templates = []
            for eid in event_ids:
                tpl = templates.loc[templates["EventId"] == eid, "EventTemplate"].values
                event_templates.append(tpl[0] if len(tpl) > 0 else f"[Missing Event {eid}]")

            prompt = generate_prompt(event_templates)
            explanation = call_mistral(prompt)

            print("🧰 Events:")
            for j, evt in enumerate(event_templates, 1):
                print(f"   {j}. {evt}")
            print("\n🧠 Mistral-7B RCA Explanation:")
            print(explanation)
            print("-" * 60)

if __name__ == "__main__":
    detect_anomalies_and_explain()
