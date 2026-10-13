# Tone-aware donor transfer for Indic ASR

Research project: when a new low-resource Indic language borrows weights from a donor language, should the donor share its **script** or its **sound system** (tone)? Example: Dogri is tonal and written in Devanagari. Hindi is the same-script donor but non-tonal. Punjabi is tonal but written in Gurmukhi. The study also asks whether language families help both initialization and inference, so the main backbone is the multilingual IndicConformer.

Owner: rimraf-adi. Repository: https://github.com/rimraf-adi/warm-init

## Where to read what

| File | What it holds |
|---|---|
| [plan.md](plan.md) | The original plan as pasted (hypotheses H1-H5, phases, language pool). Not edited after the fact. |
| [novelty-check.md](novelty-check.md) | Literature and novelty check of the plan, with a search log and a reference check. |
| [NOTES.md](NOTES.md) | Lab notebook: status board, environment facts, dated findings, decisions, open items. Newest at the bottom. |
| [results/README.md](results/README.md) | Layout and rules for results. |
| [docs/agent-memory/](docs/agent-memory/README.md) | Mirror of the assistant's memory notes (preferences, design direction, project facts). |
| [results/RESULTS.md](results/RESULTS.md) | Tables generated from the run log. Never edited by hand. |
| `results/runs.jsonl` | Append-only run log. One line per run, with git commit, config hash and library versions. |

If these disagree, the order of trust is: `results/runs.jsonl`, then `NOTES.md`, then `plan.md`.

## Current status (update the date when you change this)

As of 2026-10-13. Setup and Phase 1 are done on Dogri; the main hypotheses are mostly not supported; one real inference-side effect was found. Everything below uses the multilingual `ai4bharat/IndicConformer`, the gender-balanced v2 split, speaker-cluster bootstrap CIs, and predictions that were written down before the confirmatory runs (NOTES.md has the tables).

| Question | Result |
|---|---|
| H2 / H3: does copying a donor head into Dogri hurt tone, and does a tonal donor (Punjabi) win? | Copying any donor head hurts the ha+virama tone mark by about +0.09 CER at 0.25 h (shrinking to about +0.005 at 5 h); Punjabi is no better than Hindi (+0.006 [-0.002, +0.014]). No donor head beats random init on overall CER at any budget. About 40% of the penalty is the donor's blank column. H3 not supported. |
| H1: do tonal-donor encoders keep more tone information? | Punjabi's encoder beats Hindi's on the tone-mark probe (+0.016 [+0.007, +0.025]) but equally on a non-tone control (+0.019); difference of differences -0.003 [-0.012, +0.006]. Not tone-specific. H1 not supported. |
| Inference-side family effect (zero-shot decoding with each language head) | Real and replicated: the Punjabi head has far lower error than Hindi on the ha of Dogri's ha+virama tone mark (0.356 vs 0.776; -0.420 [-0.460, -0.381]), with no difference on ordinary ha. No head except Dogri's writes the virama. |

Open: whether the inference effect is tone or closeness to Dogri; other targets and non-tonal controls; unseen languages; a Dogri speaker or grammar check of the tone labels. Caveats are listed per result in NOTES.md.

## Data

- Source: IndicVoices (`ai4bharat/IndicVoices`), Dogri first. Splits are materialised locally by `tone_donor.make_splits`: manifests (tracked) in `data/manifests/`, 16 kHz audio (gitignored) in `data/audio/`. Data budget: 50 GB in total.
- VAANI (`ARTPARK-IISc/VAANI`) is not used in experiments for now (only surveyed; see NOTES.md). It may come back for SSL-based learning.
- Text fields: manifests keep `text`, `verbatim`, `normalized` and the unsanitized versions; which field is scored is recorded in NOTES.md.

## Repository layout

```
src/tone_donor/
  vaani_stream.py   stream a VAANI language (transcribed rows only); reads HF_TOKEN from .env
  survey.py         Phase 0 survey: script and annotation-tag counts per VAANI language
  text.py           transcript normalization, tone-context CER, aspirate/plain CER
  runlog.py         append-only run log (log_run, read_runs)
  report.py         rebuilds results/RESULTS.md from the run log
  prep_features.py  speaker-disjoint Dogri splits + cached frozen-encoder features (BACKBONE=hi|multi)
  train_head.py     Phase 1: train Dogri CTC head columns on cached features (arms: random, own, hindi, donor-<code>)
  translit.py       Indic script -> Devanagari by Unicode offset (for donor token matching)
  make_splits.py    materialise IndicVoices split manifests + audio
  analyze_phase1.py step 0 analysis: tone vs control characters, paired bootstrap
  nemo_check.py     smoke test: pretrained checkpoint on IndicVoices utterances
scripts/            WSL setup/run helpers, grid driver, model inspection scripts
tests/test_text.py  tests for normalization and tone CER
results/            run log, generated tables, per-phase outputs (see results/README.md)
```

## Set up

Two environments are used.

1. **Windows, uv** (data work, survey, reports):
   ```bash
   uv sync
   ```
   Put a Hugging Face read token in `.env` as `HF_TOKEN=...` (the file is gitignored; never commit it). The account must have accepted the terms of the gated datasets and models used (IndicVoices, VAANI, the IndicConformer checkpoints).
2. **WSL Ubuntu-22.04, NeMo** (model code; the GPU is visible from WSL):
   ```bash
   wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/wsl_setup_ai4b.sh
   ```
   This builds `.venv-ai4b` with the AI4Bharat NeMo fork (branch nemo-v2), which is required to load IndicConformer checkpoints. System packages needed once, as root: `build-essential libsndfile1 ffmpeg python3.10-dev`. Version pins that matter: `huggingface_hub==0.23.2`, `transformers==4.40.2`, `datasets==2.19.2`, `pytorch-lightning==2.2.5`.

Call `wsl` from PowerShell, not Git Bash (Git Bash rewrites `/mnt/...` paths).

## Run

```bash
# tests (Windows)
uv run python tests/test_text.py

# Phase 1 data: Dogri splits + cached encoder features (WSL; BACKBONE=multi for the multilingual model)
wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.prep_features dogri doi 5.0 /home/vnit/data/dogri

# Phase 1 grid (WSL), skips configs already in results/runs.jsonl
wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/run_phase1.sh

# head-only grids on the multilingual encoder (BACKBONE=multi is set inside these scripts)
wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/run_phase1_multi.sh          # own / random / hindi arms
wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/run_phase1_multi_donors.sh   # Punjabi, Marathi, Nepali, Bengali donor heads

# step 0 analysis (bootstrap, tone vs control characters); argument = backbone label as logged
uv run python -m tone_donor.analyze_phase1 indicconformer_multi_frozen_encoder

# regenerate result tables
uv run python -m tone_donor.report
```

Cached features live outside git (`/home/vnit/data/...` inside WSL, about 1 GB per backbone).

## Conventions

- Every result is a line in `results/runs.jsonl` written through `log_run`. Wrong runs are never deleted: log a new run with `notes="supersedes <run_id>"` or set `status` to `invalid` and say why.
- Tone-context CER for Dogri is measured on ह and the virama that follows it (the apostrophe tone mark is not in the IndicConformer vocabulary, so it is dropped from text and reported as not testable). Punjabi uses ਘ ਝ ਢ ਧ ਭ ਹ.
- Splits are speaker-disjoint: IndicVoices `valid` is divided by speaker into dev and test; training speakers are drawn from `train` and never overlap with them.
- Claims name their backbone. Results from the Hindi-only checkpoint are not results about the multilingual model.
- Commits: short, plain, one line, authored as rimraf-adi.
- Documentation rule: any new finding goes into NOTES.md with its date and the run ids it rests on; any change to how things run goes into this README.
