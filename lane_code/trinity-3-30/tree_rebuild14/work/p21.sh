W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"
cat $W/w24/out/BUILD24E_REPORT.md; echo; head -c 1500 $W/w24/out/SESSION_NAMES_24F.json; echo
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24f | head -1); ls $d | tr '\n' ' '; grep -c "at capacity" $d/transcript.log; tail -c 2000 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -4 | cut -c1-300
