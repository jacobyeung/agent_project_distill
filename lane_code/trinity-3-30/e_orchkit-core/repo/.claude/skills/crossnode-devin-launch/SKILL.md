---
name: crossnode-devin-launch
description: Launch Devin (Astra max) builder sessions on other Trinity nodes through a Codex Luna ssh launcher, with in-workspace inputs, a 5-minute heartbeat, pgrep-based session discovery and no duplicate launches. Use whenever more than one or two Devin sessions are needed, when the local node is loaded, or when Claude's own ssh is denied.
---

# Cross-node Devin launch (recipe verified 2026-09-18)

## When
Any Devin build lane beyond the first one or two on the orchestrator's node, any time `uptime` shows load above the core count or more than five processes in D state, or when the harness denies Claude's `ssh`. USER 2026-09-18: Devin usage is unlimited and Devin builders run Astra max with priority service; Codex and Claude quotas are finite, so the launcher is a cheap Codex Luna (`gpt-5.6-luna`, effort high) lane.

## Rules that make Devin succeed
1. **Inputs inside the workspace.** Devin runs non-interactively (`-p`): any tool call needing confirmation is auto-rejected, and its file tools refuse paths outside `/home/jjyeung/agent_project`. Stage every input the brief names as a byte copy under `agent/scratch/devin_lanes/<lane>/inputs/` (and code copies under `work/`); tell the brief "do not read or write /data2 or /home outside the workspace". Lanes given external paths sat silent for hours; lanes given copies produced output.
2. **Heartbeat clause in every brief** (`agent/scratch/devin_lanes/_COMMON_HEADER.md`, section "Liveness heartbeat"): append a line to `out/HEARTBEAT.log` every 5 minutes from the first minute and write partial artifacts early. Silent 10 minutes = kill and relaunch; a second silence on the same task = move the brief to Codex Astra.
3. **Report file, not exit code.** `-p` lingers after its final answer; read `out/REPORT.md` (last line `DEVIN_LANE_DONE`) and terminate the CLI afterwards.
4. **Never launch a lane twice.** Discover sessions with `pgrep -af "devin -p --prompt-file agent/scratch/devin_lanes/<lane>/BRIEF.md"` on every node before launching; write `devin.pid` as `PID:<pid> HOST:<host>` from discovery.

## Launch shape
Queue file: `agent/scratch/devin_lanes/_LAUNCH_QUEUE.jsonl`, one JSON per line `{"lane","brief","timeout_s","model":"gpt-6-astra-max-priority","status":"queued"}`. Never edit lines; the launcher appends actions to its own `LAUNCHES.jsonl`.

Remote command (one plain line; the workspace is NFS-shared so any node sees the brief):
```
ssh -f -n -F /dev/null -o BatchMode=yes <node> 'cd /home/jjyeung/agent_project && setsid nohup timeout <timeout_s> /home/jjyeung/.local/bin/devin -p --prompt-file <brief> --permission-mode dangerous --respect-workspace-trust false --model gpt-6-astra-max-priority > agent/scratch/devin_lanes/<lane>/devin.out 2>&1 < /dev/null & echo "PID:$! HOST:$(hostname)" > agent/scratch/devin_lanes/<lane>/devin.pid'
```
`ssh -f` backgrounds ssh after auth. A foreground `ssh` with a short `timeout` returns 124 even though the remote session started (the login shell on a slow NFS node holds the session), so **never treat the ssh return code as the outcome**: verify by pgrep on the node after 30 s and 120 s, then by `out/HEARTBEAT.log` within 12 minutes.

## Node choice
Probe candidates (`trinity-0-3 0-18 0-23 1-13 2-13 2-28 3-18 3-23`, any reachable `trinity-*`; 2026-09-18 scan: `0-8`, `1-3`, `1-18` refused with kex errors, `2-16` does not resolve). Score by loadavg/nproc, penalize D-state > 5, require free memory > 60 GB and `/home/jjyeung/.local/bin/devin` present. At most two queued sessions per node; skip the orchestrator's node.

## Dispatch the launcher
```
bash agent/scripts/codex_dispatch.sh mech <dir> <dir>/BRIEF.md --net --model gpt-5.6-luna --effort high --label luna_devin_launcher --writable-root /home/jjyeung/agent_project/agent/scratch/devin_lanes
```
Brief template: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/codex_luna_devin_launcher_v2/BRIEF.md` (discovery first, `ssh -f -n` launch, pgrep verification, 2-minute polling for 150 minutes, `STATUS.md` with a sessions table). The orchestrator keeps its own Monitor on `agent/scratch/devin_lanes/*/out/HEARTBEAT.log` mtimes.

## Related
`memory/spread-lanes-across-nodes.md`, `memory/devin-preferred-executor.md`, `memory/builder-lanes-five-minute-heartbeat.md`, `memory/devin-internal-errors-codex-fallback.md`.

## Amendment 2026-09-18 10:20 UTC (launch defect found by the r1307 lane)
`ssh -f` does NOT work from inside a sandboxed Codex relay: `-f` backgrounds the ssh client locally, and the
sandboxed exec kills detached local children when the call returns, so the client dies before delivering the
command. Symptom: rc=0 on four nodes, yet no devin.out, no devin.pid and no remote process ever appeared (a
shell redirect creates its file the instant a command starts, so the remote shell never ran).
Use instead a FOREGROUND ssh whose remote side detaches itself, plus a launch marker written before devin:
```
ssh -n -F /dev/null -o BatchMode=yes -o ConnectTimeout=20 <node> 'cd /home/jjyeung/agent_project && \
  echo "launch $(date -u +%FT%TZ) $(hostname)" > <lane>/launch_marker.txt && \
  setsid nohup timeout <s> /home/jjyeung/.local/bin/devin -p --prompt-file <brief> \
    --permission-mode dangerous --respect-workspace-trust false --model gpt-6-astra-max-priority \
    > <lane>/devin.out 2>&1 < /dev/null & echo "PID:$! HOST:$(hostname)" > <lane>/devin.pid'
```
The remote shell exits on its own once the process is detached. Verify with pgrep on the node at 30 s and
120 s as before; the marker distinguishes "remote shell never ran" from "devin started and failed".
Rule set confirmed by both orchestrators (10:25 UTC): foreground ssh with a ~90 s `timeout`; rc=124 means "the
slow NFS login shell held the session", NOT failure: verify by launch_marker.txt + pgrep; never `-f` from a sandbox.
