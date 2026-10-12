# Tone-Aware Donor Transfer for Indic ASR: Novelty and Plan

Oct 12, 2026 · @aditya

> Saved as pasted; the body below is unchanged. Later changes live elsewhere: see [README.md](README.md) for the layout and [NOTES.md](NOTES.md) for status and decisions. Known differences from this plan: the multilingual backbone is `ai4bharat/IndicConformer` (NeMo, 628M), not the ONNX `indic-conformer-600m-multilingual` release; Dogri tone is marked by ह् and an apostrophe rather than the aspirate letters listed under H2; [novelty-check.md](novelty-check.md) narrows gaps 1, 4 and 5.

## Summary

The contribution that remains open is tone-aware donor choice and initialization for low-resource adaptation of Indic tonal languages, tested across a pool of about 25 Indian languages that varies tonality, script, family and whether IndicConformer saw the language.

Core question: when a new language borrows from a donor, should it borrow from the donor that shares its script or the one that shares its sound system? For Dogri, the same-script donor (Hindi) is non-tonal; the same-tone donor (Punjabi) uses a different script.

The study runs on two setups: IndicConformer (a multilingual Conformer, not Whisper) and our own from-scratch Devanagari models, where targets are truly held out. Estimated novelty is about 40–50%. That estimate is provisional and depends on the first two kill tests.

## Already done — do not claim

Every earlier idea in this project is covered by published work. Cite these; do not present them as ours.

| Idea we had | Taken by | What they already show |
|---|---|---|
| Warm-start a new language from one similar donor | LoRA-Whisper (2024) | Copies the most similar language's LoRA; a poor donor can be worse than scratch |
| Similarity-selected averaging of adapters | AdapterSoup (2023) | Averages adapters chosen by clustering, for unseen domains |
| Weighted blend of many modules | LoraHub (2023) | Learns blend weights from a few labelled target examples |
| Predicting merge choices or coefficients | SimMerge (2026), LoRA.rar (ICCV 2025) | Learned predictors from similarity signals; hypernetwork-predicted coefficients |
| Closed-form, shift-based adapter init | ConsNoTrainLoRA (ICCV 2025), EVA, CorDA | LoRA init as source–target domain shift, closed form, with rank allocation |
| Where cross-lingual shift lives, by layer | Adapting Where It Matters (2026), SeqStack (2026) | Layer-wise language probes guide where to adapt; layer-band donor similarity |
| Learned donor ranking for Indic ASR | DonorRank (2026) | Zero-shot donor ranking on 20 Devanagari Indo-Aryan varieties |
| Tone-aware adaptation | SITA (2026) | Tone-repulsive loss for Hmong; small ASR cost |
| Non-tonal ASR fine-tuning erases tone | Shen et al. (NAACL 2024) | Tone probe accuracy falls after English fine-tuning, rises after Mandarin |

Also established: similarity alone does not explain transfer (Dialect Matters, DonorRank), and multi-donor data mixing saturates at 2–4 donors (DonorRank).

## What remains novel

Eight gaps remain open. Each is a limitation another paper states or leaves visible, so the motivation section can cite them directly.

| Gap | Left open by | Our delta |
|---|---|---|
| Tone in languages beyond Mandarin and Vietnamese, inside multilingual models | Shen et al. (limitations and future work) | Dogri and Bodo on multilingual IndicConformer |
| Tone written indirectly through consonant letters | Shen et al. compare only unmarked (Mandarin) and marked (Vietnamese) tone | Dogri and Punjabi, if the spelling–tone link is confirmed |
| Same-script vs same-phonology donor | DonorRank and Dialect Matters restrict to Devanagari | Hindi (same script, non-tonal) vs Punjabi (Gurmukhi, tonal) for Dogri |
| Low-resource adaptation with target data | DonorRank studies zero-shot only | Initialization followed by fine-tuning, measured at 15 min, 1 h, 5 h |
| Backbones other than Whisper or one SSL model | SeqStack (future work); DonorRank (fixed w2vBERT) | IndicConformer: Conformer, hybrid CTC+RNNT, per-language heads |
| Tone-awareness without a WER cost | SITA (stated trade-off) | Get tone from donor choice or initialization, not an extra loss |
| Aspiration errors left unexplained | Dialect Matters (Garhwali error table) | Test whether tone explains aspirate-letter errors in Dogri |
| Tonal targets lose to tonal neighbours on CER | DonorRank WAXAL table, not discussed | Re-analysis by tonality as motivating evidence |

The full set of target, control and donor languages, with tone status and data hours, is in Language pool and data below.

This estimate rests on about 20 searches plus full reads of DonorRank, SeqStack, Dialect Matters, SITA, ConsNoTrainLoRA and Shen et al. Absence of evidence here is not proof of absence.

## Hypotheses

Five falsifiable hypotheses carry the paper, each tested across the whole language pool. H2 is the kill test: if it fails, stop before investing further.

1. **H1 — Supervised non-tonal donors suppress tone.** Upper encoder layers adapted on a non-tonal donor encode less tone than layers adapted on a tonal donor, measured by layer-wise tone probes on each tonal target's audio.
2. **H2 — Errors cluster where tone matters.** With a same-script non-tonal donor, character errors in tonal targets concentrate on tone-bearing contexts more than on comparable non-tonal contrasts (for Dogri: घ झ ढ ध भ vs ग ज ड द ब).
3. **H3 — A tonal donor wins at low data, even across scripts.** Across tonal targets, at 15 min and 1 h, a tonal donor beats the same-script non-tonal donor on tone-context CER (for example Punjabi vs Hindi for Dogri, Manipuri vs Garo for Mizo); the gap shrinks by 5 h.
4. **H4 — The effect is specific to tone.** For non-tonal targets a tonal donor gives no advantage, so the effect appears as a donor-tonality × target-tonality interaction; within tonal targets it appears on tone-bearing words, not the rest.
5. **H5 — Tone match improves donor ranking.** Adding a donor–target tonality-match feature to a DonorRank-style ranker improves ranking quality for tonal targets and leaves non-tonal targets unchanged.

H4 separates a tone effect from tonal donors simply being closer relatives; the relatedness term in the cross-language model does the same.

## What we do: phased plan

The work runs in five phases, and each one starts only if the gate before it passes. Gate 1 is the kill test and the main point where we may stop.

Phases 0–2 are cheap: no full training grid until the error analysis and the probes support the tone story.

## Full task list

The tasks follow the five phases in the roadmap above; each phase ends with its gate decision.

### Phase 0 · Verify and set up

- [ ] Confirm, from a reference grammar or a Dogri linguist, how Dogri spelling marks tone: which letters, in which contexts
- [ ] Confirm tone status for every language in the pool from WALS, PHOIBLE or a grammar; record the source for each
- [ ] Confirm whether spelling marks tone in each tonal target (Dogri, Bodo, Punjabi, Mizo, Wancho, Kokborok, Manipuri)
- [ ] Request VAANI access and download the subsets for all pool languages
- [ ] Obtain IndicVoices data for Dogri, Bodo, Santali and Manipuri; record transcribed hours and test-set sizes
- [ ] Record the script used in each VAANI subset (Kokborok, Wancho, Tulu, Garo, Nagamese, Chakma, Sumi)
- [ ] Build fixed, speaker-disjoint train / dev / test splits per language before any experiment
- [ ] Normalize transcripts per script (Unicode NFC, punctuation, code-mixed English); document the rules
- [ ] Download the IndicConformer NeMo checkpoint; record encoder size, LayerNorm and batch-norm placement, and per-language head vocabularies
- [ ] Set up the AI4Bharat NeMo fork and reproduce IndicConformer's reported WER on one language as a sanity check
- [ ] Prepare the from-scratch Devanagari models (Marathi base, every size); confirm a shared tokenizer and training data
- [ ] Build cross-script grapheme mappings (Gurmukhi→Devanagari, and Manipuri's script→Latin for Mizo); hand-check each table
- [ ] Define tone-bearing contexts for each tonal target (character sets or word lists) for the tone-context CER metric
- [ ] Re-tabulate DonorRank's WAXAL CER results by target tonality
- [ ] Start refs.bib and a lit-notes file from the reference list
- [ ] Set up a results log that records language, donor, budget, seed, config and metrics for every run
- [ ] Gate 0 decision: does Dogri spelling encode tone, and are the test sets usable?

### Phase 1 · Kill test (H2)

- [ ] Train a Hindi-initialized adapter and head on Dogri at the chosen budget
- [ ] Train a random-init baseline at the same budget
- [ ] Compute WER, CER and tone-context CER for both
- [ ] Build character confusion matrices; compare aspirate vs plain letter errors with comparable non-tonal contrasts
- [ ] Repeat on at least one more tonal target (Punjabi as a simulated low-resource target, or Mizo) and one non-tonal control
- [ ] Test whether the error concentration exceeds chance (bootstrap or permutation test)
- [ ] Gate 1 decision: continue only if errors cluster on tone contexts; otherwise record the negative result and pivot

### Phase 2 · Mechanism (H1)

- [ ] Train donor adapters: Hindi, Punjabi, Manipuri, Garo, Bengali, Assamese, Marathi, Nepali, Odia, Kannada
- [ ] Extract per-layer encoder features on each tonal target's audio for every donor-adapted model
- [ ] Create tone labels for probing: from spelling where it encodes tone, otherwise a small hand-labelled set
- [ ] Train layer-wise linear tone probes on speaker- and lexically-disjoint splits
- [ ] Compare tone-probe accuracy by layer for tonal vs non-tonal donors
- [ ] Draft and post the arXiv preprint with the kill-test and probe results
- [ ] Gate 2 decision: do tonal donors keep more tone information in upper layers?

### Phase 3 · Main grid (H3–H5)

- [ ] For each target, choose budgets, seeds and donor set from its data and complexity; record the reasoning
- [ ] Run every initialization condition per target on IndicConformer
- [ ] Run the same conditions on the from-scratch Devanagari models, with targets held out
- [ ] Run the model-size ablation on the from-scratch models
- [ ] Compute WER, CER and tone-context CER for every run and log them
- [ ] Fit the cross-language mixed-effects model (donor tonality × target tonality, script match, relatedness, budget; random effects for target and donor)
- [ ] Report per-language results, with "unclear"-tone languages as a separate group
- [ ] Train a DonorRank-style ranker with and without a tone-match feature; compare NDCG leave-one-target-out (H5)
- [ ] Run the WAXAL check outside India
- [ ] Run significance tests for every headline comparison
- [ ] Gate 3 decision: do tonal donors win on tone-context CER at low data?

### Phase 4 · Write and submit

- [ ] Generate every table and figure directly from the results log
- [ ] Write related work from the "Already done" and "What remains novel" sections
- [ ] Write method, setup, results, analysis and limitations
- [ ] Re-check novelty claims against the newest papers before submitting
- [ ] Release code, splits, grapheme mappings, tone-context lists and adapters
- [ ] Choose a venue and submit; if Gate 3 failed, frame the paper as a negative result with the probe evidence

## Language pool and data

This is a study, so the tone effect is tested across about 25 target languages rather than a few case studies. The pool crosses four factors: target tonality, whether IndicConformer saw the language, script match with the best donor, and language family.

### Tiers

- **Tier A (core):** all initialization conditions; budgets set per language.
- **Tier B (breadth):** fewer conditions, chosen per language from its data and complexity.
- **Tier C (outside India):** generalization check on WAXAL African languages (about 1,250 h, 19 languages), contrasting tonal Ewe, Ikposo, Akan and Dagbani with non-tonal donors such as Fula.

| Language | Family | Tonal? | Script | Seen by IndicConformer | VAANI transcribed (h) | Tier and role |
|---|---|---|---|---|---|---|
| Dogri | Indo-Aryan (Western Pahari) | yes | Devanagari | yes | 0 — use IndicVoices | A · tonal, seen |
| Bodo | Tibeto-Burman | yes | Devanagari | yes | not in VAANI — use IndicVoices | A · tonal, seen |
| Punjabi | Indo-Aryan | yes | Gurmukhi | yes | 20.4 | A · tonal, seen; also a donor |
| Mizo | Tibeto-Burman | yes | Latin | no | 20.7 | A · tonal, unseen |
| Wancho | Tibeto-Burman (Konyak) | likely | check | no | 11.9 | A · tonal, unseen |
| Tulu | Dravidian | no | check | no | 3.0 | A · non-tonal, unseen |
| Chhattisgarhi | Indo-Aryan | no | Devanagari | no | 17.7 | A · non-tonal, unseen |
| Santali | Austroasiatic | no | Ol Chiki (check) | yes | 0.12 — use IndicVoices | A · non-tonal, seen |
| Kokborok | Tibeto-Burman | yes | check | no | 3.8 | B · tonal, unseen |
| Manipuri | Tibeto-Burman | yes | check | yes | 0.46 — use IndicVoices | B · tonal, seen; also a donor |
| Sumi | Tibeto-Burman (Naga) | likely | check | no | 1.6 | B · test-only |
| Garo | Tibeto-Burman | unclear | Latin (check) | no | 47.1 | B; also a donor |
| Chakma | Indo-Aryan | unclear | check | no | 49.2 | B |
| Garhwali | Indo-Aryan (Central Pahari) | unclear | Devanagari | no | 8.8 | B |
| Kumaoni | Indo-Aryan (Central Pahari) | unclear | Devanagari | no | 2.5 | B |
| Nagamese | Assamese-based creole | no | check | no | 26.2 | B · non-tonal, unseen |
| Bhojpuri | Indo-Aryan | no | Devanagari | no | 26.6 | B · non-tonal, unseen |
| Marwari | Indo-Aryan | no | Devanagari | no | 9.0 | B · non-tonal, unseen |
| Magahi | Indo-Aryan | no | Devanagari | no | 6.5 | B · non-tonal, unseen |
| Bajjika | Indo-Aryan | no | Devanagari | no | 5.0 | B · non-tonal, unseen |
| Maithili | Indo-Aryan | no | Devanagari | yes | 20.8 | B · non-tonal, seen |
| Nepali | Indo-Aryan | no | Devanagari | yes | 38.1 | B · non-tonal, seen; also a donor |
| Odia | Indo-Aryan | no | Odia | yes | 51.2 | B · non-tonal, seen; also a donor |
| Konkani | Indo-Aryan | no | Devanagari | yes | 4.0 | B · non-tonal, seen |
| Hindi | Indo-Aryan | no | Devanagari | yes | 1,004 | Donor |
| Bengali | Indo-Aryan | no | Bengali | yes | 162.4 | Donor |
| Marathi | Indo-Aryan | no | Devanagari | yes | 68.1 | Donor |
| Assamese | Indo-Aryan | no | Assamese | yes | 33.4 | Donor |
| Kannada | Dravidian | no | Kannada | yes | 151.1 | Donor (for Tulu) |

Tone status comes from general knowledge and must be checked against WALS, PHOIBLE or a reference grammar. Languages marked "unclear" form their own group in the analysis instead of being forced into tonal or non-tonal. VAANI hours are from the dataset card; IndicVoices hours still need to be collected.

Access: VAANI on Hugging Face, CC BY 4.0, gated (log in and accept the conditions). Load per language, e.g. `load_dataset("ARTPARK-IISc/VAANI", "Mizo", token=...)`. Totals: about 31,278 h of audio and 2,122 h transcribed, across 105 languages (VAANI paper).

### Caveats

- VAANI is spontaneous, noisy and code-mixed; inconsistent spelling raises WER (Dialect Matters).
- Small subsets (Kokborok 3.8 h, Tulu 3.0 h, Kumaoni 2.5 h, Sumi 1.6 h) leave little test data, so their budgets are set accordingly.
- Scripts of several VAANI subsets, and whether each tonal language's spelling marks tone, are open checks.

## How: experimental setup

One grid answers all four hypotheses: targets × donor initializations × data budgets, on two backbones, scored with tone-specific metrics.

### Backbones

- **IndicConformer-600M-Multi** (NeMo checkpoint, not the ONNX release). Encoder frozen; train a per-language adapter and head. Dogri, Bodo and Santali were seen in pre-training, so discard their own heads, re-initialize from a donor, and frame this as low-resource adaptation. Mizo, Kokborok and Tulu were never seen, so they give the clean test on this backbone.
- **Our from-scratch Devanagari models** (Marathi base, several sizes). Targets are truly held out here, so this is the clean test. Model size becomes an ablation.

### Initialization conditions

| Condition | What it means | Dogri example | Mizo example |
|---|---|---|---|
| Random / zero-init | No donor | — | — |
| Same-script, non-tonal donor | Best donor sharing the target's script, without tone | Hindi | Garo (if non-tonal) |
| Tonal donor | Closest tonal language; cross-script via phonetic grapheme mapping when needed | Punjabi | Manipuri |
| Ranked donor | Top pick of a DonorRank-style ranker (lang2vec + corpus features, no tone feature) | ranker's choice | ranker's choice |
| Two-donor blend (ablation) | Same-script + tonal donor | Hindi + Punjabi | Garo + Manipuri |
| Upper bound | IndicConformer's own target head | yes | not available (unseen) |

Budgets and runs: set per language, not fixed in advance. Each language's data budgets, seeds and donor set follow from its transcribed hours and its complexity (tone inventory, script, orthographic consistency, relatedness to donors).

### Metrics and analyses

- WER and CER overall.
- Tone-context CER: CER restricted to tone-bearing characters or words. This is the main metric, because WER can hide tone errors.
- Character confusion matrices for aspirate vs plain letters (H2).
- Layer-wise linear tone probes on frozen encoder features (H1). If Dogri spelling encodes tone, the spelling itself supplies probe labels.
- Significance via matched-pairs or bootstrap tests.

### Analysis across languages

- One mixed-effects model over all targets: tone-context CER ~ donor tonality × target tonality + script match + relatedness + data budget, with random effects for target and donor. The interaction term is the main test.
- Per-language results reported alongside, with "unclear"-tone languages as a separate group.
- Tone-match ranking test (H5): add a donor–target tonality-match feature to a DonorRank-style ranker and compare ranking quality (NDCG) with and without it, leave-one-target-out.

Tools: AI4Bharat NeMo fork for training; Aksharamukha-style transliteration for the Gurmukhi→Devanagari grapheme mapping.

## Risks and confounds

The biggest risk is that the effect is real but small: earlier work found Hindi a good donor for Punjabi (ATDS), so measure tone-context CER, not just WER.

| Risk | Why it matters | Mitigation |
|---|---|---|
| Dogri spelling may not encode tone | H2 and the free probe labels both depend on it | Confirm with a reference grammar or a Dogri linguist before Phase 1; fallback: Punjabi as a simulated low-resource target |
| Tone confounded with relatedness | Punjabi is both tonal and closer to Dogri than Hindi is | H4's within-language contrast (tone-bearing vs other words) and the Santali control |
| Effect may hide in WER | ATDS found Hindi helps Punjabi overall | Tone-context CER as the primary metric |
| Encoder leakage in IndicConformer | Targets were in pre-training | Report as low-resource adaptation; base clean claims on unseen VAANI targets (Mizo, Kokborok, Tulu) and the from-scratch study |
| Cross-script mapping errors | Gurmukhi→Devanagari is not one-to-one everywhere | Rule-based transliteration plus a hand-checked mapping table |
| Dogri data quality and size | Small or noisy test sets weaken significance | VAANI has no transcribed Dogri; source it from IndicVoices; report confidence intervals |
| Scoop | The DonorRank / Dialect Matters group already works on Pahari varieties | Post an arXiv preprint once H2 holds |

Open checks: tone status of every pool language (WALS, PHOIBLE or a grammar); scripts of the VAANI subsets; whether spelling marks tone in each tonal target; whether lang2vec phonology vectors include tone features.

Breadth risks: with about 25 targets, mislabelled tone status would blur the interaction, so "unclear" languages stay a separate group; compute grows with the pool, so each language's grid is sized to its data and complexity.

## Positioning and references

Use this framing in the introduction and abstract:

> DonorRank (Dhasmana et al., 2026) learns donor rankings for zero-shot ASR within Devanagari Indo-Aryan varieties, and Shen et al. (2024) show that ASR fine-tuning on a non-tonal language erases tone. We study the case these leave open: low-resource adaptation of tonal Indic languages, where the closest same-script donor is non-tonal and the closest tonal donor uses another script.

What not to say: "first to blend donor weights", "similarity alone fails" (both shown before), or "first tone-aware adaptation" (SITA).

### Key references

- Dhasmana, Srivastava, Chiang (2026). DonorRank
- Dhasmana, Srivastava, Chiang (2026). Dialect Matters
- Shen et al. (2024). Encoding of lexical tone in self-supervised models
- Xu et al. (2026). SITA
- Latent Softmax across tonal and non-tonal languages (2026)
- Dang, Qian, Knill (2026). SeqStack
- San et al. (2024). ATDS: predicting positive transfer
- Song et al. (2024). LoRA-Whisper
- Das et al. (2025). ConsNoTrainLoRA
- Bowden (2012). Punjabi Tonemics and the Gurmukhi Script
- AI4Bharat. IndicConformer-600M-Multi
