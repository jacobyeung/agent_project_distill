# wait up to $1 s (default 580) for an alarm in watch.log or a new event/inbox file; print a short summary
L=/scratch/jjyeung/orch_n30/tree_rebuild30/work/watch.log; B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events; I=/scratch/jjyeung/orch_n30/tree_rebuild30/inbox
c() { ls $B/tree_rebuild $B/n_review $I 2>/dev/null | grep -c 'Z_'; }
n0=$(c); t=0; M=${1:-580}
until [ $t -ge $M ] || tail -5 $L | grep -q 'REFUS\|state=GONE\|hold=YES\|WAITING_REVIEW.json bytes\|Traceback\|ERROR' || [ $(c) -gt $n0 ]; do sleep 20; t=$((t+20)); done
date -u +%TZ; tail -5 $L | head -1 | cut -c1-140; tail -5 $L | grep -o 'gate=\[[^]]*\]'; tail -5 $L | grep '  j2:' | cut -c1-250
tail -1 /scratch/jjyeung/orch_n30/n_ops1/work/mon/hist.txt | grep -o '"stage":"[^"]*"\|"prep_min":[0-9]*\|"frames":[^,]*\|FLAG.*'
[ $(c) -gt $n0 ] && { echo NEW:; ls -t $B/tree_rebuild $B/n_review $I 2>/dev/null | grep 'Z_' | head -3; }
true
