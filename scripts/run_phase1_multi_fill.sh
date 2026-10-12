#!/bin/bash
# Fill strategies for tokens the donor does not have (tests the token-coverage explanation).
# Donors: hi (non-tonal, same script) and pa (tonal, other script). Fills: mean row, composition from characters.
export BACKBONE=multi
specs=""
for h in 0.25 1.0; do
  for s in 0 1 2; do
    for d in hi pa; do
      for f in mean comp; do
        specs="$specs donor-$d+$f:$h:$s"
      done
    done
  done
done
bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head /home/vnit/data/dogri_multi $specs 2>&1 \
  | grep --line-buffered -E "^init=|^  last|^TEST|^skip|Traceback|Error"
echo "=== fill grid done $(date +%T)"
