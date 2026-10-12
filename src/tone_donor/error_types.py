"""Split errors on tone characters into deletions vs substitutions (character alignment on saved test predictions).

    uv run python -m tone_donor.error_types
Compares arms at 0.25 h on the multilingual backbone; writes results/phase1/error_types_multi_0.25h.json.
"""
import json
import collections

from tone_donor.runlog import read_runs
from tone_donor.text import tone_positions


def ops(ref, hyp):
    """Levenshtein with backtrace. Returns per-ref-char op: 'M' match, 'S' substitution, 'D' deletion; insertions counted."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]))
    out, ins, i, j = ["M"] * n, 0, n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            out[i - 1] = "M" if ref[i - 1] == hyp[j - 1] else "S"
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            out[i - 1] = "D"
            i -= 1
        else:
            ins += 1
            j -= 1
    return out, ins


def stats(path):
    c = collections.Counter()
    sub_to = collections.Counter()
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        ref, hyp = d["ref"], d["hyp"]
        o, ins = ops(ref, hyp)
        tp = tone_positions(ref, "dogri", "ha")
        c["ins_total"] += ins
        c["all_chars"] += len(ref)
        for k, op in enumerate(o):
            if op != "M":
                c["all_err"] += 1
            if op == "D":
                c["all_del"] += 1
            if k in tp:
                c["tone_n"] += 1
                c["tone_" + op] += 1
    return c


def main():
    arms = ["random", "hindi", "donor-hi+noblank", "donor-hi+comp+noblank", "donor-pa", "donor-pa+noblank"]
    runs = [r for r in read_runs() if r["stage"] == "phase1" and r["status"] == "done"
            and r["backbone"] == "indicconformer_multi_frozen_encoder" and r["budget_h"] < 0.5]
    res = {}
    print("| arm (0.25 h, 3 seeds pooled) | tone chars | tone deleted | tone substituted | tone error | all-char deletion rate | insertions per 100 chars |")
    print("|---|---|---|---|---|---|---|")
    for arm in arms:
        tot = collections.Counter()
        for r in runs:
            if r["init"] == arm:
                tot.update(stats(r["artifacts"]["predictions"]))
        if not tot:
            continue
        n = tot["tone_n"]
        res[arm] = dict(tot)
        print(f"| {arm} | {n} | {tot['tone_D'] / n:.3f} | {tot['tone_S'] / n:.3f} | {(tot['tone_D'] + tot['tone_S']) / n:.3f} | "
              f"{tot['all_del'] / tot['all_chars']:.3f} | {100 * tot['ins_total'] / tot['all_chars']:.2f} |")
    json.dump(res, open("results/phase1/error_types_multi_0.25h.json", "w"), indent=1)


if __name__ == "__main__":
    main()
