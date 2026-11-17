# Removal candidates (review_tree9; the user deletes, agents never do)
- /scratch/jjyeung/orch_n30/review_tree9/mut/ — 13 mutant tree copies, about 13 MB each.
- /scratch/jjyeung/orch_n30/review_tree9/suite_fail1 and suite_fail2 — logs from two harness runs that failed on path policy.
- /scratch/jjyeung/orch_n30/review_tree9/b8, tree_rebuild_b9_eca323a0.tar and lane/ — review copies; delete them once the verdict is accepted.
- The rm_guard hook queued two commands from this lane in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md. One is a recursive delete of review_tree9/suite; the other is a false match on an event-writing command. Neither is needed; drop both.
