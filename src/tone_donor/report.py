"""Rebuild results/RESULTS.md from results/runs.jsonl. Run: uv run python -m tone_donor.report"""
from collections import defaultdict
from pathlib import Path

from tone_donor.runlog import read_runs


def f(x, p=3):
    return "" if x is None else (f"{x:.{p}f}" if isinstance(x, float) else str(x))


def main():
    runs = read_runs()
    out = ["# Results", "", "Generated from `results/runs.jsonl`; do not edit by hand.",
           f"Runs logged: {len(runs)}", ""]
    by_stage = defaultdict(list)
    for r in runs:
        by_stage[r["stage"]].append(r)
    for stage, rs in sorted(by_stage.items()):
        out += [f"## Stage: {stage}", "",
                "| run | target | donor | init | budget h | seed | WER | CER | tone CER | tone chars | CI | utts | status | commit |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: (r["target"], r["init"] or "", r["budget_h"] or 0, r["seed"] or 0)):
            ci = f"[{f(r['ci_low'])}, {f(r['ci_high'])}]" if r.get("ci_low") is not None else ""
            commit = (r["git_commit"] or "") + ("*" if r.get("git_dirty") else "")
            out.append("| " + " | ".join([r["run_id"], r["target"], r.get("donor") or "", r["init"],
                       f(r.get("budget_h")), f(r.get("seed")), f(r.get("wer")), f(r.get("cer")),
                       f(r.get("tone_cer")), f(r.get("tone_chars")), ci, f(r.get("n_utts")),
                       r["status"], commit]) + " |")
        out.append("")
    out += ["`*` after a commit means the working tree had uncommitted changes when the run started.", ""]
    Path("results/RESULTS.md").write_text("\n".join(out), encoding="utf-8")
    print("wrote results/RESULTS.md,", len(runs), "runs")


if __name__ == "__main__":
    main()
