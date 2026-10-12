---
name: feedback-caveman-skill
description: User asked to install and use the caveman terse-reply skill; installed at user level
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0417092b-8b87-48d0-8eba-16a358a53bf8
  modified: 2026-10-12T17:55:44.375Z
---

User asked (2026-10-12) to install and use the caveman skill from skills.sh (repo juliusbrussee/caveman). Installed only the SKILL.md text at `~/.claude/skills/caveman/SKILL.md` after reading it. Did not install the npm CLI (it sends telemetry) or the proxy.

**Why:** user wants shorter chat replies and told me to pull useful skills from skills.sh for my own benefit.

**How to apply:** keep chat replies terse: answer first, no filler, never drop not/never/no/only, code and paths verbatim. Switch off only on "stop caveman" or "normal mode". Plain prose for commits, docs, memory files, plan files, security warnings, irreversible actions and questions to the user. Read any other third-party skill before installing; classifier blocks `git clone` of it, so fetch single SKILL.md files as text.
