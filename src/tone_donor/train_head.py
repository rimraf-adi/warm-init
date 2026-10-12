"""Phase 1 kill test: train only Dogri's CTC output columns on cached frozen-encoder features.

Arms (init):
  random : the Dogri columns (and blank) of the shared 1x1 conv head are re-initialised (xavier).
  hindi  : Dogri columns copied from the Hindi columns for tokens whose string is in both
           tokenizers; unmatched Dogri tokens re-initialised. Blank copied.
Encoder and every other parameter are frozen. Loss: CTC over the Dogri token slice.
Protocol (fixed): AdamW lr 1e-3, batch 16, 40 epochs, model selection by best dev[:300] CER.
One process runs all configs so the model loads once; configs already logged are skipped.

    python -m tone_donor.train_head /home/vnit/data/dogri random:0.25:0 hindi:0.25:0 ...
"""
import json
import os
import random
import sys

import editdistance
import torch

from tone_donor.prep_features import backbone_name, load_encoder
from tone_donor.runlog import log_run, read_runs
from tone_donor.text import ASPIRATES_DEVANAGARI, PLAIN_DEVANAGARI, charset_cer, normalize, tone_cer
from tone_donor.vaani_stream import _load_dotenv

LANG = "doi"
EPOCHS, LR, BS = 40, 1e-3, 16


def lang_columns(model, lang):
    return torch.tensor([i for i, b in enumerate(model.ctc_decoder.language_masks[lang]) if b])


def pieces(model, lang):
    return list(model.tokenizer.tokenizers_dict[lang].vocab)


def build_head(model, init, seed):
    torch.manual_seed(seed)
    conv = model.ctc_decoder.decoder_layers[0]
    cols_d, cols_h = lang_columns(model, LANG), lang_columns(model, "hi")
    sp_d, sp_h = pieces(model, LANG), pieces(model, "hi")
    W, b = conv.weight.data.clone().cpu(), conv.bias.data.clone().cpu()
    newW = torch.empty(len(cols_d), W.shape[1])
    torch.nn.init.xavier_uniform_(newW.unsqueeze(-1))
    newb = torch.zeros(len(cols_d))
    copied = 0
    if init == "own":
        newW, newb = W[cols_d, :, 0].clone(), b[cols_d].clone()
        copied = len(sp_d)
    if init == "hindi":
        h_index = {s: i for i, s in enumerate(sp_h)}
        for j, s in enumerate(sp_d):
            if s in h_index:
                src = cols_h[h_index[s]]
                newW[j] = W[src, :, 0]
                newb[j] = b[src]
                copied += 1
        newW[-1] = W[cols_h[-1], :, 0]
        newb[-1] = b[cols_h[-1]]
    head = torch.nn.Linear(W.shape[1], len(cols_d))
    head.weight.data, head.bias.data = newW, newb
    return head.cuda(), copied, len(sp_d)


def to_gpu(items, model):
    """Features to GPU once, targets pre-tokenised."""
    for it in items:
        it["f"] = it["feat"].cuda()
        it["ids"] = torch.tensor(model.tokenizer.text_to_ids(it["text"], LANG))
    return items


def pad(items):
    x = torch.nn.utils.rnn.pad_sequence([it["f"] for it in items], batch_first=True).float()
    return x, torch.tensor([len(it["f"]) for it in items], device=x.device)


@torch.no_grad()
def decode(model, head, items, bs=64):
    out, blank = [], head.out_features - 1
    for i in range(0, len(items), bs):
        chunk = items[i:i + bs]
        x, lens = pad(chunk)
        am = head(x).argmax(-1).cpu()
        for k in range(len(chunk)):
            s = am[k, :lens[k].item()]
            keep = torch.ones_like(s, dtype=torch.bool)
            keep[1:] = s[1:] != s[:-1]
            s = s[keep & (s != blank)]
            out.append(model.tokenizer.ids_to_text(s.tolist(), LANG).strip())
    return out


def evaluate(model, head, items):
    hyps = [normalize(h, drop_apos=True) for h in decode(model, head, items)]
    pairs = list(zip([it["text"] for it in items], hyps))
    ha, allc = tone_cer(pairs, "dogri", "ha"), tone_cer(pairs, "dogri", "all")
    asp, n_asp = charset_cer(pairs, ASPIRATES_DEVANAGARI)
    pln, n_pln = charset_cer(pairs, PLAIN_DEVANAGARI)
    we = wn = 0
    for r, h in pairs:
        we += editdistance.eval(r.split(), h.split())
        wn += len(r.split())
    return {"cer": allc["cer"], "wer": we / max(wn, 1), "ha_tone_cer": ha["tone_cer"], "n_ha": ha["tone_chars"],
            "aspirate_cer": asp, "n_asp": n_asp, "plain_cer": pln, "n_plain": n_pln}, pairs


def train_one(model, data, init, hours, seed):
    train, dev, test = data
    random.seed(seed)
    sel, tot, last = [], 0.0, None
    for it in train:
        if tot >= hours * 3600 and it["speaker"] != last:
            break
        sel.append(it)
        tot += it["dur"]
        last = it["speaker"]
    head, copied, nd = build_head(model, init, seed)
    print(f"init={init} hours={tot/3600:.3f} utts={len(sel)} copied {copied}/{nd} tokens", flush=True)
    opt = torch.optim.AdamW(head.parameters(), lr=LR, weight_decay=0.0)
    ctc = torch.nn.CTCLoss(blank=head.out_features - 1, zero_infinity=True)
    best, best_state, hist = 1e9, {k: v.clone() for k, v in head.state_dict().items()}, [{"epoch": -1, "train_loss": None, "dev_cer": None}]
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
        m, _ = evaluate(model, head, dev[:300])
        hist.append({"epoch": ep, "train_loss": tl / nb, "dev_cer": m["cer"]})
        if m["cer"] < best:
            best = m["cer"]
            best_state = {k: v.clone() for k, v in head.state_dict().items()}
    print(f"  last epoch loss {hist[-1]['train_loss']} best dev300 CER {best:.4f}", flush=True)
    head.load_state_dict(best_state)
    head.eval()
    res = {}
    for name, items in (("dev", dev), ("test", test)):
        res[name], pairs = evaluate(model, head, items)
    tag = backbone_name()
    rid = f"phase1-{tag}-dogri-{init}-{hours}h-s{seed}"
    os.makedirs("results/phase1", exist_ok=True)
    with open(f"results/phase1/{rid}.jsonl", "w", encoding="utf-8") as f:
        for r, h in pairs:
            f.write(json.dumps({"ref": r, "hyp": h}, ensure_ascii=False) + "\n")
    t = res["test"]
    log_run(stage="phase1", hypothesis="H2", target="dogri", donor={"hindi": "hi", "own": "doi"}.get(init),
            init=init, budget_h=round(tot / 3600, 3), seed=seed, backbone=("indicconformer_multi_frozen_encoder" if tag == "multi" else "indicconformer_hi_frozen_encoder"),
            split="speaker-disjoint test (IndicVoices valid, alternating speakers)", n_utts=len(test),
            wer=t["wer"], cer=t["cer"], tone_cer=t["ha_tone_cer"], tone_chars=t["n_ha"],
            aspirate_cer=t["aspirate_cer"], plain_cer=t["plain_cer"],
            config={"epochs": EPOCHS, "lr": LR, "bs": BS, "trained": "ctc head columns only", "tokens_copied": copied,
                    "requested_hours": hours, "dev": res["dev"], "history_last": hist[-3:],
                    "apostrophe": "dropped from text", "tone_chars": "ha + virama only",
                    "model_selection": "best dev-300 CER", "impl": "gpu-cached v2 (same protocol as v1)", "backbone_tag": tag},
            artifacts={"predictions": f"results/phase1/{rid}.jsonl"},
            notes="kill test arm; encoder frozen; head-only training")
    print("TEST", json.dumps(t), flush=True)


def already_done(init, hours, seed):
    tag = backbone_name()
    for r in read_runs():
        if r["stage"] != "phase1" or r["status"] != "done" or r["init"] != init or r["seed"] != seed:
            continue
        if r["config"].get("backbone_tag", "hi") != tag:
            continue
        req = r["config"].get("requested_hours")
        if req is not None and abs(req - hours) < 1e-6:
            return True
        if req is None and abs((r["budget_h"] or 0) - hours) < 0.1 * max(hours, 1) + 0.03:   # v1 logs realised hours
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
