"""Phase 1 data: speaker-disjoint Dogri splits from IndicVoices plus cached frozen-encoder features.

Streams IndicVoices (no full download), resamples to 16 kHz, runs the frozen IndicConformer
encoder once, and stores fp16 features. Splits:
  dev/test: IndicVoices `valid`, divided by speaker (alternating over speakers sorted by id).
  train:    IndicVoices `train` streamed in shard order; speakers in valid are excluded;
            utterances are taken whole-speaker at a time, so budgets are nested and speaker-disjoint.
Apostrophe tone marks are dropped from text (they are <unk> in the IndicConformer vocabulary).

    python -m tone_donor.prep_features dogri doi 5.0 out_dir
"""
import io
import os
import sys
import time

import soundfile as sf
import torch
import torchaudio
from datasets import Audio, load_dataset
from huggingface_hub import hf_hub_download

from tone_donor.text import normalize
from tone_donor.vaani_stream import _load_dotenv


def backbone_name():
    return os.environ.get("BACKBONE", "hi")


def load_encoder(tok):
    """BACKBONE=hi: per-language Hindi checkpoint (115M encoder). BACKBONE=multi: multilingual
    ai4bharat/IndicConformer (628M params, 24 blocks, 22 languages)."""
    import nemo.collections.asr as nemo_asr
    if backbone_name() == "multi":
        p = hf_hub_download("ai4bharat/IndicConformer", "IndicConformer.nemo", token=tok)
    else:
        p = hf_hub_download("ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large",
                            "indicconformer_stt_hi_hybrid_rnnt_large.nemo", token=tok)
    m = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(p, map_location="cuda").eval()
    return m


@torch.no_grad()
def encode(model, wavs):
    lens = torch.tensor([len(w) for w in wavs], device="cuda")
    x = torch.nn.utils.rnn.pad_sequence(wavs, batch_first=True).cuda()
    feats, flen = model.preprocessor(input_signal=x, length=lens)
    enc, elen = model.encoder(audio_signal=feats, length=flen)
    return [enc[i, :, :elen[i]].T.half().cpu() for i in range(len(wavs))]


def utts(ds, tok_audio_col="audio_filepath"):
    for ex in ds:
        wav, sr = sf.read(io.BytesIO(ex[tok_audio_col]["bytes"]), dtype="float32", always_2d=True)
        wav = torch.from_numpy(wav.mean(1))
        if sr != 16000:
            wav = torchaudio.functional.resample(wav, sr, 16000)
        text = normalize(ex["text"], drop_apos=True)
        dur = len(wav) / 16000
        if text and 0.5 <= dur <= 30:
            yield {"wav": wav, "text": text, "speaker": str(ex["speaker_id"]), "dur": dur}


def run(iv_lang, out_dir, train_hours):
    _load_dotenv()
    tok = os.environ["HF_TOKEN"]
    os.makedirs(out_dir, exist_ok=True)
    model = load_encoder(tok)

    def load(split):
        d = load_dataset("ai4bharat/IndicVoices", iv_lang, split=split, streaming=True, token=tok)
        return d.cast_column("audio_filepath", Audio(decode=False))

    def flush(buf, store):
        for i in range(0, len(buf), 8):
            chunk = buf[i:i + 8]
            for c, f in zip(chunk, encode(model, [c["wav"] for c in chunk])):
                store.append({"feat": f, "text": c["text"], "speaker": c["speaker"], "dur": c["dur"]})

    # dev/test from valid, split by speaker
    valid = list(utts(load("valid")))
    spk = sorted({u["speaker"] for u in valid})
    dev_spk = set(spk[0::2]); test_spk = set(spk[1::2])
    print("valid utts", len(valid), "speakers", len(spk), flush=True)
    for name, S in (("dev", dev_spk), ("test", test_spk)):
        store = []
        flush([u for u in valid if u["speaker"] in S], store)
        torch.save(store, os.path.join(out_dir, f"{name}.pt"))
        print(name, len(store), "utts", round(sum(s["dur"] for s in store) / 3600, 3), "h",
              len({s["speaker"] for s in store}), "speakers", flush=True)
    held = dev_spk | test_spk

    # train: whole speakers in stream order until the budget
    store, buf, hours, order = [], [], 0.0, []
    cur_spk, t0 = None, time.time()
    for u in utts(load("train")):
        if u["speaker"] in held:
            continue
        buf.append(u); hours += u["dur"] / 3600
        if len(buf) >= 64:
            flush(buf, store); buf = []
        if hours >= train_hours and (cur_spk is not None and u["speaker"] != cur_spk):
            break
        cur_spk = u["speaker"]
        if len(store) % 500 == 0 and store:
            print(f"train {len(store)} utts {hours:.2f} h {time.time()-t0:.0f}s", flush=True)
    flush(buf, store)
    torch.save(store, os.path.join(out_dir, "train.pt"))
    print("train", len(store), "utts", round(sum(s["dur"] for s in store) / 3600, 3), "h",
          len({s["speaker"] for s in store}), "speakers; overlap with dev/test:",
          len({s["speaker"] for s in store} & held), flush=True)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[3 + 1], float(sys.argv[3]))
