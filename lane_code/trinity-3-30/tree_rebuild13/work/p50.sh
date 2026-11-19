W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; M=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/ops_mirror
for f in tree_rebuild_b24c_22859833.tar tree_rebuild_b24d_7babb413.tar; do test -e $M/tr13_$f || { nice -n 10 rsync --bwlimit=4000 $W/w24/out/$f $M/tr13_$f && sha256sum $M/tr13_$f | cut -c1-16; }; sleep 2; done
