import os
from huggingface_hub import hf_hub_download
import nemo.collections.asr as nemo_asr
from tone_donor.vaani_stream import _load_dotenv
_load_dotenv()
p = hf_hub_download("ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large", "indicconformer_stt_hi_hybrid_rnnt_large.nemo", token=os.environ["HF_TOKEN"])
m = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(p, map_location="cpu")
tk = m.tokenizer
for lg in ("hi", "doi"):
    t = tk.tokenizers_dict[lg]
    print("TOK", lg, type(t).__name__, [a for a in dir(t) if not a.startswith("_")][:25])
    print("TOK", lg, "vocab", type(t.vocab), len(t.vocab), list(t.vocab)[:6] if not isinstance(t.vocab, dict) else list(t.vocab.items())[:6])
masks = m.ctc_decoder.language_masks
print("TOK masks type", type(masks), len(masks["doi"]), sum(masks["doi"]), sum(masks["hi"]), masks["doi"][-1], masks["hi"][-1])
print("TOK conv", m.ctc_decoder.decoder_layers[0].weight.shape)
print("TOK offsets", tk.token_id_offset if hasattr(tk, "token_id_offset") else None)
