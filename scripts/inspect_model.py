import os, sys
from huggingface_hub import hf_hub_download
import nemo.collections.asr as nemo_asr
from tone_donor.vaani_stream import _load_dotenv
_load_dotenv()
p = hf_hub_download("ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large", "indicconformer_stt_hi_hybrid_rnnt_large.nemo", token=os.environ["HF_TOKEN"])
m = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(p, map_location="cpu")
tk = m.tokenizer
print("tokenizer type", type(tk).__name__, "vocab", tk.vocab_size)
print("tokenizer attrs", [a for a in dir(tk) if not a.startswith("_")][:30])
for s in ["ह्", "'", "ओह्", "जेह्ड़ा", "उं'दे", "ʼ"]:
    ids = tk.text_to_ids(s, "hi") if "lang" in tk.text_to_ids.__code__.co_varnames else tk.text_to_ids(s)
    print(repr(s), ids, tk.ids_to_text(ids) if "lang" not in tk.ids_to_text.__code__.co_varnames else tk.ids_to_text(ids, "hi"))
print("encoder params(M)", round(sum(x.numel() for x in m.encoder.parameters())/1e6,1))
print("ctc decoder:", m.ctc_decoder)
print("decoder (rnnt pred):", type(m.decoder).__name__, "joint:", type(m.joint).__name__)
print("cfg keys:", list(m.cfg.keys()))
print("tokenizer cfg:", m.cfg.tokenizer)
print("decoder cfg vocab/num_classes:", m.cfg.decoder.get("vocab_size"), m.cfg.get("aux_ctc", {}).get("decoder", {}).get("num_classes"))
