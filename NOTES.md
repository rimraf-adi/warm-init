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

## Roadmap after the head-only runs (written 2026-10-13, before the results are in)

The head-only runs give a baseline. The steps below are ordered by cost, and each has a rule for what counts as a result, fixed in advance. Backbone for everything from step 2 on is the multilingual `ai4bharat/IndicConformer`; the Hindi-only checkpoint is a baseline.

### Step 0: analyse the head-only runs (no new training)
- Per run, paired over test utterances: tone-character CER vs plain-character CER, with a bootstrap 95% CI (utterances resampled; seeds pooled after checking they agree).
- Tone-character controls: ha-based tone characters vs a frequency-matched set of non-tone consonants, so a difference is not just rarity.
- Confusion matrices for ह/virama and aspirate-vs-plain errors.
- Decision rule (Gate 1, H2 on this backbone): supported only if (a) tone-character CER exceeds the matched control with the CI excluding zero, in the Hindi-init arm at 0.25 h and 1 h, and (b) that excess is smaller in the own-head arm. If not, H2 is recorded as not supported on this backbone; it does not stop the multilingual work.

### Step 1: zero-shot donor-head map (cheap, no training, multilingual model)
Decode each target's test audio with every one of the 22 language heads (`language_id` sweep), CTC and RNNT. Targets: Dogri, Punjabi, Bodo, Manipuri, Santali, Konkani, Maithili, Nepali. Report CER and tone-character CER per (target, head) and relate them to family, script and tonality of the head language. This is the inference-side family effect, and it also ranks candidate donors without any fine-tuning.

### Step 2: head-only arms on the multilingual encoder (needs the extraction job)
Arms for Dogri: random; own head (upper bound, no training); Hindi head; Punjabi head (tonal, other script, needs a Gurmukhi-to-Devanagari token mapping, with the fraction of Dogri tokens that find a match reported); a same-script non-tonal donor other than Hindi (Marathi or Nepali); the best head from Step 1. Budgets 0.25, 1 and 5 h, 3 seeds. Same protocol as the Hindi-encoder runs.

### Step 3: encoder adapters with donor initialization (tests H1 and the family effect)
- Bottleneck adapters in the top 6 of the 24 blocks. The output of the frozen lower blocks is cached once, so training is cheap. (To check first: whether the AI4Bharat NeMo fork's Conformer supports adapters; otherwise a small custom module.)
- Donor adapters: train on 5 h of IndicVoices for Hindi and for Punjabi, each with its own frozen head. Then initialize the Dogri adapter from a donor adapter, from random, or from the average of the two; the Dogri head follows the Step 2 init.
- Compare Hindi-init vs Punjabi-init vs random at 0.25, 1 and 5 h, 3 seeds, on tone-character CER first and WER second.

### Step 4: mechanism (H1)
Layer-wise linear tone probes. Labels: word contains ह् (from the transcript), using forced alignment to place the word in the frames. Compare probe accuracy by layer between the base encoder and encoders adapted from a tonal vs a non-tonal donor. Speaker- and word-disjoint splits.

### Step 5: more targets (H3, H4)
Punjabi as a simulated low-resource target (own head discarded), Bodo, Manipuri, Santali and non-tonal controls (Konkani, Maithili, Nepali), then the donor-tonality by target-tonality model from the plan. Dogri alone cannot separate tone from relatedness; the non-tonal controls and the within-language tone-bearing vs other-word contrast are what do.

### Gates and stopping rules
- Gate 2 (after Step 4): continue to the full grid only if a tonal donor keeps more tone information in upper layers or beats the non-tonal donor on tone-character CER at low data. If not, write up the negative result with the probes.
- Every step logs to `results/runs.jsonl`; every step ends with a NOTES.md entry and a README status update in the same commit.

### Known weaknesses to carry into every result
- Dogri was seen by the multilingual model, so this is low-resource adaptation, not zero-shot. Unseen targets (Mizo, Kokborok, Tulu) are needed for the clean claim and need Latin or Kannada-script handling.
- The test set is IndicVoices `valid` split by speaker, which is not audited against the model's training data.
- Dogri's apostrophe tone mark cannot be tested with this vocabulary.
- Tone is defined from spelling, not from acoustic measurement. A grammar or speaker check is still pending.

### 2026-10-13: head-only training speed fix (implementation note, same protocol)
Per-epoch model selection used the full metric with a pure-Python edit-distance alignment (four calls per dev check), which made a 1 h run take about 10 minutes. It now uses the C `editdistance` package for plain dev CER (`fast_cer`); `tests/test_fast_cer.py` checks it equals the full metric's edit count on 500 random pairs (run in the WSL env). Protocol is unchanged: AdamW lr 1e-3, batch 16, 40 epochs, best dev[:300] CER. The `impl` field in `results/runs.jsonl` marks which version produced a run (v1 = no field, v2 = gpu-cached, v3 = fast dev CER). Runs from different versions were kept and are comparable by protocol; only speed differs. The grid was restarted once at this point; completed runs were skipped.

### 2026-10-13: data policy decisions (from the project owner)
- Download and use data locally; total data budget 50 GB. Audio goes under `data/audio/` (gitignored); split manifests under `data/manifests/` are tracked in git together with the dataset revision and the filter rules.
- IndicVoices is the main source for experiments. Dogri splits are being materialised with `tone_donor.make_splits` (rules in its docstring and in `data/manifests/indicvoices_dogri_splits.json`); the manifests must reproduce the counts behind the cached features (929 dev, 969 test, 2,382 train utterances) or the difference is reported.
- VAANI is skipped for now. It is only needed for the unseen-language targets (Mizo, Kokborok, Tulu) and the survey; most of its rows are untranscribed, so using it needs a separate extraction effort. Revisit it for SSL-based learning later. The Phase 0 survey of 29 languages stays as the record of what VAANI contains.
- Head-only grid on the Hindi-only encoder: stopped by the owner at 12 of 18 runs (the 5 h runs and hindi 1 h seed 2 remain). To be restarted by the assistant once the Dogri download finishes; the runner skips configs already logged.

### 2026-10-13: Dogri splits materialised and audited (`data/manifests/`, source revision c96f9088f138cf89d419da7e8e643e1f05c00a87)
- `make_splits` output: dev 929 utts (2.207 h, 68 speakers), test 969 (2.119 h, 67), train 2,381 (5.016 h, 160), no speaker overlap. Audio is 16 kHz already (all rows). Audio (1.1 GB) is in `data/audio/` (gitignored); manifests are tracked.
- The cached features used by the Phase 1 runs (`/home/vnit/data/dogri*`, built by streaming) have the same dev and test sets and 2,382 train utterances: the feature script appended the first utterance of the next speaker before stopping. Only budgets that reach the end of the train file (5 h) are affected; the 0.25 h and 1 h runs use an identical prefix. Future extractions should read the manifests.
- Text fields (over all 4,279 rows): `text` equals `normalized` in every row; `verbatim` differs in 1,483 rows and has fewer apostrophes (1,385 vs 1,849); the `unsanitized_*` fields keep bracket annotations and punctuation. Experiments score on `text` (identical to `normalized`), normalised by `tone_donor.text.normalize` with apostrophes dropped.
- Composition differences between splits (from the manifest columns): dev gender is balanced (469 M / 460 F), test is 727 M / 242 F, train 1,277 M / 1,104 F. Task types differ between splits (test: Agriculture, Biking, Traveling; train: Basic, Cooking, District Specific). The train sample is the first speakers in shard order, not a random draw. Limitation: the test set is not matched to train in gender or domain; speaker-disjointness is the only guarantee. A random-speaker train draw needs more shards (budget allows it, up to 50 GB total).

### 2026-10-13: Step 0 analysis, head-only runs on the Hindi-only encoder (`python -m tone_donor.analyze_phase1`; output `results/phase1/analysis_indicconformer_hi_frozen_encoder.json`)
Setup: 18 runs (random vs Hindi-copied Dogri CTC head columns, budgets 0.25 / 1 / 5 h, seeds 0-2), frozen 115M Hindi encoder, speaker-disjoint test set of 969 utterances, tone characters = ह plus its following virama (4,852 positions), control characters = गपम chosen to match the tone count (4,916). Bootstrap resamples test utterances (2,000 draws, seeds pooled); it does not include seed-to-seed variance.

| budget h | arm | CER | tone CER | control CER | tone-control [95% CI] | aspirate | plain |
|---|---|---|---|---|---|---|---|
| 0.25 | hindi | 0.333 | 0.499 | 0.237 | +0.263 [+0.239, +0.285] | 0.570 | 0.241 |
| 0.25 | random | 0.368 | 0.553 | 0.260 | +0.293 [+0.269, +0.317] | 0.695 | 0.280 |
| 1.0 | hindi | 0.295 | 0.408 | 0.209 | +0.199 [+0.176, +0.220] | 0.545 | 0.206 |
| 1.0 | random | 0.303 | 0.413 | 0.206 | +0.208 [+0.186, +0.228] | 0.574 | 0.212 |
| 5.0 | hindi | 0.263 | 0.339 | 0.175 | +0.164 [+0.144, +0.186] | 0.396 | 0.173 |
| 5.0 | random | 0.262 | 0.322 | 0.177 | +0.146 [+0.126, +0.165] | 0.406 | 0.175 |

Hindi minus random (paired bootstrap): CER -0.035 [-0.038, -0.033] at 0.25 h, -0.008 [-0.010, -0.006] at 1 h, +0.001 [-0.001, +0.002] at 5 h. Tone CER -0.053 [-0.065, -0.042], -0.005 [-0.013, +0.002], +0.017 [+0.011, +0.022]. Tone-minus-control -0.030 [-0.044, -0.015], -0.009 [-0.018, -0.000], +0.018 [+0.012, +0.025].

Reading (mine):
1. Tone characters (ह and its virama) are error-prone in every arm, including the random-init arm with no donor. Rule (a) of the pre-registered Gate 1 is met, but the excess does not depend on a non-tonal donor, and the control set is easier per character than ह, so this alone does not support a tone-specific effect. Aspirated letters (घझढधभ) also err about twice as often as plain ones (0.40 vs 0.17 at 5 h), but they are 12 times rarer in the test text (843 vs 10,238 positions), so frequency is a confound.
2. Hindi-init helps at 0.25 h, mostly on tone characters too, which is the opposite of what H2 predicts for a non-tonal donor. The advantage disappears by 1 h and flips to a small disadvantage on tone characters at 5 h (tone CER 0.339 vs 0.322 on seed means, per-seed values 0.326/0.351/0.339 vs 0.331/0.318/0.318). The seed spread is about as large as the difference (a seed-level t-test gives roughly p of 0.1), so the 5 h reversal is not established.
3. Rule (b) of Gate 1 (the excess being smaller with the model's own Dogri head) cannot be tested on this backbone because the Hindi-only encoder has no Dogri head. Gate 1 is therefore undecided here, and the multilingual backbone is where it is decided.
Caveats: single frozen-encoder linear head only; one test set with a different gender and task mix from train; Dogri was seen in IndicConformer's training; seeds are 3.

### 2026-10-13: Step 0 analysis on the multilingual backbone (`analysis_indicconformer_multi_frozen_encoder.json`; Gate 1)
Setup as for the Hindi-only encoder but the frozen encoder is `ai4bharat/IndicConformer` (628M). Arms: `own` (the model's trained Dogri head, no training, one run), `random` and `hindi` (Hindi head columns copied for the 168 of 256 Dogri tokens whose string also exists in Hindi's tokenizer, blank copied), 3 seeds. Same test set, tone characters, control characters and bootstrap as before.

| budget h | arm | CER | tone CER | control CER | tone-control [95% CI] | tone/CER | aspirate | plain |
|---|---|---|---|---|---|---|---|---|
| 0.25 | hindi | 0.193 | 0.243 | 0.119 | +0.124 [+0.105, +0.142] | 1.26 | 0.218 | 0.130 |
| 0.25 | random | 0.185 | 0.175 | 0.117 | +0.059 [+0.041, +0.076] | 0.95 | 0.272 | 0.109 |
| 1.0 | hindi | 0.166 | 0.155 | 0.102 | +0.053 [+0.036, +0.068] | 0.93 | 0.176 | 0.094 |
| 1.0 | random | 0.162 | 0.135 | 0.095 | +0.039 [+0.024, +0.054] | 0.83 | 0.178 | 0.084 |
| 5.0 | hindi | 0.157 | 0.137 | 0.096 | +0.041 [+0.025, +0.057] | 0.87 | 0.139 | 0.089 |
| 5.0 | random | 0.153 | 0.129 | 0.096 | +0.032 [+0.018, +0.047] | 0.84 | 0.138 | 0.084 |
| own head | own | 0.145 | 0.113 | 0.075 | +0.038 [+0.025, +0.052] | 0.78 | 0.117 | 0.075 |

Hindi minus random (paired bootstrap): CER +0.008 [+0.005, +0.011] / +0.004 / +0.004 at 0.25 / 1 / 5 h; tone CER +0.067 [+0.055, +0.080] / +0.020 [+0.013, +0.028] / +0.009 [+0.002, +0.014]; tone-minus-control +0.065 [+0.052, +0.079] / +0.013 [+0.005, +0.022] / +0.008 [+0.002, +0.015]. Per-seed tone CER at 0.25 h: Hindi 0.241 / 0.242 / 0.245, random 0.181 / 0.175 / 0.170, so the 0.25 h gap is far larger than seed spread; at 5 h the per-seed ranges are 0.133-0.140 (Hindi) and 0.127-0.132 (random).

Gate 1 (rules fixed in the roadmap): (a) tone-character CER exceeds the matched control with the CI excluding zero in the Hindi arm at 0.25 h and 1 h: met. (b) the excess is smaller with the model's own Dogri head: met against Hindi-init at 0.25 h (+0.038 vs +0.124); at 5 h the excess is about equal (+0.038 vs +0.041). Decision: Gate 1 passes on the multilingual backbone; continue.

Reading (mine) and limits:
- Copying the Hindi (non-tonal, same-script) head into Dogri's slice leaves more errors on ह/virama than a random head does, mostly at 0.25 h. With a random head, tone characters are no longer an error hotspot (tone/CER below 1).
- This does not yet show the cause is tone. A mismatched donor head could hurt ह for other reasons. Needed: other non-tonal donors (Marathi, Nepali, Bengali) and the tonal donor (Punjabi, cross-script), compared on the same metric. The control set (गपम) is easier per character than ह, so the +0.03 to +0.06 floor in the random and own arms is expected and the contrast between arms is what matters.
- On the Hindi-only encoder the picture differed (Hindi-init helped at 0.25 h). The result depends on the backbone and must be reported per backbone.
- Own head: one run, no seeds. Dogri was seen by this model. Test set composition differs from train (see data audit entry).

### 2026-10-13: donor-head grid on the multilingual encoder (Punjabi, Marathi, Nepali, Bengali) and a token-coverage finding
Runs: `donor-<code>` arms copy the donor's head columns into Dogri's slice for Dogri tokenizer pieces whose (script-mapped) string also exists in the donor's tokenizer (`tone_donor.translit` maps Gurmukhi and Bengali to Devanagari by Unicode offset); blank copied; unmatched Dogri tokens stay Xavier-random. 0.25 h and 1 h, 3 seeds. Regression check: `donor-hi` reproduces the earlier `hindi` arm (CER 0.193, tone CER 0.241 vs 0.243, 168 tokens copied).

Means over 3 seeds (tone CER = ह and its virama):

| budget | donor | tokens copied | CER | tone CER | aspirate | plain |
|---|---|---|---|---|---|---|
| 0.25 h | random | 0 | 0.185 | 0.175 | 0.272 | 0.109 |
| 0.25 h | Hindi | 168 | 0.193 | 0.243 | 0.218 | 0.130 |
| 0.25 h | Marathi | 149 | 0.197 | 0.249 | 0.255 | 0.129 |
| 0.25 h | Nepali | 144 | 0.197 | 0.230 | 0.174 | 0.134 |
| 0.25 h | Bengali | 143 | 0.202 | 0.242 | 0.219 | 0.125 |
| 0.25 h | Punjabi (tonal) | 140 | 0.205 | 0.244 | 0.177 | 0.130 |
| 1 h | random | 0 | 0.162 | 0.135 | 0.178 | 0.084 |
| 1 h | Hindi | 168 | 0.166 | 0.155 | 0.176 | 0.094 |
| 1 h | Marathi | 149 | 0.167 | 0.152 | 0.209 | 0.098 |
| 1 h | Nepali | 144 | 0.166 | 0.143 | 0.190 | 0.095 |
| 1 h | Bengali | 143 | 0.168 | 0.151 | 0.196 | 0.094 |
| 1 h | Punjabi (tonal) | 140 | 0.169 | 0.152 | 0.170 | 0.094 |

Findings:
1. Every copied donor head, tonal or not, same script or not, raises tone-character CER over random init by a similar amount (about +0.06 to +0.07 at 0.25 h; +0.01 to +0.02 at 1 h). The tonal donor (Punjabi) is not better than the non-tonal donors. H3 (a tonal donor wins at low data) is not supported for Dogri on this backbone, and the Hindi-specific reading of the Hindi result is withdrawn: it is a property of copying a donor head into Dogri's slice.
2. Exploratory (this explanation was formed after seeing the results, from `data/vocab_pieces.json`): of Dogri's 256 pieces, 12 contain ह and 6 contain ह plus virama (`ह्`, `ह्ल`, `▁एह्`, `▁ओह्`, `ाह्`, `▁आह्ल`). No donor vocabulary matches any ह-virama piece, and tone-bearing pieces are matched at 25-42% (4/12 Hindi, 4/12 Marathi, 3/12 Nepali, 5/12 Punjabi, 3/12 Bengali) against 55-66% of all pieces. So donor copying gives trained weights to ordinary tokens and leaves the tone-bearing ones at random init, which would disadvantage exactly those tokens. This predicts that a better fill of the unmatched tokens removes the penalty. Next run tests that (fill strategies below).
3. Limits: this is head-only copying on a frozen encoder, Dogri only, tone from spelling, piece matching by string (script mapping approximate), and the token-coverage explanation is not yet tested.

### 2026-10-13: fill-strategy test of the token-coverage explanation (not supported)
Test: for donors Hindi and Punjabi, Dogri tokens the donor lacks are filled with the donor's mean row (`+mean`) or the mean of the donor rows for the piece's characters (`+comp`, falling back to the mean row), instead of staying random. 0.25 h and 1 h, 3 seeds. Tone CER (mean of 3 seeds, seed sd about 0.001-0.003):

| budget | random | donor-hi | donor-hi+mean | donor-hi+comp | donor-pa | donor-pa+mean | donor-pa+comp |
|---|---|---|---|---|---|---|---|
| 0.25 h | 0.175 | 0.243 | 0.256 | 0.232 | 0.244 | 0.258 | 0.238 |
| 1 h | 0.135 | 0.155 | 0.158 | 0.148 | 0.152 | 0.160 | 0.156 |

CER at 0.25 h: random 0.185, donor-hi 0.193 / +mean 0.196 / +comp 0.189, donor-pa 0.205 / +mean 0.209 / +comp 0.206.
Reading (mine): composition fill lowers tone CER by about 0.01 and mean fill raises it by about 0.01, but none closes the roughly 0.06 gap to random init. The exploratory explanation that unmatched (tone-bearing) tokens at random init cause the penalty is therefore not supported as the main cause. Candidates not yet tested: the copied blank column, the scale of copied rows versus random rows, and interference between the donor's rows and the Dogri-specific directions the multilingual encoder already contains (Dogri was in its training). The tonal donor still does no better than the non-tonal ones in any fill setting.

### 2026-10-13: blank-column control and error types (mechanism of the head-copy penalty)
Control: the same donors with the blank column left at its random init (`+noblank`), 0.25 h, 3 seeds. Tone CER: donor-hi 0.243 -> 0.208 (+noblank) and 0.198 (+comp+noblank); donor-pa 0.244 -> 0.216 (+noblank) and 0.218 (+comp+noblank); random 0.175. CER: donor-hi 0.193 -> 0.198 / 0.201, donor-pa 0.205 -> 0.213 / 0.215, random 0.185. So the copied blank accounts for roughly half of the tone-character penalty and a small part of the overall change in the other direction.

Error types on the 14,556 tone-character positions (3 seeds pooled; `python -m tone_donor.error_types`, output `results/phase1/error_types_multi_0.25h.json`):

| arm | tone deleted | tone substituted | tone error | deletion rate, all chars | insertions per 100 chars |
|---|---|---|---|---|---|
| random | 0.121 | 0.055 | 0.175 | 0.080 | 4.84 |
| hindi (copied) | 0.173 | 0.069 | 0.243 | 0.095 | 4.26 |
| donor-hi+noblank | 0.134 | 0.074 | 0.208 | 0.075 | 6.22 |
| donor-hi+comp+noblank | 0.123 | 0.075 | 0.198 | 0.068 | 7.17 |
| donor-pa (copied) | 0.179 | 0.066 | 0.244 | 0.103 | 4.11 |
| donor-pa+noblank | 0.133 | 0.083 | 0.216 | 0.080 | 6.42 |

Reading (mine):
- Most of the extra tone-character error with a copied head is deletion of ह and its virama (0.121 -> 0.173 for Hindi, 0.179 for Punjabi); overall deletion also rises (0.080 -> 0.095 / 0.103). With the donor's blank row left random, tone deletions return to about the random level (0.133-0.134) and overall insertions go up, so the donor blank shifts the model toward emitting nothing, which hits short, acoustically weak tokens first.
- This is a calibration effect of copying a CTC blank row. It is the same for the tonal donor (Punjabi) and the non-tonal donors, so it says nothing about tone. The random-init arm also deletes ह/virama more than any other class (0.121 deleted vs 0.055 substituted), consistent with those characters being weak in the audio.
- Status of the hypotheses on this setup (head-only, frozen multilingual encoder, Dogri): H2 as phrased (a same-script non-tonal donor concentrates errors on tone contexts) is not distinguishable from a generic copied-head effect; H3 (a tonal donor wins at low data) is not supported; no donor head beats random init at any budget on CER. Head-copy initialisation is not where a family effect should be looked for. The encoder-adapter and zero-shot-sweep steps of the roadmap are next.
- Not yet tested: scaling of copied rows, other fills of the blank, other targets (Punjabi, Bodo), unseen languages.

### 2026-10-13: Step 1, zero-shot sweep of all language heads on Dogri (`python -m tone_donor.zero_shot_sweep`, output `results/phase1/zero_shot_sweep_dogri_test.json`)
Multilingual encoder, cached final-layer features of the 969-utterance speaker-disjoint Dogri test set, greedy CTC with each language's output columns, text mapped to Devanagari by Unicode offset, scored against the Dogri reference (no training, one run per head, no CIs). Five heads (ks, mni, sat, sd, ur) have no offset mapping and are not scored. Check: the own Dogri head gives CER 0.145 on this set via cached features, matching the transcribe-based 0.144 on the first 100 validation utterances, so the cached-feature path is faithful.

| head | family | tonal (general knowledge) | CER | WER | tone CER |
|---|---|---|---|---|---|
| doi (own) | Indo-Aryan | tonal | 0.145 | 0.311 | 0.113 |
| hi | Indo-Aryan | non-tonal | 0.338 | 0.759 | 0.654 |
| pa | Indo-Aryan | tonal | 0.361 | 0.821 | 0.516 |
| mai | Indo-Aryan | non-tonal | 0.364 | 0.795 | 0.691 |
| mr | Indo-Aryan | non-tonal | 0.390 | 0.829 | 0.671 |
| gu | Indo-Aryan | non-tonal | 0.400 | 0.839 | 0.751 |
| kok | Indo-Aryan | non-tonal | 0.402 | 0.826 | 0.788 |
| ne | Indo-Aryan | non-tonal | 0.426 | 0.874 | 0.706 |
| sa | Indo-Aryan | non-tonal | 0.447 | 0.882 | 0.774 |
| bn | Indo-Aryan | non-tonal | 0.454 | 0.903 | 0.761 |
| or | Indo-Aryan | non-tonal | 0.460 | 0.903 | 0.735 |
| te | Dravidian | non-tonal | 0.472 | 0.921 | 0.857 |
| as | Indo-Aryan | non-tonal | 0.486 | 0.963 | 0.766 |
| kn | Dravidian | non-tonal | 0.490 | 0.933 | 0.739 |
| brx | Tibeto-Burman | tonal | 0.550 | 0.952 | 0.772 |
| ml | Dravidian | non-tonal | 0.561 | 0.955 | 0.846 |
| ta | Dravidian | non-tonal | 0.635 | 0.985 | 0.892 |

Reading (mine):
1. Inference-side family effect: Indo-Aryan heads decode Dogri audio far better than Dravidian or Tibeto-Burman heads (CER 0.34-0.49 vs 0.47-0.64), and Hindi and Punjabi are the closest.
2. Tonal Punjabi has by far the lowest tone-character error among the non-own heads (0.516 vs 0.654 for Hindi and 0.67-0.89 for the others) although its overall CER is slightly worse than Hindi's (0.361 vs 0.338). This is the first result in favour of the tone-aware donor idea, on the inference side, and it points the opposite way from the head-copy results (where all donors were alike).
3. Tonality alone does not explain it: Bodo (tonal, Tibeto-Burman, Devanagari script) decodes poorly (CER 0.550, tone CER 0.772). Closeness to Dogri (Western Pahari / Punjabi area) seems to matter more, which is why the plan separates tone from relatedness (H4).
Caveats: single run per head and no confidence intervals (predictions were not saved; rerun with saved hypotheses before any claim); Gurmukhi is mapped to Devanagari by code-point offset, and Punjabi writes tone through consonant letters (the voiced aspirates and ha), not through a ha-virama sequence, so the tone-character score for the Punjabi head depends on how that mapping lines up with Dogri's ha-virama spelling; tonal labels are general knowledge and unverified; Dogri was seen by the model.
