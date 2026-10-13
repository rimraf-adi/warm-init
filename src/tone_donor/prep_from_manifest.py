"""Cache frozen-encoder features from the materialised manifests (no streaming).

    BACKBONE=multi python -m tone_donor.prep_from_manifest dogri v2 /home/vnit/data/dogri_multi_v2
Reads data/manifests/indicvoices_<lang>_<tag>_{dev,test,train}.jsonl and data/audio/...; writes dev.pt, test.pt, train.pt
with the same fields as prep_features (feat fp16 [T, D], text, speaker, dur) plus gender.
"""
import json
import os
import sys

import soundfile as sf
import torch

from tone_donor.prep_features import backbone_name, encode, load_encoder
from tone_donor.text import normalize
from tone_donor.vaani_stream import _load_dotenv


def run(lang, tag, out):
    _load_dotenv()
    os.makedirs(out, exist_ok=True)
    model = load_encoder(os.environ["HF_TOKEN"])
    name = f"indicvoices_{lang}" + ("" if tag == "v1" else f"_{tag}")
    for split in ("dev", "test", "train"):
        rows = [json.loads(l) for l in open(f"data/manifests/{name}_{split}.jsonl", encoding="utf-8")]
        store, buf = [], []
        for r in rows:
            w = torch.from_numpy(sf.read(f"data/{r['audio']}", dtype="float32")[0])
            buf.append((r, w))
            if len(buf) == 8:
                for (rr, _), f in zip(buf, encode(model, [b[1] for b in buf])):
                    store.append({"feat": f, "text": normalize(rr["text"], drop_apos=True), "speaker": str(rr["speaker_id"]),
                                  "dur": rr["audio_s"], "gender": rr["gender"]})
                buf = []
        if buf:
            for (rr, _), f in zip(buf, encode(model, [b[1] for b in buf])):
                store.append({"feat": f, "text": normalize(rr["text"], drop_apos=True), "speaker": str(rr["speaker_id"]),
                              "dur": rr["audio_s"], "gender": rr["gender"]})
        torch.save(store, os.path.join(out, f"{split}.pt"))
        print(split, len(store), "utts", round(sum(s["dur"] for s in store) / 3600, 3), "h",
              len({s["speaker"] for s in store}), "speakers", f"backbone={backbone_name()}", flush=True)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3])
