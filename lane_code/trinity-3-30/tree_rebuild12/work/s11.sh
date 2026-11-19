W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21/pkg
ls $W/w21/work | tr '\n' ' '; echo
for d in $(ls $W/w21/work); do [ -e $C/work/$d ] || ln -s $W/w21/work/$d $C/work/$d; done
ls -la $C/work | head -40 | awk '{print $9,$10,$11}' | tr '\n' ';'; echo
mkdir -p $W/work/conf21/r3; sed -e 's/ff2_/r3\/ff3_/g' -e 's/conf21_/conf21r3_/g' $W/work/conf21/ff2.sh > $W/work/conf21/ff3.sh; head -2 $W/work/conf21/ff3.sh | cut -c1-200
tmux new -d -s tr12_ff3 "bash $W/work/conf21/ff3.sh"; tail -2 $W/work/review21_dispatch.log; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_rev21 | head -1); stat -c '%s %y' $d/transcript.log
