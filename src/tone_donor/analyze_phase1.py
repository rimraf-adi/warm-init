"""Step 0 analysis of the head-only runs: per-utterance error counts from the saved test predictions,
tone-character CER vs a count-matched control set, paired bootstrap over test utterances.

    uv run python -m tone_donor.analyze_phase1 [backbone_label]      (default: indicconformer_hi_frozen_encoder)
Writes results/phase1/analysis_<backbone>.json and prints a markdown table.

Definitions (fixed before looking at results, see NOTES.md roadmap):
  tone positions    : ह and the virama right after it (Dogri, tone_positions(..., "ha")).
  control positions : occurrences of other Devanagari consonants (U+0915-U+0939 minus ह, not aspirates), taken in
                      order of how close each character's test-set count is to the tone-position count, until
                      the control count reaches the tone count. Same reference text for both, so rarity of
                      the text is matched in count but not in per-character difficulty (a per-character table
                      is written to the JSON for that reason).
  Seeds are pooled by summing error counts per utterance; resampling is over utterances.
"""
import collections
import json
import random
import sys

from tone_donor.runlog import read_runs
from tone_donor.text import ASPIRATES_DEVANAGARI, PLAIN_DEVANAGARI, _align, tone_positions

CONS = {chr(c) for c in range(0x0915, 0x093A)} - {"ह"}


def load_pairs(path):
    return [(d["ref"], d["hyp"]) for d in map(json.loads, open(path, encoding="utf-8"))]


def pick_control(refs, n_target):
    cnt = collections.Counter(ch for r in refs for ch in r if ch in CONS and ch not in ASPIRATES_DEVANAGARI)
    ha = sum(len(tone_positions(r, "dogri", "ha")) for r in refs)
    chosen, tot = [], 0
    for ch, n in sorted(cnt.items(), key=lambda kv: abs(kv[1] - ha / 3)):
        if tot >= n_target:
            break
        chosen.append(ch)
        tot += n
    return set(chosen), tot


def per_utt(pairs, ctrl):
    out = []
    for ref, hyp in pairs:
        err, edits = _align(ref, hyp)
        tp = tone_positions(ref, "dogri", "ha")
        cp = {i for i, ch in enumerate(ref) if ch in ctrl}
        ap = {i for i, ch in enumerate(ref) if ch in ASPIRATES_DEVANAGARI}
        pp = {i for i, ch in enumerate(ref) if ch in PLAIN_DEVANAGARI}
        out.append((edits, len(ref), sum(err[i] for i in tp), len(tp), sum(err[i] for i in cp), len(cp),
                    sum(err[i] for i in ap), len(ap), sum(err[i] for i in pp), len(pp)))
    return out


def metrics(rows):
    s = [sum(r[i] for r in rows) for i in range(10)]
    d = lambda a, b: a / b if b else float("nan")
    cer, tone, ctrl, asp, pln = d(s[0], s[1]), d(s[2], s[3]), d(s[4], s[5]), d(s[6], s[7]), d(s[8], s[9])
    return {"cer": cer, "tone": tone, "ctrl": ctrl, "tone_minus_ctrl": tone - ctrl, "tone_over_cer": d(tone, cer),
            "asp": asp, "plain": pln, "asp_minus_plain": asp - pln}


def pooled(arm_runs):
    """Sum per-utterance counts over seeds."""
    n = len(arm_runs[0])
    return [tuple(sum(run[i][k] for run in arm_runs) for k in range(10)) for i in range(n)]


def ci(vals):
    v = sorted(vals)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]


def main(backbone="indicconformer_hi_frozen_encoder", B=2000):
    runs = {}
    for r in read_runs():
        if r["stage"] == "phase1" and r["status"] == "done" and r["backbone"] == backbone:
            key = (r["init"], round(r["budget_h"] * 4) / 4 if r["budget_h"] < 4.9 else 5.0, r["seed"])
            runs[key] = r                                      # later duplicates replace earlier ones
    refs0 = [p[0] for p in load_pairs(next(iter(runs.values()))["artifacts"]["predictions"])]
    n_target = sum(len(tone_positions(r, "dogri", "ha")) for r in refs0)
    ctrl, n_ctrl = pick_control(refs0, n_target)
    print(f"control characters {''.join(sorted(ctrl))}  (count {n_ctrl} vs tone count {n_target})")
    data = {}
    for (init, h, s), r in sorted(runs.items()):
        pairs = load_pairs(r["artifacts"]["predictions"])
        assert [p[0] for p in pairs] == refs0, "test references differ between runs"
        data.setdefault((init, h), []).append(per_utt(pairs, ctrl))
    random.seed(0)
    n = len(refs0)
    res = {}
    lines = ["| budget h | arm | seeds | CER | tone CER | control CER | tone-control [95% CI] | tone/CER | aspirate | plain |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    boots = {}
    for (init, h), seed_runs in sorted(data.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        pl = pooled(seed_runs)
        m = metrics(pl)
        bs = [metrics([pl[random.randrange(n)] for _ in range(n)]) for _ in range(B)]
        boots[(init, h)] = bs
        lo, hi = ci([b["tone_minus_ctrl"] for b in bs])
        res[f"{init}|{h}"] = {"seeds": len(seed_runs), **m, "tone_minus_ctrl_ci": [lo, hi]}
        lines.append(f"| {h} | {init} | {len(seed_runs)} | {m['cer']:.3f} | {m['tone']:.3f} | {m['ctrl']:.3f} | "
                     f"{m['tone_minus_ctrl']:+.3f} [{lo:+.3f}, {hi:+.3f}] | {m['tone_over_cer']:.2f} | {m['asp']:.3f} | {m['plain']:.3f} |")
    lines += ["", "Hindi-init minus random-init (paired bootstrap over test utterances, seeds pooled):", "",
              "| budget h | d CER [95% CI] | d tone CER [95% CI] | d (tone-control) [95% CI] |", "|---|---|---|---|"]
    for h in sorted({k[1] for k in data}):
        if ("hindi", h) not in data or ("random", h) not in data:
            continue
        ph, pr = pooled(data[("hindi", h)]), pooled(data[("random", h)])
        diffs = {"cer": [], "tone": [], "tmc": []}
        for _ in range(B):
            idx = [random.randrange(n) for _ in range(n)]
            a, b = metrics([ph[i] for i in idx]), metrics([pr[i] for i in idx])
            diffs["cer"].append(a["cer"] - b["cer"])
            diffs["tone"].append(a["tone"] - b["tone"])
            diffs["tmc"].append(a["tone_minus_ctrl"] - b["tone_minus_ctrl"])
        mh, mr = metrics(ph), metrics(pr)
        f = lambda k, x: f"{x:+.3f} [{ci(diffs[k])[0]:+.3f}, {ci(diffs[k])[1]:+.3f}]"
        lines.append(f"| {h} | {f('cer', mh['cer'] - mr['cer'])} | {f('tone', mh['tone'] - mr['tone'])} | "
                     f"{f('tmc', mh['tone_minus_ctrl'] - mr['tone_minus_ctrl'])} |")
        res[f"hindi-minus-random|{h}"] = {k: [mh[k2] - mr[k2], *ci(diffs[k])] for k, k2 in
                                          (("cer", "cer"), ("tone", "tone"), ("tmc", "tone_minus_ctrl"))}
    out = f"results/phase1/analysis_{backbone}.json"
    json.dump({"control_chars": sorted(ctrl), "control_count": n_ctrl, "tone_count": n_target, "bootstrap": B,
               "results": res}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(lines))
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:2])
