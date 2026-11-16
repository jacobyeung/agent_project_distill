# agent_project_distill — CLAUDE.md
@AGENTS.md

## Orchestrator only

Subagents and lanes can skip this section; the rules above cover their work.

- At session start, read the newest `docs/DISTILLATION_HANDOFF_*.md` (the UTC stamp in the name orders them). Older handoffs and `docs/DISTILLATION_SUCCESSOR_BOOTSTRAP.md` are history: search them when a task needs a specific fact, and never read them end to end.
- Operating rules (user): always autonomous; never wait for permission to restart, launch or ramp. Devin builders run `gpt-6-astra-max-priority` with inputs staged inside the workspace and a 5-minute heartbeat (`agent/scratch/devin_lanes/_COMMON_HEADER.md`). Two silent Devin attempts move a task to Codex Astra (`--effort high`; `xhigh` only for design or gate review, never max). Spread lanes across nodes (skill `crossnode-devin-launch`).
- Every lane message that reaches you starts a turn over your whole context. Brief lanes to message only for questions, blockers and final results; the watchdog already reports lane state changes.
- Until 2026-11-01, run every lane on Devin: surveys, scans, monitoring, the Git owner, reviews, builds and fixes (user, 2026-10-21). Devin serves the best models at max effort: `claude-opus-5-5-max` for judgement and error analysis, `gpt-6-astra-max-priority` for builds, fixes and reviews, and `claude-fable-5-1-max` as an alternative. Claude subagents remain allowed, but choose Devin whenever it can do the work.
- Skills in `.claude/skills/` are copies from the main repository. `agent/scripts/codex_dispatch.sh` writes receipts under `agent/scratch/codex_runs/` of this repository.
- Pending code change for the next epoch: make the supervisor's package path (`PKG` in `tools/recover_boundary_remediation.py`) configurable so production launches from the epoch checkout instead of the working tree.
