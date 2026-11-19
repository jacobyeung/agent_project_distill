W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1; du -s --block-size=1G $W | tail -1
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild24e | head -1); echo "== $d"; ls $d | tr '\n' ' '; echo; grep -c "at capacity" $d/transcript.log; tail -c 1500 $d/transcript.log | tr -cd "[:print:]\n" | grep -v "^[ +@-]" | tail -5 | cut -c1-300
ls $W/w24/out | tr '\n' ' '; echo
B=$W/w24/work/build24d; ls $B | tr '\n' ' '; echo; echo "== GO_GATES"; head -c 3000 $B/GO_GATES.json 2>/dev/null; echo
ls $W/w24/out/kit_n_go $W/w24/out/kit_n_go/k $W/w24/out/kit_n_go/b 2>/dev/null | tr '\n' ' '; echo
K=$W/w24/out/kit_n_go; echo "== job.sh"; cat $K/job.sh; echo "== j.json"; head -c 2500 $K/k/j.json; echo; echo "== o.py"; head -60 $K/b/o.py
