#!/bin/bash
# Run a command inside the WSL NeMo env from the repo on D:.
#   wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/wsl_run.sh python -m tone_donor.nemo_check doi dogri 40
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib/wsl/lib:$HOME/.local/bin
source ~/warm-init/.venv-nemo/bin/activate
cd /mnt/d/warm-init
export PYTHONPATH=src PYTHONIOENCODING=utf-8
exec "$@"
