W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls 2>&1 | grep -E "tr1[34]"
cat $W/w24/work/build24f/go_rehearsal.sh | head -40
grep -n -E "boot_hx\s*=|boot_hx=" $W/w24/out/kit_n_go/b/z.py </dev/null | head -5 | cut -c1-250
grep -n "sess.json" $W/w24/out/kit_n_go/b/*.sh $W/w24/out/kit_n_go/b/*.py </dev/null | head -5 | cut -c1-200
