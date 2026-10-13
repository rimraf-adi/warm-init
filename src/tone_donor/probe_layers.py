"""H1: layer-wise linear probes for the Dogri tone-mark token across different encoders.

For each encoder (monolingual donors and the multilingual model) the same Dogri utterances are run and the hidden
state of every Conformer block is taken at the frame where a CTC forced alignment (from the monolingual Dogri
model) places each reference token. A linear probe predicts whether the token is a tone-mark token (a Dogri
tokenizer piece containing ha+virama) versus any other token; a control probe predicts a frequency-comparable
non-tone class (pieces containing PA). Train and test tokens come from different speakers (manifest splits).

    python -m tone_donor.probe_layers doi hi pa mr ne bn multi
Writes results/phase2/probe_layers.json. Run in the WSL AI4Bharat env.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

import nemo.collections.asr as nemo_asr
from tone_donor.text import normalize
from tone_donor.vaani_stream import _load_dotenv

LANG = "doi"
TRAIN_HOURS, TEST_HOURS = 1.5, 1.0


def load_model(code, tok):
    if code == "multi":
        p = hf_hub_download("ai4bharat/IndicConformer", "IndicConformer.nemo", token=tok)
    else:
        p = hf_hub_download(f"ai4bharat/indicconformer_stt_{code}_hybrid_ctc_rnnt_large",
                            f"indicconformer_stt_{code}_hybrid_rnnt_large.nemo", token=tok)
    return nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(p, map_location="cuda").eval()


def read_split(name, hours):
    rows, tot = [], 0.0
    for line in open(f"data/manifests/indicvoices_dogri_{name}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        rows.append(r)
        tot += r["audio_s"]
        if tot >= hours * 3600:
            break
    return rows


def wavs(rows):
    return [torch.from_numpy(sf.read(f"data/{r['audio']}", dtype="float32")[0]) for r in rows]


@torch.no_grad()
def enc_forward(model, wav_list, collect):
    lens = torch.tensor([len(w) for w in wav_list], device="cuda")
    x = torch.nn.utils.rnn.pad_sequence(wav_list, batch_first=True).cuda()
    feats, flen = model.preprocessor(input_signal=x, length=lens)
    store = []
    hooks = []
    if collect:
        for layer in model.encoder.layers:
            hooks.append(layer.register_forward_hook(lambda m, i, o: store.append(o[0] if isinstance(o, tuple) else o)))
    enc, elen = model.encoder(audio_signal=feats, length=flen)
    for h in hooks:
        h.remove()
    return enc, elen, store


@torch.no_grad()
def align_tokens(model, rows, wav_list, bs=8):
    """Frame index of each reference token (first frame of its CTC run) from the Dogri model."""
    import torchaudio.functional as AF
    out = []
    blank = None
    for i in range(0, len(rows), bs):
        chunk = wav_list[i:i + bs]
        enc, elen, _ = enc_forward(model, chunk, False)
        lp = model.ctc_decoder(encoder_output=enc, language_ids=[LANG] * enc.shape[0])
        blank = lp.shape[-1] - 1
        for k in range(len(chunk)):
            r = rows[i + k]
            ids = model.tokenizer.text_to_ids(normalize(r["text"], drop_apos=True), LANG)
            T = int(elen[k])
            if len(ids) == 0 or len(ids) > T:
                out.append(None)
                continue
            try:
                al, _ = AF.forced_align(lp[k:k + 1, :T].float().cpu(), torch.tensor([ids], dtype=torch.int32), blank=blank)
            except Exception:
                out.append(None)
                continue
            al = al[0].tolist()
            frames, prev = [], blank
            for t, a in enumerate(al):
                if a != blank and (a != prev):
                    frames.append(t)
                prev = a
            out.append((ids, frames) if len(frames) == len(ids) else None)
    return out


def tone_ids_and_control(model):
    vocab = list(model.tokenizer.tokenizers_dict[LANG].vocab)
    tone = {i for i, p in enumerate(vocab) if "ह्" in p}
    ctrl = {i for i, p in enumerate(vocab) if "प" in p and "ह" not in p}
    return tone, ctrl


def extract(model, wav_list, aligned, bs=8):
    """Per-layer features at token frames: returns list over layers of [N, D] float arrays, plus token ids."""
    layers = None
    ids_all = []
    for i in range(0, len(wav_list), bs):
        chunk = wav_list[i:i + bs]
        enc, elen, store = enc_forward(model, chunk, True)
        if layers is None:
            layers = [[] for _ in range(len(store))]
        for k in range(len(chunk)):
            a = aligned[i + k]
            if a is None:
                continue
            ids, frames = a
            fr = torch.tensor(frames, device="cuda")
            for li, h in enumerate(store):
                layers[li].append(h[k, fr].float().cpu().numpy())
            ids_all.extend(ids)
    return [np.concatenate(l) for l in layers], np.array(ids_all)


def probe(Xtr, ytr, Xte, yte):
    if ytr.sum() < 20 or yte.sum() < 20:
        return None
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=300, C=0.5, class_weight="balanced")
    clf.fit(sc.transform(Xtr), ytr)
    return float(roc_auc_score(yte, clf.decision_function(sc.transform(Xte))))


def main(codes):
    _load_dotenv()
    tok = os.environ["HF_TOKEN"]
    tr_rows, te_rows = read_split("train", TRAIN_HOURS), read_split("test", TEST_HOURS)
    tr_w, te_w = wavs(tr_rows), wavs(te_rows)
    ref = load_model("doi", tok)
    tone, ctrl = tone_ids_and_control(ref)
    print("tone pieces", len(tone), "control pieces", len(ctrl), flush=True)
    tr_al, te_al = align_tokens(ref, tr_rows, tr_w), align_tokens(ref, te_rows, te_w)
    print("aligned utts", sum(a is not None for a in tr_al), "/", len(tr_al), "train;",
          sum(a is not None for a in te_al), "/", len(te_al), "test", flush=True)
    del ref
    torch.cuda.empty_cache()
    res = {}
    os.makedirs("results/phase2", exist_ok=True)
    for code in codes:
        model = load_model(code, tok)
        Xtr, itr = extract(model, tr_w, tr_al)
        Xte, ite = extract(model, te_w, te_al)
        row = {"tone_tokens_train": int(np.isin(itr, list(tone)).sum()), "tone_tokens_test": int(np.isin(ite, list(tone)).sum()),
               "n_train": len(itr), "n_test": len(ite), "layers": []}
        for li in range(len(Xtr)):
            a = probe(Xtr[li], np.isin(itr, list(tone)).astype(int), Xte[li], np.isin(ite, list(tone)).astype(int))
            c = probe(Xtr[li], np.isin(itr, list(ctrl)).astype(int), Xte[li], np.isin(ite, list(ctrl)).astype(int))
            row["layers"].append({"layer": li + 1, "auc_tone": a, "auc_control": c})
        res[code] = row
        print(code, "AUC tone by layer:", [round(l["auc_tone"], 3) if l["auc_tone"] else None for l in row["layers"]], flush=True)
        json.dump(res, open("results/phase2/probe_layers.json", "w"), indent=1)
        del model, Xtr, Xte
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main(sys.argv[1:])
