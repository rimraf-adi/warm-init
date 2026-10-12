#!/bin/bash
# Second venv with the AI4Bharat NeMo fork (branch nemo-v2), needed to load IndicConformer .nemo files.
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib/wsl/lib:$HOME/.local/bin
set -e
cd ~/warm-init
[ -d .venv-ai4b ] || uv venv --python 3.10 .venv-ai4b
source .venv-ai4b/bin/activate
uv pip install --quiet "torch==2.4.1" "torchaudio==2.4.1" --index-url https://download.pytorch.org/whl/cu121
uv pip install --quiet "cython<3" "setuptools<70" wheel "numpy<2"
uv pip install --quiet --no-build-isolation youtokentome
uv pip install --quiet "nemo_toolkit[asr] @ git+https://github.com/AI4Bharat/NeMo.git@nemo-v2" "huggingface_hub==0.23.5" "transformers==4.40.2" "datasets==2.19.2" soundfile python-dotenv "numpy<2" "setuptools<70"
python -c "import torch, nemo; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'nemo', nemo.__version__, nemo.__file__)"
