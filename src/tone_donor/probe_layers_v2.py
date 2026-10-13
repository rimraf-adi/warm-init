"""H1 probe v2 (replaces probe_layers for conclusions): layer-wise linear probes on the v2 Dogri split.

Fixes over v1: (1) the main contrast is tone-mark token (Dogri piece with ha+virama) vs ORDINARY-ha token (piece with
ha but no virama), so the consonant is held constant; a second contrast (any consonant+virama piece other than ha vs
plain consonant pieces) controls for 'virama conjunct' detection in general; the original 'tone-mark vs all other
tokens' task is kept for continuity. (2) frames are aligned with the CTC head of the aligner model named by ALIGNER (default doi, a monolingual
model: a CTC aligner's emission timing is specific to the model family, and the first attempt with the multilingual
aligner gave chance-level probes for every monolingual encoder because of a timing mismatch), and the feature is the mean of the emission frame and its two
neighbours (indices clamped to the utterance length; the clamp fixes the v1 CUDA assert). (3) 95% CIs by
speaker-cluster bootstrap on the test tokens; paired differences between encoders use the same resamples.
The multilingual encoder is included but flagged: it produced the alignments.

    python -m tone_donor.probe_layers_v2 doi hi pa mr ne bn multi
Writes results/phase2/probe_layers_v2.json
"""
import json
import os
import random
import sys

import numpy as np
import soundfile as sf
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from tone_donor.probe_layers import enc_forward, load_model
from tone_donor.text import normalize
from tone_donor.vaani_stream import _load_dotenv

LANG = "doi"
TRAIN_H, TEST_H = 1.5, 1.5
VIRAMA = "्"
NEG_CAP_TRAIN, NEG_CAP_TEST = 20000, 12000
BOOT = 400


def read(split, hours):
    rows, tot = [], 0.0
    for line in open(f"data/manifests/indicvoices_dogri_v2_{split}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        rows.append(r)
        tot += r["audio_s"]
        if tot >= hours * 3600:
            break
    return rows


def load_wavs(rows):
    return [torch.from_numpy(sf.read(f"data/{r['audio']}", dtype="float32")[0]) for r in rows]


@torch.no_grad()
def align(model, rows, wavs, bs=8):
    import torchaudio.functional as AF
    out = []
    for i in range(0, len(rows), bs):
        chunk = wavs[i:i + bs]
        enc, elen, _ = enc_forward(model, chunk, False)
        lp = model.ctc_decoder(encoder_output=enc, language_ids=[LANG] * enc.shape[0])
        blank = lp.shape[-1] - 1
        for k in range(len(chunk)):
            ids = model.tokenizer.text_to_ids(normalize(rows[i + k]["text"], drop_apos=True), LANG)
            T = int(elen[k])
            if not ids or len(ids) > T:
                out.append(None)
                continue
            try:
                al, _ = AF.forced_align(lp[k:k + 1, :T].float().cpu(), torch.tensor([ids], dtype=torch.int32), blank=blank)
            except Exception:
                out.append(None)
                continue
            frames, prev = [], blank
            for t, a in enumerate(al[0].tolist()):
                if a != blank and a != prev:
                    frames.append(t)
                prev = a
            out.append((ids, frames) if len(frames) == len(ids) else None)
    return out


def piece_classes(model):
    v = list(model.tokenizer.tokenizers_dict[LANG].vocab)
    tone = {i for i, p in enumerate(v) if "ह" + VIRAMA in p}
    plain_ha = {i for i, p in enumerate(v) if "ह" in p and ("ह" + VIRAMA) not in p}
    cons = [chr(c) for c in range(0x0915, 0x093A) if chr(c) != "ह"]
    conj = {i for i, p in enumerate(v) if any(c + VIRAMA in p for c in cons) and "ह" not in p}
    plain_c = {i for i, p in enumerate(v) if any(c in p for c in cons) and VIRAMA not in p and "ह" not in p}
    return tone, plain_ha, conj, plain_c


@torch.no_grad()
def extract(model, wavs, aligned, rows, keep_ids, cap, rng, bs=8):
    """Features (mean of emission frame and its two neighbours) for tokens of interest + a capped random sample of others."""
    feats = None
    ids_all, spk_all = [], []
    for i in range(0, len(wavs), bs):
        chunk = wavs[i:i + bs]
        enc, elen, store = enc_forward(model, chunk, True)
        if feats is None:
            feats = [[] for _ in store]
        for k in range(len(chunk)):
            a = aligned[i + k]
            if a is None:
                continue
            ids, frames = a
            T = int(elen[k])
            sel = [j for j, t in enumerate(ids) if t in keep_ids or ((i + k) * 7919 + j * 104729) % 10007 < cap * 10007]
            if not sel:
                continue
            fr = torch.tensor([frames[j] for j in sel], device="cuda").clamp(0, T - 1)
            idx = torch.stack([(fr - 1).clamp(0, T - 1), fr, (fr + 1).clamp(0, T - 1)], 1)
            for li, h in enumerate(store):
                x = h[k][idx].mean(1)                           # [n, D]
                feats[li].append(x.float().cpu().numpy())
            ids_all.extend(ids[j] for j in sel)
            spk_all.extend([rows[i + k]["speaker_id"]] * len(sel))
    return [np.concatenate(f) for f in feats], np.array(ids_all), np.array(spk_all)


def task_masks(ids, tone, plain_ha, conj, plain_c):
    m = {}
    t = np.isin(ids, list(tone))
    ph = np.isin(ids, list(plain_ha))
    m["tone_vs_plain_ha"] = (t | ph, t.astype(int))
    m["tone_vs_all"] = (np.ones(len(ids), bool), t.astype(int))
    c = np.isin(ids, list(conj))
    pc = np.isin(ids, list(plain_c))
    m["conj_vs_plain_consonant"] = (c | pc, c.astype(int))
    return m


def fit_scores(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=300, C=0.5, class_weight="balanced").fit(sc.transform(Xtr), ytr)
    return clf.decision_function(sc.transform(Xte))


def main(codes):
    _load_dotenv()
    tok = os.environ["HF_TOKEN"]
    rng = random.Random(0)
    tr_rows, te_rows = read("train", TRAIN_H), read("test", TEST_H)
    tr_w, te_w = load_wavs(tr_rows), load_wavs(te_rows)
    aligner_code = os.environ.get("ALIGNER", "doi")
    aligner = load_model(aligner_code, tok)
    print("aligner:", aligner_code, flush=True)
    tone, plain_ha, conj, plain_c = piece_classes(aligner)
    keep = tone | plain_ha | conj | plain_c
    print("pieces: tone", len(tone), "plain-ha", len(plain_ha), "conj", len(conj), "plain-consonant", len(plain_c), flush=True)
    tr_al, te_al = align(aligner, tr_rows, tr_w), align(aligner, te_rows, te_w)
    print("aligned utts train", sum(a is not None for a in tr_al), "/", len(tr_al), " test", sum(a is not None for a in te_al), "/", len(te_al), flush=True)
    del aligner
    torch.cuda.empty_cache()

    scores = {}                                            # code -> task -> layer -> scores on test tokens
    meta = {}
    for code in codes:
        model = load_model(code, tok)
        cap_tr = NEG_CAP_TRAIN / 60000.0
        cap_te = NEG_CAP_TEST / 40000.0
        Xtr, itr, _ = extract(model, tr_w, tr_al, tr_rows, keep, cap_tr, rng)
        Xte, ite, ste = extract(model, te_w, te_al, te_rows, keep, cap_te, rng)
        trm, tem = task_masks(itr, tone, plain_ha, conj, plain_c), task_masks(ite, tone, plain_ha, conj, plain_c)
        scores[code] = {}
        for task in tem:
            mtr, ytr = trm[task]
            mte, yte = tem[task]
            scores[code][task] = {"y": yte[mte], "spk": ste[mte], "layers": []}
            for li in range(len(Xtr)):
                scores[code][task]["layers"].append(fit_scores(Xtr[li][mtr], ytr[mtr], Xte[li][mte]))
            meta[(code, task)] = {"n_test": int(mte.sum()), "pos_test": int(yte[mte].sum()), "n_train": int(mtr.sum()), "pos_train": int(ytr[mtr].sum())}
        print(code, "done", {t: meta[(code, t)] for t in tem}, flush=True)
        del model, Xtr, Xte
        torch.cuda.empty_cache()

    os.makedirs("data", exist_ok=True)
    np.savez_compressed(f"data/probe_v2_scores_{aligner_code}.npz", **{f"{c}|{t}|{li}": scores[c][t]["layers"][li]
                        for c in scores for t in scores[c] for li in range(len(scores[c][t]["layers"]))},
                        **{f"y|{t}": scores[codes[0]][t]["y"] for t in scores[codes[0]]},
                        **{f"spk|{t}": scores[codes[0]][t]["spk"] for t in scores[codes[0]]})
    # every encoder must have scored exactly the same test tokens in each task
    for t in scores[codes[0]]:
        for c in codes:
            assert np.array_equal(scores[c][t]["y"], scores[codes[0]][t]["y"]) and np.array_equal(scores[c][t]["spk"], scores[codes[0]][t]["spk"]), (c, t)
    # speaker-cluster bootstrap, same resamples for every encoder within a task
    out = {"meta": {f"{c}|{t}": v for (c, t), v in meta.items()}, "auc": {}, "diff_vs_hi": {}}
    np_rng = np.random.default_rng(0)
    for task in next(iter(scores.values())):
        base = scores[codes[0]][task]
        spk = base["spk"]
        users = np.unique(spk)
        by = {u: np.where(spk == u)[0] for u in users}
        draws = [np.concatenate([by[u] for u in np_rng.choice(users, len(users))]) for _ in range(BOOT)]
        n_layers = len(base["layers"])
        auc = {c: [[roc_auc_score(scores[c][task]["y"], scores[c][task]["layers"][li]) for li in range(len(scores[c][task]["layers"]))]] for c in codes}
        boots = {}
        for c in codes:
            y = scores[c][task]["y"]
            L = scores[c][task]["layers"]
            top = list(range(max(len(L) - 4, 0), len(L)))
            b = []
            for d in draws:
                if y[d].sum() in (0, len(d)):
                    continue
                b.append(np.mean([roc_auc_score(y[d], L[li][d]) for li in top]))
            boots[c] = np.array(b)
        out["auc"][task] = {c: {"per_layer": auc[c][0], "top4_mean": float(np.mean(auc[c][0][-4:])),
                                "top4_ci": [float(np.percentile(boots[c], 2.5)), float(np.percentile(boots[c], 97.5))]} for c in codes}
        if "hi" in codes:
            out["diff_vs_hi"][task] = {}
            for c in codes:
                if c == "hi":
                    continue
                k = min(len(boots[c]), len(boots["hi"]))
                dd = boots[c][:k] - boots["hi"][:k]
                out["diff_vs_hi"][task][c] = {"diff": float(np.mean(auc[c][0][-4:]) - np.mean(auc["hi"][0][-4:])),
                                              "ci": [float(np.percentile(dd, 2.5)), float(np.percentile(dd, 97.5))]}
    os.makedirs("results/phase2", exist_ok=True)
    json.dump(out, open(f"results/phase2/probe_layers_v2_{aligner_code}.json", "w"), indent=1)
    for task, d in out["auc"].items():
        print("TASK", task)
        for c, v in d.items():
            print(f"  {c:6s} top-4-layer mean AUC {v['top4_mean']:.3f} [{v['top4_ci'][0]:.3f}, {v['top4_ci'][1]:.3f}]", flush=True)
        for c, v in out["diff_vs_hi"].get(task, {}).items():
            print(f"  diff {c:6s} - hi: {v['diff']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}]", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
