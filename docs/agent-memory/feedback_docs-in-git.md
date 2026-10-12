---
name: feedback-docs-in-git
description: "Keep README, NOTES and results docs consistent and pushed to git after every milestone"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0417092b-8b87-48d0-8eba-16a358a53bf8
  modified: 2026-10-12T20:53:24.094Z
---

User said (2026-10-13): "document everything consistently and push changes", "make sure that doc is in git", "keep updating the readme properly".

**Why:** the user is away for long stretches and wants to pick the project up from the repo alone.

**How to apply:** after each milestone (new result, env change, decision, failed approach) update in the same commit: README.md status section and run commands if anything changed, NOTES.md dated entry with run ids, results tables via `uv run python -m tone_donor.report`. Check `git status` is clean and `git log origin/main..HEAD` is empty before ending a stretch of work. Never commit `.env`. Plan.md body stays as pasted; point to NOTES.md for differences.
