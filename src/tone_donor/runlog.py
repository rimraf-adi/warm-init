"""Append-only results log: one JSON line per run in results/runs.jsonl."""
import json
import time
from pathlib import Path

LOG = Path("results/runs.jsonl")
FIELDS = ["run_id", "stage", "target", "donor", "init", "budget_h", "seed", "backbone",
          "split", "wer", "cer", "tone_cer", "tone_chars", "n_utts", "config", "notes", "time"]


def log_run(**kw):
    missing = [f for f in ("stage", "target", "init") if f not in kw]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    rec = {f: kw.get(f) for f in FIELDS}
    rec["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["run_id"] = rec["run_id"] or f"{kw['stage']}-{kw['target']}-{kw['init']}-{int(time.time())}"
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec["run_id"]
