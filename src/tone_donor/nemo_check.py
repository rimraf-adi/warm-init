"""Smoke test: load an IndicConformer .nemo model, transcribe IndicVoices valid utterances,
score CER and tone-context CER, log the run. Run inside WSL .venv-nemo with
PYTHONPATH=src from the repo root.

    python -m tone_donor.nemo_check doi dogri 40
"""
import io
import os
import sys
import tempfile

import soundfile as sf
import torch
import torchaudio
from datasets import Audio, load_dataset
from huggingface_hub import hf_hub_download

from tone_donor.runlog import log_run
from tone_donor.text import ASPIRATES_DEVANAGARI, PLAIN_DEVANAGARI, charset_cer, normalize, tone_cer
from tone_donor.vaani_stream import _load_dotenv


def main(code, iv_lang, n, lang_id=None):
    lang_id = lang_id or code
    _load_dotenv()
    tok = os.environ["HF_TOKEN"]
    import nemo.collections.asr as nemo_asr

    repo = f"ai4bharat/indicconformer_stt_{code}_hybrid_ctc_rnnt_large"
    fname = f"indicconformer_stt_{code}_hybrid_rnnt_large.nemo"
    path = hf_hub_download(repo, fname, token=tok)
    model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(path, map_location="cuda").eval()
    print("loaded", type(model).__name__, "params(M)=", round(sum(p.numel() for p in model.parameters()) / 1e6, 1),
          "encoder(M)=", round(sum(p.numel() for p in model.encoder.parameters()) / 1e6, 1), flush=True)
    print("tokenizer vocab:", model.tokenizer.vocab_size if hasattr(model, "tokenizer") else "n/a", flush=True)

    ds = load_dataset("ai4bharat/IndicVoices", iv_lang, split="valid", streaming=True, token=tok)
    ds = ds.cast_column("audio_filepath", Audio(decode=False))
    tmp = tempfile.mkdtemp(prefix="smoke_")
    files, refs, secs = [], [], 0.0
    for ex in ds:
        wav, sr = sf.read(io.BytesIO(ex["audio_filepath"]["bytes"]), dtype="float32", always_2d=True)
        wav = torch.from_numpy(wav.mean(1))
        if sr != 16000:
            wav = torchaudio.functional.resample(wav, sr, 16000)
        p = os.path.join(tmp, f"{len(files)}.wav")
        sf.write(p, wav.numpy(), 16000)
        files.append(p); refs.append(normalize(ex["text"])); secs += len(wav) / 16000
        if len(files) >= n:
            break

    out = {}
    for dec in ("ctc", "rnnt"):
        model.cur_decoder = dec
        kw = {"logprobs": False} if dec == "ctc" else {}
        hyp = model.transcribe(files, batch_size=8, language_id=lang_id, **kw)
        if isinstance(hyp, tuple):
            hyp = hyp[0]
        hyp = [h.text if hasattr(h, "text") else h for h in hyp]
        hyp = [normalize(h) for h in hyp]
        m = tone_cer(list(zip(refs, hyp)), iv_lang if iv_lang in ("dogri", "punjabi") else "dogri")
        pairs = list(zip(refs, hyp))
        asp, n_asp = charset_cer(pairs, ASPIRATES_DEVANAGARI)
        pln, n_pln = charset_cer(pairs, PLAIN_DEVANAGARI)
        m.update(aspirate_cer=asp, plain_cer=pln, n_asp=n_asp, n_plain=n_pln)
        out[dec] = (m, hyp[:2])
        print(dec, m, flush=True)
        print("  ref:", refs[0], "\n  hyp:", hyp[0], flush=True)
        log_run(stage="phase0-smoke", target=iv_lang, donor=code, init=("zero-shot-" if lang_id != "doi" else "own-head-") + lang_id, budget_h=None,
                backbone=f"indicconformer_{code}", split="IndicVoices-valid-first-n", n_utts=len(files),
                cer=m["cer"], aspirate_cer=m["aspirate_cer"], plain_cer=m["plain_cer"], tone_cer=m["tone_cer"], tone_chars=m["tone_chars"],
                config={"decoder": dec, "n": n, "audio_h": round(secs / 3600, 3)},
                notes="pretrained checkpoint, no fine-tuning; first n valid utterances; supersedes earlier phase0-smoke runs labelled own-head (wrong label: these are zero-shot Hindi)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else None)
