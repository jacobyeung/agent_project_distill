# Lane demo_lane (reviewer on trinity-3-30)

Read first, in order: section "Key Trinity Cluster Rules" of `/home/jjyeung/.claude/CLAUDE.md`, then `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. They bind and win over this brief; this brief states only what is specific to the lane.
Lane folder `/scratch/jjyeung/orch_n30/demo_lane` on trinity-3-30. Events `B/events/demo_lane`. Session limit 2026-11-16T22:30Z (UTC); rotate before it as the lane rules say.

## Budgets (inside these, act without asking)
| Budget | Value | Inside it | Above it |
|---|---|---|---|
| Lane folder | 5 GB | act without asking | QUESTION event with your default, then continue on the default |
| Free space on trinity-3-30 `/scratch` | at least 150 GB | write without asking | stop writing; BLOCKER event |
| IO class | named-reads | read the files this brief names on /home and /data*, each once, in bounded parts; nothing above 20 MB | anything beyond the class: QUESTION event with your default |
| Session | until 2026-11-16T22:30Z | work without asking | RESULT `rotate` with STATUS.md exact |

Limits: at most two ssh calls a minute into Trinity

## Role
You review once and you fix nothing. Reproduce first, then write the verdict (GO, GO_AFTER_FIXES or NO_GO) as `orchkit-verdict-v1` JSON plus a Markdown copy in the events folder; every finding names file, lines and the command that reproduces it. Then end the lane.

## Why
TODO(orchestrator): fill in.

## Do
TODO(orchestrator): fill in.

## Done when
The verdict files exist in the events folder and one RESULT event names them.
