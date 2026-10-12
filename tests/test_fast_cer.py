"""The C edit distance used for per-epoch model selection must equal the full metric's edit count.
Run in the WSL env (editdistance is installed there): bash scripts/wsl_run_ai4b.sh python tests/test_fast_cer.py"""
import random

import editdistance

from tone_donor.text import cer_stats

random.seed(1)
alphabet = "कखगघहाि्ऐ "
for _ in range(500):
    r = "".join(random.choice(alphabet) for _ in range(random.randint(1, 80)))
    h = "".join(random.choice(alphabet) for _ in range(random.randint(0, 80)))
    assert cer_stats(r, h)[0] == editdistance.eval(r, h), (r, h)
print("fast CER matches full metric on 500 random pairs")
