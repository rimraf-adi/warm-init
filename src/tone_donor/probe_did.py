"""Is an encoder's probe advantage specific to the tone mark? Difference of differences with speaker-cluster bootstrap.

    uv run python -m tone_donor.probe_did [aligner]
For encoder X versus Hindi (top-4-layer mean AUC):  DiD = (X - hi on tone_vs_plain_ha) - (X - hi on conj_vs_plain_consonant).
A tone-specific advantage needs DiD > 0 with a CI excluding zero. Speakers are resampled jointly for both tasks.
Reads data/probe_v2_scores_<aligner>.npz written by probe_layers_v2.
"""
import json
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

TASKS = ("tone_vs_plain_ha", "conj_vs_plain_consonant")


def main(aligner="doi", draws=400, top=4, codes=("doi", "pa", "mr", "ne", "bn")):
    z = np.load(f"data/probe_v2_scores_{aligner}.npz")
    y = {t: z[f"y|{t}"] for t in TASKS}
    spk = {t: z[f"spk|{t}"] for t in TASKS}
    nl = len({k for k in z.files if k.startswith(f"hi|{TASKS[0]}|")})
    layers = range(nl - top, nl)
    sc = {(c, t, li): z[f"{c}|{t}|{li}"] for c in ("hi",) + tuple(codes) for t in TASKS for li in layers}
    speakers = np.unique(np.concatenate([spk[t] for t in TASKS]))
    by = {t: {s: np.where(spk[t] == s)[0] for s in speakers} for t in TASKS}
    rng = np.random.default_rng(0)

    def auc(c, t, ix):
        yy = y[t][ix]
        if yy.sum() in (0, len(yy)):
            return np.nan
        return np.mean([roc_auc_score(yy, sc[(c, t, li)][ix]) for li in layers])

    full = {t: np.arange(len(y[t])) for t in TASKS}
    res = {}
    draws_ix = [rng.choice(speakers, len(speakers)) for _ in range(draws)]
    for c in codes:
        pt = {t: auc(c, t, full[t]) - auc("hi", t, full[t]) for t in TASKS}
        did_b, tone_b, ctrl_b = [], [], []
        for d in draws_ix:
            ix = {t: np.concatenate([by[t][s] for s in d if len(by[t][s])]) for t in TASKS}
            a = {t: auc(c, t, ix[t]) - auc("hi", t, ix[t]) for t in TASKS}
            tone_b.append(a[TASKS[0]])
            ctrl_b.append(a[TASKS[1]])
            did_b.append(a[TASKS[0]] - a[TASKS[1]])
        f = lambda v: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
        res[c] = {"tone_diff": [pt[TASKS[0]], *f(tone_b)], "control_diff": [pt[TASKS[1]], *f(ctrl_b)],
                  "did": [pt[TASKS[0]] - pt[TASKS[1]], *f(did_b)]}
    print(f"aligner {aligner}; encoder minus hi, mean AUC over top {top} layers; speaker-cluster bootstrap ({draws} draws)")
    print("| encoder | tone vs ordinary-ha | control (conjunct vs plain) | difference of differences |\n|---|---|---|---|")
    for c, r in res.items():
        print(f"| {c} | " + " | ".join(f"{v[0]:+.3f} [{v[1]:+.3f}, {v[2]:+.3f}]" for v in (r['tone_diff'], r['control_diff'], r['did'])) + " |")
    json.dump(res, open(f"results/phase2/probe_did_{aligner}.json", "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:2])
