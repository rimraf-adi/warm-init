"""Materialise the IndicVoices splits used in the experiments: manifests (tracked) + 16 kHz audio (gitignored).

Rules:
  dev/test : IndicVoices `valid`. tag v1: speakers sorted by id, alternating -> dev, test.
             tag v2: the same alternation inside each gender, so dev and test have the same gender mix.
  train    : IndicVoices `train` streamed in shard order; speakers present in valid are skipped;
             whole speakers are taken until the budget is reached. For v2 the pool is large (about 15 h) and
             experiments draw random speaker subsets from it, so seeds vary the data as well.
  kept rows: normalized text non-empty and 0.5 s <= audio duration <= 30 s.
Manifests keep every text field so the choice of scoring field stays visible.

    python -m tone_donor.make_splits dogri 15.0 data v2
Writes  data/manifests/indicvoices_<lang>_<tag>_{dev,test,train}.jsonl and ..._splits.json (tag v1: no tag in the name),
        data/audio/indicvoices_<lang>_<tag>/<split>/<row>.wav
"""
import io
import json
import os
import sys

import soundfile as sf
import torch
import torchaudio
from datasets import Audio, load_dataset
from huggingface_hub import HfApi

from tone_donor.text import normalize
from tone_donor.vaani_stream import _load_dotenv

META = ["text", "verbatim", "normalized", "unsanitized_verbatim", "unsanitized_normalized", "speaker_id",
        "scenario", "task_name", "gender", "age_group", "duration", "lang"]


def audio_16k(ex):
    wav, sr = sf.read(io.BytesIO(ex["audio_filepath"]["bytes"]), dtype="float32", always_2d=True)
    w = torch.from_numpy(wav.mean(1))
    if sr != 16000:
        w = torchaudio.functional.resample(w, sr, 16000)
    return w.numpy(), sr


def split_speakers(valid, tag):
    spk = sorted({r["speaker_id"] for r in valid})
    if tag == "v1":
        return set(spk[0::2]), set(spk[1::2])
    gender = {}
    for r in valid:
        gender.setdefault(r["speaker_id"], str(r.get("gender")))
    dev_s, test_s = set(), set()
    for g in sorted(set(gender.values())):
        ss = sorted(s for s in spk if gender[s] == g)
        dev_s |= set(ss[0::2])
        test_s |= set(ss[1::2])
    return dev_s, test_s


def run(lang, train_hours, out, tag="v2"):
    _load_dotenv()
    tok = os.environ["HF_TOKEN"]
    rev = HfApi(token=tok).dataset_info("ai4bharat/IndicVoices").sha
    man_dir = os.path.join(out, "manifests")
    os.makedirs(man_dir, exist_ok=True)
    name = f"indicvoices_{lang}" + ("" if tag == "v1" else f"_{tag}")

    def stream(split):
        d = load_dataset("ai4bharat/IndicVoices", lang, split=split, streaming=True, token=tok)
        return d.cast_column("audio_filepath", Audio(decode=False))

    def keep(ex, w):
        t = normalize(ex["text"], drop_apos=True)
        return bool(t) and 0.5 <= len(w) / 16000 <= 30

    def write(split_name, rows):
        d = os.path.join(out, "audio", name, split_name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(man_dir, f"{name}_{split_name}.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                sf.write(os.path.join(d, f"{r['hf_row']}.wav"), r.pop("_wav"), 16000)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def row(ex, i, split, w, sr):
        r = {k: ex.get(k) for k in META}
        r.update(hf_split=split, hf_row=i, audio_s=round(len(w) / 16000, 3), orig_sr=sr, _wav=w)
        return r

    valid = []
    for i, ex in enumerate(stream("valid")):
        w, sr = audio_16k(ex)
        if keep(ex, w):
            valid.append(row(ex, i, "valid", w, sr))
    dev_s, test_s = split_speakers(valid, tag)
    counts = {}
    for sname, S in (("dev", dev_s), ("test", test_s)):
        rows = [r for r in valid if r["speaker_id"] in S]
        for r in rows:
            r["audio"] = f"audio/{name}/{sname}/{r['hf_row']}.wav"
        write(sname, rows)
        counts[sname] = len(rows)
        g = {}
        for r in rows:
            g[r["gender"]] = g.get(r["gender"], 0) + 1
        print(sname, len(rows), "utts", round(sum(r["audio_s"] for r in rows) / 3600, 3), "h",
              len({r["speaker_id"] for r in rows}), "speakers", "gender", g, flush=True)
    held = dev_s | test_s

    train, hours, cur = [], 0.0, None
    for i, ex in enumerate(stream("train")):
        if ex["speaker_id"] in held:
            continue
        w, sr = audio_16k(ex)
        if not keep(ex, w):
            continue
        if hours >= train_hours and cur is not None and ex["speaker_id"] != cur:
            break
        r = row(ex, i, "train", w, sr)
        r["audio"] = f"audio/{name}/train/{i}.wav"
        r["train_order"] = len(train)
        train.append(r)
        hours += len(w) / 16000 / 3600
        cur = ex["speaker_id"]
    write("train", train)
    counts["train"] = len(train)
    g = {}
    for r in train:
        g[r["gender"]] = g.get(r["gender"], 0) + 1
    print("train", len(train), "utts", round(hours, 3), "h", len({r["speaker_id"] for r in train}), "speakers",
          "gender", g, "overlap with dev/test:", len({r["speaker_id"] for r in train} & held), flush=True)

    json.dump({"dataset": "ai4bharat/IndicVoices", "config": lang, "tag": tag, "revision": rev,
               "rules": __doc__.split("Rules:")[1].split("Manifests keep")[0].strip(),
               "counts": counts, "train_budget_hours": train_hours, "train_hours": round(hours, 3),
               "dev_speakers": sorted(dev_s), "test_speakers": sorted(test_s)},
              open(os.path.join(man_dir, f"{name}_splits.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    run(sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "v2")
