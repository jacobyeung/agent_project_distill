T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1; cd $T
grep -n "proof_mode\|export_only\|export-only\|weights\|def verify\|def scope" student_pilot/r1_persisted.py | head -30 | cut -c1-200
grep -n "milestone\|600\|400" launch_r1/entry.py | head -20 | cut -c1-200
ls launch_r1 | tr '\n' ' '
echo; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild23 | head -1); echo $d; stat -c %s $d/transcript.log; grep -c "at capacity" $d/transcript.log
