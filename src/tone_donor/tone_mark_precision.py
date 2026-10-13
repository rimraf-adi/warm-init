"""Does a head emit the ha+virama tone mark where Dogri has it (detection), or indiscriminately (habit)?

Per utterance, count occurrences of "ha+virama" in the reference and in the hypothesis of each zero-shot head.
recall    = sum(min(ref, hyp)) / sum(ref)        (how many reference tone marks are produced)
precision = sum(min(ref, hyp)) / sum(hyp)        (how many produced tone marks are in the reference)
Also the Spearman correlation across utterances between the reference and hypothesis counts, and hypothesised marks
per 100 reference characters. Speaker-cluster bootstrap for precision and recall.

    uv run python -m tone_donor.tone_mark_precision
Reads results/phase1/zero_shot_hyps_dogri_v2_test/<lang>.jsonl.
"""
import collections
import json
import random

D = "results/phase1/zero_shot_hyps_dogri_v2_test"
MARK = "ह्"


def load(lang):
    rows = [json.loads(l) for l in open(f"{D}/{lang}.jsonl", encoding="utf-8")]
    return [(r["ref"].count(MARK), r["hyp"].count(MARK), len(r["ref"]), r["speaker"]) for r in rows]


def pr(rows):
    m = sum(min(a, b) for a, b, _, _ in rows)
    return m / max(sum(a for a, _, _, _ in rows), 1), m / max(sum(b for _, b, _, _ in rows), 1)


def spearman(rows):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2
            i = j + 1
        return r
    a, b = rank([x[0] for x in rows]), rank([x[1] for x in rows])
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


def main(draws=1000):
    langs = ["doi", "hi", "pa", "mai", "mr", "ne", "bn", "gu", "kok", "brx", "kn"]
    data = {l: load(l) for l in langs}
    spk = [r[3] for r in data["hi"]]
    by = collections.defaultdict(list)
    for i, s in enumerate(spk):
        by[s].append(i)
    keys = list(by)
    rnd = random.Random(0)
    idx = [[i for k in (rnd.choice(keys) for _ in keys) for i in by[k]] for _ in range(draws)]
    ci = lambda v: (sorted(v)[int(0.025 * len(v))], sorted(v)[int(0.975 * len(v)) - 1])
    print("reference tone marks:", sum(r[0] for r in data["hi"]), "in", len(data["hi"]), "utterances")
    print("| head | recall [95% CI] | precision [95% CI] | marks produced per reference mark | Spearman ref vs hyp counts |\n|---|---|---|---|---|")
    for l in langs:
        rows = data[l]
        rec, prec = pr(rows)
        bs = [pr([rows[i] for i in ix]) for ix in idx]
        rc, pc = ci([b[0] for b in bs]), ci([b[1] for b in bs])
        ratio = sum(r[1] for r in rows) / max(sum(r[0] for r in rows), 1)
        print(f"| {l} | {rec:.3f} [{rc[0]:.3f}, {rc[1]:.3f}] | {prec:.3f} [{pc[0]:.3f}, {pc[1]:.3f}] | {ratio:.2f} | {spearman(rows):.3f} |")


if __name__ == "__main__":
    main()
