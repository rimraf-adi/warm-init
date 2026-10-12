#!/bin/bash
# Donor-head arms on the multilingual encoder: Punjabi (tonal, Gurmukhi, mapped), Marathi and Nepali
# (non-tonal, Devanagari), Bengali (non-tonal, Bengali script, mapped). donor-hi at 0.25 h seed 0 is a regression
# check: it must reproduce the earlier `hindi` arm (same weights, same seed).
export BACKBONE=multi
specs="donor-hi:0.25:0"
for h in 0.25 1.0; do
  for s in 0 1 2; do
    for d in pa mr ne bn; do
      specs="$specs donor-$d:$h:$s"
    done
  done
done
bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head /home/vnit/data/dogri_multi $specs 2>&1 \
  | grep --line-buffered -E "^init=|^  last|^TEST|^skip|Traceback|Error"
echo "=== donors grid done $(date +%T)"
