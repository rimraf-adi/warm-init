#!/bin/bash
# Phase 1 kill-test grid (one process, sequential). Skips configs already logged.
specs=""
for h in 0.25 1.0 5.0; do
  for s in 0 1 2; do
    for i in random hindi; do
      specs="$specs $i:$h:$s"
    done
  done
done
bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head /home/vnit/data/dogri $specs 2>&1 \
  | grep -E "^init=|^  last|^TEST|^skip|Traceback|Error"
echo "=== grid done $(date +%T)"
