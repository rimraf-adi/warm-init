"""Audit IndicVoices Dogri: what the text fields are, how splits compare, how my train sample is drawn.
    uv run python scripts/audit_indicvoices.py
"""
import collections
import os
import re
import statistics

from datasets import Audio, load_dataset

from tone_donor.text import normalize
from tone_donor.vaani_stream import _load_dotenv

_load_dotenv()
tok = os.environ["HF_TOKEN"]


def rows(split, n):
    d = load_dataset("ai4bharat/IndicVoices", "dogri", split=split, streaming=True, token=tok)
    d = d.cast_column("audio_filepath", Audio(decode=False))
    for i, ex in enumerate(d):
        if i >= n:
            break
        ex = dict(ex)
        ex.pop("audio_filepath")
        yield ex


valid = list(rows("valid", 10_000))
train = list(rows("train", 2500))
print("valid rows", len(valid), "train rows sampled", len(train))
print("fields:", sorted(valid[0].keys()))

# 1. How do the text fields differ?
fields = ["text", "verbatim", "normalized", "unsanitized_verbatim", "unsanitized_normalized"]
for f in fields:
    vals = [r.get(f) or "" for r in valid]
    chars = collections.Counter("".join(vals))
    odd = {c: n for c, n in chars.items() if not (c.isalnum() or c.isspace()) and ord(c) < 0x900 or c in "'ʼ"}
    print(f"[{f}] empty={sum(1 for v in vals if not v)} mean_len={statistics.mean(len(v) for v in vals):.1f} "
          f"non-alnum ascii/punct={dict(list(odd.items())[:10])}")
same = {f: sum(1 for r in valid if (r.get(f) or "") == (r.get("text") or "")) for f in fields}
print("rows identical to `text`:", same)
for r in valid[:3]:
    print("--- example")
    for f in fields:
        print(f"  {f:24s}: {(r.get(f) or '')[:110]}")

# 2. Duration
for name, rs in (("valid", valid), ("train sample", train)):
    d = [r["duration"] for r in rs]
    print(f"{name}: dur mean {statistics.mean(d):.1f}s min {min(d):.1f} max {max(d):.1f}; "
          f"outside [0.5,30]: {sum(1 for x in d if x < 0.5 or x > 30)}; empty text: {sum(1 for r in rs if not r['text'])}")

# 3. Speakers and composition
vs, ts = {r["speaker_id"] for r in valid}, {r["speaker_id"] for r in train}
print("speakers valid", len(vs), "train sample", len(ts), "overlap", len(vs & ts))
for col in ("scenario", "task_name", "gender", "age_group"):
    cv = collections.Counter(r.get(col) for r in valid)
    ct = collections.Counter(r.get(col) for r in train)
    print(f"[{col}] valid {dict(cv.most_common(5))} | train-sample {dict(ct.most_common(5))}")
runs = []
prev = None
for r in train:
    if r["speaker_id"] != prev:
        runs.append(1)
        prev = r["speaker_id"]
    else:
        runs[-1] += 1
print("train sample: speaker blocks", len(runs), "mean utts per consecutive block", round(statistics.mean(runs), 1))
