# Lab notebook

Newest entries at the bottom. Facts only; each result says where it came from.
Results of every run go to `results/runs.jsonl` through `tone_donor.runlog.log_run`.

## Status board

| Phase | State | Evidence |
|---|---|---|
| 0. Verify and set up | Mostly done | env, data access, splits, metric, survey; open: grammar check of Dogri tone, VAANI scripts mapped (see survey entry) |
| 1. Kill test (H2) | Running | head-only grid on the Hindi-only encoder (baseline) and multilingual-backbone runs; Gate 1 not decided |
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

### 2026-10-13: the "hi" checkpoint is the multilingual model
- `ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large` loads with the AI4Bharat NeMo fork (branch nemo-v2, venv `.venv-ai4b`) and has a MultilingualTokenizer (5632 tokens) for 22 languages: as, bn, brx, doi, kok, gu, hi, kn, ks, mai, ml, mr, mni, ne, or, pa, sa, sat, sd, ta, te, ur. Transcribing takes `language_id=<code>`; the decoder is chosen with `model.cur_decoder`. Encoder is 115.1M parameters. So Dogri, Bodo, Punjabi, Manipuri and the donor heads may be reachable with this one ungated file; this still has to be verified per language.
- The apostrophe (ASCII ' and U+02BC) is `<unk>` in both the hi and doi tokenizers. IndicConformer's own heads cannot emit the Dogri apostrophe tone mark. Tone-context CER for Dogri must therefore be reported in two parts: ha-based (ह and following virama, encodable) and apostrophe (unencodable by the stock tokenizer; a fine-tuned head needs an extended vocabulary).
- Zero-shot Hindi head on 200 IndicVoices Dogri validation utterances (first 200, not speaker-audited), n tone chars 1282 counting ह, virama and apostrophe: CTC CER 0.413, tone CER 0.794, aspirate CER 0.618, plain CER 0.386; RNNT CER 0.422, tone CER 0.789, aspirate CER 0.599, plain CER 0.421. This is only a zero-shot baseline: Hindi's script and vocabulary differ (no apostrophe), so it cannot show that tone causes the errors. Run ids are in `results/runs.jsonl`.

### 2026-10-13: Dogri head inside the hi checkpoint is untrained
`language_id="doi"` on the `hi` checkpoint gave empty CTC output and a looping RNNT output (CER 41.5), so the multilingual tokenizer exists but only the Hindi head is trained in that file. The two runs are logged as invalid in `results/runs.jsonl` (kept, with `status=invalid`). The Dogri upper bound still needs the gated `doi` checkpoint (terms must be accepted by the account owner). The zero-shot Hindi baseline from earlier stands.

### 2026-10-13: backbone correction (not the 600M model)
The plan names IndicConformer-600M-Multi. That checkpoint (`ai4bharat/indic-conformer-600m-multilingual`) is ONNX plus custom code, inference only, so it is not trainable here and is not what any run in `results/runs.jsonl` uses. All Phase 1 runs use the per-language checkpoint `indicconformer_stt_hi_hybrid_ctc_rnnt_large`: Conformer-large encoder, 17 blocks, d_model 512, 115.1M encoder parameters measured (model card says about 120M). Total model size with decoder and joint network was not measured. Results apply to this Hindi-trained encoder only and must not be described as results on the 600M multilingual model. Open question: whether its encoder saw other languages (not verified).

### 2026-10-13: the multilingual NeMo model exists and works (use this as the backbone)
- `ai4bharat/IndicConformer` (file `IndicConformer.nemo`, 2.5 GB, readable with the project token) restores with the AI4Bharat NeMo fork as EncDecHybridRNNTCTCBPEModel: 628.4M parameters, ConformerEncoder with 24 blocks (607.7M), MultilingualTokenizer with 5632 tokens for the 22 languages. This is the 600M multilingual model of the plan, in trainable form. Set `BACKBONE=multi` to use it in `prep_features` and `train_head`; default `hi` is the 115M Hindi-only checkpoint.
- First 100 IndicVoices Dogri validation utterances (not audited against its training data; Dogri was seen in its training), CER / ha-tone CER:
  - own Dogri head: CTC 0.144 / 0.078, RNNT 0.144 / 0.083.
  - Hindi head on Dogri audio: CTC 0.343 / 0.702, RNNT 0.450 / 0.742.
  Reading (mine): with the own head, ha-tone errors are below overall error; with the Hindi head they are about twice overall error. This is the zero-shot version of the H2 pattern, in the multilingual model.
- All 22 monolingual `indicconformer_stt_<code>` checkpoints became readable after the account owner accepted their terms. Their heads live in a different feature space (115M encoder) from the multilingual encoder, so their weights cannot be dropped into the multilingual head; donor heads for the multilingual backbone are the multilingual model's own heads for other languages. The monolingual models remain useful as separate backbones.


### 2026-10-13: VAANI survey results (`results/phase0/vaani_survey.json`)
Sample: first 150 transcribed rows per language (0.12-0.34 h each), from `tone_donor.survey`. Dominant script by character count in that sample:
- Latin: Mizo, Wancho, Kokborok, Sumi, Garo, Chakma, Nagamese. Chakma is written in Latin in VAANI, not in Chakma script.
- Devanagari: Chhattisgarhi, Garhwali, Kumaoni, Bhojpuri, Marwari, Magahi, Bajjika, Maithili, Nepali, Konkani, Hindi, Marathi.
- Kannada script: Tulu, Kannada. Gurmukhi: Punjabi. Meetei Mayek: Manipuri. Ol Chiki: Santali (79 transcribed rows found, 263 Devanagari characters mixed in). Odia: mostly Odia script with 1,458 Bengali-block characters. Bengali and Assamese both show the Bengali-Assamese block.
- Dogri: 0 transcribed rows in VAANI (as in the plan; use IndicVoices). Bodo: config `Bodo` does not exist in VAANI (use IndicVoices).
Caveat: counts come from a small head-of-file sample; tag counts per language are in the JSON. The Latin-script languages need a grapheme mapping before any cross-script donor copy (open item for Mizo/Manipuri donors).
