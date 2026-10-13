#!/bin/bash
# v2 pipeline on the multilingual encoder: features from manifests, then the confirmatory head-only grid.
# Arms first block: random, donor-hi, donor-pa, donor-mr; second block: +noblank and +comp variants for hi and pa.
# 3 budgets x 5 seeds each; every (budget, seed) draws different random training speakers. Skips logged configs.
export BACKBONE=multi
D=/home/vnit/data/dogri_multi_v2
if [ ! -f $D/test.pt ] || [ ! -f $D/train.pt ]; then
  bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.prep_from_manifest dogri v2 $D 2>&1 | grep -E "^dev|^test|^train|Error|Traceback"
fi
specs=""
for arms in "random donor-hi donor-pa donor-mr" "donor-hi+noblank donor-pa+noblank donor-hi+comp donor-pa+comp"; do
  for h in 0.25 1.0 5.0; do
    for s in 0 1 2 3 4; do
      for a in $arms; do
        specs="$specs $a:$h:$s"
      done
    done
  done
done
bash /mnt/d/warm-init/scripts/wsl_run_ai4b.sh python -m tone_donor.train_head_v2 $D $specs 2>&1 \
  | grep --line-buffered -E "^init=|^  best|^TEST|^skip|Traceback|Error"
echo "=== v2 grid done $(date +%T)"
