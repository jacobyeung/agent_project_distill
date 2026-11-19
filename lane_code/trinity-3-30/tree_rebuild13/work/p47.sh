cat /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/up24c.sha
{ date -u +%TZ; tmux ls | grep tr13; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_rev24c | head -1); cat $d/final_message.md 2>/dev/null || echo REVIEW_RUNNING; } >&2
