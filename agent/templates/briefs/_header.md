# Lane $lane ($role_title on $node)$title_suffix

Read first, in order: section "Key Trinity Cluster Rules" of `/home/jjyeung/.claude/CLAUDE.md`, then `$lane_rules`$extra_rules. They bind and win over this brief; this brief states only what is specific to the lane.
Lane folder `$lane_dir` on $node. Events `$events`. Session limit $limit (UTC); rotate before it as the lane rules say.

## Budgets (inside these, act without asking)
| Budget | Value | Inside it | Above it |
|---|---|---|---|
| Lane folder | $cap_gb GB | act without asking | QUESTION event with your default, then continue on the default |
| Free space on $node `/scratch` | at least $scratch_floor_gb GB | write without asking | stop writing; BLOCKER event |
| IO class | $io_class | $io_meaning | anything beyond the class: QUESTION event with your default |
| Session | until $limit | work without asking | RESULT `rotate` with STATUS.md exact |

Limits: $limits_text
