W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_qd; date -u +%TZ; grep -n "h/k\|'h'\|\"h\"\|0\.json\|<stdin>\|python3 -\b\|python3 -B -I -s -$\|- <<" $K/b/*.sh $K/b/x.py $K/job.sh 2>/dev/null | head -30 | cut -c1-250
echo ===; grep -ln "0.json" $K/b/* | head; grep -n "0.json" $K/b/*.py | head -10 | cut -c1-250
echo === jrw; cat $W/w24/out/jr.sh | head -3; ls $W/w24/work/build24m2d/ | head -30
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*_tree_rebuild24m3 | head -1); tail -c 300 $d/transcript.log | tr -cd "[:print:]\n" | tail -2 | cut -c1-200
