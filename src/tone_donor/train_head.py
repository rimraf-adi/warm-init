"""Phase 1 kill test: train only Dogri's CTC output columns on cached frozen-encoder features.

Arms (--init):
  random : the Dogri columns (and blank) of the shared 1x1 conv head are re-initialised (xavier).
  hindi  : Dogri columns are copied from the Hindi columns for tokens whose string is in both
           tokenizers; unmatched Dogri tokens and nothing else are re-initialised. Blank copied.
Encoder, preprocessor and every other parameter are frozen. Loss: CTC over the Dogri token slice.

    python -m tone_donor.train_head hindi 1.0 0 /home/vnit/data/dogri
"""
import json
import math
import os
import random
import sys

import torch

from tone_donor.runlog import log_run
from tone_donor.text import ASPIRATES_DEVANAGARI, PLAIN_DEVANAGARI, charset_cer, cer_stats, tone_cer
from tone_donor.prep_features import load_encoder
from tone_donor.vaani_stream import _load_dotenv

LANG = "doi"


def lang_columns(model, lang):
    mask = model.ctc_decoder.language_masks[lang]
    return torch.tensor([i for i, b in enumerate(mask) if b])      # global columns incl. blank (last)


def token_strings(tk, lang):
    return list(tk.tokenizers_dict[lang].vocab)      # 256 sentencepiece pieces, local ids


def build_head(model, init, seed):
    torch.manual_seed(seed)
    conv = model.ctc_decoder.decoder_layers[0]
    tk = model.tokenizer
    cols_d = lang_columns(model, LANG)
    cols_h = lang_columns(model, "hi")
    sp_d, sp_h = token_strings(tk, LANG), token_strings(tk, "hi")
    W, b = conv.weight.data.clone(), conv.bias.data.clone()
    newW = torch.empty(len(cols_d), W.shape[1])
    newb = torch.zeros(len(cols_d))
    torch.nn.init.xavier_uniform_(newW.unsqueeze(-1))
    copied = 0
    if init == "hindi":
        h_index = {s: i for i, s in enumerate(sp_h)}
        for j, s in enumerate(sp_d):
            if s in h_index:
                src = cols_h[h_index[s]]
                newW[j] = W[src, :, 0]; newb[j] = b[src]; copied += 1
        newW[-1] = W[cols_h[-1], :, 0]; newb[-1] = b[cols_h[-1]]       # blank
    head = torch.nn.Linear(W.shape[1], len(cols_d))
    head.weight.data = newW; head.bias.data = newb
    return head.cuda(), copied, len(sp_d)


def batches(data, bs, shuffle):
    idx = list(range(len(data)))
    if shuffle:
        random.shuffle(idx)
    for i in range(0, len(idx), bs):
        yield [data[j] for j in idx[i:i + bs]]


def collate(model, items):
    feats = torch.nn.utils.rnn.pad_sequence([it["feat"].float() for it in items], batch_first=True).cuda()
    flen = torch.tensor([len(it["feat"]) for it in items]).cuda()
    ids = [torch.tensor(model.tokenizer.text_to_ids(it["text"], LANG)) for it in items]
    tgt = torch.cat(ids).cuda(); tlen = torch.tensor([len(i) for i in ids]).cuda()
    return feats, flen, tgt, tlen


@torch.no_grad()
def decode(model, head, items):
    out = []
    for chunk in batches(items, 32, False):
        feats = torch.nn.utils.rnn.pad_sequence([it["feat"].float() for it in chunk], batch_first=True).cuda()
        lp = head(feats).argmax(-1).cpu()
        blank = head.out_features - 1
        for k, it in enumerate(chunk):
            seq, prev = [], -1
            for t in lp[k, :len(it["feat"])].tolist():
                if t != prev and t != blank:
                    seq.append(t)
                prev = t
            out.append(model.tokenizer.ids_to_text(seq, LANG).strip())
    return out


def evaluate(model, head, items):
    from tone_donor.text import normalize
    hyps = [normalize(h, drop_apos=True) for h in decode(model, head, items)]
    refs = [it["text"] for it in items]
    pairs = list(zip(refs, hyps))
    ha = tone_cer(pairs, "dogri", "ha"); allc = tone_cer(pairs, "dogri", "all")
    asp, n_asp = charset_cer(pairs, ASPIRATES_DEVANAGARI); pln, n_pln = charset_cer(pairs, PLAIN_DEVANAGARI)
    wer_e = wer_n = 0
    import editdistance
    for r, h in pairs:
        rw, hw = r.split(), h.split()
        wer_e += editdistance.eval(rw, hw); wer_n += len(rw)
    return {"cer": allc["cer"], "wer": wer_e / max(wer_n, 1), "ha_tone_cer": ha["tone_cer"], "n_ha": ha["tone_chars"],
            "aspirate_cer": asp, "n_asp": n_asp, "plain_cer": pln, "n_plain": n_pln}, pairs


def main(init, hours, seed, data_dir, epochs=40, lr=1e-3, bs=16):
    _load_dotenv()
    random.seed(seed)
    tok = os.environ["HF_TOKEN"]
    model = load_encoder(tok)
    for p in model.parameters():
        p.requires_grad = False
    train = torch.load(os.path.join(data_dir, "train.pt")); dev = torch.load(os.path.join(data_dir, "dev.pt"))
    test = torch.load(os.path.join(data_dir, "test.pt"))
    # budget: whole speakers in file order, nested
    sel, tot, last = [], 0.0, None
    for it in train:
        if tot >= hours * 3600 and it["speaker"] != last:
            break
        sel.append(it); tot += it["dur"]; last = it["speaker"]
    head, copied, nd = build_head(model, init, seed)
    print(f"init={init} hours={tot/3600:.3f} utts={len(sel)} copied {copied}/{nd} tokens", flush=True)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=0.0)
    ctc = torch.nn.CTCLoss(blank=head.out_features - 1, zero_infinity=True)
    best, best_state, hist = 1e9, None, []
    for ep in range(epochs):
        head.train(); tl = 0; nb = 0
        for items in batches(sel, bs, True):
            feats, flen, tgt, tlen = collate(model, items)
            lp = torch.log_softmax(head(feats), -1).transpose(0, 1)
            loss = ctc(lp, tgt, flen, tlen)
            opt.zero_grad(); loss.backward(); opt.step(); tl += loss.item(); nb += 1
        head.eval()
        m, _ = evaluate(model, head, dev[:300])
        hist.append({"epoch": ep, "train_loss": tl / nb, "dev_cer": m["cer"]})
        print(ep, round(tl / nb, 3), "dev300 CER", round(m["cer"], 4), flush=True)
        if m["cer"] < best:
            best = m["cer"]; best_state = {k: v.clone() for k, v in head.state_dict().items()}
    head.load_state_dict(best_state)
    res = {}
    for name, items in (("dev", dev), ("test", test)):
        res[name], pairs = evaluate(model, head, items)
        if name == "test":
            os.makedirs("results/phase1", exist_ok=True)
            rid = f"phase1-dogri-{init}-{hours}h-s{seed}"
            with open(f"results/phase1/{rid}.jsonl", "w", encoding="utf-8") as f:
                for r, h in pairs:
                    f.write(json.dumps({"ref": r, "hyp": h}, ensure_ascii=False) + "\n")
    t = res["test"]
    log_run(stage="phase1", hypothesis="H2", target="dogri", donor="hi" if init == "hindi" else None,
            init=init, budget_h=round(tot / 3600, 3), seed=seed, backbone="indicconformer_hi_frozen_encoder",
            split="speaker-disjoint test (IndicVoices valid, alternating speakers)", n_utts=len(test),
            wer=t["wer"], cer=t["cer"], tone_cer=t["ha_tone_cer"], tone_chars=t["n_ha"],
            aspirate_cer=t["aspirate_cer"], plain_cer=t["plain_cer"],
            config={"epochs": epochs, "lr": lr, "bs": bs, "trained": "ctc head columns only", "tokens_copied": copied,
                    "dev": res["dev"], "history_last": hist[-3:], "apostrophe": "dropped from text",
                    "tone_chars": "ha + virama only", "model_selection": "best dev-300 CER"},
            artifacts={"predictions": f"results/phase1/{rid}.jsonl"},
            notes="kill test arm; encoder frozen; head-only training")
    print("TEST", json.dumps(t), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
