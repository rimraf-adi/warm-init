"""Analysis of the v2 head-only grid with speaker-cluster bootstrap, plus a mechanical check of predictions P1-P3.

    uv run python -m tone_donor.analyze_v2
Reads predictions (with speaker ids) of runs whose config.split_tag is v2. Seeds are pooled by summing errors per
utterance. Also prints per-seed means and spread (seeds vary the training speakers as well as initialisation).
Writes results/phase1/analysis_v2.json.
"""
import collections
import json
import random

from tone_donor.runlog import read_runs
from tone_donor.text import _align

VIRAMA = "्"


def per_utt(path):
    out, spk = [], []
    for d in map(json.loads, open(path, encoding="utf-8")):
        ref, hyp = d["ref"], d["hyp"]
        err, edits = _align(ref, hyp)
        mark = {i for i, c in enumerate(ref) if c == "ह" and ref[i + 1:i + 2] == VIRAMA}
        mark |= {i + 1 for i in mark}
        plain = {i for i, c in enumerate(ref) if c == "ह" and ref[i + 1:i + 2] != VIRAMA}
        out.append((ref, edits, len(ref), sum(err[i] for i in mark), len(mark), sum(err[i] for i in plain), len(plain)))
        spk.append(d["speaker"])
    return out, spk


def rates(rows):
    s = [sum(r[k] for r in rows) for k in range(1, 7)]
    return {"cer": s[0] / s[1], "mark": s[2] / max(s[3], 1), "plain": s[4] / max(s[5], 1)}


def pooled(arm_runs):
    per, spk = zip(*[per_utt(r["artifacts"]["predictions"]) for r in arm_runs])
    assert all(s == spk[0] for s in spk), "speaker order differs between runs"
    assert all([u[0] for u in p] == [u[0] for u in per[0]] for p in per)
    n = len(per[0])
    return [tuple([per[0][i][0]] + [sum(p[i][k] for p in per) for k in range(1, 7)]) for i in range(n)], list(spk[0])


def boot(spk, pairs, draws=2000):
    """pairs: dict name -> pooled rows. Returns dict name -> list of resampled rate dicts (same resamples)."""
    by = collections.defaultdict(list)
    for i, s in enumerate(spk):
        by[s].append(i)
    keys = list(by)
    rnd = random.Random(0)
    idxs = [[i for k in (rnd.choice(keys) for _ in keys) for i in by[k]] for _ in range(draws)]
    return {n: [rates([rows[i] for i in ix]) for ix in idxs] for n, rows in pairs.items()}


def contrast(b, a, c):
    """arm a minus arm c, per metric: (point from full data computed by caller, ci)."""
    res = {}
    for m in ("cer", "mark", "plain"):
        d = sorted(x[m] - y[m] for x, y in zip(b[a], b[c]))
        res[m] = (d[int(0.025 * len(d))], d[int(0.975 * len(d)) - 1])
    return res


def main():
    runs = [r for r in read_runs() if r["stage"] == "phase1" and r["status"] == "done"
            and r["config"].get("split_tag") == "v2"]
    if not runs:
        print("no v2 runs")
        return
    arms = collections.defaultdict(list)
    for r in runs:
        arms[(r["init"], r["config"]["requested_hours"])].append(r)
    budgets = sorted({k[1] for k in arms})
    out = {}
    verdict = {}
    for h in budgets:
        names = [k[0] for k in arms if k[1] == h]
        data, spk = {}, None
        for n in names:
            data[n], s = pooled(arms[(n, h)])
            spk = spk or s
        b = boot(spk, data)
        pt = {n: rates(data[n]) for n in names}
        print(f"\n### budget {h} h (seeds per arm: {', '.join(f'{n}:{len(arms[(n, h)])}' for n in sorted(names))})")
        print("| arm | CER | tone-mark CER | ordinary-ha CER | per-seed tone-mark sd |\n|---|---|---|---|---|")
        for n in sorted(names):
            sds = [r["tone_cer"] for r in arms[(n, h)]]
            mu = sum(sds) / len(sds)
            sd = (sum((x - mu) ** 2 for x in sds) / max(len(sds) - 1, 1)) ** 0.5
            print(f"| {n} | {pt[n]['cer']:.3f} | {pt[n]['mark']:.3f} | {pt[n]['plain']:.3f} | {sd:.3f} (on combined ha set) |")
        want = [("donor-hi", "random"), ("donor-pa", "random"), ("donor-mr", "random"), ("donor-pa", "donor-hi"),
                ("donor-hi", "donor-hi+noblank"), ("donor-pa", "donor-pa+noblank"), ("donor-hi+noblank", "random"),
                ("donor-pa+noblank", "random"), ("donor-hi+comp", "donor-hi"), ("donor-pa+comp", "donor-pa")]
        print("\n| contrast (A minus B) | d CER [95% CI] | d tone-mark [95% CI] | d ordinary-ha [95% CI] |\n|---|---|---|---|")
        for a, c in want:
            if a in data and c in data:
                ci = contrast(b, a, c)
                row = " | ".join(f"{pt[a][m] - pt[c][m]:+.3f} [{ci[m][0]:+.3f}, {ci[m][1]:+.3f}]" for m in ("cer", "mark", "plain"))
                print(f"| {a} - {c} | {row} |")
                out[f"{h}|{a}-{c}"] = {m: [pt[a][m] - pt[c][m], *ci[m]] for m in ci}
        if h == min(budgets):
            g = lambda a, c, m: out.get(f"{h}|{a}-{c}", {}).get(m)
            def pos(x):
                return x is not None and x[1] > 0
            p1 = pos(g("donor-hi", "random", "mark")) and pos(g("donor-pa", "random", "mark")) and \
                (g("donor-pa", "donor-hi", "mark") is not None and abs(g("donor-pa", "donor-hi", "mark")[0]) <= 0.03)
            p2 = pos(g("donor-hi", "donor-hi+noblank", "mark")) and pos(g("donor-pa", "donor-pa+noblank", "mark")) and \
                (g("donor-hi+noblank", "random", "mark") or [0])[0] > 0 and (g("donor-pa+noblank", "random", "mark") or [0])[0] > 0
            p3 = all((g(a, c, "mark") is not None and g(a, c, "mark")[0] > -0.02) for a, c in
                     (("donor-hi+comp", "donor-hi"), ("donor-pa+comp", "donor-pa")))
            verdict = {"P1": p1, "P2": p2, "P3_comp_gain_below_0.02": p3}
    print("\nPre-registered predictions at the smallest budget (mechanical check):", verdict)
    out["verdict"] = verdict
    json.dump(out, open("results/phase1/analysis_v2.json", "w"), indent=1)


if __name__ == "__main__":
    main()
