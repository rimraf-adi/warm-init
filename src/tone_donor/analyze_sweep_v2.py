"""P4 check: zero-shot sweep on the v2 test split, speaker-cluster bootstrap, Punjabi head vs Hindi head.

    uv run python -m tone_donor.analyze_sweep_v2
Needs results/phase1/zero_shot_hyps_dogri_v2_test/<lang>.jsonl (with speaker ids).
"""
import collections
import json
import random

from tone_donor.analyze_v2 import per_utt, rates

D = "results/phase1/zero_shot_hyps_dogri_v2_test"
LANGS = ["doi", "hi", "pa", "mai", "mr", "ne", "bn", "gu", "kok", "brx", "kn"]


def main(draws=2000):
    data, spk = {}, None
    for l in LANGS:
        rows, s = per_utt(f"{D}/{l}.jsonl")
        data[l] = rows
        spk = spk or s
    by = collections.defaultdict(list)
    for i, s in enumerate(spk):
        by[s].append(i)
    keys = list(by)
    rnd = random.Random(0)
    idxs = [[i for k in (rnd.choice(keys) for _ in keys) for i in by[k]] for _ in range(draws)]
    boots = {l: [rates([data[l][i] for i in ix]) for ix in idxs] for l in LANGS}
    ci = lambda v: (sorted(v)[int(0.025 * len(v))], sorted(v)[int(0.975 * len(v)) - 1])
    print("speakers", len(keys), "utterances", len(spk))
    print("| head | CER [95% CI] | tone-mark CER [95% CI] | ordinary-ha CER [95% CI] |\n|---|---|---|---|")
    for l in LANGS:
        p = rates(data[l])
        c = {m: ci([b[m] for b in boots[l]]) for m in p}
        print(f"| {l} | " + " | ".join(f"{p[m]:.3f} [{c[m][0]:.3f}, {c[m][1]:.3f}]" for m in ("cer", "mark", "plain")) + " |")
    print("\nPaired difference to Hindi (head minus hi):\n\n| head | d CER | d tone-mark | d ordinary-ha |\n|---|---|---|---|")
    ph = rates(data["hi"])
    res = {}
    for l in LANGS:
        if l in ("hi", "doi"):
            continue
        p = rates(data[l])
        row = {}
        for m in ("cer", "mark", "plain"):
            lo, hi = ci([b[m] - h[m] for b, h in zip(boots[l], boots["hi"])])
            row[m] = (p[m] - ph[m], lo, hi)
        res[l] = row
        print(f"| {l} | " + " | ".join(f"{row[m][0]:+.3f} [{row[m][1]:+.3f}, {row[m][2]:+.3f}]" for m in row) + " |")
    pa = res["pa"]
    p4 = pa["mark"][0] < -0.10 and pa["mark"][2] < 0 and pa["plain"][1] <= 0 <= pa["plain"][2]
    print("\nP4 (Punjabi tone-mark CER lower than Hindi by >0.10 with CI below 0, ordinary-ha CI includes 0):", p4)
    json.dump({"diff_vs_hi": res, "P4": bool(p4)}, open("results/phase1/zero_shot_sweep_ci_v2.json", "w"), indent=1)


if __name__ == "__main__":
    main()
