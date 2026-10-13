"""Print the AI4Bharat NeMo fork's ConformerEncoder forward and ConformerLayer forward (source only, no weights)."""
import inspect

from nemo.collections.asr.modules.conformer_encoder import ConformerEncoder
from nemo.collections.asr.parts.submodules.conformer_modules import ConformerLayer

print("SRC ===== ConformerEncoder.forward_internal")
print(inspect.getsource(ConformerEncoder.forward_internal))
print("SRC ===== ConformerEncoder._create_masks")
print(inspect.getsource(ConformerEncoder._create_masks))
print("SRC ===== ConformerLayer.forward")
print(inspect.getsource(ConformerLayer.forward))
