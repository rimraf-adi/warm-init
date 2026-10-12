# Lab notebook

Newest entries at the bottom. Facts only; each result says where it came from.
Results of every run go to `results/runs.jsonl` through `tone_donor.runlog.log_run`.

## Status board

| Phase | State | Evidence |
|---|---|---|
| 0. Verify and set up | In progress | see entries below |
| 1. Kill test (H2) | Not started | waits on NeMo env and Dogri splits |
| 2. Mechanism (H1) | Not started | gated on Gate 1 |
| 3. Main grid (H3-H5) | Not started | gated on Gate 2 |
| 4. Write and submit | Not started | |

Gate rule: a phase starts only if the gate before it passes. If Gate 1 fails, record the negative result and stop; do not launch the grid.

## Environment

- Windows host, RTX A5000 24 GB, D: has about 88 GB free.
- WSL Ubuntu-22.04 sees the GPU (951 GB disk, 31 GB RAM). NeMo training runs there; the env is built by `scripts/wsl_setup.sh` into `~/warm-init/.venv-nemo`.
- Windows uv project `tone-donor` for data work (loader, survey, text tools).
- HF token is in `.env` (gitignored). It was pasted in chat and should be rotated.
- Audio is read with `Audio(decode=False)` and soundfile because torchcodec is not installed.

## 2026-10-12 entries

### Novelty check (see novelty-check.md)
Core question open in the sources that loaded. Four uncited papers narrow gaps 1, 4, 5 and H1 (Kim et al. 2511.12285, Gogoi et al. 2506.03606, Florian et al. 2607.04814, Wang et al. 2411.18217). Florian et al. found related-language pre-adaptation gives no practical gain once about 1 h of target data exists, which is a risk for H3 on WER. OpenAlex lookup was rate-limited, so references were not checked against it.

### Data access
- VAANI streams with the token. Most rows have no transcript (`isTranscriptionAvailable` is "No"); the loader filters to transcribed rows by default. Transcripts contain tags such as `<pause>`, `[inhaling]`, `<static>...</static>`, `{word}`.
- IndicVoices (`ai4bharat/IndicVoices`) streams with the token for dogri, bodo, manipuri, punjabi, santali (also assamese, bengali, hindi, kannada, konkani, maithili, marathi, nepali, odia and others). Fields: `text`, `normalized`, `verbatim`, `duration`, `speaker_id`, `lang`.
- AI4Bharat hosts per-language NeMo checkpoints `ai4bharat/indicconformer_stt_<code>_hybrid_ctc_rnnt_large` (doi, brx, hi, bn, kn, kok, as, gu, ks, ...). About 523 MB for doi. The multilingual repo `indic-conformer-600m-multilingual` holds ONNX files only, so the plan's "multilingual NeMo checkpoint" may not exist as such. Open question: use per-language checkpoints as encoders/donors, or find the multilingual NeMo file.

### Gate 0: how Dogri spelling marks tone (first 500 validation rows of IndicVoices Dogri)
Counts in `text`: ह् (ha + virama) 756 occurrences, word-final ह् 328, ASCII apostrophe 232, U+02BC 0, nukta 426. Aspirates घझढधभ 336 versus plain गजडदब 4924 out of 47,581 characters. Common ह् words: ओह्, एह्, केह्, जेह्ड़ा.
Reading (mine, not from a grammar): Dogri in this corpus writes tone mainly with ह् and the apostrophe, so the plan's aspirate letter set is not where Dogri marks tone. The Unicode Standard 16.0 (ch. 12) describes U+02BC after short vowels and ha after long vowels, which matches the ha part. A reference grammar or Dogri speaker is still needed; this has not been confirmed that way.
Decision: tone-context CER for Dogri is measured on ह, the following virama, and the apostrophe. Punjabi uses ਘ ਝ ਢ ਧ ਭ ਹ.

### Code
- `tone_donor.vaani_stream`: streams a VAANI language, transcribed rows only.
- `tone_donor.survey`: samples 150 transcribed rows per pool language (script and tag counts) into `results/vaani_survey.json`.
- `tone_donor.text`: `normalize` (tags stripped, NFC, punctuation removed, apostrophe marks kept) and `tone_cer`. Bug found and fixed: a `\w`-based filter deleted Indic vowel signs; test in `tests/test_text.py` now covers it.
- `tone_donor.runlog`: append-only run log.

## Open items

- Confirm Dogri tone spelling with a grammar or speaker.
- Decide the checkpoint question (per-language .nemo vs multilingual).
- Speaker-disjoint splits for IndicVoices Dogri; check how many hours are transcribed.
- Survey results to be merged into the language pool table.
- Rotate the HF token.

### 2026-10-13 notes: environment and checkpoint access
- WSL NeMo env works: torch 2.4.1+cu121, NeMo 1.23.0, huggingface_hub 0.23.5, transformers 4.40.2, datasets 2.19.2 (newer hub/transformers break NeMo 1.23 imports). Needed `build-essential`, `python3.10-dev`, `libsndfile1`, `ffmpeg` installed as root in WSL for `youtokentome`. Run anything in WSL through `scripts/wsl_run.sh` and call `wsl` from PowerShell, not Git Bash (Git Bash rewrites /mnt paths).
- Checkpoint access, tested with the project token on 22 `ai4bharat/indicconformer_stt_*` repos: only `hi` is readable. The other 21 (as, bn, brx, doi, gu, kn, kok, ks, mai, ml, mni, mr, ne, or, pa, sa, sat, sd, ta, te, ur) are gated and the account has not accepted their terms (403 GatedRepoError). Accepting terms must be done by the account owner on each model page; I did not do it.
- Consequence: Dogri's own `doi` head (the upper bound) and the Punjabi, Manipuri and Bengali/Kannada/Assamese donors are not available until access is granted. Phase 1 can still run with Hindi as the donor encoder.
- The multilingual repo is ONNX plus custom code only, with no trainable PyTorch weights.
