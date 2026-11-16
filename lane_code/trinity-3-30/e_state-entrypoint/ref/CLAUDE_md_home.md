# agent_project_distill — CLAUDE.md
@AGENTS.md

## Orchestrator only

Subagents and lanes can skip this section; the rules above cover their work.

- At session start, read the newest `docs/DISTILLATION_HANDOFF_*.md` (the UTC stamp in the name orders them). Older handoffs and `docs/DISTILLATION_SUCCESSOR_BOOTSTRAP.md` are history: search them when a task needs a specific fact, and never read them end to end.
- Operating rules (user): always autonomous; never wait for permission to restart, launch or ramp. Spread lanes across nodes.
- Every lane message that reaches you starts a turn over your whole context. Brief lanes to message only for questions, blockers and final results; the watchdog already reports lane state changes.
- Codex is the default executor for every lane it can do: builds, fixes, reviews, surveys, copies, babysitting and analysis (user, 2026-11-05). Dispatch with `agent/scripts/codex_dispatch.sh`: `implement` (GPT-6.1 Sol, high), `review` (GPT-6 Astra, high, read-only), `mech` (GPT-6.1 Terra); use Astra for hard builds or gate reviews, never max effort. Claude Opus subagents take critical debugging. Argon, Devin and Cursor are fallbacks when Codex is down.
- Skills in `.claude/skills/` are copies from the main repository. `agent/scripts/codex_dispatch.sh` writes receipts under `agent/scratch/codex_runs/` of this repository.
- Pending code change for the next epoch: make the supervisor's package path (`PKG` in `tools/recover_boundary_remediation.py`) configurable so production launches from the epoch checkout instead of the working tree.
