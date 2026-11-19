W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; cat $W/work/up24k.sha; sha256sum $W/w24/out/jr.sh
for k in q n; do echo "$k $(wc -l < $W/w24/work/build24k/kits/$k/SHA256SUMS.txt 2>/dev/null)"; done; ls $W/w24/work/build24k/ | grep -i kit
tmux ls | grep tr15; d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild24kr | head -1); grep -c "at capacity" $d/transcript.log; tail -c 600 $d/transcript.log | tr -cd "[:print:]\n" | tail -3 | cut -c1-250
