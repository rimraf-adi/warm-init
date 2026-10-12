---
name: project-design-direction
description: "User's design direction: multilingual backbone for inference, monolingual models as init donors, focus on language families"
metadata:
  node_type: memory
  type: project
  originSessionId: 0417092b-8b87-48d0-8eba-16a358a53bf8
  modified: 2026-10-12T20:46:58.680Z
---

User said (2026-10-13): use the multilingual IndicConformer as the backbone ("we need advantage of multiple languages"). Monolingual models may be used to extract init weights for a language. The research focus is language families helping initialisation AND inference, so inference needs the multilingual model. Adapters in the encoder make sense (user agreed).

**Why:** the single-language `hi` checkpoint cannot test family effects at inference. Head-only runs on that encoder are only a baseline.

**How to apply:** build experiments on the multilingual model (candidate: `ai4bharat/IndicConformer`, 2.5 GB NeMo file, openly readable with the project token; the `indic-conformer-600m-multilingual` repo is ONNX only). Use per-language checkpoints (gated except `hi`; account owner must accept terms) or the multilingual model's own heads as donors. Report claims per backbone and never describe `hi`-checkpoint results as multilingual results.

Data decisions (2026-10-13): always download and use data locally, up to 50 GB total; do not guess data fields, keep split manifests in git. Skip VAANI for now (revisit for SSL-based learning). After the Dogri splits finish downloading, restart the stopped head-only grid myself (`scripts/run_phase1.sh`, it skips logged runs).
