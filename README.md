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

As of 2026-10-13. Phase 0 (set-up) is mostly done and Phase 1 (the kill test for H2) is running. Gate 1 has not been decided.

- Data access works for VAANI and IndicVoices by streaming, and all 22 monolingual and the multilingual IndicConformer checkpoints are readable.
- Backbone: `ai4bharat/IndicConformer` (NeMo, 628M parameters, 24-block encoder, 22 languages). The 115M Hindi-only checkpoint is used as a baseline backbone.
- Preliminary signals (not conclusions) are in NOTES.md. Hypotheses H1-H5 are untested; the statistics have not been run.
- Done: the head-only Phase 1 grid on the Hindi-only encoder (random vs Hindi-copied Dogri head, 0.25/1/5 h, 3 seeds, 18 runs) and its Step 0 analysis (NOTES.md, 2026-10-13). Result in short: tone characters (ह + virama) are error-prone in every arm including random init; Hindi-init helps at 0.25 h and not at 5 h; nothing here supports H2 yet, and Gate 1 is undecided because the own-head comparison needs the multilingual backbone. Multilingual-encoder head-only grid is also done (19 runs): copying the Hindi head into Dogri leaves more errors on tone characters than a random head, mostly at 0.25 h (tone CER 0.243 vs 0.175), and Gate 1 passes on this backbone (NOTES.md, 2026-10-13). Donor-head grids (Punjabi, Marathi, Nepali, Bengali, Hindi; fill and blank controls) showed that every copied donor head, tonal or not, hurts tone characters about equally, mainly through deletions caused by the copied blank column. So on this setup H3 (a tonal donor wins) is not supported and the Hindi effect is a generic copy artefact, not a tone effect. No donor head beat random init on CER at any budget.
- Zero-shot sweep of all language heads on Dogri (no training): Indo-Aryan heads decode best, and the tonal Punjabi head has clearly the lowest tone-character error among the non-own heads (0.516 vs 0.654 for Hindi), though one run without CIs (NOTES.md). Next: rerun the sweep with saved hypotheses and CIs, then encoder adapters with donor initialisation and layer-wise tone probes, then more targets. (Detail and decision rules in NOTES.md, section "Roadmap after the head-only runs"): analyse the head-only runs; zero-shot sweep of all 22 language heads per target; head-only arms on the multilingual encoder (random, Hindi, Punjabi, own head as upper bound); encoder adapters with donor initialization; layer-wise tone probes (H1); more targets and non-tonal controls (H3, H4).
- Not done yet: a Dogri tone check against a reference grammar or speaker; the statistical tests; Punjabi/Bodo/Manipuri targets; the mixed-effects model across languages.

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
