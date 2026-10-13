"""Bootstrap CIs for the zero-shot head sweep (needs results/phase1/zero_shot_hyps_dogri_<split>/<lang>.jsonl).

    uv run python -m tone_donor.analyze_sweep [split]
Per head: CER and ha-tone CER with 95% CIs (resampling test utterances). Paired differences versus Hindi (the
same-script non-tonal reference) for the tonal Punjabi head and the other Indo-Aryan heads. Also reports
aspirate-letter CER, because Punjabi writes tone on aspirate letters, to see whether the tone-character result
depends on which letters are counted.
"""
import json
import random
import sys

from tone_donor.text import ASPIRATES_DEVANAGARI, _align, tone_positions


def load(path):
    out = []
    for d in map(json.loads, open(path, encoding="utf-8")):
        err, edits = _align(d["ref"], d["hyp"])
        tp = tone_positions(d["ref"], "dogri", "ha")
        ap = {i for i, ch in enumerate(d["ref"]) if ch in ASPIRATES_DEVANAGARI}
        out.append((edits, len(d["ref"]), sum(err[i] for i in tp), len(tp), sum(err[i] for i in ap), len(ap)))
    return out


def rate(rows, k):
    num = sum(r[k] for r in rows)
    den = sum(r[k + 1] for r in rows) if k else sum(r[1] for r in rows)
    return num / den


def m(rows):
    return (sum(r[0] for r in rows) / sum(r[1] for r in rows), sum(r[2] for r in rows) / sum(r[3] for r in rows),
            sum(r[4] for r in rows) / sum(r[5] for r in rows))


def ci(v):
    v = sorted(v)
    return v[int(0.025 * len(v))], v[int(0.975 * len(v)) - 1]


def main(split="test", B=2000):
    d = f"results/phase1/zero_shot_hyps_dogri_{split}"
    langs = ["doi", "hi", "pa", "mai", "mr", "gu", "kok", "ne", "bn", "brx", "kn"]
    data = {l: load(f"{d}/{l}.jsonl") for l in langs}
    n = len(data["hi"])
    random.seed(0)
    idx = [[random.randrange(n) for _ in range(n)] for _ in range(B)]
    boots = {l: [m([data[l][i] for i in ix]) for ix in idx] for l in langs}
    print("| head | CER [95% CI] | tone CER [95% CI] | aspirate CER [95% CI] |\n|---|---|---|---|")
    for l in langs:
        pt = m(data[l])
        cs = [ci([b[k] for b in boots[l]]) for k in range(3)]
        print(f"| {l} | {pt[0]:.3f} [{cs[0][0]:.3f}, {cs[0][1]:.3f}] | {pt[1]:.3f} [{cs[1][0]:.3f}, {cs[1][1]:.3f}] | "
              f"{pt[2]:.3f} [{cs[2][0]:.3f}, {cs[2][1]:.3f}] |")
    print("\nPaired difference to Hindi (head minus hi), same resamples:\n\n| head | d CER | d tone CER | d aspirate CER |\n|---|---|---|---|")
    ph = m(data["hi"])
    res = {}
    for l in langs:
        if l in ("hi", "doi"):
            continue
        pl = m(data[l])
        row = []
        for k in range(3):
            diffs = [boots[l][b][k] - boots["hi"][b][k] for b in range(B)]
            lo, hi = ci(diffs)
            row.append((pl[k] - ph[k], lo, hi))
        res[l] = row
        print(f"| {l} | " + " | ".join(f"{x:+.3f} [{lo:+.3f}, {hi:+.3f}]" for x, lo, hi in row) + " |")
    json.dump(res, open(f"results/phase1/zero_shot_sweep_ci_{split}.json", "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:2])
