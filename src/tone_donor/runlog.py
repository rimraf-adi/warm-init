"""Append-only results log: one JSON line per run in results/runs.jsonl.

Every record is self-describing: git commit, dirty flag, config hash, library
versions, host, and paths to artifacts (hypotheses, predictions, checkpoints).
Never edit or delete lines; add a new run with notes="supersedes <run_id>".
"""
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

LOG = Path("results/runs.jsonl")
REQUIRED = ("stage", "target", "init")
FIELDS = [
    "run_id", "time", "stage", "hypothesis", "target", "donor", "init", "budget_h", "seed",
    "backbone", "split", "n_utts", "n_speakers", "wer", "cer", "tone_cer", "tone_chars",
    "aspirate_cer", "plain_cer", "ci_low", "ci_high", "status", "config", "artifacts",
    "notes", "git_commit", "git_dirty", "config_hash", "env", "host",
]


def _git(*a):
    try:
        return subprocess.check_output(["git", *a], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def _env():
    out = {"python": platform.python_version()}
    for mod in ("torch", "nemo", "datasets", "numpy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            pass
    return out


def log_run(**kw):
    missing = [f for f in REQUIRED if kw.get(f) is None]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    unknown = set(kw) - set(FIELDS)
    if unknown:
        raise ValueError(f"unknown fields: {sorted(unknown)}")
    rec = {f: kw.get(f) for f in FIELDS}
    rec["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["status"] = rec["status"] or "done"
    rec["config"] = rec["config"] or {}
    rec["config_hash"] = hashlib.sha256(
        json.dumps(rec["config"], sort_keys=True, default=str).encode()).hexdigest()[:12]
    rec["git_commit"] = _git("rev-parse", "--short", "HEAD")
    rec["git_dirty"] = bool(_git("status", "--porcelain"))
    rec["env"] = _env()
    rec["host"] = platform.node()
    rec["run_id"] = rec["run_id"] or f"{kw['stage']}-{kw['target']}-{kw['init']}-{int(time.time())}"
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    return rec["run_id"]


def read_runs():
    if not LOG.exists():
        return []
    return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
