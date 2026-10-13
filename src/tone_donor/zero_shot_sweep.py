"""Step 1: zero-shot sweep. Decode cached multilingual-encoder features of a target with every language head.

For each head language: greedy CTC over that language's output columns (+ blank), tokens -> text with that
language's tokenizer, then mapped to Devanagari by Unicode offset (tone_donor.translit) so it can be scored
against a Devanagari reference. Scripts without an offset mapping (Latin, Arabic-script, Ol Chiki, Meetei) are
decoded but not scorable; they are reported as such. No training. Run in the WSL env:

    BACKBONE=multi python -m tone_donor.zero_shot_sweep /home/vnit/data/dogri_multi test
Writes results/phase1/zero_shot_sweep_dogri_<split>.json and logs one run per head.
"""
import json
import os
import sys

import editdistance
import torch

from tone_donor.prep_features import backbone_name, load_encoder
from tone_donor.runlog import log_run, read_runs
from tone_donor.text import normalize, tone_cer
from tone_donor.translit import BLOCK_START, DEVANAGARI_LANGS, to_devanagari
from tone_donor.vaani_stream import _load_dotenv

FAMILY = {  # coarse family / tonality of each head language (general knowledge; not verified here)
    "hi": ("Indo-Aryan", "non-tonal"), "mr": ("Indo-Aryan", "non-tonal"), "ne": ("Indo-Aryan", "non-tonal"),
    "mai": ("Indo-Aryan", "non-tonal"), "kok": ("Indo-Aryan", "non-tonal"), "sa": ("Indo-Aryan", "non-tonal"),
    "gu": ("Indo-Aryan", "non-tonal"), "bn": ("Indo-Aryan", "non-tonal"), "as": ("Indo-Aryan", "non-tonal"),
    "or": ("Indo-Aryan", "non-tonal"), "pa": ("Indo-Aryan", "tonal"), "doi": ("Indo-Aryan", "tonal"),
    "ur": ("Indo-Aryan", "non-tonal"), "sd": ("Indo-Aryan", "non-tonal"), "ks": ("Indo-Aryan", "non-tonal"),
    "brx": ("Tibeto-Burman", "tonal"), "mni": ("Tibeto-Burman", "tonal"), "sat": ("Austroasiatic", "non-tonal"),
    "ta": ("Dravidian", "non-tonal"), "te": ("Dravidian", "non-tonal"), "kn": ("Dravidian", "non-tonal"),
    "ml": ("Dravidian", "non-tonal"),
}
SCORABLE = DEVANAGARI_LANGS | set(BLOCK_START)


@torch.no_grad()
def decode(model, lang, feats):
    conv = model.ctc_decoder.decoder_layers[0]
    cols = torch.tensor([i for i, b in enumerate(model.ctc_decoder.language_masks[lang]) if b]).cuda()
    W = conv.weight.data[cols, :, 0]
    b = conv.bias.data[cols]
    blank = len(cols) - 1
    out = []
    for f in feats:
        am = (f.float() @ W.T + b).argmax(-1).cpu()
        keep = torch.ones_like(am, dtype=torch.bool)
        keep[1:] = am[1:] != am[:-1]
        ids = am[keep & (am != blank)].tolist()
        out.append(model.tokenizer.ids_to_text(ids, lang).strip())
    return out


def main(data_dir, split):
    _load_dotenv()
    model = load_encoder(os.environ["HF_TOKEN"])
    items = torch.load(os.path.join(data_dir, f"{split}.pt"))
    feats = [it["feat"].cuda() for it in items]
    refs = [it["text"] for it in items]
    res = {}
    done = {r["donor"] for r in read_runs() if r["stage"] == "step1-zero-shot" and r["status"] == "done"}
    hyp_dir = f"results/phase1/zero_shot_hyps_dogri_{split}"
    os.makedirs(hyp_dir, exist_ok=True)
    for lang in model.tokenizer.tokenizers_dict:
        hyp_raw = decode(model, lang, feats)
        row = {"family": FAMILY.get(lang, ("?", "?"))[0], "tonal": FAMILY.get(lang, ("?", "?"))[1]}
        if lang in SCORABLE:
            hyp = [normalize(to_devanagari(h, lang), drop_apos=True) for h in hyp_raw]
            with open(f"{hyp_dir}/{lang}.jsonl", "w", encoding="utf-8") as f:
                for r, h in zip(refs, hyp):
                    f.write(json.dumps({"ref": r, "hyp": h}, ensure_ascii=False) + "\n")
            m = tone_cer(list(zip(refs, hyp)), "dogri", "ha")
            e = sum(editdistance.eval(r, h) for r, h in zip(refs, hyp))
            we = sum(editdistance.eval(r.split(), h.split()) for r, h in zip(refs, hyp))
            row.update(scorable=True, cer=e / sum(len(r) for r in refs), wer=we / sum(len(r.split()) for r in refs),
                       tone_cer=m["tone_cer"], example=hyp[0][:80])
            if lang not in done:
              log_run(stage="step1-zero-shot", hypothesis="family", target="dogri", donor=lang, init=f"zero-shot-head-{lang}",
                      backbone="indicconformer_multi_frozen_encoder" if backbone_name() == "multi" else "indicconformer_hi_frozen_encoder",
                      split=f"speaker-disjoint {split}", n_utts=len(items), cer=row["cer"], wer=row["wer"],
                      tone_cer=row["tone_cer"], tone_chars=m["tone_chars"],
                      config={"decode": "greedy CTC on cached final-layer features", "script_map": "unicode offset to Devanagari"},
                      notes="no training; output mapped to Devanagari by offset, so cross-script rows are approximate")
        else:
            row.update(scorable=False, example=hyp_raw[0][:80])
        res[lang] = row
        print(lang, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items() if k != "example"}, flush=True)
    json.dump(res, open(f"results/phase1/zero_shot_sweep_dogri_{split}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
