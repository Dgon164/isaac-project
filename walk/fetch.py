#!/usr/bin/env python3
"""fetch.py -- the 2026-09-14 download list (see docs/DOWNLOADS_2026-09-14.md).
Run once, while the bandwidth is there. Everything lands in the hugging
face cache; a second run skips what is already complete."""
import subprocess
import sys
import time

MODELS = [
    "deepset/roberta-base-squad2",
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "bert-base-uncased",
    "microsoft/deberta-v3-base",
    "deepset/deberta-v3-large-squad2",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "microsoft/Phi-4-mini-instruct",
    "Qwen/Qwen2.5-14B-Instruct",
]
DATASETS = [
    ("rajpurkar/squad", None), ("rajpurkar/squad_v2", None),
    ("openai/gsm8k", "main"), ("ChilleD/SVAMP", None), ("EleutherAI/asdiv", None),
    ("ucinlp/drop", None), ("google/boolq", None),
    ("allenai/ai2_arc", "ARC-Challenge"), ("allenai/ai2_arc", "ARC-Easy"),
    ("allenai/sciq", None), ("allenai/openbookqa", "main"),
    ("google-research-datasets/mbpp", "full"), ("openai/openai_humaneval", None),
    ("hotpotqa/hotpot_qa", "distractor"),
    ("bigcode/the-stack-smol", None),
    ("conceptnet5", "conceptnet5"),
]


def main():
    t0 = time.time()
    print("pip: sentence-transformers", flush=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"])
    from huggingface_hub import snapshot_download
    for m in MODELS:
        t = time.time()
        try:
            p = snapshot_download(m, allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model",
                                                     "*.py", "tokenizer*", "*.tiktoken", "merges.txt"])
            print("model ok   %-45s %5.0fs  %s" % (m, time.time() - t, p), flush=True)
        except Exception as e:
            print("model FAIL %-45s %s" % (m, str(e)[:120]), flush=True)
    from datasets import load_dataset
    for name, cfg in DATASETS:
        t = time.time()
        try:
            d = load_dataset(name, cfg) if cfg else load_dataset(name)
            print("data ok    %-45s %5.0fs  %s" % (name + (":" + cfg if cfg else ""), time.time() - t,
                                                  {k: len(v) for k, v in d.items()}), flush=True)
        except Exception as e:
            print("data FAIL  %-45s %s" % (name, str(e)[:120]), flush=True)
    print("done in %.0f min" % ((time.time() - t0) / 60), flush=True)


if __name__ == "__main__":
    main()
