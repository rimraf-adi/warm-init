"""Materialise the IndicVoices splits used in the experiments: manifests (tracked) + 16 kHz audio (gitignored).

Rules (same as prep_features):
  dev/test : IndicVoices `valid`; speakers sorted by id, alternating -> dev, test.
  train    : IndicVoices `train` streamed in shard order; speakers present in valid are skipped;
             whole speakers are taken until the budget is reached.
  kept rows: normalized text non-empty and 0.5 s <= audio duration <= 30 s.
Manifests keep every text field so the choice of scoring field stays visible.

    python -m tone_donor.make_splits dogri 5.0 data
Writes  data/manifests/indicvoices_<lang>_{dev,test,train}.jsonl, data/manifests/indicvoices_<lang>_splits.json,
        data/audio/indicvoices_<lang>/<split>/<row>.wav
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


def run(lang, train_hours, out):
    _load_dotenv()
    tok = os.environ["HF_TOKEN"]
    rev = HfApi(token=tok).dataset_info("ai4bharat/IndicVoices").sha
    man_dir = os.path.join(out, "manifests")
    os.makedirs(man_dir, exist_ok=True)

    def stream(split):
        d = load_dataset("ai4bharat/IndicVoices", lang, split=split, streaming=True, token=tok)
        return d.cast_column("audio_filepath", Audio(decode=False))

    def keep(ex, w):
        t = normalize(ex["text"], drop_apos=True)
        return bool(t) and 0.5 <= len(w) / 16000 <= 30

    def write(split_name, rows):
        d = os.path.join(out, "audio", f"indicvoices_{lang}", split_name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(man_dir, f"indicvoices_{lang}_{split_name}.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                sf.write(os.path.join(d, f"{r['hf_row']}.wav"), r.pop("_wav"), 16000)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def row(ex, i, split, w):
        r = {k: ex.get(k) for k in META}
        r.update(hf_split=split, hf_row=i, audio_s=round(len(w) / 16000, 3), _wav=w,
                 audio=f"audio/indicvoices_{lang}/{{split}}/{i}.wav")
        return r

    valid = []
    for i, ex in enumerate(stream("valid")):
        w, sr = audio_16k(ex)
        if keep(ex, w):
            r = row(ex, i, "valid", w)
            r["orig_sr"] = sr
            valid.append(r)
    spk = sorted({r["speaker_id"] for r in valid})
    dev_s, test_s = set(spk[0::2]), set(spk[1::2])
    for name, S in (("dev", dev_s), ("test", test_s)):
        rows = [r for r in valid if r["speaker_id"] in S]
        for r in rows:
            r["audio"] = r["audio"].format(split=name)
        write(name, rows)
        print(name, len(rows), "utts", round(sum(r["audio_s"] for r in rows) / 3600, 3), "h",
              len({r["speaker_id"] for r in rows}), "speakers", flush=True)
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
        r = row(ex, i, "train", w)
        r["audio"] = r["audio"].format(split="train")
        r["orig_sr"] = sr
        r["train_order"] = len(train)
        train.append(r)
        hours += len(w) / 16000 / 3600
        cur = ex["speaker_id"]
    write("train", train)
    print("train", len(train), "utts", round(hours, 3), "h", len({r["speaker_id"] for r in train}), "speakers",
          "overlap with dev/test:", len({r["speaker_id"] for r in train} & held), flush=True)

    json.dump({"dataset": "ai4bharat/IndicVoices", "config": lang, "revision": rev,
               "rules": __doc__.split("Rules")[1].split("Manifests keep")[0].strip(),
               "counts": {"dev": sum(1 for r in valid if r["speaker_id"] in dev_s),
                          "test": sum(1 for r in valid if r["speaker_id"] in test_s), "train": len(train)},
               "train_budget_hours": train_hours, "train_hours": round(hours, 3),
               "dev_speakers": sorted(dev_s), "test_speakers": sorted(test_s)},
              open(os.path.join(man_dir, f"indicvoices_{lang}_splits.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    run(sys.argv[1], float(sys.argv[2]), sys.argv[3])
