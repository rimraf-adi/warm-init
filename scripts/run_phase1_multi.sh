#!/bin/bash
# Phase 1 head-only grid on the multilingual encoder (BACKBONE=multi). Skips configs already logged.
# "own" = the model's own trained Dogri head, evaluated without training (budget label is nominal).
export BACKBONE=multi
specs="own:5.0:0"
for h in 0.25 1.0 5.0; do
  for s in 0 1 2; do
    for i in random hindi; do
      specs="$specs $i:$h:$s"
    done
  done
done
bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head /home/vnit/data/dogri_multi $specs 2>&1 \
  | grep --line-buffered -E "^init=|^  last|^TEST|^skip|Traceback|Error"
echo "=== multi grid done $(date +%T)"
