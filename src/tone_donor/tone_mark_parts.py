"""At the Dogri tone-mark spelling (ha followed by virama), which character does each zero-shot head get right?

Error rates per reference character, split into: the ha of a ha+virama mark, the virama of the mark, and ordinary ha
(ha not followed by virama). Deletion vs substitution is split with a character alignment. Speaker-cluster bootstrap
for the paired difference to Hindi.

    uv run python -m tone_donor.tone_mark_parts
"""
import collections
import json
import random

from tone_donor.error_types import ops

D = "results/phase1/zero_shot_hyps_dogri_v2_test"
VIRAMA = "्"
CLASSES = ("mark_ha", "mark_virama", "plain_ha")


def per_utt(lang):
    rows = []
    for line in open(f"{D}/{lang}.jsonl", encoding="utf-8"):
        d = json.loads(line)
        ref, hyp = d["ref"], d["hyp"]
        o, _ = ops(ref, hyp)
        c = {k: [0, 0, 0] for k in CLASSES}                       # n, deleted, substituted
        for i, ch in enumerate(ref):
            if ch == "ह":
                k = "mark_ha" if ref[i + 1:i + 2] == VIRAMA else "plain_ha"
            elif ch == VIRAMA and ref[i - 1:i] == "ह":
                k = "mark_virama"
            else:
                continue
            c[k][0] += 1
            c[k][1] += o[i] == "D"
            c[k][2] += o[i] == "S"
        rows.append((c, d["speaker"]))
    return rows


def rate(rows, k, which):
    n = sum(r[0][k][0] for r in rows)
    return sum(r[0][k][which] for r in rows) / max(n, 1)


def main(draws=1000):
    langs = ["doi", "hi", "pa", "mai", "mr", "ne", "bn"]
    data = {l: per_utt(l) for l in langs}
    by = collections.defaultdict(list)
    for i, (_, s) in enumerate(data["hi"]):
        by[s].append(i)
    keys = list(by)
    rnd = random.Random(0)
    idx = [[i for k in (rnd.choice(keys) for _ in keys) for i in by[k]] for _ in range(draws)]
    ci = lambda v: (sorted(v)[int(0.025 * len(v))], sorted(v)[int(0.975 * len(v)) - 1])
    print("positions:", {k: sum(r[0][k][0] for r in data["hi"]) for k in CLASSES})
    print("\nError rate (deleted + substituted) per reference character class:\n")
    print("| head | ha of tone mark | virama of tone mark | ordinary ha | ha of mark: deleted / substituted |\n|---|---|---|---|---|")
    for l in langs:
        r = data[l]
        print(f"| {l} | {rate(r, 'mark_ha', 1) + rate(r, 'mark_ha', 2):.3f} | {rate(r, 'mark_virama', 1) + rate(r, 'mark_virama', 2):.3f} | "
              f"{rate(r, 'plain_ha', 1) + rate(r, 'plain_ha', 2):.3f} | {rate(r, 'mark_ha', 1):.3f} / {rate(r, 'mark_ha', 2):.3f} |")
    print("\nPaired difference to Hindi (head minus hi), speaker-cluster 95% CI:\n")
    print("| head | ha of tone mark | virama of tone mark | ordinary ha |\n|---|---|---|---|")
    for l in langs:
        if l in ("hi", "doi"):
            continue
        row = []
        for k in CLASSES:
            f = lambda rows: rate(rows, k, 1) + rate(rows, k, 2)
            pt = f(data[l]) - f(data["hi"])
            bs = [f([data[l][i] for i in ix]) - f([data["hi"][i] for i in ix]) for ix in idx]
            lo, hi = ci(bs)
            row.append(f"{pt:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        print(f"| {l} | " + " | ".join(row) + " |")


if __name__ == "__main__":
    main()
