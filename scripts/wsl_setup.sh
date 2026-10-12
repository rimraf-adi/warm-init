#!/bin/bash
# Build the NeMo training env inside WSL (run from Windows: wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/wsl_setup.sh)
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$HOME/.local/bin
set -e
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
cd ~
[ -d warm-init ] && git -C warm-init pull -q || git clone -q https://github.com/rimraf-adi/warm-init.git
cd warm-init
git log --oneline | head -3
[ -d .venv-nemo ] || uv venv --python 3.10 .venv-nemo
source .venv-nemo/bin/activate
uv pip install --quiet "torch==2.4.1" "torchaudio==2.4.1" --index-url https://download.pytorch.org/whl/cu121
uv pip install --quiet "cython<3" "setuptools<70" wheel "numpy<2"
uv pip install --quiet --no-build-isolation youtokentome
uv pip install --quiet "nemo_toolkit[asr]==1.23.0" "huggingface_hub==0.23.5" "transformers==4.40.2" "datasets==2.19.2" soundfile python-dotenv "numpy<2" "setuptools<70"
python -c "import torch, nemo; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'nemo', nemo.__version__)"
