#!/bin/bash
# Is the copied blank column responsible for the tone-character penalty? Same donors, blank left random.
export BACKBONE=multi
specs=""
for s in 0 1 2; do
  for d in hi pa; do
    specs="$specs donor-$d+noblank:0.25:$s donor-$d+comp+noblank:0.25:$s"
  done
done
bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head /home/vnit/data/dogri_multi $specs 2>&1 \
  | grep --line-buffered -E "^init=|^  last|^TEST|^skip|Traceback|Error"
echo "=== blank grid done $(date +%T)"
