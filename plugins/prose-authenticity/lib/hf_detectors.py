#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
HF detector wrapper. Loads detectors per detectors.yaml and runs
inference on raw text. Returns per-detector p(AI) score (mean across
sliding-window chunks).

Usage (from run_detectors.py):
    from hf_detectors import score_text_all
    results = score_text_all(text, config)

Check that the hf tier can run (prints True or False):
    uv run --with torch==2.15.0 --with transformers==5.22.2 ${CLAUDE_PLUGIN_ROOT}/lib/hf_detectors.py
"""

import os
import warnings

warnings.filterwarnings("ignore")
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    import torch  # noqa: F401,E402 — availability probe; env vars above must precede import
    import transformers  # noqa: F401,E402
    _HF_AVAILABLE = True
except ImportError:
    _HF_AVAILABLE = False


def available():
    """True when the optional hf tier can run (torch + transformers installed)."""
    return _HF_AVAILABLE


def chunks_for(text, tokenizer, max_len=400, stride=50):
    ids = tokenizer.encode(text, add_special_tokens=False, truncation=False)
    if not ids:
        return []
    if len(ids) <= max_len:
        return [text]
    chunks = []
    pos = 0
    while pos < len(ids):
        end = min(pos + max_len, len(ids))
        chunk_ids = ids[pos:end]
        chunks.append(tokenizer.decode(chunk_ids, skip_special_tokens=True))
        if end == len(ids):
            break
        pos += max_len - stride
    return chunks


def score_text(text, tokenizer, model, ai_idx, max_len, stride):
    import torch
    chunks = chunks_for(text, tokenizer, max_len, stride)
    if not chunks:
        return None, 0
    probs = []
    model.eval()
    with torch.no_grad():
        for c in chunks:
            inputs = tokenizer(c, return_tensors="pt", truncation=True, max_length=512)
            outputs = model(**inputs)
            probs_chunk = torch.nn.functional.softmax(outputs.logits, dim=-1)
            if probs_chunk.shape[-1] <= ai_idx:
                continue
            probs.append(probs_chunk[0, ai_idx].item())
    if not probs:
        return None, 0
    return sum(probs) / len(probs), len(chunks)


def load_detector(name, allow_mismatched=False):
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    try:
        tok = AutoTokenizer.from_pretrained(name)
        model = AutoModelForSequenceClassification.from_pretrained(
            name, ignore_mismatched_sizes=allow_mismatched
        )
        return tok, model, None
    except Exception as e:
        return None, None, str(e)[:300]


def score_text_all(text, config):
    """
    text: raw text to score
    config: dict with 'detectors' (list of {id, ai_label_idx, status, ...})
            and 'inference' (chunk_token_max, chunk_stride)
    Returns: list of {detector_id, score, n_chunks, error}
    """
    if not _HF_AVAILABLE:
        return [{"detector_id": d["id"], "status": "UNAVAILABLE",
                 "reason": "torch/transformers not installed", "score": None}
                for d in config.get("detectors", []) if d.get("status") == "active"]

    results = []
    inf = config.get("inference", {})
    max_len = inf.get("chunk_token_max", 400)
    stride = inf.get("chunk_stride", 50)

    for d in config["detectors"]:
        if d.get("status") != "active":
            continue
        tok, model, err = load_detector(d["id"])
        if tok is None:
            results.append({
                "detector_id": d["id"],
                "score": None,
                "n_chunks": 0,
                "error": err,
                "baseline_fpr": d.get("baseline_fpr_on_pe_writing"),
            })
            continue
        score, n_chunks = score_text(text, tok, model, d["ai_label_idx"], max_len, stride)
        results.append({
            "detector_id": d["id"],
            "score": score,
            "n_chunks": n_chunks,
            "error": None,
            "baseline_fpr": d.get("baseline_fpr_on_pe_writing"),
            "labels": getattr(model.config, "id2label", None),
        })
        del model, tok
    return results


if __name__ == "__main__":
    print(available())
