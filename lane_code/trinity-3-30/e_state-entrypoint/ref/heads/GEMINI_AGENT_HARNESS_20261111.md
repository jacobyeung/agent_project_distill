# Gemini-key coding agents: harness choice, any model on the key, workflows, Antigravity CLI (2026-11-11)

Paths are on trinity-2-18. Raw results: `GEMINI_AGENT_HARNESS_20261111_results.tgz` beside this file
(runs.jsonl, SUMMARY.json, every transcript, diff and test log, the runner and the settings).

## Question

Which harness should run Gemini-key models as coding agents: `argon-agent` (Claude Code headless behind
a per-run LiteLLM proxy), Hermes Agent, Gemini CLI or Antigravity CLI? How do we run any model the key
serves, and do Claude Code workflows run on the key?

## Answer

- Keep `argon-agent` for workflows, subagents, Carbon and any work that needs the Claude tooling
  (rm_guard, skills, lanemsg hooks, the usage meter). It runs any model id on the key
  (`--model <id>`, `--list-models`), and every agent in a run uses the selected model.
- `argon-agent` compacts where Antigravity CLI does. Antigravity compacts at about 260k tokens on
  Argon and on Flash; `argon-agent --window` (100k to 1m, default 290k) makes Claude Code compact at
  about 260k as well. Under Claude Code's own 200k assumption it compacted at about 170k and lost a
  median 10 minutes on six of ten coding sessions. With the new default it compacted in none of those
  six and took the same time as Antigravity (median 30.7 against 30.1 minutes on a heavily loaded
  node).
- For located bug fixes, Argon at high thinking is the better default than Carbon at medium: both
  pass, Argon finishes sooner, uses fewer tokens and changes far less code.
- A workflow of 100 agents completes inside one `argon-agent` session on Argon and on Carbon. A Claude
  orchestrator cannot name a Gemini model for a workflow agent, so it starts that one session through
  Bash; 100 separate `argon-agent` runs would start 100 proxies.
- Antigravity CLI is a test install on trinity-2-18 only. It has no usage meter, no rm_guard, no
  lanemsg hooks and, in key mode at version 1.5.0, no Carbon.

