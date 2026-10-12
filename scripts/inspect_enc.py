import os, inspect
from huggingface_hub import hf_hub_download
import nemo.collections.asr as nemo_asr
from tone_donor.vaani_stream import _load_dotenv
_load_dotenv()
p = hf_hub_download("ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large", "indicconformer_stt_hi_hybrid_rnnt_large.nemo", token=os.environ["HF_TOKEN"])
m = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(p, map_location="cpu")
e = m.encoder
print("ENC type", type(e).__name__, "n layers", len(e.layers), "d_model", e.d_model if hasattr(e, "d_model") else None)
print("ENC layer0 sig", inspect.signature(e.layers[0].forward))
print("ENC layer0 children", [n for n, _ in e.layers[0].named_children()])
print("ENC layer0 params(M)", round(sum(x.numel() for x in e.layers[0].parameters()) / 1e6, 2))
src = inspect.getsource(type(e).forward_internal)
print("ENC forward_internal:\n" + src[:3500])
print("ENC has adapter api", hasattr(e, "add_adapter"), "self_attention_model", e.self_attention_model if hasattr(e, "self_attention_model") else None)
