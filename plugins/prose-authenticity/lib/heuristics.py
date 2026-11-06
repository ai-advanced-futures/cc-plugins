#!/usr/bin/env python3
"""
Stdlib-only heuristic detector. Takes raw text; returns metrics dict.
Used by run_ai_check.py per zone.
"""

import re
import statistics

MODIFIERS = {
    "very", "really", "highly", "significantly", "substantially", "notably",
    "essentially", "fundamentally", "remarkably", "particularly", "extensively",
    "considerably", "exceptionally", "tremendously", "incredibly", "vastly",
    "extremely", "deeply", "broadly", "comprehensively", "robustly",
    "demonstrably", "meaningfully", "appreciably",
}

HEDGES = {
    "may", "might", "could", "perhaps", "possibly", "potentially",
    "likely", "presumably", "arguably", "apparently", "seemingly", "tends",
}

CONNECTORS_INITIAL = {
    "however", "moreover", "furthermore", "additionally", "specifically",
    "notably", "importantly", "crucially", "fundamentally", "essentially",
    "consequently", "therefore", "thus", "hence", "accordingly",
}

PAT_PHRASES = [
    r"it is worth noting",
    r"it'?s important to",
    r"it'?s crucial to",
    r"in conclusion",
    r"in summary",
    r"not only [a-z]+ but also",
    r"not just [a-z]+,? (?:but|it'?s)",
    r"on the one hand",
    r"on the other hand",
    r"at the end of the day",
    r"first and foremost",
    r"plays? a (?:crucial|key|vital|critical) role",
    r"navigate the complex",
    r"in today'?s (?:rapidly|fast)",
    r"in the realm of",
]

WEIGHTS = {"b": 0.20, "t": 0.10, "m": 0.15, "h": 0.10, "c": 0.15, "e": 0.15, "p": 0.15}

L048_DASH_RE = re.compile(r"\bfrom\b[^.;:\n]{0,30}[–—]")  # L-048: en/em dash shortly after "from"


def strip_markdown(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---+\s*$', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'\|', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def split_sentences(text):
    text = re.sub(r'\s+', ' ', text).strip()
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z\(])', text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 4]


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", text.lower())


def burstiness(sent_lengths):
    if len(sent_lengths) < 2:
        return 0.0
    return statistics.stdev(sent_lengths) / max(statistics.mean(sent_lengths), 1)


def ttr(tokens):
    return len(set(tokens)) / max(len(tokens), 1)


def per_1000(count, wordcount):
    return (count / max(wordcount, 1)) * 1000


def composite_ai_score(metrics):
    b = metrics["burstiness"]
    burst_score = max(0, min(100, (0.6 - b) / 0.3 * 100))
    t = metrics["ttr"]
    ttr_score = max(0, min(100, (0.55 - t) / 0.25 * 100))
    m = metrics["modifier_per_1000"]
    mod_score = max(0, min(100, (m - 8) / 17 * 100))
    h = metrics["hedge_per_1000"]
    hedge_score = max(0, min(100, (h - 5) / 13 * 100))
    c = metrics["initial_connector_freq"]
    conn_score = max(0, min(100, (c - 0.03) / 0.12 * 100))
    e = metrics["emdash_per_1000"]
    em_score = max(0, min(100, (e - 2) / 18 * 100))
    p = metrics["pat_phrase_hits"]
    pat_score = max(0, min(100, p / 5 * 100))

    composite = (
        burst_score * WEIGHTS["b"] + ttr_score * WEIGHTS["t"]
        + mod_score * WEIGHTS["m"] + hedge_score * WEIGHTS["h"]
        + conn_score * WEIGHTS["c"] + em_score * WEIGHTS["e"]
        + pat_score * WEIGHTS["p"]
    )
    return {
        "composite_ai_score": round(composite, 1),
        "subscores": {
            "burstiness": round(burst_score, 1),
            "ttr": round(ttr_score, 1),
            "modifier": round(mod_score, 1),
            "hedge": round(hedge_score, 1),
            "connector": round(conn_score, 1),
            "emdash": round(em_score, 1),
            "patphrase": round(pat_score, 1),
        },
    }


def analyze(raw_text):
    text = strip_markdown(raw_text)
    sents = split_sentences(text)
    sent_lengths = [len(words(s)) for s in sents]
    tokens = words(text)

    emdash_count = text.count("—") + text.count("--")
    mod_count = sum(1 for t in tokens if t in MODIFIERS)
    hedge_count = sum(1 for t in tokens if t in HEDGES)

    init_conn = 0
    for s in sents:
        m = re.match(r'^([A-Za-z]+)', s)
        if m and m.group(1).lower() in CONNECTORS_INITIAL:
            init_conn += 1

    pat_count = 0
    tl = text.lower()
    for pat in PAT_PHRASES:
        pat_count += len(re.findall(pat, tl))

    wc = len(tokens)
    metrics = {
        "wordcount": wc,
        "sentence_count": len(sents),
        "sentence_length_mean": round(statistics.mean(sent_lengths), 1) if sent_lengths else 0,
        "sentence_length_std": round(statistics.stdev(sent_lengths), 1) if len(sent_lengths) > 1 else 0,
        "burstiness": round(burstiness(sent_lengths), 3),
        "ttr": round(ttr(tokens), 3),
        "modifier_hits": mod_count,
        "modifier_per_1000": round(per_1000(mod_count, wc), 1),
        "hedge_hits": hedge_count,
        "hedge_per_1000": round(per_1000(hedge_count, wc), 1),
        "initial_connector_hits": init_conn,
        "initial_connector_freq": round(init_conn / max(len(sents), 1), 3),
        "emdash_count": emdash_count,
        "emdash_per_1000": round(per_1000(emdash_count, wc), 1),
        "pat_phrase_hits": pat_count,
    }
    metrics.update(composite_ai_score(metrics))
    return metrics


def locate_hits(raw_text):
    """Line-level tell locations. Port change vs. the original toolkit, which
    returned only aggregates: the humanizer needs to know WHERE to rewrite."""
    hits = []
    for lineno, line in enumerate(raw_text.splitlines(), 1):
        ll = line.lower()
        for pat in PAT_PHRASES:
            for m in re.finditer(pat, ll):
                hits.append({"line": lineno, "signal": "pat_phrase", "match": m.group(0)})
        for m in re.finditer(r"—|--", line):
            hits.append({"line": lineno, "signal": "emdash", "match": m.group(0)})
        m = L048_DASH_RE.search(ll)
        if m:
            hits.append({"line": lineno, "signal": "l048_dash_after_from", "match": m.group(0)})
        for t in words(line):
            if t in MODIFIERS:
                hits.append({"line": lineno, "signal": "modifier", "match": t})
            elif t in HEDGES:
                hits.append({"line": lineno, "signal": "hedge", "match": t})
        first = re.match(r"^\s*([A-Za-z]+)", line)
        if first and first.group(1).lower() in CONNECTORS_INITIAL:
            hits.append({"line": lineno, "signal": "initial_connector", "match": first.group(1)})
    return hits


def analyze_with_hits(raw_text):
    result = analyze(raw_text)
    result["hits"] = locate_hits(raw_text)
    return result


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(description="Stylometric AI-tell scorer (stdlib only)")
    ap.add_argument("path", help="Text/markdown file to score")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    from pathlib import Path as _P

    r = analyze_with_hits(_P(args.path).read_text())
    if args.json:
        print(_json.dumps(r, indent=2))
    else:
        print(f"composite_ai_score: {r['composite_ai_score']}/100 (lower = more human)")
        print(f"hits: {len(r['hits'])} line-level tells")
