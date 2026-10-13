"""v2 protocol for head-only training on the v2 split (gender-balanced dev/test, large train pool).

Differences from train_head (v1): each (budget, seed) draws a different random set of whole training speakers
from the pool, so the seed spread includes data variation; model selection uses a fixed strided 300-utterance
dev sample; predictions are saved with the speaker id for speaker-cluster bootstrap. Optimiser, epochs, batch size,
losses and head construction are identical to v1 (imported from tone_donor.train_head).

    BACKBONE=multi python -m tone_donor.train_head_v2 /home/vnit/data/dogri_multi_v2 donor-hi:0.25:0 random:1.0:3 ...
"""
import json
import os
import random
import sys

import torch

from tone_donor.prep_features import backbone_name, load_encoder
from tone_donor.runlog import log_run, read_runs
from tone_donor.train_head import (BS, EPOCHS, LR, build_head, evaluate, fast_cer, pad, to_gpu)
from tone_donor.vaani_stream import _load_dotenv

SPLIT_TAG = "v2"


def draw_speakers(train, hours, seed):
    by = {}
    for it in train:
        by.setdefault(it["speaker"], []).append(it)
    spk = sorted(by)
    random.Random(1000 + seed).shuffle(spk)
    sel, tot = [], 0.0
    for s in spk:
        if tot >= hours * 3600:
            break
        sel.extend(by[s])
        tot += sum(it["dur"] for it in by[s])
    return sel, tot, sum(1 for s in spk if any(it in sel for it in by[s][:1])) if False else None


def train_one(model, data, init, hours, seed):
    train, dev, test = data
    random.seed(seed)
    sel, tot, _ = draw_speakers(train, hours, seed)
    nspk = len({it["speaker"] for it in sel})
    dev_sel = dev[::max(len(dev) // 300, 1)][:300]
    head, copied, nd = build_head(model, init, seed)
    print(f"init={init} hours={tot/3600:.3f} utts={len(sel)} speakers={nspk} copied {copied}/{nd} tokens", flush=True)
    opt = torch.optim.AdamW(head.parameters(), lr=LR, weight_decay=0.0)
    ctc = torch.nn.CTCLoss(blank=head.out_features - 1, zero_infinity=True)
    best, best_state, hist = 1e9, {k: v.clone() for k, v in head.state_dict().items()}, []
    for ep in range(0 if init == "own" else EPOCHS):
        head.train()
        tl = nb = 0
        idx = list(range(len(sel)))
        random.shuffle(idx)
        for i in range(0, len(idx), BS):
            items = [sel[j] for j in idx[i:i + BS]]
            x, flen = pad(items)
            tgt = torch.cat([it["ids"] for it in items]).cuda()
            tlen = torch.tensor([len(it["ids"]) for it in items]).cuda()
            loss = ctc(torch.log_softmax(head(x), -1).transpose(0, 1), tgt, flen, tlen)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tl += loss.item()
            nb += 1
        head.eval()
        dcer = fast_cer(model, head, dev_sel)
        hist.append({"epoch": ep, "train_loss": tl / nb, "dev_cer": dcer})
        if dcer < best:
            best = dcer
            best_state = {k: v.clone() for k, v in head.state_dict().items()}
    print(f"  best dev300 CER {best:.4f}", flush=True)
    head.load_state_dict(best_state)
    head.eval()
    res = {}
    for name, items in (("dev", dev), ("test", test)):
        res[name], pairs = evaluate(model, head, items)
    rid = f"phase1-{SPLIT_TAG}-{backbone_name()}-dogri-{init}-{hours}h-s{seed}"
    os.makedirs("results/phase1", exist_ok=True)
    with open(f"results/phase1/{rid}.jsonl", "w", encoding="utf-8") as f:
        for (r, h), it in zip(pairs, test):
            f.write(json.dumps({"ref": r, "hyp": h, "speaker": it["speaker"]}, ensure_ascii=False) + "\n")
    t = res["test"]
    log_run(stage="phase1", hypothesis="v2-confirmatory", target="dogri",
            donor={"own": "doi"}.get(init) or (init.split("+")[0].split("-", 1)[1] if init.startswith("donor-") else None),
            init=init, budget_h=round(tot / 3600, 3), seed=seed, backbone="indicconformer_multi_frozen_encoder",
            split=f"{SPLIT_TAG}: gender-balanced speaker-disjoint test (IndicVoices valid)", n_utts=len(test),
            n_speakers=nspk, wer=t["wer"], cer=t["cer"], tone_cer=t["ha_tone_cer"], tone_chars=t["n_ha"],
            aspirate_cer=t["aspirate_cer"], plain_cer=t["plain_cer"],
            config={"epochs": EPOCHS, "lr": LR, "bs": BS, "trained": "ctc head columns only", "tokens_copied": copied,
                    "requested_hours": hours, "dev": res["dev"], "history_last": hist[-3:],
                    "apostrophe": "dropped from text", "model_selection": "best CER on strided 300 dev utterances",
                    "impl": "train_head_v2", "backbone_tag": backbone_name(), "split_tag": SPLIT_TAG,
                    "subset": "random whole speakers per (budget, seed)", "train_speakers": nspk},
            artifacts={"predictions": f"results/phase1/{rid}.jsonl"},
            notes="v2 split, random speaker subsets; encoder frozen; head-only")
    print("TEST", json.dumps({k: round(v, 4) for k, v in t.items() if isinstance(v, float)}), flush=True)


def already_done(init, hours, seed):
    for r in read_runs():
        if (r["stage"] == "phase1" and r["status"] == "done" and r["init"] == init and r["seed"] == seed
                and r["config"].get("split_tag") == SPLIT_TAG and abs(r["config"].get("requested_hours", -1) - hours) < 1e-6):
            return True
    return False


def main(data_dir, specs):
    _load_dotenv()
    model = load_encoder(os.environ["HF_TOKEN"])
    for p in model.parameters():
        p.requires_grad = False
    train = to_gpu(torch.load(os.path.join(data_dir, "train.pt")), model)
    dev = to_gpu(torch.load(os.path.join(data_dir, "dev.pt")), model)
    test = to_gpu(torch.load(os.path.join(data_dir, "test.pt")), model)
    for spec in specs:
        init, h, s = spec.split(":")
        h, s = float(h), int(s)
        if already_done(init, h, s):
            print("skip", spec, flush=True)
            continue
        train_one(model, (train, dev, test), init, h, s)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
