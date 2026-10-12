#!/bin/bash
# Phase 1 kill-test grid, sequential: budgets ascending, both arms, 3 seeds.
# Run: wsl -d Ubuntu-22.04 -- bash /mnt/d/warm-init/scripts/run_phase1.sh
for h in 0.25 1.0 5.0; do
  for s in 0 1 2; do
    for init in random hindi; do
      echo "=== $init ${h}h seed $s $(date +%T)"
      bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head $init $h $s /home/vnit/data/dogri 2>&1 \
        | grep -E "^init=|^TEST|Traceback|Error"
    done
  done
done
echo "=== grid done $(date +%T)"
