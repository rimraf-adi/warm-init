---
name: project-tone-donor-status
description: "Tone-aware donor transfer for Indic ASR: setup facts, findings and where work stands"
metadata:
  node_type: memory
  type: project
  originSessionId: 0417092b-8b87-48d0-8eba-16a358a53bf8
  modified: 2026-10-12T17:53:02.645Z
---

Project in D:\warm-init (uv, package `tone_donor`). Plan in plan.md, novelty check in novelty-check.md. User handed full control on 2026-10-12 and asked to run all experiments sequentially, using background tasks with notifications; permissions are automated.

Setup facts:
- HF token lives in D:\warm-init\.env (gitignored, user-provided). Loader `vaani_stream.py` reads it. It has an HF token in chat history; user was told to rotate it.
- Audio decode: use `Audio(decode=False)` plus soundfile, because torchcodec is not installed.
- VAANI: most rows are untranscribed; filter `isTranscriptionAvailable == "Yes"`. Transcripts carry tags like `<pause>`, `[inhaling]`, `{word}` that need normalizing.
- IndicVoices (ai4bharat/IndicVoices) streams fine with this token: dogri, bodo, manipuri, punjabi, santali are present. Fields: text, normalized, verbatim, duration.
- Hub has per-language NeMo checkpoints `ai4bharat/indicconformer_stt_<code>_hybrid_ctc_rnnt_large` (doi, brx, hi, bn, kn, kok, ...). The multilingual repo is ONNX only.
- Machine: Windows, RTX A5000 24 GB, ~88 GB free on D:.

Finding (Gate 0): Dogri IndicVoices text marks tone with ह् (ha+virama, ~756 per 500 rows) and ASCII apostrophe (~232), NOT U+02BC and not mainly the aspirates (336 aspirated vs 4924 plain). H2 tone-bearing contexts should be redefined around ह् and the apostrophe.

**Why:** these change the H2 kill test and the tone-context CER definition.
**How to apply:** build tone-context CER from ह् and the apostrophe for Dogri; do not use the घ झ ढ ध भ letter set alone.
