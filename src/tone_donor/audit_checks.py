"""Audit checks on earlier conclusions.

1. Speaker-cluster bootstrap (resample test speakers, keep all their utterances) for the key contrasts, instead of
   resampling utterances (which ignores that utterances from one speaker are correlated).
2. Split the head-only 'tone' set into ha+virama tone mark vs ordinary ha.

    uv run python -m tone_donor.audit_checks
"""
import collections
import json
import random

from tone_donor.runlog import read_runs
from tone_donor.text import _align, normalize

MAN = "data/manifests/indicvoices_dogri_test.jsonl"
VIRAMA = "्"


def speakers():
    rows = [json.loads(l) for l in open(MAN, encoding="utf-8")]
    return [r["speaker_id"] for r in rows], [normalize(r["text"], drop_apos=True) for r in rows]


def per_utt(path):
    out = []
    for d in map(json.loads, open(path, encoding="utf-8")):
        ref, hyp = d["ref"], d["hyp"]
        err, edits = _align(ref, hyp)
        mark = {i for i, c in enumerate(ref) if c == "ह" and ref[i + 1:i + 2] == VIRAMA}
        mark |= {i + 1 for i in mark}
        plain = {i for i, c in enumerate(ref) if c == "ह" and ref[i + 1:i + 2] != VIRAMA}
        out.append((ref, edits, len(ref), sum(err[i] for i in mark), len(mark), sum(err[i] for i in plain), len(plain)))
    return out


def rates(rows):
    s = [sum(r[k] for r in rows) for k in range(1, 7)]
    return {"cer": s[0] / s[1], "mark": s[2] / max(s[3], 1), "plain": s[4] / max(s[5], 1)}


def cluster_boot(spk, A, B, B_draws=2000):
    """Paired speaker-cluster bootstrap of rates(A)-rates(B). A, B: per-utterance rows in the same order."""
    by = collections.defaultdict(list)
    for i, s in enumerate(spk):
        by[s].append(i)
    keys = list(by)
    random.seed(0)
    diffs = collections.defaultdict(list)
    for _ in range(B_draws):
        idx = [i for k in (random.choice(keys) for _ in keys) for i in by[k]]
        ra, rb = rates([A[i] for i in idx]), rates([B[i] for i in idx])
        for m in ra:
            diffs[m].append(ra[m] - rb[m])
    pa, pb = rates(A), rates(B)
    out = {}
    for m in pa:
        d = sorted(diffs[m])
        out[m] = (pa[m] - pb[m], d[int(0.025 * len(d))], d[int(0.975 * len(d)) - 1])
    return out


def fmt(d):
    return " | ".join(f"{d[m][0]:+.3f} [{d[m][1]:+.3f}, {d[m][2]:+.3f}]" for m in ("cer", "mark", "plain"))


def main():
    spk, refs = speakers()
    print("speakers in test:", len(set(spk)), "utterances:", len(spk))
    runs = [r for r in read_runs() if r["stage"] == "phase1" and r["status"] == "done"
            and r["backbone"] == "indicconformer_multi_frozen_encoder"]

    def pooled(init, hours):
        files = [r["artifacts"]["predictions"] for r in runs if r["init"] == init and abs(r["budget_h"] - hours) < 0.1 * max(hours, 1)]
        per = [per_utt(f) for f in files]
        assert all([u[0] for u in p] == refs for p in per), "prediction order differs from the manifest"
        return [tuple([per[0][i][0]] + [sum(p[i][k] for p in per) for k in range(1, 7)]) for i in range(len(refs))], len(files)

    print("\n## Head-only grid, multilingual encoder: Hindi-init minus random, speaker-cluster bootstrap")
    print("| budget h | seeds | d CER | d tone-mark CER | d ordinary-ha CER |\n|---|---|---|---|---|")
    for h in (0.25, 1.0, 5.0):
        A, na = pooled("hindi", h)
        B, nb = pooled("random", h)
        print(f"| {h} | {na}+{nb} | {fmt(cluster_boot(spk, A, B))} |")
    print("\n## Same, donor-pa minus random")
    for h in (0.25, 1.0):
        A, na = pooled("donor-pa", h)
        B, nb = pooled("random", h)
        print(f"| {h} | {na}+{nb} | {fmt(cluster_boot(spk, A, B))} |")

    print("\n## Zero-shot sweep: Punjabi head minus Hindi head, speaker-cluster bootstrap")
    d = "results/phase1/zero_shot_hyps_dogri_test"
    A, B = per_utt(f"{d}/pa.jsonl"), per_utt(f"{d}/hi.jsonl")
    assert [u[0] for u in A] == refs
    print("| d CER | d tone-mark CER | d ordinary-ha CER |\n|---|---|---|")
    print(f"| {fmt(cluster_boot(spk, A, B))} |")


if __name__ == "__main__":
    main()
