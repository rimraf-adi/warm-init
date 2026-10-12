# Novelty check — Tone-Aware Donor Transfer for Indic ASR

Date: 2026-10-12. Checked by Claude (Opus 5.5) using web search and arXiv page reads.
This is an in-project AI reading, not an outside review. It checks [plan.md](plan.md).

## Verdict

- **The core question survives.** No source that loaded compares a same-script non-tonal donor with a cross-script tonal donor for a tonal target, or scores donors with a tone-context error metric, or adds a tonality-match feature to a donor ranker.
- **Three gaps and H1 are narrower than the plan states.** Four uncited papers cover part of gaps 1, 4 and 5 and most of the H1 mechanism outside Indic languages.
- **One prior result argues against H3 on WER.** Related and unrelated auxiliary languages came out equivalent from 1 h of target data upward on four models.
- **The 40–50% estimate looks high** until the four papers below are cited and the gaps reworded. This is my judgement, not a measurement.
- **Reach of this check:** about 25 web searches and 12 page reads. The OpenAlex lookup tool was down, and Google Scholar, Semantic Scholar and the ISCA archive were not searched directly. Absence here is not proof of absence.

## Papers to add

| Paper | What it shows | Hits | Access |
|---|---|---|---|
| Kim, Um, Kim (2025). *How Far Do SSL Speech Models Listen for Tone?* [arXiv 2511.12285](https://arxiv.org/abs/2511.12285) | Tone probes on Burmese, Thai, Lao, Vietnamese. Mandarin-ASR fine-tuning gives better tone probes on these targets than English-ASR fine-tuning. No WER or CER | H1; gap 1 | Full HTML via summarizer |
| Gogoi et al. (Interspeech 2025). *Tone recognition in low-resource languages of North-East India* [arXiv 2506.03606](https://arxiv.org/abs/2506.03606) | Layer-wise tone probes on Mizo, Angami, Ao with wav2vec2 models pre-trained on tonal vs non-tonal languages. Middle layers carry tone either way. No ASR fine-tuning, no WER | Gap 1; H1 on Mizo | Full HTML via summarizer |
| Florian et al. (2026). *Evaluating the Effect of Linguistic Relatedness on Cross-Lingual Transfer in Large Multilingual ASR* [arXiv 2607.04814](https://arxiv.org/abs/2607.04814) | Pre-adapting on a related vs unrelated auxiliary is practically equivalent from 1 h of target data (±5 WER points) on Whisper Small, Whisper Large v3, XLS-R, OmniASR. Notes that transcripts do not capture tone; no tone analysis | H3; gaps 4, 5 | Full HTML via summarizer |
| Wang et al. (2024). *How to Learn a New Language?* [arXiv 2411.18217](https://arxiv.org/abs/2411.18217) | Adapter warmed up on tree-selected related source languages, then fine-tuned on the target at 10 min and 1 h; HuBERT, mHuBERT, XLSR-128. No tone, phonology or script criterion | Gap 4 | Full HTML via summarizer |

Seen in search summaries only, not opened: *Tone in Yoruba ASR* ([LoResLM 2026](https://aclanthology.org/2026.loreslm-1.14.pdf)), *Tone-Conditioned Curriculum Learning for Low-Resource Bantu Speech Recognition* (arXiv 2606.31642, adapters gated by tonal statistics), *Which Languages Transfer Best to Warlpiri?* ([arXiv 2607.10256](https://arxiv.org/abs/2607.10256)), Wu et al. (ASRU 2021) on acoustic language similarity. Open the Bantu paper before claiming gap 6.

## Gap-by-gap status

| # | Gap in the plan | Status | Reword to |
|---|---|---|---|
| 1 | Tone beyond Mandarin and Vietnamese, inside multilingual models | Narrowed | Mizo, Angami, Ao, Burmese, Thai and Lao are already probed in SSL models. Open part: Dogri, Bodo, Punjabi, and a supervised multilingual ASR encoder |
| 2 | Tone written indirectly through consonant letters | Needs a factual fix | Holds for Punjabi. Dogri marks tone explicitly (see below) |
| 3 | Same-script vs same-phonology donor | Not found | Keep |
| 4 | Low-resource adaptation with target data | Closed as a general gap | SeqStack and Wang et al. already do donor choice followed by target fine-tuning at 1 h. Open part: doing it with a tone criterion and a tone metric |
| 5 | Backbones other than Whisper or one SSL model | Narrowed | Florian et al. cover Whisper, XLS-R and OmniASR. Open part: a Conformer with CTC+RNNT and per-language heads |
| 6 | Tone-awareness without a WER cost | Not found, one unread candidate | Keep, after reading the Bantu curriculum paper |
| 7 | Aspiration errors left unexplained | Confirmed | Dialect Matters Table 6 lists aspiration errors (ब vs भ) and explains only the length and halant patterns |
| 8 | Tonal targets lose to tonal neighbours on CER | Half confirmed | DonorRank does not discuss WAXAL by tonality. The "lose to tonal neighbours" pattern was not checked against Table 3 |

H5 (tonality-match feature in a ranker): not found. DonorRank's lang2vec features include WALS-derived phonology, which may already carry tone; the plan lists this as an open check and it decides how new H5 is.

## Factual corrections to the plan

1. **Dogri orthography.** The Unicode Standard 16.0, section 12.1, says Dogri writes a high-falling tone with U+02BC MODIFIER LETTER APOSTROPHE (*sur chinha*) after short vowels and with ह after long vowels. For Gurmukhi (section 12.3) it says there are no tone signs and that gha, jha, ddha, dha and ha carry tone. So the "indirect, through consonant letters" story is Punjabi's. Consequences for Gate 0 (my reasoning):
   - The H2 letter set घ झ ढ ध भ may not be where Dogri spelling marks tone.
   - Punctuation stripping in transcript normalization would delete U+02BC and erase the tone signal. Check whether IndicVoices Dogri transcripts and the IndicConformer Dogri vocabulary contain it.
   - Secondary sources on Dogri tone phonology disagree with each other; a reference grammar is still needed.
2. **DonorRank variety count.** The paper says 20 Devanagari varieties in the data section, lists 18 targets in Table 8, and says "all 19 varieties" in section 6.1. Cite the number with its location.
3. **Shen et al.** They note in a footnote that Mandarin writing does not mark tone and Vietnamese does. They do not compare the two orthographies' effect. "Compare only unmarked and marked tone" overstates it.
4. **Gogoi et al. caution.** A search summary credited them with showing that tonal ASR fine-tuning helps tone recognition. The paper attributes that to prior work and lists it as their future work.
5. **Dialect Matters** now has a venue: VarDial 2026, pp. 145–156 ([ACL Anthology](https://aclanthology.org/2026.vardial-1.12)).

## Reference check

| Reference in plan | Exists | Claim in plan | Access |
|---|---|---|---|
| DonorRank, Dhasmana, Srivastava, Chiang, [arXiv 2608.11441](https://arxiv.org/abs/2608.11441) | Yes | Zero-shot only, fixed w2vBERT, k = 2–4 saturation, single script: confirmed | Full HTML via summarizer |
| Dialect Matters, [arXiv 2601.04373](https://arxiv.org/abs/2601.04373) | Yes | Devanagari only, similarity does not fully explain transfer, aspiration errors unexplained: confirmed | Full HTML via summarizer |
| Shen et al., NAACL 2024, [arXiv 2403.16865](https://arxiv.org/abs/2403.16865) | Yes | Non-tonal fine-tuning lowers tone probes; multilingual models named as future work: confirmed | Full HTML via summarizer |
| SITA, Xu et al., [arXiv 2601.09050](https://arxiv.org/abs/2601.09050) | Yes | Tone-repulsive loss for Hmong: confirmed. "Stated trade-off" on ASR: abstract only | Abstract |
| SeqStack, Dang, Qian, Knill, [arXiv 2609.15758](https://arxiv.org/abs/2609.15758) | Yes | Layer-band encoder similarity, other backbones left for future work: confirmed. Also ranks sources and fine-tunes at 1 h, on Assamese among others | PDF read directly |
| Adapting Where It Matters, Findings of ACL 2026, [arXiv 2602.01008](https://arxiv.org/abs/2602.01008) | Yes | "Layer-wise language probes" wording not confirmed | Search summary |
| Latent Softmax, [arXiv 2608.01281](https://arxiv.org/abs/2608.01281) | Yes | Not used for a claim | Search summary |
| SimMerge, [arXiv 2601.09473](https://arxiv.org/abs/2601.09473); LoRA.rar, ICCV 2025 | Yes | As described | Search summary |
| ATDS, San et al., [SIGTYP 2024](https://aclanthology.org/2024.sigtyp-1.13/) | Yes | Hindi helps Punjabi: confirmed | Search summary |
| LoRA-Whisper, Song et al., Interspeech 2024 | Yes | Seen in SeqStack's reference list, which describes it as warm initialization. "Poor donor worse than scratch" not checked | Indirect |
| Bowden, *Punjabi Tonemics and the Gurmukhi Script* | Title found | Year 2012 not confirmed | Search summary |
| AdapterSoup, LoraHub, ConsNoTrainLoRA, EVA, CorDA | Not checked | Not checked | None |
| IndicConformer seen languages, VAANI hours, WAXAL hours | Not checked | Not checked | None |

## Search log

All searches ran on 2026-10-12. Each conclusion holds only within what opened.

| Query topic | Opened | Conclusion |
|---|---|---|
| Tone-aware donor selection, Punjabi, Dogri | Search summary | No tone-aware donor study found; ATDS and DonorRank surfaced |
| Tone probing in multilingual ASR, Punjabi, Bodo, Mizo | arXiv 2506.03606 | Found Gogoi et al. |
| Tonal vs non-tonal donor for a tonal target | arXiv 2511.12285, 2403.16865 | Found Kim et al.; no WER-level comparison found |
| Script vs phonological similarity, cross-script donor | arXiv 2607.04814 | Found Florian et al.; no script-vs-phonology contrast found |
| Dogri tone orthography | Unicode 16.0 ch. 12 | Explicit tone marks in Dogri |
| Punjabi ASR tone errors, aspirate letters | Search summary | No Punjabi ASR tone-error analysis found |
| Dogri ASR tone errors, IndicVoices, IndicConformer | Search summary | None found |
| Bodo, Mizo, Manipuri, Kokborok ASR tone errors | Search summary | None found for ASR output; ManiTo (ICON 2021) is tone recognition |
| Tonal donor for African tonal ASR, Whisper, MMS | Search summary | None found |
| IndicConformer adapters on unseen VAANI languages | arXiv 2411.18217 | Found Wang et al.; no IndicConformer adapter study found |
| lang2vec tone feature in donor ranking | Search summary | None found |
| Tonal source-language selection for tonal targets | Search summary | None found; Bantu curriculum paper surfaced, unread |
| Each named reference (nine queries) | See reference table | All found |

Blocked: the OpenAlex reference-lookup tool (HTTP 429 and timeouts on all nine calls), so no reference was checked against OpenAlex. Page reads went through a summarizing fetcher, except the SeqStack PDF, which was read directly.
