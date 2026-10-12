---
name: feedback-git-identity-and-commits
description: "Git identity, commit style and push target for the warm-init project"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0417092b-8b87-48d0-8eba-16a358a53bf8
  modified: 2026-10-12T17:52:57.498Z
---

Commit and push as `rimraf-adi` <kinjawadekaradi112@gmail.com> to https://github.com/rimraf-adi/warm-init.git (branch main). Never as Claude, and no Co-Authored-By or "Generated with" trailers.

Commit messages: short, plain, human-written, one line. No long bodies.

**Why:** the user said "not claude" and "easy commit msgs, dont complicate them". Their instruction overrides the default attribution reminder.

**How to apply:** run `git config user.name/user.email` locally (already set in D:\warm-init), commit small and often, push after each stage. Never commit `.env` or the HF token.
