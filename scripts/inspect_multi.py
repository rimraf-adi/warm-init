"""Load ai4bharat/IndicConformer (NeMo) and report architecture, tokenizer, languages and a Dogri sanity check."""
import io
import os
import sys

import soundfile as sf
import torch
import torchaudio
from datasets import Audio, load_dataset
from huggingface_hub import hf_hub_download

import nemo.collections.asr as nemo_asr
from tone_donor.text import normalize, tone_cer
from tone_donor.vaani_stream import _load_dotenv

_load_dotenv()
tok = os.environ["HF_TOKEN"]
p = hf_hub_download("ai4bharat/IndicConformer", "IndicConformer.nemo", token=tok)
print("INFO path", p, flush=True)
m = None
for cls in (nemo_asr.models.EncDecHybridRNNTCTCBPEModel, nemo_asr.models.ASRModel):
    try:
        m = cls.restore_from(p, map_location="cuda").eval()
        print("INFO restored with", cls.__name__, flush=True)
        break
    except Exception as e:
        print("INFO restore failed", cls.__name__, type(e).__name__, str(e)[:160], flush=True)
if m is None:
    sys.exit(1)

n = lambda mod: round(sum(x.numel() for x in mod.parameters()) / 1e6, 1)
print("INFO total params (M)", n(m), "encoder", n(m.encoder), flush=True)
print("INFO class", type(m).__name__, "encoder", type(m.encoder).__name__, "n blocks", len(m.encoder.layers), flush=True)
tk = m.tokenizer
print("INFO tokenizer", type(tk).__name__, "vocab", getattr(tk, "vocab_size", None), flush=True)
print("INFO langs", list(getattr(tk, "langs", [])), flush=True)
print("INFO ctc decoder", type(m.ctc_decoder).__name__, "has masks", getattr(m.ctc_decoder, "language_masks", None) is not None, flush=True)

ds = load_dataset("ai4bharat/IndicVoices", "dogri", split="valid", streaming=True, token=tok).cast_column("audio_filepath", Audio(decode=False))
tmp = "/tmp/multi_check"
os.makedirs(tmp, exist_ok=True)
files, refs = [], []
for ex in ds:
    wav, sr = sf.read(io.BytesIO(ex["audio_filepath"]["bytes"]), dtype="float32", always_2d=True)
    w = torch.from_numpy(wav.mean(1))
    if sr != 16000:
        w = torchaudio.functional.resample(w, sr, 16000)
    fp = f"{tmp}/{len(files)}.wav"
    sf.write(fp, w.numpy(), 16000)
    files.append(fp)
    refs.append(normalize(ex["text"], drop_apos=True))
    if len(files) >= 100:
        break
for lang in ("doi", "hi"):
    for dec in ("ctc", "rnnt"):
        m.cur_decoder = dec
        kw = {"logprobs": False} if dec == "ctc" else {}
        try:
            hyp = m.transcribe(files, batch_size=8, language_id=lang, **kw)
            if isinstance(hyp, tuple):
                hyp = hyp[0]
            hyp = [normalize(h.text if hasattr(h, "text") else h, drop_apos=True) for h in hyp]
            r = tone_cer(list(zip(refs, hyp)), "dogri", "ha")
            print(f"INFO dogri-audio lang_id={lang} {dec} CER {r['cer']:.3f} ha-tone CER {r['tone_cer']:.3f}", flush=True)
            print("INFO   ref:", refs[0][:90], "\nINFO   hyp:", hyp[0][:90], flush=True)
        except Exception as e:
            print("INFO", lang, dec, "ERR", type(e).__name__, str(e)[:160], flush=True)
