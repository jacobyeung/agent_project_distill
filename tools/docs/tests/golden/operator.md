# Lane demo_lane (operator on trinity-3-30)

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
You operate the run named under Do: watch it, act only on a GO file that names the job and the action, and write an event only for a state change, a question, a blocker or a result. A verdict that a registered rule produces goes to the orchestrator in a RESULT before anyone acts on it.

## Why
TODO(orchestrator): fill in.

## Do
TODO(orchestrator): fill in.

## Done when
The run has ended and its RESULT event names the job id, the final state and the outputs; or your session limit is near and the RESULT `rotate` and STATUS.md let a successor resume.
