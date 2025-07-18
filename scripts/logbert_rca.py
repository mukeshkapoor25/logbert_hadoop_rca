import sys
import os
sys.path.append('../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
import tqdm
from torch.utils.data import DataLoader
from bert_pytorch.dataset import LogDataset, WordVocab
from bert_pytorch.model.log_model import BERTLog  # ✅ Correct model class
from transformers import AutoTokenizer, AutoModelForCausalLM


def load_model(model_path, options):
    model = torch.load(model_path, map_location=options["device"])  # ✅ loads BERTLog instance
    model.eval()
    return model


def calculate_distance(center, vectors):
    return torch.norm(vectors - center, dim=1)


def explain_with_llm(log_keys):
    text = "The system detected the following log events as most responsible for the anomaly:\n"
    text += "\n".join(f"- {key}" for key in log_keys)
    text += "\n\nExplain what could be the root cause or issue behind these logs in simple language."

    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2")

    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    outputs = model.generate(**inputs, max_new_tokens=100, do_sample=True)

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


def do_rca_with_explanation(options):
    # Load vocab
    vocab = WordVocab.load_vocab(options["vocab_path"])

    # Load trained model (BERTLog)
    model = load_model(options["model_path"], options)
    model.to(options["device"])

    # Load center and radius
    center_path = os.path.join(options["model_dir"], "best_center.pt")
    center_data = torch.load(center_path, map_location=options["device"])
    center = center_data["center"]
    radius = center_data["radius"]
    print(f"✅ Loaded center. Radius = {radius:.4f}")

    # Load test sequences
    test_file = os.path.join(options["output_dir"], "rca_abnormal")
    with open(test_file, "r") as f:
        lines = [line.strip().split() for line in f if line.strip()]
    sequences = [[vocab.stoi[token] if token in vocab.stoi else vocab.unk_index for token in line] for line in lines]

    dummy_times = [[0] * len(seq) for seq in sequences]

    # Dataset & DataLoader
    test_dataset = LogDataset(sequences, dummy_times, vocab,
                              seq_len=options["seq_len"],
                              on_memory=True, mask_ratio=options["mask_ratio"])
    test_loader = DataLoader(test_dataset, batch_size=1,
                             collate_fn=test_dataset.collate_fn,
                             shuffle=False)

    for i, data in tqdm.tqdm(enumerate(test_loader), total=len(test_loader)):
        data = {k: v.to(options["device"]) for k, v in data.items()}

        with torch.no_grad():
            output = model(x=data["bert_input"], time_info=data["time_input"])

            cls_vector = output["cls_output"]               # shape: [1, hidden]
            token_embeddings = output["token_embeddings"]   # shape: [seq_len, hidden/vocab]

            dist = calculate_distance(center, cls_vector)[0].item()
            print(f"\n🧪 Sample {i+1}: Distance = {dist:.4f} | Threshold = {radius:.4f}")
            if dist <= radius:
                print("✅ Normal log sequence")
                continue

            print("🚨 Anomaly Detected")

            token_dists = torch.norm(token_embeddings - center, dim=1)
            topk = torch.topk(token_dists, k=3)
            top_token_ids = [data["bert_input"][0][i].item() for i in topk.indices]
            top_log_keys = [vocab.itos[i] for i in top_token_ids]

            print("🔍 Top contributing log keys:", top_log_keys)

            explanation = explain_with_llm(top_log_keys)
            print("\n🧠 LLM Explanation:\n", explanation)


# === Options ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_DIR = os.path.join(BASE_DIR, 'AI_MODELS', 'trained_models', 'Hadoop_logbert')

options = {
    "device": torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    "output_dir": OUTPUT_DIR,
    "model_dir": os.path.join(OUTPUT_DIR, "bert"),
    "model_path": os.path.join(OUTPUT_DIR, "bert", "best_bert.pth"),
    "vocab_path": os.path.join(OUTPUT_DIR, "vocab.pkl"),
    "seq_len": 256,
    "max_len": 256,
    "hidden": 256,
    "layers": 4,
    "attn_heads": 8,
    "is_logkey": True,
    "is_time": False,
    "mask_ratio": 0.65,
}

if __name__ == "__main__":
    do_rca_with_explanation(options)
