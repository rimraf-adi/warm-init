"""Dump the per-language tokenizer pieces of the multilingual model to data/vocab_pieces.json (run in the WSL env)."""
import json
import os

from huggingface_hub import hf_hub_download

import nemo.collections.asr as nemo_asr
from tone_donor.vaani_stream import _load_dotenv

_load_dotenv()
p = hf_hub_download("ai4bharat/IndicConformer", "IndicConformer.nemo", token=os.environ["HF_TOKEN"])
m = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(p, map_location="cpu")
out = {lang: list(t.vocab) for lang, t in m.tokenizer.tokenizers_dict.items()}
os.makedirs("data", exist_ok=True)
json.dump(out, open("data/vocab_pieces.json", "w", encoding="utf-8"), ensure_ascii=False)
print("DONE", len(out), "languages", {k: len(v) for k, v in list(out.items())[:3]})
