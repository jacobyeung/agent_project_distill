W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; P=$W/work/conf21c/pkg/work/build21
sed -n '1,200p' $P/OPERATOR.md | cut -c1-400; ls $P/kits/q $P/kits/q/b; head -30 $P/kits/q/job.sh
bash /dev/stdin <<'EOP'
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr12; ls $W/w21/out | grep -E 'b21d|21D'
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild21d | head -1); stat -c '%s' $d/transcript.log; grep -c "at capacity" $d/transcript.log; ls $d | tr '\n' ' '
EOP
